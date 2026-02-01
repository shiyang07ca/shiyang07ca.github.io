# -*- coding: utf-8 -*-
"""博客生成工具函数"""

import os
from github import Github

# 配置常量
BACKUP_DIR = "BACKUP"
ANCHOR_NUMBER = 5

# Labels 配置
TOP_ISSUES_LABELS = ["Top"]
TODO_ISSUES_LABELS = ["TODO"]
FRIENDS_LABELS = ["Friends"]
IGNORE_LABELS = FRIENDS_LABELS + TOP_ISSUES_LABELS + TODO_ISSUES_LABELS


def get_me(user):
    """获取当前用户名"""
    return user.get_user().login


def is_me(issue, me):
    """检查 issue 是否属于当前用户"""
    return issue.user.login == me


def format_time(time):
    """格式化时间为 YYYY-MM-DD 格式"""
    return str(time)[:10]


def login(token):
    """登录 GitHub"""
    return Github(token)


def get_repo(user: Github, repo: str):
    """获取仓库对象"""
    return user.get_repo(repo)


def get_repo_labels(repo):
    """获取仓库所有标签"""
    return [l for l in repo.get_labels()]


def get_issues_from_label(repo, label):
    """根据标签获取 issues"""
    return repo.get_issues(labels=(label, ))


def get_top_issues(repo):
    """获取置顶 issues"""
    return repo.get_issues(labels=TOP_ISSUES_LABELS)


def get_todo_issues(repo):
    """获取 TODO issues"""
    return repo.get_issues(labels=TODO_ISSUES_LABELS)


def get_to_generate_issues(repo, dir_name, issue_number=None):
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


def save_issue_to_file(issue, me, dir_name, template_content=None):
    """
    保存 issue 到文件
    
    Args:
        issue: GitHub Issue 对象
        me: 当前用户名
        dir_name: 保存目录
        template_content: 可选的自定义模板
    """
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    
    md_name = os.path.join(dir_name, f"{issue.number}_{issue.title.replace(' ', '.')}.md")
    
    with open(md_name, "w", encoding="utf-8") as f:
        f.write(f"# [{issue.title}]({issue.html_url})\n\n")
        f.write(issue.body)
        
        if issue.comments:
            for c in issue.get_comments():
                if is_me(c, me):
                    f.write("\n\n---\n\n")
                    f.write(c.body)
    
    return md_name
