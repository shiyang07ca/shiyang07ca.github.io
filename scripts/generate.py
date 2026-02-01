# -*- coding: utf-8 -*-
"""
生成 Zola 格式的博客文章

从 GitHub Issues 同步文章并转换为 Zola 兼容的 Markdown 格式
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import TYPE_CHECKING

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .utils import get_me, get_repo, get_to_generate_issues, is_me, login

if TYPE_CHECKING:
    from github.Issue import Issue

# Zola 文章模板
ZOLA_TEMPLATE = """+++
title = "{title}"
date = {date}
updated = {updated}
draft = false
description = "{description}"

[taxonomies]
categories = []
tags = []

[extra]
lang = "zh-CN"
toc = true
comment = false
copy = true
math = false
mermaid = false
featured = false
display_tags = true
truncate_summary = false
+++

{content}

"""

# 用于 Markdown 转换的锚点标题
MARKDOWN_TITLE_TEMPLATE = "# [{title}]({url})\n\n"


def sanitize_description(text: str | None, max_length: int = 100) -> str:
    """
    清理描述文本，移除 TOML 不支持的特殊字符

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        清理后的安全文本
    """
    if not text:
        return ""

    # 移除 Markdown 格式字符和特殊字符
    result = text.replace("#", "").replace("*", "").replace("_", "").replace("`", "")
    result = result.replace('"', "'").replace("\\", "")
    result = result.replace("\n", " ").replace("\r", " ")
    result = result.replace("[", "(").replace("]", ")")
    result = result.strip()

    # 限制长度
    if len(result) > max_length:
        result = result[:max_length].strip()

    return result


def save_issue_as_zola(issue: Issue, me: str, posts_dir: str = "content/posts") -> str:
    """
    将 GitHub Issue 保存为 Zola 格式的 Markdown 文件

    Args:
        issue: GitHub Issue 对象
        me: 当前用户名
        posts_dir: Zola 文章保存目录
    """
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir, exist_ok=True)

    # 生成文件名（使用数字前缀确保排序）
    safe_title = "".join(
        c for c in issue.title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    safe_title = safe_title[:50]  # 限制长度
    md_name = os.path.join(
        posts_dir, f"{issue.number:04d}_{safe_title.replace(' ', '-')}.md"
    )

    # 处理内容
    title = issue.title.replace('"', '\\"')
    date_str = issue.created_at.strftime("%Y-%m-%d")
    updated_str = (
        issue.updated_at.strftime("%Y-%m-%d") if issue.updated_at else date_str
    )

    # 清理描述（移除特殊字符）
    description = (
        sanitize_description(issue.body, max_length=100)
        if issue.body
        else sanitize_description(title, max_length=100)
    )

    # 处理内容，添加锚点标题
    content = MARKDOWN_TITLE_TEMPLATE.format(title=issue.title, url=issue.html_url)
    content += issue.body or ""

    # 添加作者评论（IssueComment 与 Issue 均有 user.login）
    if issue.comments:
        for c in issue.get_comments():
            if is_me(c, me):
                content += "\n\n---\n\n"
                content += c.body

    # 生成 Zola 格式内容
    zola_content = ZOLA_TEMPLATE.format(
        title=title,
        date=date_str,
        updated=updated_str,
        description=description,
        content=content,
    )

    with open(md_name, "w", encoding="utf-8") as f:
        f.write(zola_content)

    return md_name


def main(token: str, repo_name: str, posts_dir: str = "content/posts") -> None:
    """
    主函数：从 GitHub Issues 生成博客文章

    Args:
        token: GitHub Personal Access Token
        repo_name: 仓库名称（格式: owner/repo）
        posts_dir: 文章保存目录
    """
    user = login(token)
    me = get_me(user)
    repo = get_repo(user, repo_name)

    # 确保目录存在
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir, exist_ok=True)

    # 根据 posts 目录判断已生成
    to_generate_issues = get_to_generate_issues(repo, posts_dir)

    generated_count = 0
    for issue in to_generate_issues:
        if is_me(issue, me):
            save_issue_as_zola(issue, me, posts_dir)
            generated_count += 1
            print(f"Generated: {issue.title}")

    print(f"\n完成！共生成 {generated_count} 篇文章")
    print(f"文章保存目录: {os.path.abspath(posts_dir)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 Zola 格式博客文章")
    _ = parser.add_argument("github_token", help="GitHub Personal Access Token")
    _ = parser.add_argument("repo_name", help="仓库名称 (owner/repo)")
    _ = parser.add_argument(
        "--posts_dir",
        default="content/posts",
        help="文章保存目录 (默认: content/posts)",
    )

    args: argparse.Namespace = parser.parse_args()
    main(str(args.github_token), str(args.repo_name), str(args.posts_dir))
