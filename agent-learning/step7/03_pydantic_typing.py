"""Step 7-3 · 类型注解 + Pydantic

运行： python 03_pydantic_typing.py
为什么重要：
  - LangChain / FastAPI 全是用类型注解驱动的
  - 能读懂 -> 才看得懂源码；会写 -> FastAPI 接口才不会 500
"""

import sys
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------- 1. 基础类型注解（只是给人和 IDE 看的，运行时不强制）----------
def greet(name: str, times: int = 1) -> str:
    return ("你好 " + name + "! ") * times


def maybe_none(value: Optional[str] = None) -> str:
    # Optional[str] 等价于 str | None
    return value if value is not None else "(空)"


# ---------- 2. Pydantic：运行时真校验 ----------
class ToolCall(BaseModel):
    """对应模型返回的 tool_call 结构。"""

    name: str = Field(..., min_length=1, description="工具名")
    arguments: dict[str, Any] = Field(default_factory=dict)
    # Literal 限制取值范围
    risk: Literal["low", "medium", "high"] = "low"


class UserQuery(BaseModel):
    """对应 FastAPI 的请求体。"""

    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=50)  # ge=大于等于, le=小于等于
    use_rerank: bool = False
    session_id: Optional[str] = None

    # 自定义校验：在字段级做业务规则
    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("问题不能只有空白字符")
        return v.strip()


class RagAnswer(BaseModel):
    """对应给前端的返回结构。用 Pydantic 保证输出格式稳定。"""

    answer: str
    sources: list[str] = Field(default_factory=list)
    latency_ms: int = 0

    def brief(self) -> str:
        return f"{self.answer[:30]}... ({len(self.sources)} 个来源, {self.latency_ms}ms)"


def main() -> None:
    print("=== 1. 基础注解（运行时其实不检查）===")
    print(f"  {greet('喻太胜', 2)}")
    print(f"  maybe_none() -> {maybe_none()}")
    print(f"  maybe_none('有值') -> {maybe_none('有值')}")
    print("  注意： greet('x') 传错类型 Python 不会报错，Pydantic 才会")

    print()
    print("=== 2. Pydantic 自动校验与默认值 ===")
    q = UserQuery(question="  什么是 RAG  ")  # 注意前后有空格
    print(f"  输入 '  什么是 RAG  '")
    print(f"  -> question='{q.question}'（自动 strip 了）")
    print(f"  -> top_k={q.top_k}（默认值自动填上）")
    print(f"  -> use_rerank={q.use_rerank}")

    print()
    print("=== 3. 校验失败会抛什么（这是要会看的报错）===")
    for bad in [
        {"question": "ok", "top_k": 999},        # 超出范围
        {"question": "   "},                      # 空白
        {"top_k": 3},                             # 缺必填字段
    ]:
        try:
            UserQuery(**bad)
            print(f"  {bad} -> 通过")
        except ValidationError as exc:
            first = exc.errors()[0]
            print(f"  {bad}")
            print(f"     ❌ {first['loc']} : {first['msg']} (类型 {first['type']})")

    print()
    print("=== 4. 模型返回的值也能校验 ===")
    call = ToolCall(name="search", arguments={"query": "python"}, risk="medium")
    print(f"  {call.model_dump()}")  # model_dump() 转成 dict
    print(f"  JSON: {call.model_dump_json()}")

    print()
    print("=== 5. 结构化输出：让返回值格式永远可控 ===")
    ans = RagAnswer(answer="RAG 是检索增强生成，先检索再生成", sources=["doc1.pdf:p3"], latency_ms=812)
    print(f"  {ans.brief()}")

    print()
    print("=== 关键：这些类型注解就是 LangChain 源码的阅读钥匙 ===")
    for code, meaning in [
        ("def f(x: str) -> list[str]", "接收字符串，返回字符串列表"),
        ("Optional[str] = None", "可以为空"),
        ("Literal['a','b']", "只能是 a 或 b"),
        ("dict[str, Any]", "键是字符串，值任意"),
        ("Field(default=5, ge=1)", "默认 5，最小 1"),
    ]:
        print(f"  {code:<32} # {meaning}")


# =====================================================================
# 练习：
#   1. 定义 Document 模型：text, source, page(>=1), metadata(dict)
#   2. 给 Document 加校验：text 不能超过 10000 字
#   3. 定义 ChatMessage：role 只能是 system/user/assistant
#   4. 定义 AgentState：messages(list[ChatMessage]), steps(int, 默认0), done(bool)
#      —— 这就是 LangGraph State 的真实长相
# =====================================================================

if __name__ == "__main__":
    main()
