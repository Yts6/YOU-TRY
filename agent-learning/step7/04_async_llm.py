"""Step 7-4 · 综合实战：把 Step 5 升级成异步版

运行： python 04_async_llm.py
这是 Step 7 的验收题，也是 Step 8-9（FastAPI）的直接基础。

它综合考了：
  - 异步并发（asyncio.gather）
  - 限流（Semaphore）
  - 超时（wait_for）
  - 重试（装饰器）
  - 类型注解 + Pydantic
  - 异常处理
"""

import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent  # 上两级 = agent-learning/
load_dotenv(BASE_DIR / ".env", override=True)

import os


# ---------- 用 Pydantic 定义返回结构（Step 7-3 的实战）----------
class ModelResult(BaseModel):
    task_id: int
    question: str
    answer: str = ""
    latency_ms: int = 0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


# ---------- 配置 ----------
PROVIDER = {
    "name": "智谱 GLM",
    "key_env": "ZHIPU_API_KEY",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "model": "glm-4-flash",
}

MAX_CONCURRENT = 3    # 同时最多几个请求
TIMEOUT_SECONDS = 30  # 单个请求超时
RETRY_TIMES = 2       # 失败重试次数


def make_client() -> AsyncOpenAI:
    key = (os.getenv(PROVIDER["key_env"]) or "").strip()
    if not key:
        print(f"[错误] 缺少 {PROVIDER['key_env']}")
        sys.exit(1)
    return AsyncOpenAI(api_key=key, base_url=PROVIDER["base_url"])


async def ask_once(client: AsyncOpenAI, task_id: int, question: str, sem: asyncio.Semaphore) -> ModelResult:
    """带限流 + 超时 + 重试的单次调用。"""
    result = ModelResult(task_id=task_id, question=question)
    start = time.perf_counter()

    async with sem:  # 限流：最多 MAX_CONCURRENT 个同时跑
        last_err: Exception | None = None
        for attempt in range(1, RETRY_TIMES + 1):
            try:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=PROVIDER["model"],
                        messages=[
                            {"role": "system", "content": "回答要简短，不超过40个字"},
                            {"role": "user", "content": question},
                        ],
                    ),
                    timeout=TIMEOUT_SECONDS,
                )
                result.answer = (resp.choices[0].message.content or "").strip()
                last_err = None
                break
            except asyncio.TimeoutError:
                last_err = TimeoutError(f"超过 {TIMEOUT_SECONDS}s")
                print(f"  [任务{task_id}] 第{attempt}次超时，重试...")
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                print(f"  [任务{task_id}] 第{attempt}次失败：{type(exc).__name__}")
                if attempt < RETRY_TIMES:
                    await asyncio.sleep(1.5 * attempt)  # 退避重试

        if last_err is not None:
            result.error = f"{type(last_err).__name__}: {last_err}"

    result.latency_ms = int((time.perf_counter() - start) * 1000)
    return result


async def run_batch(questions: list[str], concurrency: int) -> tuple[list[ModelResult], float]:
    """并发跑一批问题。"""
    client = make_client()
    sem = asyncio.Semaphore(concurrency)
    start = time.perf_counter()

    tasks = [ask_once(client, i, q, sem) for i, q in enumerate(questions)]
    results = await asyncio.gather(*tasks)

    total = time.perf_counter() - start
    await client.close()
    return results, total


async def main() -> None:
    questions = [
        "什么是 RAG？",
        "什么是 Function Calling？",
        "什么是 MCP 协议？",
        "向量数据库是做什么的？",
        'LangGraph 和 LangChain 什么关系？',
    ]

    print("=" * 64)
    print(f"Provider: {PROVIDER['name']} / {PROVIDER['model']}")
    print(f"并发上限: {MAX_CONCURRENT} | 超时: {TIMEOUT_SECONDS}s | 重试: {RETRY_TIMES}次")
    print(f"任务数: {len(questions)}")
    print("=" * 64)

    results, total = await run_batch(questions, MAX_CONCURRENT)

    print()
    print("---- 逐条结果 ----")
    ok_count = 0
    for r in results:
        if r.ok:
            ok_count += 1
            print(f"  ✅ [{r.task_id}] {r.question}")
            print(f"       {r.answer}")
            print(f"       ({r.latency_ms}ms)")
        else:
            print(f"  ❌ [{r.task_id}] {r.question}")
            print(f"       {r.error}")

    print()
    print("---- 汇总 ----")
    print(f"  成功: {ok_count}/{len(results)}")
    print(f"  总耗时: {total:.2f}s")
    if ok_count:
        per = [r.latency_ms for r in results if r.ok]
        print(f"  单次平均耗时: {sum(per)/len(per):.0f}ms")
        print(f"  串行估算: {sum(per)/1000:.2f}s -> 并发实际: {total:.2f}s")
        print(f"  加速比: {sum(per)/1000/total:.1f}x")

    print()
    print("=" * 64)
    print("如果上面全绿：Step 7 的 asyncio + Pydantic + 异常处理 你就过关了")
    print("下一步：Step 8 把这些代码包成 FastAPI 接口")
    print("=" * 64)


# =====================================================================
# 练习（进阶）：
#   1. 改成"谁先返回就先用"：用 asyncio.wait(FIRST_COMPLETED)
#   2. 加一个缓存：相同问题直接返回上次结果，不重复调用（省钱）
#   3. 把 MAX_CONCURRENT 改成 1 和 5，各跑一次，比较总耗时
#   4. 故意填错 base_url，验证重试 + 错误捕获是否按预期工作
# =====================================================================

if __name__ == "__main__":
    asyncio.run(main())
