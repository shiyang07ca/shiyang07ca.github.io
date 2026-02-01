# -*- coding: utf-8 -*-
"""博客生成工具函数"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import TYPE_CHECKING, Protocol

from github import Github

if TYPE_CHECKING:
    from github.Issue import Issue
    from github.IssueComment import IssueComment
    from github.Label import Label
    from github.Repository import Repository


class _PaginatedIssues(Protocol):
    """PaginatedList 风格：含 totalCount 且可迭代"""

    @property
    def totalCount(self) -> int: ...

    def __iter__(self) -> Iterator[Issue]: ...

# 配置常量
BACKUP_DIR = "BACKUP"
ANCHOR_NUMBER = 5

# Labels 配置
TOP_ISSUES_LABELS = ["Top"]
TODO_ISSUES_LABELS = ["TODO"]
FRIENDS_LABELS = ["Friends"]
IGNORE_LABELS = FRIENDS_LABELS + TOP_ISSUES_LABELS + TODO_ISSUES_LABELS


def get_me(user: Github) -> str:
    """获取当前用户名"""
    return user.get_user().login


def is_me(issue: Issue | IssueComment, me: str) -> bool:
    """检查 issue/comment 是否属于当前用户"""
    return issue.user.login == me


def format_time(time: object) -> str:
    """格式化时间为 YYYY-MM-DD 格式"""
    return str(time)[:10]


def login(token: str) -> Github:
    """登录 GitHub"""
    return Github(token)


def get_repo(user: Github, repo: str) -> Repository:
    """获取仓库对象"""
    return user.get_repo(repo)  # type: ignore[return-value]


def get_repo_labels(repo: Repository) -> list[Label]:
    """获取仓库所有标签"""
    return list(repo.get_labels())  # type: ignore[return-value]


def get_issues_from_label(repo: Repository, label: str) -> _PaginatedIssues:
    """根据标签获取 issues"""
    return repo.get_issues(labels=[label])  # type: ignore[return-value]


def get_top_issues(repo: Repository) -> _PaginatedIssues:
    """获取置顶 issues"""
    return repo.get_issues(labels=TOP_ISSUES_LABELS)  # type: ignore[return-value]


def get_todo_issues(repo: Repository) -> _PaginatedIssues:
    """获取 TODO issues"""
    return repo.get_issues(labels=TODO_ISSUES_LABELS)  # type: ignore[return-value]


def get_to_generate_issues(
    repo: Repository, dir_name: str, issue_number: int | None = None
) -> list[Issue]:
    """获取需要生成的 issues"""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    
    md_files = os.listdir(dir_name)
    generated_issues_numbers = [
        int(i.split("_")[0]) for i in md_files if i.split("_")[0].isdigit()
    ]
    
    to_generate_issues = [
        i for i in list(repo.get_issues())
        if int(i.number) not in generated_issues_numbers
    ]
    
    if issue_number:
        to_generate_issues.append(repo.get_issue(int(issue_number)))
    
    return to_generate_issues


def save_issue_to_file(
    issue: Issue, me: str, dir_name: str, _template_content: str | None = None
) -> str:
    """
    保存 issue 到文件

    Args:
        issue: GitHub Issue 对象
        me: 当前用户名
        dir_name: 保存目录
        _template_content: 可选的自定义模板（保留供扩展）
    """
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    md_name = os.path.join(
        dir_name, f"{issue.number}_{issue.title.replace(' ', '.')}.md"
    )

    with open(md_name, "w", encoding="utf-8") as f:
        _ = f.write(f"# [{issue.title}]({issue.html_url})\n\n")
        body = issue.body or ""
        _ = f.write(body)

        if issue.comments:
            for c in issue.get_comments():
                if is_me(c, me):
                    _ = f.write("\n\n---\n\n")
                    _ = f.write(c.body or "")

    return md_name
