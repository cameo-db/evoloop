"""Backend: the Anthropic Python SDK. Credentials come from the environment (ANTHROPIC_API_KEY)."""
from __future__ import annotations

from typing import Any, Dict, Tuple

from . import catalog
from .base import QUOTA_PATTERN, ModelError, QuotaExhausted, TransientError, quota_reset_time


class AnthropicBackend:
    def __init__(self, cfg: Any, client: Any = None):
        self.cfg = cfg
        if client is None:
            import anthropic  # imported only here, so the core has no hard dependency on it
            # Retries are handled by ModelClient, so the SDK's own are switched off.
            client = anthropic.Anthropic(max_retries=0, timeout=float(cfg.model.call_timeout_seconds))
        self.client = client

    def call(self, role: str, system: str, user: str, schema: Dict[str, Any],
             context: Any = None) -> Tuple[str, Dict[str, Any]]:
        import anthropic
        model = self.cfg.model_for(role)
        if not model:
            raise ModelError("no model is set for role %r (give agents.default_model)" % role)
        effort = getattr(self.cfg, "effort_for", lambda _: None)(role)
        beta, kwargs = request(model, effort, getattr(self.cfg.model, "fallbacks", "off"), int(self.cfg.model.max_tokens),
                               system, user)
        try:
            create = self.client.beta.messages.create if beta else self.client.messages.create
            response = create(**kwargs)
        except anthropic.RateLimitError as exc:
            raise TransientError("rate limited: %s" % exc)
        except anthropic.APIStatusError as exc:
            if exc.status_code == 402 or QUOTA_PATTERN.search(str(exc.message or "")):
                raise QuotaExhausted("API error %s: %s" % (exc.status_code, exc.message),
                                     quota_reset_time(str(exc.message or "")))
            if exc.status_code >= 500 or exc.status_code in (408, 409):
                raise TransientError("server error %s" % exc.status_code)
            raise ModelError("API error %s: %s" % (exc.status_code, exc.message))
        except anthropic.APIConnectionError as exc:
            raise TransientError("connection error: %s" % exc)
        given = self.cfg.model.prices

        def cost(usage: Dict[str, Any]) -> Any:   # by the model that answered (a fallback is priced as itself), else the one asked for
            return price(catalog.rates(usage.get("model"), given)[0] or catalog.rates(model, given)[0], usage)
        try:
            text, usage = parse_message(response)
        except ModelError as exc:
            if getattr(exc, "usage", None):
                exc.usage["cost_usd"] = cost(exc.usage)
            raise
        usage["cost_usd"] = cost(usage)
        usage["effort"] = kwargs.get("output_config", {}).get("effort")
        return text, usage


def request(model: str, effort: Any, fallbacks: Any, max_tokens: int, system: str, user: str) -> Tuple[bool, Dict[str, Any]]:
    """The arguments of one Messages request, and whether it goes to the beta endpoint.

    Effort goes in `output_config`; it is left out when none is set or the model takes none, and the model
    then uses its own default. Thinking is not set: current models think adaptively by themselves, and how
    deeply follows the effort. With `agents.fallbacks: default`, a model that supports it is given the
    API's server-side fallback, so a request the model declines is answered by another model in the same
    call rather than lost; the answering model is in the reply and is priced as itself."""
    kwargs: Dict[str, Any] = {"model": model, "max_tokens": max_tokens, "system": system,
                              "messages": [{"role": "user", "content": user}]}
    send = catalog.effort_to_send(model, effort)
    if send:
        kwargs["output_config"] = {"effort": send}
    beta = fallbacks == "default" and bool((catalog.MODELS.get(model) or {}).get("fallbacks"))
    if beta:
        kwargs.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    return beta, kwargs


def price(rates: Any, usage: Dict[str, Any]) -> Any:
    """Cost in dollars from `model.prices` (dollars per million tokens), or None when no price is set."""
    if not rates or usage.get("input_tokens") is None or usage.get("output_tokens") is None:
        return None
    return (usage["input_tokens"] * rates["input"] + usage["output_tokens"] * rates["output"]) / 1e6


def parse_message(response: Any) -> Tuple[str, Dict[str, Any]]:
    """Text and token counts of a Messages API response."""
    usage = {"input_tokens": getattr(response.usage, "input_tokens", None),
             "output_tokens": getattr(response.usage, "output_tokens", None),
             "model": getattr(response, "model", None)}
    if response.stop_reason in ("refusal", "max_tokens"):
        # The tokens were used and are charged, though the reply cannot be.
        error = ModelError("the model declined the request" if response.stop_reason == "refusal"
                           else "the reply was cut off at agents.max_tokens; raise it")
        error.usage = usage
        raise error
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, usage
