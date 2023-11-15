# -*- coding: utf-8 -*-
import argparse
import os

from github import Github
from marko.ext.gfm import gfm as marko

BACKUP_DIR = "BACKUP"

ANCHOR_NUMBER = 5
TOP_ISSUES_LABELS = ["Top"]
TODO_ISSUES_LABELS = ["TODO"]
FRIENDS_LABELS = ["Friends"]
IGNORE_LABELS = FRIENDS_LABELS + TOP_ISSUES_LABELS + TODO_ISSUES_LABELS


def get_me(user):
    return user.get_user().login


def is_me(issue, me):
    return issue.user.login == me


def format_time(time):
    return str(time)[:10]


def login(token):
    return Github(token)


def get_repo(user: Github, repo: str):
    return user.get_repo(repo)


def get_repo_labels(repo):
    return [l for l in repo.get_labels()]


def get_issues_from_label(repo, label):
    return repo.get_issues(labels=(label, ))


def get_to_generate_issues(repo, dir_name, issue_number=None):
    # md_files = os.listdir(dir_name)
    # generated_issues_numbers = [
    #     int(i.split("_")[0]) for i in md_files if i.split("_")[0].isdigit()
    # ]
    to_generate_issues = [i for i in list(repo.get_issues())]
    if issue_number:
        to_generate_issues.append(repo.get_issue(int(issue_number)))

    return to_generate_issues


template = """+++
title = "{}"
date = {}
draft = false

[extra]
lang = "zh-CN"
toc = true
comment = true
copy = true
math = false
mermaid = false
display_tags = true
truncate_summary = false
+++

"""


def save_issue(issue, me, dir_name="content/blog"):
    md_name = os.path.join(dir_name, f"{issue.title.replace(' ', '.')}.md")
    with open(md_name, "w") as f:
        f.write(
            template.format(issue.title, issue.created_at.strftime("%Y-%m-%d"))
            + "\n\n")
        # f.write(f"# [{issue.title}]({issue.html_url})\n\n")
        f.write(issue.body)
        if issue.comments:
            for c in issue.get_comments():
                if is_me(c, me):
                    f.write("\n\n---\n\n")
                    f.write(c.body)


def main(token, repo_name, dir_name=BACKUP_DIR):
    user = login(token)
    me = get_me(user)
    repo = get_repo(user, repo_name)

    to_generate_issues = get_to_generate_issues(repo, dir_name)
    # save md files to content folder
    for issue in to_generate_issues:
        save_issue(issue, me)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    options = parser.parse_args()
    main(options.github_token, options.repo_name)
