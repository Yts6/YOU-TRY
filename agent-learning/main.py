"""Step 8 · FastAPI 服务：把模型调用包成 REST 接口

启动：
    uvicorn main:app --reload
    或： python main.py

验收：
    浏览器打开 http://127.0.0.1:8000/docs
    点开 POST /ask -> Try it out -> 输入问题 -> Execute

接口清单：
    GET  /             服务信息
    GET  /health       健康检查（含 Key 配置状态）
    POST /ask          单轮问答
    GET  /ask          便捷 GET 版（浏览器可直接测）
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from llm_client import ModelCallError, NoProviderError, get_client, translate_error
from schemas import AskRequest, AskResponse, ErrorResponse, HealthResponse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------- 生命周期：启动时初始化客户端 ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 新版推荐的启动/关闭钩子（替代已废弃的 @app.on_event）。"""
    print("[启动] 正在初始化模型客户端...")
    try:
        client = get_client()
        app.state.ready = True
        app.state.provider = client.provider_name
        app.state.model = client.model
        print(f"[启动] 就绪：{client.provider_name} / {client.model}")
    except NoProviderError as exc:
        app.state.ready = False
        app.state.provider = "-"
        app.state.model = "-"
        print(f"[启动] 警告：{exc}")
        print("[启动] 服务仍会运行，但 /ask 会返回 503")
    yield
    print("[关闭] 正在释放客户端...")
    try:
        await get_client().aclose()
    except Exception:  # noqa: BLE001
        pass


app = FastAPI(
    title="Agent Learning API",
    description="AI Agent 学习项目 · Step 8 第一个 FastAPI 服务",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------- 全局异常处理器（Step 9 的核心）----------------
@app.exception_handler(ModelCallError)
async def model_error_handler(request: Request, exc: ModelCallError) -> JSONResponse:
    """模型调用出错时，返回统一结构，而不是 500 堆栈。"""
    print(f"[错误] {exc.error_type}: {exc.message}")
    return JSONResponse(
        status_code=exc.status,
        content=ErrorResponse(
            error=exc.error_type,
            message=exc.message,
            suggestion=exc.suggestion,
        ).model_dump(),
    )


# ---------------- 路由 ----------------
@app.get("/", summary="服务信息")
async def root() -> dict:
    return {
        "service": "Agent Learning API",
        "step": "Step 8",
        "docs": "/docs",
        "endpoints": ["/health", "/ask"],
    }


@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health(request: Request) -> HealthResponse:
    """前端/运维用它判断服务是否可用。"""
    ready = getattr(request.app.state, "ready", False)
    return HealthResponse(
        status="ok" if ready else "degraded",
        provider=request.app.state.provider,
        model=request.app.state.model,
        api_key_configured=ready,
    )


@app.post("/ask", response_model=AskResponse, summary="单轮问答（推荐）")
async def ask(body: AskRequest) -> AskResponse:
    """接收问题 -> 调模型 -> 返回答案。

    用 async def + AsyncOpenAI：并发请求时不会互相阻塞。
    """
    try:
        client = get_client()
        result = await client.ask(
            question=body.question,
            system_prompt=body.system_prompt,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except NoProviderError as exc:
        raise ModelCallError("no_provider", str(exc), "请配置 .env 中的 API Key。", 503) from exc
    except Exception as exc:  # noqa: BLE001 - 统一翻译成友好错误
        raise translate_error(exc) from exc

    return AskResponse(**result)


@app.get("/ask", response_model=AskResponse, summary="单轮问答（GET 便捷版）")
async def ask_get(
    question: str = Query(..., min_length=1, max_length=2000, description="你的问题"),
) -> AskResponse:
    """方便在浏览器地址栏直接测试，不用打开 /docs。"""
    try:
        result = await get_client().ask(question=question)
    except NoProviderError as exc:
        raise ModelCallError("no_provider", str(exc), "请配置 .env 中的 API Key。", 503) from exc
    except Exception as exc:  # noqa: BLE001
        raise translate_error(exc) from exc

    return AskResponse(**result)


# ---------------- 本地直接运行 ----------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
