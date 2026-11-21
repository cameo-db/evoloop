"""Backend: Claude Code run non-interactively as a subprocess, with no tools.

Invocation checked against `claude --help` (2.1.311): the prompt goes on standard input,
`--tools ""` disables every built-in tool and `--strict-mcp-config` drops MCP servers.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Tuple

from .base import QUOTA_PATTERN, ModelError, QuotaExhausted, TransientError, quota_reset_time


def build_argv(binary: str, system: str, model: Any = None, effort: Any = None) -> List[str]:
    argv = [binary, "--print", "--output-format", "json", "--tools", "", "--strict-mcp-config",
            "--disable-slash-commands", "--no-session-persistence", "--system-prompt", system]
    from . import catalog
    effort = catalog.effort_to_send(model, effort)      # an effort the model does not take is left out, not sent to fail
    if effort:   # checked against `claude --help` (2.1.329): low, medium, high, xhigh, max
        argv += ["--effort", str(effort)]
    if model:
        argv += ["--model", str(model)]
    return argv


def parse_output(stdout: str) -> Tuple[str, Dict[str, Any]]:
    """The reply text and token counts from `claude --print --output-format json`."""
    try:
        data = json.loads(stdout)
    except ValueError:
        raise ModelError("claude returned output that is not JSON: %r" % stdout[:200])
    if isinstance(data, list):  # some versions print the whole event list
        data = next((item for item in reversed(data) if isinstance(item, dict) and item.get("type") == "result"),
                    None)
    if not isinstance(data, dict) or data.get("type") != "result":
        raise ModelError("claude output has no result object")
    if data.get("is_error") or data.get("subtype") != "success":
        status = data.get("api_error_status")
        message = "claude reported an error (%s): %s" % (data.get("subtype"), str(data.get("result"))[:300])
        if status == 402 or QUOTA_PATTERN.search(str(data.get("result") or "")):
            raise QuotaExhausted(message, quota_reset_time(str(data.get("result") or "")))
        if status in (408, 409, 429) or (isinstance(status, int) and status >= 500):
            raise TransientError(message)
        raise ModelError(message)
    usage = data.get("usage") or {}
    tokens_in = sum(usage.get(key) or 0 for key in
                    ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    models = data.get("modelUsage") or {}
    main = max(models, key=lambda name: models[name].get("costUSD") or 0) if models else None
    return str(data.get("result") or ""), {"input_tokens": tokens_in, "output_tokens": usage.get("output_tokens"),
                                           "cost_usd": data.get("total_cost_usd"), "model": main}


class ClaudeCodeBackend:
    def __init__(self, cfg: Any, binary: str = "claude"):
        self.cfg = cfg
        self.binary = shutil.which(binary) or binary

    def call(self, role: str, system: str, user: str, schema: Dict[str, Any],
             context: Any = None) -> Tuple[str, Dict[str, Any]]:
        argv = build_argv(self.binary, system, self.cfg.model_for(role), getattr(self.cfg, "effort_for", lambda _: None)(role))
        with tempfile.TemporaryDirectory(prefix="evoloop-cc-") as cwd:  # no project context is picked up
            try:
                done = subprocess.run(argv, input=user, capture_output=True, text=True, cwd=cwd,
                                      timeout=float(self.cfg.model.call_timeout_seconds))
            except FileNotFoundError:
                raise ModelError("the `claude` binary was not found on PATH")
            except subprocess.TimeoutExpired:
                raise TransientError("claude timed out")
        if not done.stdout.strip():
            if QUOTA_PATTERN.search(done.stderr or ""):
                raise QuotaExhausted("claude: %s" % done.stderr[-300:], quota_reset_time(done.stderr))
            raise ModelError("claude exited with code %s: %s" % (done.returncode, done.stderr[-300:]))
        return parse_output(done.stdout)
