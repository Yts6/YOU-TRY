"""Step 5 · 第一个大模型调用（流式）

用法：
    python first_call.py

说明：
    - 只读本项目自己的 .env（不向上查找父目录）
    - 自动挑选已配置 Key 的平台
    - 支持 DeepSeek / 智谱 / 硅基流动 / 通义千问（都兼容 OpenAI 接口）
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Windows 控制台按 UTF-8 输出，避免中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 只加载本项目根目录的 .env（override=True 保证以本文件为准）
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

# ---------------- 模型配置表 ----------------
PROVIDERS = [
    {
        "name": "DeepSeek",
        "key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
    },
    {
        "name": "智谱 GLM（免费）",
        "key_env": "ZHIPU_API_KEY",
        "base_url_env": "ZHIPU_BASE_URL",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
    {
        "name": "硅基流动",
        "key_env": "SILICONFLOW_API_KEY",
        "base_url_env": "SILICONFLOW_BASE_URL",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-7B-Instruct",
    },
    {
        "name": "通义千问",
        "key_env": "DASHSCOPE_API_KEY",
        "base_url_env": "DASHSCOPE_BASE_URL",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
    },
]


def pick_provider() -> dict:
    """返回第一个配置了非空 Key 的平台。"""
    for p in PROVIDERS:
        if (os.getenv(p["key_env"]) or "").strip():
            return p
    print("[错误] 本项目 .env 里没有任何可用的 API Key。")
    print(f"       请执行： Copy-Item .env.example .env  然后填入至少一个平台的 Key")
    print(f"       .env 路径应为： {BASE_DIR / '.env'}")
    sys.exit(1)


def friendly_error(exc: Exception) -> str:
    """把 SDK 异常翻译成人话。"""
    text = str(exc)
    if "429" in text or "RateLimit" in type(exc).__name__:
        return "触发限流（429）。可能是该 Key 的免费额度用尽，或调用太频繁，稍后重试或换平台。"
    if "401" in text or "Authentication" in type(exc).__name__:
        return "鉴权失败（401）。请检查 Key 是否填对、是否有多余空格。"
    if "403" in text or "AccessDenied" in text:
        return "无该模型权限（403）。换一个模型，或在控制台开通对应模型。"
    if "Connection" in type(exc).__name__ or "Timeout" in type(exc).__name__:
        return "网络连接失败。检查网络/代理，或换一个平台试试。"
    return text


def main() -> None:
    provider = pick_provider()
    base_url = os.getenv(provider["base_url_env"]) or provider["base_url"]

    print(f"[使用平台] {provider['name']}")
    print(f"[模型]     {provider['model']}")
    print(f"[接口]     {base_url}")
    print("-" * 60)

    client = OpenAI(api_key=os.getenv(provider["key_env"]).strip(), base_url=base_url)

    question = "用一句话解释什么是 RAG"
    print(f"[提问] {question}")
    print("[回答] ", end="", flush=True)

    try:
        resp = client.chat.completions.create(
            model=provider["model"],
            messages=[
                {"role": "system", "content": "你是一个简洁的助手"},
                {"role": "user", "content": question},
            ],
            stream=True,
        )
        for chunk in resp:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
    except Exception as exc:  # noqa: BLE001 - 学习脚本，统一翻译成提示
        print()
        print("-" * 60)
        print(f"[调用失败] {type(exc).__name__}")
        print(f"[原因]     {friendly_error(exc)}")
        sys.exit(1)

    print()
    print("-" * 60)
    print("[完成] 流式调用成功 ✅")


if __name__ == "__main__":
    main()
