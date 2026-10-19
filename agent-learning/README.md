# agent-learning

AI Agent / 大模型应用开发 · 实习上岸学习仓库

> 属于 [YOU-TRY](https://github.com/Yts6/YOU-TRY) 仓库下的子项目。

## 进度（对照《智能体实习-分步执行手册.md》）

- [x] **Step 1** 安装 Python 3.11 —— Python 3.11.9 ✅
- [x] **Step 2** 配置 pip 国内镜像源 —— 清华源 ✅
- [x] **Step 3** 建项目目录 + 虚拟环境 —— `.venv` ✅
- [x] **Step 4** 注册模型 API，拿到 Key —— 智谱 GLM-4-Flash（免费）✅
- [x] **Step 5** 跑通第一个大模型调用（流式）—— `first_call.py` 实测通过 ✅
- [x] **Step 6** 建 GitHub 仓库并推送 —— https://github.com/Yts6/YOU-TRY ✅
- [x] **Step 7** Python 补缺 —— 4 个演示脚本 + 异步并发验收（2.8x 加速）✅
- [ ] **Step 8** FastAPI 把模型调用包成接口

## 环境信息

| 项 | 值 |
|---|---|
| Python | 3.11.9 |
| 虚拟环境 | `.venv\`（本子目录内） |
| pip 镜像 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 当前模型 | 智谱 `glm-4-flash`（免费） |

## 从零复现环境

```powershell
cd agent-learning

# 1. 建虚拟环境
py -3.11 -m venv .venv

# 2. 激活（若报"禁止运行脚本"）
#    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

# 3. 升级 pip 并装依赖
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. 配置密钥
Copy-Item .env.example .env   # 然后编辑填入 Key

# 5. 跑通第一个调用
python first_call.py
```

## 目录结构

```
agent-learning/
├── .venv/                    # 虚拟环境（不提交）
├── .env                      # 本地密钥（不提交）
├── .env.example              # 密钥模板（提交）
├── .gitignore
├── requirements.txt
├── README.md
├── first_call.py             # Step 5：多平台流式调用示例
└── step7/                    # Step 7：Python 补缺
    ├── README.md
    ├── 01_oop_decorator.py   # 类/装饰器/异常
    ├── 02_async.py           # asyncio 异步
    ├── 03_pydantic_typing.py # 类型注解 + Pydantic
    ├── 04_async_llm.py       # 验收题：异步并发调模型
    └── 模型幻觉实测记录.md    # 免费小模型 4/4 答错的实证
```

## 支持的大模型平台

`first_call.py` 会自动挑选第一个配置了 Key 的平台：

| 平台 | 环境变量 | 默认模型 | 费用 |
|---|---|---|---|
| 智谱 GLM | `ZHIPU_API_KEY` | `glm-4-flash` | 免费 |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` | 约 1 元/百万 token |
| 硅基流动 | `SILICONFLOW_API_KEY` | `Qwen/Qwen2.5-7B-Instruct` | 有免费额度 |
| 通义千问 | `DASHSCOPE_API_KEY` | `qwen-turbo` | 有免费额度 |

## 实测记录

### Step 5 · 流式调用

```
[使用平台] 智谱 GLM（免费）
[提问] 用一句话解释什么是 RAG
[回答] RAG是"检索-摘要-生成"的缩写……
[完成] 流式调用成功 ✅
```

### Step 7 · 异步并发（验收题 04）

```
任务数: 5 | 并发上限: 3
成功: 5/5
总耗时: 3.62s
串行估算: 9.95s -> 并发实际: 3.62s
加速比: 2.8x
```

> ⚠️ 同时实测发现：`glm-4-flash` 对 RAG / Function Calling / MCP / LangGraph
> **4 个问题全部答错**，且同一问题三次调用得到三个不同错误答案。
> 详见 [`step7/模型幻觉实测记录.md`](./step7/模型幻觉实测记录.md)。
