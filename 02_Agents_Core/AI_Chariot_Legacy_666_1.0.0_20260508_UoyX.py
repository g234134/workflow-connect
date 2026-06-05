"""
cleaner_core.py

用 LiteLLM 的 Fallbacks / Retries 方式，集中管理「模型故障轉移」與「重試」。

設計目標：
- 把原本散落在各處的「切模型 / 重試 / timeout」集中到一個地方
- 呼叫端只要給 messages 與想要的主要模型即可
- 可搭配 SmartRouter（OPENAI_API_BASE 指到 http://127.0.0.1:8000/v1）或直接走各家 API
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LLMFallbackPlan:
    """
    LiteLLM fallbacks 的最小封裝。

    primary_model：主要模型
    fallback_models：依序嘗試的備援模型
    retries：每個模型的重試次數（LiteLLM 的 num_retries）
    timeout_s：單次請求 timeout（LiteLLM 的 request_timeout）
    """

    primary_model: str
    fallback_models: List[str]
    retries: int = 2
    timeout_s: float = 30.0

    def as_litellm_fallbacks(self) -> List[Dict[str, str]]:
        # LiteLLM 常見範例：fallbacks=[{"model": "x"}, {"model": "y"}]
        return [{"model": m} for m in self.fallback_models]


def _load_litellm() -> Any:
    try:
        import litellm  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "缺少依賴：litellm。請在『實驗室』環境安裝：pip install litellm"
        ) from e
    return litellm


def smart_completion(
    *,
    messages: List[Dict[str, str]],
    plan: LLMFallbackPlan,
    temperature: float = 0.2,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    用 LiteLLM completion + fallbacks + retries。

    回傳：LiteLLM/OpenAI-compatible 的回應 dict（含 choices[0].message.content）
    """
    litellm = _load_litellm()

    payload: Dict[str, Any] = {
        "model": plan.primary_model,
        "messages": messages,
        "temperature": temperature,
        "fallbacks": plan.as_litellm_fallbacks(),
        "num_retries": int(plan.retries),
        "request_timeout": float(plan.timeout_s),
    }
    if extra:
        payload.update(extra)

    # LiteLLM 的 completion 會依環境變數（OPENAI_API_BASE/KEY 等）決定實際打哪裡
    return litellm.completion(**payload)


def default_smartrouter_plan() -> LLMFallbackPlan:
    """
    預設策略（可按你環境調整）：
    - primary: SmartRouter 端模型（透過 OPENAI_API_BASE 指向本機路由）
    - fallback: Groq / OpenAI 等（若你有各家 key）

    注意：若你只想走 SmartRouter，將 fallback_models 設為 [] 即可。
    """
    # 你目前 SmartRouter 用的是 meta/llama-3.1-8b-instruct；LiteLLM 的 model 名稱
    # 取決於你怎麼配置 provider。這裡提供「可用且容易改」的預設值。
    primary = os.getenv("TANK_PRIMARY_MODEL", "meta/llama-3.1-8b-instruct")
    fallbacks = [
        m.strip()
        for m in os.getenv("TANK_FALLBACK_MODELS", "groq/llama-3.1-8b-instant").split(",")
        if m.strip()
    ]
    return LLMFallbackPlan(primary_model=primary, fallback_models=fallbacks, retries=2, timeout_s=30.0)

