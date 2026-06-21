# 小红书收藏清单采集器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在用户已登录的小红书收藏页中自动滚动并导出不含凭据的笔记来源清单。

**Architecture:** `tools/xhs_collect_favorites.js` 是可直接粘贴到 Edge DevTools Snippets 的浏览器脚本。脚本暴露纯函数供 Node 内置测试调用，并在显式调用 `run()` 时扫描可见笔记链接、自动滚动直到稳定、下载 JSON 清单。采集数据存入被 Git 忽略的 `data/xhs/`，导入、转写和取消收藏留给后续独立子项目。

**Tech Stack:** 浏览器原生 DOM API、Node.js 内置测试运行器、MkDocs、Python 项目环境 `uv`。

---

## 文件结构

- 创建：`tools/xhs_collect_favorites.js`。提供链接规范化、记录合并、页面扫描、自动滚动和 JSON 下载。
- 创建：`tests/xhs_collect_favorites.test.mjs`。用 Node 内置测试验证不依赖浏览器 DOM 的链接和去重逻辑。
- 创建：`tools/README.md`。说明在 Edge DevTools Snippets 中运行脚本及产物处理方式。
- 创建：`data/xhs/.gitkeep`。保留本地采集数据目录。
- 修改：`.gitignore`。忽略采集到的 JSON，保留目录标记文件。

### Task 1: 为可测试的采集核心建立失败测试

**Files:**
- Create: `tests/xhs_collect_favorites.test.mjs`
- Create: `tools/xhs_collect_favorites.js`

- [ ] **Step 1: 写入链接规范化和记录合并的失败测试**

