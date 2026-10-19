"""Step 7-1 · 面向对象 / 装饰器 / 异常

运行： python 01_oop_decorator.py
判断： 能看懂每一行注释，并能独立完成底部练习，就不用再学这块。
"""

import sys
import time
from dataclasses import dataclass, field
from functools import wraps

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------- 1. 类与继承 ----------
class BaseTool:
    """所有工具的基类。LangChain 里每个 Tool 也是这种思路。"""

    name: str = "base"

    def run(self, query: str) -> str:
        # 子类要覆盖这个方法
        raise NotImplementedError("子类必须实现 run()")


class SearchTool(BaseTool):
    name = "search"

    def run(self, query: str) -> str:
        return f"[搜索] 找到关于「{query}」的 3 条结果"


class CalcTool(BaseTool):
    name = "calc"

    def run(self, query: str) -> str:
        return f"[计算] {query} = 42"


# ---------- 2. dataclass：少写样板代码 ----------
@dataclass
class Message:
    role: str
    content: str
    metadata: dict = field(default_factory=dict)  # 注意：可变默认值必须用 default_factory

    def brief(self) -> str:
        return f"{self.role}: {self.content[:20]}"


# ---------- 3. 装饰器：不改函数体就加上额外能力 ----------
def timer(func):
    """最基础的装饰器：统计耗时。"""

    @wraps(func)  # 不加这行，函数名会变成 wrapper
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        cost = time.perf_counter() - start
        print(f"  [{func.__name__}] 耗时 {cost:.4f}s")
        return result

    return wrapper


def retry(times: int = 3):
    """带参数的装饰器：失败自动重试。Agent 调工具失败时就是这么做的。"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    print(f"  第 {i + 1} 次失败：{exc}")
            raise last_exc

        return wrapper

    return decorator


# ---------- 4. 自定义异常 ----------
class ToolError(Exception):
    """自定义异常：让上层能精确区分'工具有问题'和'其它问题'。"""

    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"工具 {tool_name} 出错：{reason}")


_attempts = {"n": 0}


@retry(times=3)
def flaky_call() -> str:
    """模拟前两次失败、第三次成功的接口调用。"""
    _attempts["n"] += 1
    if _attempts["n"] < 3:
        raise ToolError("flaky_api", "网络抖动")
    return "成功拿到数据"


@timer
def main() -> None:
    print("=== 1. 多态：同一个 run()，不同行为 ===")
    for tool in (SearchTool(), CalcTool()):
        print(f"  {tool.name}: {tool.run('python')}")

    print()
    print("=== 2. dataclass ===")
    msg = Message(role="user", content="帮我总结一下这篇论文的核心观点")
    print(f"  {msg.brief()}")
    print(f"  可变默认值是否共享？ {Message('a', 'x').metadata is Message('b', 'y').metadata}"
          "  (False 才对，说明没踩坑)")

    print()
    print("=== 3. 带参数装饰器 + 重试 ===")
    print(f"  结果：{flaky_call()}")

    print()
    print("=== 4. 异常捕获要精确 ===")
    try:
        raise ToolError("search", "超时")
    except ToolError as exc:
        print(f"  捕获到自定义异常 -> tool={exc.tool_name}, reason={exc.reason}")

    print()
    print("=== 5. 上下文管理器（读文件自动关闭）===")
    with open(__file__, encoding="utf-8") as f:
        print(f"  本文件第一行：{f.readline().strip()}")


# =====================================================================
# 练习（做完写进 step7/练习答案/01_answer.py，然后告诉我）：
#   1. 写一个 @count_calls 装饰器，统计函数被调用了几次
#   2. 给 BaseTool 加一个 description 字段，并让每个子类提供自己的描述
#   3. 写一个自定义异常 ContextTooLongError，带 limit 和 actual 两个属性
#   4. 用 dataclass 定义一个 Chunk 类（text, source, page），并加一个 __len__ 方法
# =====================================================================

if __name__ == "__main__":
    main()
