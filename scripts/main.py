# -*- coding: utf-8 -*-
"""
生成 README.md 和 RSS 订阅源

从 GitHub Issues 同步文章信息，生成 README 索引和 RSS feed
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import io
from typing import TYPE_CHECKING, cast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feedgen.feed import FeedGenerator
from lxml.etree import CDATA
from marko.ext.gfm import gfm as marko

from .utils import (
    ANCHOR_NUMBER,
    BACKUP_DIR,
    FRIENDS_LABELS,
    IGNORE_LABELS,
    format_time,
    get_issues_from_label,
    get_me,
    get_repo,
    get_repo_labels,
    get_to_generate_issues,
    get_todo_issues,
    get_top_issues,
    is_me,
    login,
    save_issue_to_file,
)

if TYPE_CHECKING:
    from github.Issue import Issue
    from github.IssueComment import IssueComment
    from github.Repository import Repository

# README 头部模板
MD_HEAD = """# {name}'s Blog

个人博客，使用 GitHub Actions 自动构建

## 订阅

- [RSS 订阅](https://raw.githubusercontent.com/{repo_name}/master/feed.xml)

---

"""

# 友情链接表格配置
FRIENDS_TABLE_HEAD = "| Name | Link | Desc |\n| ---- | ---- | ---- |\n"
FRIENDS_TABLE_TEMPLATE = "| {name} | {link} | {desc} |\n"
FRIENDS_INFO_DICT = {
    "名字": "",
    "链接": "",
    "描述": "",
}


def is_hearted_by_me(comment: IssueComment, me: str) -> bool:
    """检查评论是否被当前用户点赞"""
    reactions = list(comment.get_reactions())
    return any(r.content == "heart" and r.user.login == me for r in reactions)


def make_friend_table_string(s: str) -> str | None:
    """解析友链信息并生成表格行"""
    info_dict = FRIENDS_INFO_DICT.copy()
    try:
        string_list = [line for line in s.splitlines() if line and not line.isspace()]
        for line in string_list:
            string_info_list = re.split("：", line, maxsplit=1)
            if len(string_info_list) >= 2:
                info_dict[string_info_list[0]] = string_info_list[1]

        return FRIENDS_TABLE_TEMPLATE.format(
            name=info_dict["名字"], link=info_dict["链接"], desc=info_dict["描述"]
        )
    except Exception as e:
        print(f"解析友链失败: {e}")
        return None


def valid_xml_char_ordinal(c: str) -> bool:
    """检查字符是否为有效 XML 字符"""
    codepoint = ord(c)
    return (
        0x20 <= codepoint <= 0xD7FF
        or codepoint in (0x9, 0xA, 0xD)
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def add_issue_info(issue: Issue, md_file: io.TextIOBase) -> None:
    """向 README 添加 issue 信息"""
    time = format_time(issue.created_at)
    _ = md_file.write(f"- [{issue.title}]({issue.html_url}) - {time}\n")


def add_md_header(
    md_file: io.TextIOBase, repo_name: str, owner_name: str
) -> None:
    """添加 README 头部"""
    _ = md_file.write(MD_HEAD.format(name=owner_name, repo_name=repo_name))


def add_md_top(repo: Repository, md_file: io.TextIOBase, me: str) -> None:
    """添加置顶文章"""
    top_issues = list(get_top_issues(repo))
    if not top_issues:
        return

    _ = md_file.write("## 置顶文章\n\n")
    for issue in top_issues:
        if is_me(issue, me):
            add_issue_info(issue, md_file)


def add_md_recent(
    repo: Repository, md_file: io.TextIOBase, me: str, limit: int = 10
) -> None:
    """添加最近更新文章"""
    _ = md_file.write("## 最近更新\n\n")
    count = 0

    try:
        for issue in repo.get_issues():
            if is_me(issue, me) and not issue.pull_request:
                add_issue_info(issue, md_file)
                count += 1
                if count >= limit:
                    break
    except Exception as e:
        print(f"获取最近文章失败: {e}")


def add_md_label(repo: Repository, md_file: io.TextIOBase, me: str) -> None:
    """按标签分类添加文章"""
    labels = get_repo_labels(repo)
    labels = sorted(
        labels,
        key=lambda x: (
            (x.description or "") == "",
            x.description or "",
            x.name,
        ),
    )

    for label in labels:
        if label.name in IGNORE_LABELS:
            continue

        issues = get_issues_from_label(repo, label.name)
        if not issues.totalCount:
            continue

        _ = md_file.write(f"\n## {label.name}\n\n")
        issues_list = sorted(issues, key=lambda x: x.created_at, reverse=True)

        i = 0
        for issue in issues_list:
            if is_me(issue, me):
                if i == ANCHOR_NUMBER:
                    _ = md_file.write("<details><summary>显示更多</summary>\n\n")
                add_issue_info(issue, md_file)
                i += 1

        if i > ANCHOR_NUMBER:
            _ = md_file.write("</details>\n")


def add_md_todo(repo: Repository, md_file: io.TextIOBase, me: str) -> None:
    """添加 TODO 列表"""
    todo_issues = list(get_todo_issues(repo))
    if not todo_issues:
        return

    _ = md_file.write("\n## TODO 列表\n\n")

    for issue in todo_issues:
        if not is_me(issue, me):
            continue

        body = (issue.body or "").splitlines()
        todo_undone = [line for line in body if line.startswith("- [ ] ")]
        todo_done = [line for line in body if line.startswith("- [x] ")]

        todo_title = (
            f"[{issue.title}]({issue.html_url}) "
            f"- {len(todo_done)} 完成, {len(todo_undone)} 待办"
        )

        _ = md_file.write(f"### {todo_title}\n\n")

        for t in todo_done + todo_undone:
            _ = md_file.write(f"{t}\n")
        _ = md_file.write("\n")


def add_md_friends(repo: Repository, md_file: io.TextIOBase, me: str) -> None:
    """添加友情链接"""
    friends_issues = list(repo.get_issues(labels=FRIENDS_LABELS))
    if not friends_issues:
        return

    _ = md_file.write("\n## 友情链接\n\n")
    _ = md_file.write(FRIENDS_TABLE_HEAD)

    for issue in friends_issues:
        for comment in issue.get_comments():
            if is_hearted_by_me(comment, me):
                row = make_friend_table_string(comment.body or "")
                if row:
                    _ = md_file.write(row)


def generate_rss_feed(
    repo: Repository, filename: str, me: str
) -> None:
    """生成 RSS 订阅源"""
    generator = FeedGenerator()
    _ = generator.id(repo.html_url)
    _ = generator.title(f"{repo.owner.login}'s Blog")
    _ = generator.subtitle("技术博客文章订阅")
    _ = generator.link(href=repo.html_url)
    _ = generator.link(
        href=f"https://raw.githubusercontent.com/{repo.full_name}/master/{filename}",
        rel="self",
    )

    for issue in repo.get_issues():
        if not issue.body or not is_me(issue, me) or issue.pull_request:
            continue

        item = generator.add_entry(order="append")
        _ = item.id(issue.html_url)
        _ = item.link(href=issue.html_url)
        _ = item.title(issue.title)
        _ = item.published(issue.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"))

        for label in issue.labels:
            _ = item.category({"term": label.name})

        body = "".join(
            c for c in issue.body if valid_xml_char_ordinal(c)
        )
        _ = item.content(CDATA(marko.convert(body)), type="html")

    generator.rss_file(filename)


def main(
    token: str,
    repo_name: str,
    issue_number: int | None = None,
    backup_dir: str = BACKUP_DIR,
) -> None:
    """主函数：生成 README 和 RSS"""
    user = login(token)
    me = get_me(user)
    repo = get_repo(user, repo_name)

    # 确保备份目录存在
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)

    # 生成 README
    with open("README.md", "w", encoding="utf-8") as md:
        add_md_header(md, repo_name, repo.owner.login)
        add_md_top(repo, md, me)
        add_md_recent(repo, md, me)
        add_md_label(repo, md, me)
        add_md_todo(repo, md, me)
        add_md_friends(repo, md, me)

    # 生成 RSS 订阅源
    generate_rss_feed(repo, "feed.xml", me)

    # 备份文章
    to_generate_issues = get_to_generate_issues(repo, backup_dir, issue_number)

    for issue in to_generate_issues:
        if is_me(issue, me):
            _ = save_issue_to_file(issue, me, backup_dir)

    print("生成完成！")
    print("- README.md: 更新完成")
    print("- feed.xml: RSS 订阅源已生成")
    print("- BACKUP/: 文章备份已更新")


if __name__ == "__main__":
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(description="生成 README 和 RSS")
    _ = parser.add_argument("github_token", help="GitHub Personal Access Token")
    _ = parser.add_argument("repo_name", help="仓库名称 (owner/repo)")
    _ = parser.add_argument("--issue_number", help="指定 Issue 编号", default=None)

    args: argparse.Namespace = parser.parse_args()
    issue_num: int | None = (
        int(cast(str, args.issue_number)) if args.issue_number else None
    )
    main(
        cast(str, args.github_token),
        cast(str, args.repo_name),
        issue_num,
    )