```js
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

async function loadCollector() {
  const source = await readFile(new URL("../tools/xhs_collect_favorites.js", import.meta.url), "utf8");
  const context = { URL };
  context.globalThis = context;
  vm.runInNewContext(source, context, { filename: "xhs_collect_favorites.js" });
  return context.XhsFavoritesCollector;
}

test("规范化笔记链接并丢弃无关地址", async () => {
  const collector = await loadCollector();

  assert.equal(
    collector.normalizeNoteUrl("https://www.xiaohongshu.com/explore/abc123?xsec_token=secret#comment"),
    "https://www.xiaohongshu.com/explore/abc123",
  );
  assert.equal(collector.normalizeNoteUrl("https://www.xiaohongshu.com/user/profile/123"), null);
  assert.equal(collector.normalizeNoteUrl("https://example.com/explore/abc123"), null);
});

test("按来源链接去重并用新记录补全缺失字段", async () => {
  const collector = await loadCollector();
  const merged = collector.mergeRecords([
    {
      source_url: "https://www.xiaohongshu.com/explore/abc123",
      title: "红烧肉",
      author: "",
      media_type: "unknown",
    },
    {
      source_url: "https://www.xiaohongshu.com/explore/abc123",
      title: "",
      author: "厨房小王",
      media_type: "video",
    },
  ]);

  assert.deepEqual(merged, [
    {
      source_url: "https://www.xiaohongshu.com/explore/abc123",
      title: "红烧肉",
      author: "厨房小王",
      media_type: "video",
    },
  ]);
});
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `node --test tests/xhs_collect_favorites.test.mjs`

Expected: FAIL，错误指向缺少 `tools/xhs_collect_favorites.js`。

- [ ] **Step 3: 实现可测试的采集脚本**

```js
(() => {
  const XHS_ORIGIN = "https://www.xiaohongshu.com";
  const NOTE_PATH = /^\/explore\/([^/?#]+)$/;

  function normalizeText(value) {
    return typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "";
  }

  function normalizeNoteUrl(rawUrl) {
    try {
      const url = new URL(rawUrl, XHS_ORIGIN);
      const match = url.origin === XHS_ORIGIN ? url.pathname.match(NOTE_PATH) : null;
      return match ? `${XHS_ORIGIN}/explore/${match[1]}` : null;
    } catch {
      return null;
    }
  }

  function mergeRecord(current, candidate) {
    return {
      source_url: current.source_url,
      title: current.title || candidate.title,
      author: current.author || candidate.author,
      media_type: current.media_type === "video" || candidate.media_type === "video"
        ? "video"
        : current.media_type === "article" || candidate.media_type === "article"
          ? "article"
          : "unknown",
    };
  }

  function mergeRecords(records) {
    const byUrl = new Map();
    for (const record of records) {
      const current = byUrl.get(record.source_url);
      byUrl.set(record.source_url, current ? mergeRecord(current, record) : record);
    }
    return [...byUrl.values()].sort((left, right) => left.source_url.localeCompare(right.source_url));
  }

  function closestCard(anchor) {
    let node = anchor;
    let best = anchor;
    while (node && node !== document.body) {
      const text = normalizeText(node.innerText);
      if (text.length >= 2 && text.length <= 800) {
        best = node;
      }
      node = node.parentElement;
    }
    return best;
  }

  function extractRecord(anchor) {
    const sourceUrl = normalizeNoteUrl(anchor.href);
    if (!sourceUrl) {
      return null;
    }
    const card = closestCard(anchor);
    const image = card.querySelector("img[alt]");
    const lines = typeof card.innerText === "string"
      ? card.innerText.split(/\n+/).map(normalizeText).filter(Boolean)
      : [];
    const title = normalizeText(anchor.getAttribute("title")) || normalizeText(image?.alt) || lines[0] || "";
    const author = lines.length > 1 ? lines[lines.length - 1] : "";
    const mediaType = card.querySelector("video") || /播放|视频/.test(normalizeText(card.innerText))
      ? "video"
      : "article";
    return { source_url: sourceUrl, title, author, media_type: mediaType };
  }

  function collectVisibleRecords() {
    return mergeRecords(
      [...document.querySelectorAll("a[href]")]
        .map(extractRecord)
        .filter((record) => record !== null),
    );
  }

  function findScrollContainer() {
    const candidates = [document.scrollingElement, ...document.querySelectorAll("div")]
      .filter((element) => element && element.scrollHeight > element.clientHeight + 200)
      .sort((left, right) => right.scrollHeight - left.scrollHeight);
    if (!candidates[0]) {
      throw new Error("No scrollable favorites container found");
    }
    return candidates[0];
  }

  function pause(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  }

  function downloadManifest(manifest) {
    const blob = new Blob([`${JSON.stringify(manifest, null, 2)}\n`], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `xhs-favorites-${manifest.collected_at.slice(0, 10)}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  async function run({ maxRounds = 800, stableRounds = 5, waitMs = 800 } = {}) {
    const container = findScrollContainer();
    const records = new Map();
    let stable = 0;

    for (let round = 0; round < maxRounds && stable < stableRounds; round += 1) {
      const before = records.size;
      for (const record of collectVisibleRecords()) {
        records.set(record.source_url, mergeRecord(records.get(record.source_url) || record, record));
      }
      const previousTop = container.scrollTop;
      container.scrollTop = Math.min(
        container.scrollTop + Math.max(600, Math.floor(container.clientHeight * 0.85)),
        container.scrollHeight,
      );
      await pause(waitMs);
      stable = records.size === before && container.scrollTop === previousTop ? stable + 1 : 0;
    }

    const notes = mergeRecords([...records.values()]);
    if (notes.length === 0) {
      throw new Error("No Xiaohongshu note links were collected");
    }
    const manifest = {
      schema_version: 1,
      profile_url: window.location.href,
      collected_at: new Date().toISOString(),
      notes,
    };
    downloadManifest(manifest);
    return manifest;
  }

  globalThis.XhsFavoritesCollector = {
    collectVisibleRecords,
    mergeRecords,
    normalizeNoteUrl,
    run,
  };
})();
```

- [ ] **Step 4: 运行测试并确认通过**

Run: `node --test tests/xhs_collect_favorites.test.mjs`

Expected: PASS，两个子测试均通过。

- [ ] **Step 5: 提交采集核心和测试**

```bash
git add tools/xhs_collect_favorites.js tests/xhs_collect_favorites.test.mjs
git commit -m "feat(cookbook): 添加小红书收藏采集器"
```

### Task 2: 记录本地数据边界和运行方式

**Files:**
- Create: `tools/README.md`
- Create: `data/xhs/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: 写入采集数据忽略规则**

```gitignore
data/xhs/*.json
!data/xhs/.gitkeep
```

- [ ] **Step 2: 创建数据目录标记文件**

创建空文件 `data/xhs/.gitkeep`，使本地采集 JSON 有固定存放位置且不会被提交。

- [ ] **Step 3: 写入运行说明**

```markdown
# 本地工具

## 小红书收藏采集

1. 在 Edge 中登录小红书并打开收藏页。
2. 按 `F12`，在 DevTools 的 `Sources` 面板创建 Snippet。
3. 粘贴 `tools/xhs_collect_favorites.js` 的完整内容并运行。
4. 在 Console 执行：

   ```js
   await XhsFavoritesCollector.run()
   ```

5. 浏览器下载 JSON 后，将文件移动到 `data/xhs/`。

脚本只导出笔记来源链接、标题、作者、媒体类型和采集时间。它不会导出登录凭据、不会修改页面、不会取消收藏。
```

- [ ] **Step 4: 验证采集脚本和站点构建**

Run: `node --test tests/xhs_collect_favorites.test.mjs`

Expected: PASS，两个子测试均通过。

Run: `uv run mkdocs build --strict`

Expected: exit code 0；站点构建成功，未导航的 `docs/superpowers/**` 文档仅产生信息提示。

- [ ] **Step 5: 提交运行说明和数据忽略规则**

```bash
git add .gitignore data/xhs/.gitkeep tools/README.md
git commit -m "docs(cookbook): 说明收藏采集流程"
```

## 计划自检

- 设计中的只读采集边界由 Task 1 的 `run()` 和 Task 2 的运行说明落实；脚本不包含取消收藏逻辑。
- 去重键、输出字段与设计文档一致，采集 JSON 不包含 Cookie、请求头或令牌。
- 采集器会在没有笔记链接或找不到滚动容器时抛出明确错误，不会产生可用于后续清理的虚假成功清单。
- 计划不实现正文抓取、视频下载、菜谱导入或取消收藏；这些依赖真实笔记页面和成功清单，属于后续独立子项目。
