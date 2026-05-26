# shiyang07ca.github.io

个人博客源码，使用 MkDocs 构建并发布到 GitHub Pages。

## 写作流程

正式内容放在 `docs/content/`，草稿放在 `docs/drafts/`，图片和其他静态资源放在 `docs/assets/`。

本地预览：

```bash
mkdocs serve
```

本地构建：

```bash
mkdocs build --strict
```

提交并推送到 `master` 后，GitHub Actions 会自动构建并部署站点。

## 目录约定

- `docs/index.md` 是站点首页。
- `docs/content/**` 是正式发布内容，会进入站点导航。
- `docs/drafts/**` 是草稿内容，不进入站点导航。
- `docs/assets/**` 用于存放图片和附件。
- `mkdocs.yml` 是站点配置和导航的唯一入口。
