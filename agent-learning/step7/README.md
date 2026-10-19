# Step 7 · Python 补缺

> 目标：能读懂 LangChain 源码的类型注解，会写异步代码。
> 原则：**只补你缺的**。跑完下面 4 个脚本，哪里看不懂就补哪里，不用从头学 Python。

## 怎么用

```powershell
cd D:\A-Code\YOU-TRY\agent-learning
.\.venv\Scripts\Activate.ps1

cd step7
python 01_oop_decorator.py
python 02_async.py
python 03_pydantic_typing.py
python 04_async_llm.py     # 会真实调用模型
```

## 4 个脚本分别练什么

| 文件 | 知识点 | 为什么 AI 开发需要 |
|---|---|---|
| `01_oop_decorator.py` | 类/继承、dataclass、装饰器、自定义异常 | LangChain 的 Tool/Chain 全是类；重试逻辑用装饰器写 |
| `02_async.py` | async/await、gather、Semaphore、超时 | 90% 时间在等 IO；并发调模型快 N 倍；限流防封 |
| `03_pydantic_typing.py` | 类型注解、Pydantic 校验 | LangChain 源码全是注解；FastAPI 接口靠它校验 |
| `04_async_llm.py` | 综合：异步 + 限流 + 超时 + 重试 + 校验 | **验收题**，也是 Step 8-9 的直接基础 |

## 验收标准

1. 跑 `04_async_llm.py`，5 个问题全部成功，且能看到**并发比串行快 3 倍以上**
2. 能回答：为什么 `async def` 里不能用 `time.sleep()`？
3. 能回答：`Optional[str]` 和 `str` 有什么区别？`Literal` 有什么用？
4. 能回答：装饰器 `@wraps` 不加会怎样？

## 常见坑

| 坑 | 表现 | 解法 |
|---|---|---|
| 在 async 里用同步库 | 服务并发时卡死 | 用 `AsyncOpenAI`、`httpx.AsyncClient`，别用 `requests` |
| 忘记 await | 拿到 coroutine 对象，不执行 | 看到 `<coroutine object>` 就是漏了 await |
| 无限并发 | 被 API 限流（429） | 用 `Semaphore` 限制并发数 |
| 可变默认值 | 所有实例共享同一个 list | 用 `field(default_factory=list)` |

## 练习

每题都在脚本底部注释里，答案建议写到 `step7/answers/` 下。
