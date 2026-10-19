# agent-learning

AI Agent / 大模型应用开发 · 实习上岸学习仓库

> 属于 [YOU-TRY](https://github.com/Yts6/YOU-TRY) 仓库下的子项目。

## 进度（对照《智能体实习-分步执行手册.md》）

- [x] **Step 1** 安装 Python 3.11 —— Python 3.11.9 ✅
- [x] **Step 2** 配置 pip 国内镜像源 —— 清华源 ✅
- [x] **Step 3** 建项目目录 + 虚拟环境 —— `.venv` ✅
- [x] **Step 4** 注册模型 API，拿到 Key —— 智谱 GLM-4-Flash（免费）✅
- [x] **Step 5** 跑通第一个大模型调用（流式）—— `first_call.py` ✅
- [x] **Step 6** 建 GitHub 仓库并推送 —— https://github.com/Yts6/YOU-TRY ✅
- [x] **Step 7** Python 补缺 —— 4 个脚本 + 异步并发验收（2.8x）✅
- [x] **Step 8** FastAPI 把模型调用包成接口 —— `/docs` 实测可访问 ✅
- [x] **Step 9** 流式输出 + 错误处理 —— 全局异常处理 + 统一错误结构 ✅
- [x] **Step 10** Git 工作流熟练化 —— 分支开发 + 合并 + commit 规范 ✅
- [x] **Step 11** 大模型基础直觉 —— token/attention/上下文/embedding ✅
- [x] **Step 12** Prompt 工程 + 模板库 —— 10 个可复用模板 ✅
- [ ] **Step 13** 开项目一：RAG 知识库（下一阶段）

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

# 6. 看 Prompt 模板库与对比实验
python step12_prompt_demo.py
```

## 目录结构

```
agent-learning/
├── .env.example              # 密钥模板（.env 不提交）
├── requirements.txt
├── README.md
│
├── first_call.py             # Step 5：多平台流式调用
│
├── main.py                   # Step 8-9：FastAPI 服务（HTTP 层）
├── schemas.py                # Step 8-9：数据契约（Pydantic）
├── llm_client.py             # Step 8-9：模型层（平台选择/调用/错误翻译）
│
├── prompts/                  # Step 12：Prompt 模板库
│   ├── __init__.py
│   └── templates.py          # 10 个模板 + 变量校验
├── step12_prompt_demo.py     # Step 12：约束 Prompt 对比实验
│
├── step7/  · Python 补缺（4 脚本 + 幻觉实测记录）
├── step8/  · FastAPI 接口文档
├── step10/ · Git 工作流
├── step11/ · 大模型基础直觉
└── step12/ · Prompt 工程
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

## Prompt 模板库（10 个）

| 模板 | 用途 |
|---|---|
| `qa_with_citation` | 带引用问答（RAG 生成，防幻觉） |
| `extract_json` | 结构化信息抽取 |
| `summarize` | 可控摘要 |
| `score_with_reason` | 打分 + 理由（评估） |
| `query_rewrite` | 查询改写（多路召回） |
| `think_step_by_step` | CoT 分步推理 |
| `refuse_out_of_scope` | 越界拒答 |
| `agent_system_prompt` | Agent 系统提示骨架 |
| `compare_two` | 两方案对比 |
| `few_shot_classify` | 少样本分类 |

详见 [`step12/README.md`](./step12/README.md)

## 支持的大模型平台

`llm_client.py` 自动挑选第一个配置了 Key 的平台：

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
| Step 12 约束 Prompt 对比 | ✅ 无约束答错 / 给材料答对 / 无材料拒答 |

## ⚠️ 模型幻觉实证（本项目最有价值的记录）

用免费模型 `glm-4-flash` 实测，**对 RAG / Function Calling / MCP / LangGraph 四个概念全部答错**：

| 提问 | 模型回答（每次还不一样） | 正确答案 |
|---|---|---|
| 什么是 RAG | "阅读、理解、生成" / "检索-摘要-生成" / "检索-评估-生成" | **检索增强生成** |
| 什么是 MCP | "微控制器的编程协议" / "Modbus Control Protocol（1979年）" | **Model Context Protocol** |
| 什么是 token | "数字代币" | 文本最小单元 |
| LangGraph 与 LangChain | "LangGraph 是 LangChain 的数据基础" | 反向 |

**同一个问题问三次，得到三个不同的错误答案。** 这直接证明了 RAG 的核心价值：

| Prompt 策略 | 实测结果 |
|---|---|
| A. 无约束直接问 | ❌ 编造（Modbus 协议） |
| B. 给正确材料 + 只基于材料 | ✅ 答对 + 标注来源 |
| C. 给无关材料 + 没答案就拒答 | ✅ 明确说"无法回答" |

详见 [`step7/模型幻觉实测记录.md`](./step7/模型幻觉实测记录.md)
