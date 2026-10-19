# Step 8-9 · FastAPI 服务

> 验收标准（来自手册）：浏览器访问 `http://127.0.0.1:8000/docs`，点开接口能发请求并拿到结果。✅ 已实测通过

## 快速启动

```powershell
cd D:\A-Code\YOU-TRY\agent-learning
.\.venv\Scripts\Activate.ps1

# 启动服务（--reload 表示改代码自动重启）
uvicorn main:app --reload
```

看到这行就成功了：

```
[启动] 就绪：智谱 GLM / glm-4-flash
INFO:     Uvicorn running on http://127.0.0.1:8000
```

然后浏览器打开 **http://127.0.0.1:8000/docs**

## 接口清单

| 方法 | 路径 | 说明 | 实测 |
|---|---|---|---|
| GET | `/` | 服务信息 | ✅ 200 |
| GET | `/health` | 健康检查（含 Key 配置状态） | ✅ 200 |
| POST | `/ask` | 单轮问答（推荐） | ✅ 200 |
| GET | `/ask?question=xxx` | 便捷版，浏览器地址栏直接测 | ✅ 200 |
| GET | `/docs` | 自动生成的交互式文档 | ✅ 200 |
| GET | `/openapi.json` | 自动生成的 API 规范 | ✅ 200 |

## 文件职责

```
agent-learning/
├── main.py          # HTTP 层：路由、异常处理、生命周期
├── schemas.py       # 数据契约：请求/响应模型 + 校验规则
├── llm_client.py    # 模型层：平台选择、调用封装、错误翻译
├── first_call.py    # Step 5 的脚本版（保留作对照）
└── .env             # 密钥（不提交）
```

**为什么要分层？**
把「HTTP 怎么处理」和「模型怎么调用」分开，好处是：
- 换模型/加平台只改 `llm_client.py`，`main.py` 不动
- 写测试时可以单独测模型层，不用起服务
- 后面 RAG 项目直接复用这套结构

## 请求/响应示例

**POST /ask 请求体**

```json
{
  "question": "用一句话说明什么是 token",
  "temperature": 0.7,
  "max_tokens": 512,
  "system_prompt": "你是一个简洁的助手"
}
```

**成功响应（200）**

```json
{
  "answer": "Token是一种数字代币……",
  "model": "glm-4-flash",
  "provider": "智谱 GLM",
  "latency_ms": 1864,
  "usage_total_tokens": 32
}
```

**校验失败（422）** —— FastAPI 自动生成，不用自己写

```json
{
  "detail": [{
    "type": "less_than_equal",
    "loc": ["body", "temperature"],
    "msg": "Input should be less than or equal to 2",
    "input": 9.9
  }]
}
```

**模型出错（Step 9 统一格式）**

```json
{
  "error": "rate_limited",
  "message": "触发模型平台的限流（429）。",
  "suggestion": "稍后重试，或在平台控制台检查免费额度是否用尽。"
}
```

## Step 9 的错误处理设计

核心思想：**模型出错不能让服务崩，也不能给用户看堆栈。**

| 异常 | HTTP 码 | error 字段 | 用户看到的话 |
|---|---|---|---|
| 限流 | 429 | `rate_limited` | 触发限流，稍后重试 |
| Key 无效 | 401 | `auth_failed` | 鉴权失败，检查 Key |
| 无模型权限 | 403 | `model_denied` | 无权使用该模型 |
| 超时 | 504 | `timeout` | 响应超时，稍后重试 |
| 连不上 | 503 | `connection_error` | 无法连接平台，查网络 |
| 其他 | 502 | `upstream_error` | 调用失败，看日志 |
| 没配 Key | 503 | `no_provider` | 请配置 .env |

实现方式：`llm_client.translate_error()` 翻译异常 → `@app.exception_handler` 统一转成 JSON。

## 实测记录（2026-10-19）

### 接口连通性

```
GET  /           -> 200  {"service":"Agent Learning API",...}
GET  /health     -> 200  {"status":"ok","provider":"智谱 GLM",...}
GET  /docs       -> 200  text/html          <- 验收核心通过
POST /ask        -> 200  latency_ms=1864
GET  /ask?...    -> 200  latency_ms=925
```

### 边界校验

```
空 question          -> 422  ✅
temperature=9.9      -> 422  ✅
question 2500字符    -> 422  ✅
system_prompt 3000字 -> 422  ✅
不存在的路径          -> 404  ✅
```

### 并发验证（证明 async 没阻塞）

5 个请求同时发：

```
请求1: HTTP 200 耗时 2.518s
请求2: HTTP 200 耗时 2.115s
请求3: HTTP 200 耗时 1.135s
请求4: HTTP 200 耗时 1.264s
请求5: HTTP 200 耗时 1.326s
```

5 个请求**同时完成**，总耗时 ≈ 最慢的一个（2.5s），而不是串行的 6+ 秒。
如果用了同步 `OpenAI` 客户端，这里会变成一个个排队。

## 关键知识点

### 1. 为什么用 `AsyncOpenAI` 而不是 `OpenAI`

```python
# ❌ 错误：同步调用会阻塞事件循环，并发请求全部排队
@app.post("/ask")
async def ask(body: AskRequest):
    resp = client.chat.completions.create(...)   # 阻塞！

# ✅ 正确：await 期间让出控制权，能处理其他请求
@app.post("/ask")
async def ask(body: AskRequest):
    resp = await async_client.chat.completions.create(...)
```

### 2. `@asynccontextmanager lifespan` 替代废弃的 `@app.on_event`

FastAPI 新版不再推荐 `@app.on_event("startup")`，改用 lifespan 上下文管理器，
可以在启动时初始化客户端、关闭时正确释放连接。

### 3. 客户端要复用，不要每次请求新建

```python
# ❌ 每次请求都新建：浪费 TCP 连接和 TLS 握手
@app.post("/ask")
async def ask(...):
    client = AsyncOpenAI(...)

# ✅ 全局单例：连接池复用
def get_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
```

## 常见坑

| 坑 | 表现 | 解法 |
|---|---|---|
| 同步客户端塞进 async | 并发时请求排队、服务卡死 | 用 `AsyncOpenAI` |
| 没加 `--reload` | 改代码要手动重启 | 开发时加 `--reload` |
| 端口被占用 | `Address already in use` | 换 `--port 8001`，或杀掉占用进程 |
| 异常直接抛出 | 用户看到 500 堆栈 | 加 `exception_handler` |
| 中文 body 报解析错 | shell 编码问题（不是服务问题） | 用文件传 JSON，或 Apifox/Postman |

## 练习

1. 给 `/ask` 加一个 `stream: bool` 参数，为 True 时返回 SSE 流（Step 9 的进阶）
2. 加一个简单的内存缓存：相同 question 直接返回上次结果
3. 加 `/ask_batch` 接口，接收问题列表，用 `asyncio.gather` 并发处理
4. 把 `latency_ms` 记录成日志文件，观察不同问题的响应时间分布
