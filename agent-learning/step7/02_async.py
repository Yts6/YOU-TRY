"""Step 7-2 · asyncio 异步编程

运行： python 02_async.py
为什么重要：AI 应用几乎全是 IO 等待（等模型返回、等数据库、等接口），
           同步代码会把服务卡死。LangChain 的 ainvoke / astream 全基于此。
"""

import asyncio
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def fake_llm_call(name: str, seconds: float) -> str:
    """模拟一次模型调用：真实场景就是 await client.chat.completions.create()"""
    print(f"  [{name}] 开始请求...")
    await asyncio.sleep(seconds)  # 关键：await 期间让出控制权，别的任务能跑
    print(f"  [{name}] 返回结果")
    return f"{name} 的结果"


def run_sync() -> float:
    """同步做法：一个一个等，总耗时 = 所有耗时相加。"""
    print("--- 同步（串行）---")
    start = time.perf_counter()
    for i in range(3):
        # 同步版本没法真等待，用 sleep 演示串行效果
        time.sleep(0.5)
        print(f"  [task{i}] 返回结果")
    cost = time.perf_counter() - start
    print(f"  总耗时：{cost:.2f}s")
    return cost


async def run_async() -> float:
    """异步做法：gather 并发，总耗时 ≈ 最慢的那个。"""
    print("--- 异步（并发）---")
    start = time.perf_counter()
    results = await asyncio.gather(
        fake_llm_call("task0", 0.5),
        fake_llm_call("task1", 0.5),
        fake_llm_call("task2", 0.5),
    )
    cost = time.perf_counter() - start
    print(f"  结果：{results}")
    print(f"  总耗时：{cost:.2f}s")
    return cost


async def demo_gather_return_exceptions() -> None:
    """gather 的 return_exceptions=True：一个失败不影响其它。"""

    async def maybe_fail(name: str, fail: bool) -> str:
        await asyncio.sleep(0.1)
        if fail:
            raise RuntimeError(f"{name} 炸了")
        return f"{name} OK"

    print("--- 并发中有任务失败，但整体不崩 ---")
    results = await asyncio.gather(
        maybe_fail("A", False),
        maybe_fail("B", True),
        maybe_fail("C", False),
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            print(f"  失败：{r}")
        else:
            print(f"  成功：{r}")


async def demo_timeout() -> None:
    """给单个调用加超时：模型卡住时不能无限等。"""
    print("--- 超时控制 ---")
    try:
        await asyncio.wait_for(fake_llm_call("slow", 5), timeout=0.3)
    except asyncio.TimeoutError:
        print("  已超时并中断（真实场景要返回友好提示，而不是让用户干等）")


async def demo_semaphore() -> None:
    """信号量：限制并发数，防止把 API 打爆（会被限流！）"""
    print("--- 并发限流（最多同时 2 个）---")
    sem = asyncio.Semaphore(2)

    async def limited(i: int) -> str:
        async with sem:
            return await fake_llm_call(f"limited{i}", 0.3)

    results = await asyncio.gather(*(limited(i) for i in range(5)))
    print(f"  完成 {len(results)} 个任务")


async def main() -> None:
    print("【为什么必须会异步】AI 应用 90% 的时间在等 IO")
    print()
    s = run_sync()
    print()
    a = await run_async()
    print()
    print(f"结论：异步比同步快 {s / a:.1f} 倍（这就是并发调 3 个模型的价值）")

    print()
    await demo_gather_return_exceptions()
    print()
    await demo_timeout()
    print()
    await demo_semaphore()

    print()
    print("=== 关键对照表 ===")
    table = [
        ("同步写法", "异步写法"),
        ("time.sleep(1)", "await asyncio.sleep(1)"),
        ("client.create()", "await client.create()"),
        ("requests.get()", "await httpx.AsyncClient().get()"),
        ("def f()", "async def f()"),
    ]
    for row in table:
        print(f"  {row[0]:<28} -> {row[1]}")


# =====================================================================
# 练习：
#   1. 并发调用 3 个真实的大模型 API（用 first_call.py 的 client），
#      比较串行 vs asyncio.gather 的耗时
#   2. 给上题加 Semaphore(2) 限流，观察耗时变化
#   3. 给上题加 wait_for 超时 10 秒
#   4. 实现"谁先返回就用谁"：用 asyncio.wait(FIRST_COMPLETED)
# =====================================================================

if __name__ == "__main__":
    asyncio.run(main())
