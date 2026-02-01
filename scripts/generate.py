# -*- coding: utf-8 -*-
"""
生成 Zola 格式的博客文章

从 GitHub Issues 同步文章并转换为 Zola 兼容的 Markdown 格式
"""

import argparse
import os
import sys

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import BACKUP_DIR, get_me, get_repo, get_to_generate_issues, is_me, login

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


def save_issue_as_zola(issue, me, posts_dir="content/posts"):
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

    # 截取描述（取前 200 字符）
    description = issue.body[:200].replace("\n", " ").strip() if issue.body else title

    # 处理内容，添加锚点标题
    content = MARKDOWN_TITLE_TEMPLATE.format(title=issue.title, url=issue.html_url)
    content += issue.body

    # 添加作者评论
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

    # 保存文件
    with open(md_name, "w", encoding="utf-8") as f:
        f.write(zola_content)

    return md_name


def main(token, repo_name, posts_dir="content/posts"):
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

    # 获取并生成文章
    to_generate_issues = get_to_generate_issues(repo, BACKUP_DIR)

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
    parser.add_argument("github_token", help="GitHub Personal Access Token")
    parser.add_argument("repo_name", help="仓库名称 (owner/repo)")
    parser.add_argument(
        "--posts_dir",
        default="content/posts",
        help="文章保存目录 (默认: content/posts)",
    )

    args = parser.parse_args()

    main(args.github_token, args.repo_name, args.posts_dir)
