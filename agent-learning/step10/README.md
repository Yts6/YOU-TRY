# Step 10 · Git 工作流熟练化

> 目标：每个功能一个 commit，能看懂并处理分支。
> 验收：面试官点进 GitHub 能看出你的开发节奏。

## 本项目实际的 Git 操作记录

### 分支开发流程（本次真实执行）

```bash
# 1. 从 main 建功能分支
git checkout -b feat/prompt-library

# 2. 在分支上开发 + 提交（多次）
git add -A
git commit -m "feat(step12): 新增 Prompt 模板库"

# 3. 切回 main，合并
git checkout main
git merge feat/prompt-library

# 4. 推送
git push origin main

# 5. 删除已合并的分支
git branch -d feat/prompt-library
```

## 必会的 4 组命令

### 1. 看状态（最高频）

```bash
git status              # 工作区状态
git status --short      # 简洁版
git status -sb          # 简洁+分支信息（显示 ahead/behind）
git diff                # 未暂存的改动
git diff --cached       # 已暂存的改动
```

### 2. 提交

```bash
git add -A                       # 添加所有改动
git add path/to/file.py          # 只加指定文件（推荐，避免误加）
git commit -m "feat: 说明"        # 提交
git commit --amend -m "新说明"    # 修改上一次提交（未推送时用）
```

### 3. 分支

```bash
git branch                    # 列出本地分支
git branch -a                 # 列出所有（含远程）
git checkout -b feat/xxx      # 新建并切换
git checkout main             # 切回
git merge feat/xxx            # 合并到当前分支
git branch -d feat/xxx        # 删除已合并分支
```

### 4. 查看历史

```bash
git log                       # 完整历史
git log --oneline             # 一行一条
git log --oneline --graph     # 带分支图（好看）
git log --oneline -5          # 最近 5 条
git show HEAD                 # 最近一次提交的详情
git show --stat HEAD          # 只看改了哪些文件
```

## Commit Message 规范（面试官会看这个）

用 **Conventional Commits** 格式：

```
<类型>(<范围>): <简短说明>
```

| 类型 | 用途 | 例子 |
|---|---|---|
| `feat` | 新功能 | `feat(step12): 新增 Prompt 模板库` |
| `fix` | 修 bug | `fix(api): 修复空问题返回 500` |
| `docs` | 文档 | `docs: 补充接口说明` |
| `refactor` | 重构（不改功能） | `refactor: 抽出模型客户端` |
| `chore` | 杂项（配置等） | `chore: 初始化项目骨架` |
| `test` | 测试 | `test: 加校验用例` |

**❌ 反面例子**（项目里全都避免了）：

```
update
提交
修改了一堆东西
123
asdf
```

## 本项目的提交历史（真实）

```
ce5e635 feat(step8-9): FastAPI 服务 + 错误处理
58c3beb feat(step7): 完成 Python 补缺 —— 4 个演示脚本 + 异步验收
465e850 feat: 新增 agent-learning 学习子项目（Step 1-5 完成）
2b5414f Initial commit
```

从 commit 信息就能看出**项目是怎么一步步长起来的**——这正是面试官想看到的。

## .gitignore 安全实践（本项目重点）

因为要接触 API Key，防泄露是硬要求：

```
.env          # 密钥
.env.*        # 各种 .env 变体
!.env.example # 但模板要提交
.venv/        # 虚拟环境
__pycache__/  # 字节码
_*            # 下划线开头的临时脚本
```

**验证方法**（本项目每次提交前都跑）：

```bash
# 确认 .env 被忽略
git check-ignore -v .env

# 确认暂存区没有密钥文件
git diff --cached --name-only | grep -E "\\.env$|\\.venv/"

# 扫描暂存内容是否含 Key（正则匹配常见 Key 格式）
git diff --cached | grep -E "sk-[A-Za-z0-9._-]{20,}|[0-9a-f]{32}\\.[A-Za-z0-9]{20,}"
```

## 常见坑

| 坑 | 表现 | 解法 |
|---|---|---|
| 提交了 .env | 密钥进历史，删了也还在 | 用 `git rm --cached .env`；严重时删库重建 |
| 一个 commit 提交 200 文件 | 历史没法看 | 一个功能一个 commit |
| 分支太多不清理 | 混乱 | 合并后 `git branch -d` |
| 忘了 pull 就 push | 被拒（non-fast-forward） | 先 `git pull --rebase` |
| 用 `git add .` 带进垃圾 | 提交了缓存文件 | 用 `git add -A` 配合完善 .gitignore |

## 练习

1. 建一个 `feat/test-branch` 分支，加个文件，合并回 main，删掉分支
2. 用 `git log --oneline --graph --all` 画出你的分支历史
3. 故意提交一个错误，用 `git commit --amend` 修正
4. 用 `git reset --soft HEAD~1` 撤销最后一次提交（保留改动），再用 `git reset --hard HEAD~1` 撤销（丢改动）——**体会两者区别**
