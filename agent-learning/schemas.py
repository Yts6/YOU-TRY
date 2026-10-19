"""Pydantic 数据模型（Step 7-3 的实战应用）

这些类定义了什么数据能进来、什么数据能出去。
FastAPI 会自动：
  - 校验请求体 -> 不合法直接返回 422
  - 生成 /docs 的交互文档
  - 校验响应结构
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------- 请求模型 ----------------

class AskRequest(BaseModel):
    """POST /ask 的请求体。"""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户问题",
        examples=["什么是 RAG？"],
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="采样温度，越低越稳定，越高越发散",
    )
    max_tokens: int = Field(
        default=512,
        ge=1,
        le=4096,
        description="最大生成 token 数",
    )
    system_prompt: str = Field(
        default="你是一个简洁的助手",
        max_length=2000,
        description="系统提示词",
    )

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("问题不能只有空白字符")
        return v.strip()


# ---------------- 响应模型 ----------------

class AskResponse(BaseModel):
    """POST /ask 的响应体。"""

    answer: str = Field(..., description="模型回答")
    model: str = Field(..., description="实际使用的模型")
    provider: str = Field(..., description="实际使用的平台")
    latency_ms: int = Field(..., description="本次调用耗时（毫秒）")
    usage_total_tokens: int | None = Field(
        default=None, description="消耗的总 token 数（若平台返回）"
    )


class HealthResponse(BaseModel):
    """GET /health 的响应体。"""

    status: Literal["ok", "degraded"] = Field(..., description="服务状态")
    provider: str = Field(..., description="当前配置的平台")
    model: str = Field(..., description="当前配置的模型")
    api_key_configured: bool = Field(..., description="API Key 是否已配置")


class ErrorResponse(BaseModel):
    """统一错误响应。所有异常都返回这个结构，前端好处理。"""

    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="人话解释")
    suggestion: str = Field(default="", description="建议怎么解决")
