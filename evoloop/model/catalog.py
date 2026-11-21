"""The Claude models this version knows: their ids, prices, and the effort levels each accepts.

Used to offer a choice of model, to check that an effort level suits the model, and to price a run when
the brief gives no `agents.prices`. It is a dated list, not a live one: a price you give in
`agents.prices` always wins, and a model that is not here can still be used by its id (it is then
unpriced until you give a price, and its effort is sent as you set it).

Prices are Anthropic's first-party API rates in dollars per million tokens, as of AS_OF; other platforms
price separately. Reasoning tokens are billed as output tokens."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

AS_OF = "2026-11-03"
EFFORTS = ("low", "medium", "high", "xhigh", "max")
ALL = EFFORTS
NO_XHIGH = ("low", "medium", "high", "max")

# id: name, input and output price, effort levels accepted, the model's own default effort, and whether the API's
# server-side fallback on a refusal is available for it.
MODELS: Dict[str, Dict[str, Any]] = {
    "claude-opus-5-5": {"name": "Claude Opus 5.5", "input": 4.00, "output": 20.00, "efforts": ALL, "own_default": "medium",
                        "fallbacks": True, "note": "the current Opus"},
    "claude-sonnet-5-5": {"name": "Claude Sonnet 5.5", "input": 2.00, "output": 10.00, "efforts": ALL, "own_default": "high",
                          "fallbacks": True, "note": "the current Sonnet: faster and cheaper"},
    "claude-haiku-5-5": {"name": "Claude Haiku 5.5", "input": 0.10, "output": 0.50, "efforts": ALL, "own_default": "medium",
                         "fallbacks": False, "note": "the cheapest; the price is for prompts up to 100K tokens"},
    "claude-fable-5-2": {"name": "Claude Fable 5.2", "input": 8.00, "output": 40.00, "efforts": ALL, "own_default": "high",
                         "fallbacks": True, "note": "the most capable; single calls can take minutes"},
    "claude-fable-5-1": {"name": "Claude Fable 5.1", "input": 10.00, "output": 50.00, "efforts": ALL, "own_default": "high",
                         "fallbacks": True, "note": ""},
    "claude-opus-5": {"name": "Claude Opus 5", "input": 5.00, "output": 25.00, "efforts": ALL, "own_default": "high",
                      "fallbacks": True, "note": ""},
    "claude-opus-4-8": {"name": "Claude Opus 4.8", "input": 5.00, "output": 25.00, "efforts": ALL, "own_default": "high",
                        "fallbacks": False, "note": ""},
    "claude-opus-4-7": {"name": "Claude Opus 4.7", "input": 5.00, "output": 25.00, "efforts": ALL, "own_default": "high",
                        "fallbacks": False, "note": ""},
    "claude-sonnet-5": {"name": "Claude Sonnet 5", "input": 2.00, "output": 10.00, "efforts": ALL, "own_default": "high",
                        "fallbacks": False, "note": ""},
    "claude-opus-4-6": {"name": "Claude Opus 4.6", "input": 5.00, "output": 25.00, "efforts": NO_XHIGH, "own_default": "high",
                        "fallbacks": False, "note": ""},
    "claude-sonnet-4-6": {"name": "Claude Sonnet 4.6", "input": 3.00, "output": 15.00, "efforts": NO_XHIGH, "own_default": "high",
                          "fallbacks": False, "note": ""},
    "claude-haiku-4-5": {"name": "Claude Haiku 4.5", "input": 1.00, "output": 5.00, "efforts": (), "own_default": None,
                         "fallbacks": False, "note": "takes no effort setting"},
}
OFFERED = ("claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-fable-5-2")   # the current generation


def rates(model: Any, given: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, float]], str]:
    """A model's prices and where they come from: the brief's `agents.prices`, else this list, else none."""
    own = (given or {}).get(model)
    if isinstance(own, dict) and isinstance(own.get("input"), (int, float)) and isinstance(own.get("output"), (int, float)):
        return {"input": float(own["input"]), "output": float(own["output"])}, "agents.prices"
    known = MODELS.get(model)
    if known:
        return {"input": known["input"], "output": known["output"]}, "the built-in list of %s" % AS_OF
    return None, "no price"


def effort_to_send(model: Any, effort: Any) -> Optional[str]:
    """The effort to put in a request, or None to leave it to the model: when none is set, when the setting
    is `model_default`, or when the model is known not to accept that level (the plan warns of it)."""
    if effort in (None, "", "model_default"):
        return None
    known = MODELS.get(model)
    if known is not None and effort not in known["efforts"]:   # a level this model is known to refuse is left out
        return None
    return str(effort)


def fault(model: Any, effort: Any) -> Optional[str]:
    """Why this effort does not suit this model, when the model is known; None otherwise."""
    known = MODELS.get(model)
    if known is None or effort in (None, "", "model_default"):
        return None
    if not known["efforts"]:
        return "%s takes no effort setting; it will be left out for that model" % model
    if effort not in known["efforts"]:
        return "%s does not accept effort %s (it accepts: %s)" % (model, effort, ", ".join(known["efforts"]))
    return None
