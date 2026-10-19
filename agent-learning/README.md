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
- [x] **Step 8** FastAPI 把模型调用包成接口 —— `/docs` 实测可访问 ✅
- [x] **Step 9** 流式输出 + 错误处理 —— 全局异常处理 + 统一错误结构 ✅
- [ ] **Step 10** Git 工作流熟练化（在做）
- [ ] **Step 11** 大模型基础直觉
- [ ] **Step 12** Prompt 工程 + 自建模板库

## 环境信息

| 项 | 值 |
|---|---|
| Python | 3.11.9 |
| 虚拟环境 | `.venv\` |
| pip 镜像 | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| FastAPI | 0.148.0 |
| 当前模型 | 智谱 `glm-4-flash`（免费） |

## 快速开始

```powershell
cd agent-learning

# 1. 建虚拟环境
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1      # 报错先执行 Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 2. 装依赖
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. 配置密钥
Copy-Item .env.example .env          # 然后编辑填入 Key

# 4. 跑通第一个调用
python first_call.py

# 5. 启动 Web 服务
uvicorn main:app --reload
#    然后打开 http://127.0.0.1:8000/docs
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
│
├── first_call.py             # Step 5：多平台流式调用脚本
│
├── main.py                   # Step 8-9：FastAPI 服务（HTTP 层）
├── schemas.py                # Step 8-9：数据契约（Pydantic 模型）
├── llm_client.py             # Step 8-9：模型层（平台选择/调用/错误翻译）
│
├── step7/                    # Step 7：Python 补缺
│   ├── README.md
│   ├── 01_oop_decorator.py
│   ├── 02_async.py
│   ├── 03_pydantic_typing.py
│   ├── 04_async_llm.py
│   └── 模型幻觉实测记录.md
│
└── step8/                    # Step 8-9：接口文档
    └── README.md
```

## 接口速查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |
| POST | `/ask` | 单轮问答 |
| GET | `/ask?question=xxx` | 便捷 GET 版 |
| GET | `/docs` | 交互式 API 文档 |

详见 [`step8/README.md`](./step8/README.md)

## 支持的大模型平台

`llm_client.py` 会自动挑选第一个配置了 Key 的平台：

| 平台 | 环境变量 | 默认模型 | 费用 |
|---|---|---|---|
| 智谱 GLM | `ZHIPU_API_KEY` | `glm-4-flash` | 免费 |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek-chat` | 约 1 元/百万 token |
| 硅基流动 | `SILICONFLOW_API_KEY` | `Qwen/Qwen2.5-7B-Instruct` | 有免费额度 |
| 通义千问 | `DASHSCOPE_API_KEY` | `qwen-turbo` | 有免费额度 |

## 实测数据汇总

| 场景 | 结果 |
|---|---|
| Step 5 流式调用 | ✅ 逐字输出正常 |
| Step 7 异步并发（5 任务） | ✅ 2.8x 加速（9.95s → 3.62s） |
| Step 7 Semaphore 限流 | ✅ 严格 2 并发 |
| Step 8 接口连通性 | ✅ /docs、/ask、/health 全部 200 |
| Step 8 边界校验 | ✅ 5 类非法输入全部 422/404 |
| Step 8 并发 5 请求 | ✅ 总耗时 ≈ 最慢一个（2.5s） |

> ⚠️ **模型幻觉实测**：`glm-4-flash` 对 RAG / Function Calling / MCP / LangGraph
> **4 个概念全部答错**，且同一问题三次调用得到三个不同错误答案；
> 还把 AI 的 "token" 答成了加密货币的"数字代币"。
> 详见 [`step7/模型幻觉实测记录.md`](./step7/模型幻觉实测记录.md)。
