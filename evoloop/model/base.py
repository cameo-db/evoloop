"""The model client: one interface over interchangeable backends (spec section 10)."""
from __future__ import annotations

import importlib.util
import json
import logging
import os
import random
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from .quota import QUOTA_PATTERN, QUOTA_RETRY_SECONDS, quota_reset_time  # noqa: F401

log = logging.getLogger("evoloop")


class ModelError(Exception):
    """The call failed in a way that retrying the same request will not fix."""


class TransientError(ModelError):
    """Rate limit, overload or network trouble; retried with backoff."""


class BudgetExceeded(ModelError):
    """`budget.model_calls` has been reached."""


class QuotaExhausted(ModelError):
    """The account's spend or usage limit refused the call. Retrying cannot help until the limit resets
    (or is raised), so the client pauses every agent call until `reset_at` and the call is not charged."""

    def __init__(self, message: str, reset_at: Optional[float] = None):
        super().__init__(message)
        self.reset_at = reset_at


class AgentsPaused(Exception):
    """Raised to a caller that cannot go on without an agent's answer while calls are paused. The caller
    leaves its work as it stands and takes it up again once the limit has reset."""


_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool}


def validate(value: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Check `value` against the subset of JSON Schema that the agent schemas use."""
    errors: List[str] = []
    kinds = schema.get("type")
    if kinds is not None:
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not any(_is_type(value, kind) for kind in kinds):
            return ["%s: expected %s, got %s" % (path, " or ".join(kinds), type(value).__name__)]
    if "enum" in schema and value not in schema["enum"]:
        errors.append("%s: %r is not one of %s" % (path, value, schema["enum"]))
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append("%s: missing required key %r" % (path, key))
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                errors.extend(validate(value[key], sub, "%s.%s" % (path, key)))
        extra = schema.get("additionalProperties")
        if isinstance(extra, dict):
            for key, item in value.items():
                if key not in schema.get("properties", {}):
                    errors.extend(validate(item, extra, "%s.%s" % (path, key)))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append("%s: needs at least %d item(s), got %d" % (path, schema["minItems"], len(value)))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append("%s: allows at most %d item(s), got %d" % (path, schema["maxItems"], len(value)))
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(validate(item, schema["items"], "%s[%d]" % (path, i)))
    return errors


def _is_type(value: Any, kind: str) -> bool:
    if kind == "null":
        return value is None
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, _TYPES[kind])


def extract_json(text: str) -> Dict[str, Any]:
    """Find the single JSON object in a model reply, tolerating code fences and surrounding prose."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidates = [fenced.group(1)] if fenced else []
    candidates.append(text)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    raise ModelError("the reply is not a single JSON object")


class ModelClient:
    def __init__(self, backend: Any, max_concurrent: int = 4, max_calls: Optional[int] = None,
                 calls_used: int = 0, max_retries: int = 4, backoff_seconds: float = 2.0):
        self.backend = backend
        self.max_calls = max_calls
        self.calls_used = calls_used
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.paused_until = 0.0      # set by a spend/usage-limit refusal: no call is made before then
        self.pause_reason = ""
        self._slots = threading.Semaphore(max_concurrent)
        self._lock = threading.Lock()

    def exhausted(self) -> bool:
        return self.max_calls is not None and self.calls_used >= self.max_calls

    def paused(self) -> float:
        """Seconds left of a pause set by a spend/usage-limit refusal; 0 when calls may be made."""
        return max(0.0, self.paused_until - time.time())

    def pause(self, exc: "QuotaExhausted") -> None:
        """Hold every call back until the limit resets: until the time the refusal names, else for
        `QUOTA_RETRY_SECONDS`, after which one call is let through to see whether the limit still holds."""
        named = exc.reset_at if exc.reset_at and exc.reset_at > time.time() else None
        with self._lock:
            first = self.paused_until <= time.time()
            self.paused_until = max(self.paused_until, named or time.time() + QUOTA_RETRY_SECONDS)
            self.pause_reason = str(exc)
        if first:
            log.warning("agent calls paused until %s: the account's limit refused a call (%s). Jobs already "
                        "queued go on; a refused call is not charged to budget.model_calls",
                        time.strftime("%Y-%m-%d %H:%M", time.localtime(self.paused_until)), str(exc)[:200])

    def complete(self, role: str, system: str, user: str, schema: Dict[str, Any],
                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.complete_with_usage(role, system, user, schema, context)[0]

    def complete_with_usage(self, role: str, system: str, user: str, schema: Dict[str, Any],
                            context: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """One model call turned into a JSON object. `context` is the structured form of `user`;
        only the stub backend reads it."""
        with self._lock:
            if self.paused_until > time.time():
                raise QuotaExhausted("agent calls are paused until %s: %s" % (
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(self.paused_until)), self.pause_reason[:200]),
                    self.paused_until)
            if self.exhausted():
                raise BudgetExceeded("budget.model_calls (%s) reached" % self.max_calls)
            self.calls_used += 1
        attempt = 0
        with self._slots:
            started = time.time()
            while True:
                try:
                    reply, usage = self.backend.call(role, system, user, schema, context)
                    break
                except QuotaExhausted as exc:   # refused by the account's limit: not charged, and pause
                    with self._lock:
                        self.calls_used = max(0, self.calls_used - 1)
                    self.pause(exc)
                    raise
                except TransientError:
                    attempt += 1
                    if attempt > self.max_retries:
                        raise
                    time.sleep(self.backoff_seconds * (2 ** (attempt - 1)) * (0.5 + random.random()))
            usage = dict(usage or {}, seconds=time.time() - started)   # includes retries and backoff
        # The reply as the model wrote it goes with the result or the error, so that the caller can
        # keep every attempt for a later audit, a rejected one included.
        raw = reply if isinstance(reply, str) else None
        try:
            if isinstance(reply, str):
                reply = extract_json(reply)
            if not isinstance(reply, dict):
                raise ModelError("the reply is not a JSON object")
        except ModelError as exc:
            exc.raw, exc.usage = raw, usage
            raise
        if raw is not None:
            usage["raw"] = raw
        return reply, usage


class StubBackend:
    """Loads a Python module exposing `respond(role, context) -> dict`; deterministic and offline."""

    def __init__(self, module_path: Optional[str], module: Any = None):
        self._lock = threading.Lock()
        if module is not None:
            self.module = module   # the built-in stub: an object with `respond`, not a file
            return
        if not os.path.isfile(module_path):
            raise ModelError("model.stub_module %r does not exist" % module_path)
        spec = importlib.util.spec_from_file_location("evoloop_stub_%d" % (abs(hash(module_path)) % 10 ** 8),
                                                      module_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        if not callable(getattr(self.module, "respond", None)):
            raise ModelError("stub module %r must define respond(role, context)" % module_path)
        self._lock = threading.Lock()

    def call(self, role, system, user, schema, context):
        with self._lock:
            try:
                reply = self.module.respond(role, dict(context or {}, _system=system, _user=user))
            except Exception as exc:  # a stub's bug is a failed call, not a crashed run
                raise ModelError("stub raised %s: %s" % (type(exc).__name__, exc))
        return reply, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "model": "stub"}


def make_client(cfg: Any, calls_used: int = 0) -> ModelClient:
    backend_name = cfg.model.backend
    if backend_name == "stub":
        path = cfg.model.stub_module
        if not path:
            from .generic_stub import GenericStub
            backend: Any = StubBackend(None, module=GenericStub(cfg))   # a dry run on any project
        else:
            backend = StubBackend(path if os.path.isabs(path) else os.path.join(cfg.project_dir, path))
    elif backend_name == "anthropic_api":
        from .anthropic_api import AnthropicBackend
        backend = AnthropicBackend(cfg)
    else:
        from .claude_code import ClaudeCodeBackend
        backend = ClaudeCodeBackend(cfg)
    return ModelClient(backend, max_concurrent=cfg.model.max_concurrent_calls,
                       max_calls=cfg.budget.max_model_calls, calls_used=calls_used,
                       max_retries=cfg.model.max_retries)
