"""大模型客户端封装

把 first_call.py 里的"平台选择 + 调用 + 错误翻译"抽出来，
让 main.py 只管 HTTP 层，不掺和模型细节。

设计要点：
  - 用 AsyncOpenAI 而不是 OpenAI：FastAPI 是异步的，用同步客户端会阻塞事件循环
  - 单例客户端：每次请求新建会浪费连接
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)


# ---------------- 平台配置 ----------------
PROVIDERS = [
    {
        "name": "智谱 GLM",
        "key_env": "ZHIPU_API_KEY",
        "base_url_env": "ZHIPU_BASE_URL",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
    {
        "name": "DeepSeek",
        "key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
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


class NoProviderError(RuntimeError):
    """没有任何平台配置了 Key。"""


class LLMClient:
    """模型客户端。同步/异步两套，按需使用。"""

    def __init__(self) -> None:
        self.provider = self._pick_provider()
        self.base_url = (
            os.getenv(self.provider["base_url_env"]) or self.provider["base_url"]
        )
        self._api_key = os.getenv(self.provider["key_env"]).strip()

        # 复用连接，不每次新建
        self._async_client = AsyncOpenAI(api_key=self._api_key, base_url=self.base_url)
        self._sync_client = OpenAI(api_key=self._api_key, base_url=self.base_url)

    # ---------- 内部工具 ----------
    @staticmethod
    def _pick_provider() -> dict:
        for p in PROVIDERS:
            if (os.getenv(p["key_env"]) or "").strip():
                return p
        raise NoProviderError(
            "没有任何可用的 API Key。请复制 .env.example 为 .env 并填入 Key。"
        )

    @property
    def model(self) -> str:
        return self.provider["model"]

    @property
    def provider_name(self) -> str:
        return self.provider["name"]

    async def aclose(self) -> None:
        await self._async_client.close()

    # ---------- 同步调用（脚本/测试用）----------
    def ask_sync(
        self,
        question: str,
        system_prompt: str = "你是一个简洁的助手",
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> dict:
        start = time.perf_counter()
        resp = self._sync_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._build_result(resp, start)

    # ---------- 异步调用（FastAPI 用）----------
    async def ask(
        self,
        question: str,
        system_prompt: str = "你是一个简洁的助手",
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> dict:
        start = time.perf_counter()
        resp = await self._async_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._build_result(resp, start)

    # ---------- 统一结果结构 ----------
    def _build_result(self, resp, start: float) -> dict:
        usage = getattr(resp, "usage", None)
        return {
            "answer": (resp.choices[0].message.content or "").strip(),
            "model": self.model,
            "provider": self.provider_name,
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "usage_total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        }


# ---------------- 异常翻译（Step 9 会用到）----------------
class ModelCallError(Exception):
    """包装模型调用异常，附带给用户看的提示。"""

    def __init__(self, error_type: str, message: str, suggestion: str = "", status: int = 502):
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
        self.status = status
        super().__init__(message)


def translate_error(exc: Exception) -> ModelCallError:
    """把 SDK 的异常翻译成带 HTTP 状态码的友好错误。"""
    text = str(exc)
    name = type(exc).__name__

    if "429" in text or "RateLimit" in name:
        return ModelCallError(
            "rate_limited",
            "触发模型平台的限流（429）。",
            "稍后重试，或在平台控制台检查免费额度是否用尽。",
            status=429,
        )
    if "401" in text or "Authentication" in name:
        return ModelCallError(
            "auth_failed",
            "API Key 鉴权失败（401）。",
            "检查 .env 里的 Key 是否填对、是否有多余空格。",
            status=401,
        )
    if "403" in text or "AccessDenied" in text:
        return ModelCallError(
            "model_denied",
            "当前 Key 没有该模型的权限（403）。",
            "换一个模型，或在平台控制台开通对应模型。",
            status=403,
        )
    if "Timeout" in name or "timed out" in text.lower():
        return ModelCallError(
            "timeout",
            "模型响应超时。",
            "稍后重试；若频繁超时，考虑降低 max_tokens。",
            status=504,
        )
    if "Connection" in name or "APIConnection" in name:
        return ModelCallError(
            "connection_error",
            "无法连接到模型平台。",
            "检查网络/代理设置。",
            status=503,
        )
    return ModelCallError(
        "upstream_error",
        f"模型调用失败：{text[:200]}",
        "查看服务端日志获取详细信息。",
        status=502,
    )


# ---------------- 全局单例 ----------------
_client: LLMClient | None = None


def get_client() -> LLMClient:
    """获取全局客户端单例。第一次调用时初始化。"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
