# 仓库 Agent 约束

## Commit Message

- 本仓库所有提交信息必须只包含提交时间戳，格式为 `YYYYMMDDTHH:MM`，例如 `20260710T11:39`。
- 不写 conventional commit、描述正文、`Co-Authored-By` 或其他 trailer。
- 创建提交前使用 `date +%Y%m%dT%H:%M` 生成当前时间戳作为提交信息。
- 如果用户明确要求整理历史，按每个提交自己的提交时间重写 commit message 为上述格式，并使用 `git push --force-with-lease` 覆盖远端。
- 重写历史和强制推送属于高风险操作，只有用户明确要求时才执行。
