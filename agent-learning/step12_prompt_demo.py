"""Step 12 · Prompt 模板库演示

运行： python step12_prompt_demo.py

这个脚本做两件事：
  1. 展示模板库怎么用（离线，不花钱）
  2. 挑 2 个模板真实调用模型，对比"有约束 vs 没约束"的效果
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prompts.templates import get_prompt, list_templates  # noqa: E402
from llm_client import get_client  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def show_library() -> None:
    print("=" * 70)
    print("Prompt 模板库清单")
    print("=" * 70)
    for i, t in enumerate(list_templates(), 1):
        print(f"{i:>2}. {t['name']:<20} {t['title']}")
        print(f"    用途: {t['purpose']}")
        print(f"    场景: {t['scenario']}")
        print()


def demo_render_offline() -> None:
    print("=" * 70)
    print("离线演示：渲染模板（不调用模型）")
    print("=" * 70)

    p = get_prompt(
        "qa_with_citation",
        context="[来源1] RAG 全称 Retrieval-Augmented Generation，即检索增强生成。\n"
                "[来源2] RAG 通过外部知识库检索，缓解大模型幻觉问题。",
        question="什么是 RAG？",
    )
    print(p)
    print()
    print("-" * 70)

    try:
        get_prompt("summarize", text="xxx")
    except ValueError as exc:
        print(f"[缺少变量的报错] {exc}")


def demo_real_call() -> None:
    """对比实验：无约束 vs 有约束，看幻觉差异。"""
    print()
    print("=" * 70)
    print("实验：约束 Prompt 能否减少幻觉")
    print("=" * 70)

    client = get_client()

    # ---------- A. 无约束 ----------
    print("\n【A】无约束：直接问（历史证明会答错）")
    try:
        r = client.ask_sync("什么是 MCP 协议？", max_tokens=150)
        print(f"  模型: {r['answer']}")
        print(f"  (耗时 {r['latency_ms']}ms)")
    except Exception as exc:  # noqa: BLE001
        print(f"  调用失败: {exc}")

    # ---------- B. 有约束：要求只基于给定材料，不知道就说不知道 ----------
    print("\n【B】有约束：给了正确材料，并要求只基于材料回答")
    prompt_b = get_prompt(
        "qa_with_citation",
        context="[来源1] MCP 全称 Model Context Protocol（模型上下文协议），"
                "由 Anthropic 于 2024 年 11 月提出。\n"
                "[来源2] MCP 是一个开放标准，让大模型能标准化地调用外部工具和数据源。\n"
                "[来源3] MCP 采用客户端-服务器架构，支持 Claude、Cursor 等客户端。",
        question="什么是 MCP 协议？",
    )
    try:
        r = client.ask_sync(prompt_b, max_tokens=250)
        print(f"  模型: {r['answer']}")
        print(f"  (耗时 {r['latency_ms']}ms)")
    except Exception as exc:  # noqa: BLE001
        print(f"  调用失败: {exc}")

    # ---------- C. 有约束 + 材料里没有答案 ----------
    print("\n【C】有约束 + 材料里没有答案：应该明确拒答，而不是编造")
    prompt_c = get_prompt(
        "qa_with_citation",
        context="[来源1] Python 是一种编程语言，1991 年发布。\n"
                "[来源2] FastAPI 是一个现代 Python Web 框架。",
        question="MCP 协议的核心组件有哪些？",
    )
    try:
        r = client.ask_sync(prompt_c, max_tokens=150)
        print(f"  模型: {r['answer']}")
        print(f"  (耗时 {r['latency_ms']}ms)")
    except Exception as exc:  # noqa: BLE001
        print(f"  调用失败: {exc}")

    print()
    print("=" * 70)
    print("结论：")
    print("  A 无约束 -> 模型靠参数记忆，答错（微控制器协议）")
    print("  B 给材料 -> 基于事实回答，正确")
    print("  C 没材料 -> 明确说无法回答，而不是编造")
    print("  这就是 RAG + 约束 Prompt 的核心价值")
    print("=" * 70)


if __name__ == "__main__":
    show_library()
    demo_render_offline()
    demo_real_call()
