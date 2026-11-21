"""The model and the effort: defaults, per-role choices, what is sent to the backends, and how they are priced."""
import copy
import sys
import types

import pytest

from evoloop import estimate, form
from evoloop.cli import main
from evoloop.model import anthropic_api, catalog, claude_code

from helpers import search

BRIEF = {"objective": {"goal": "g", "direction": "maximize"}, "run": {"type": "explore_then_exploit"},
         "budget": {"evaluations": 100, "model_dollars": 500}, "evaluation": {"allowance": 10, "noise": 0.01},
         "baseline": {"mode": "skip"}, "compute": {"gpus": 4}, "agents": {"backend": "anthropic_api"}}


def test_there_are_defaults_and_they_can_be_changed():
    settings, sources = form.resolve(BRIEF)
    agents = settings["agents"]
    assert agents["default_model"] == "claude-opus-5-5" and sources["agents.default_model"] == "default"
    assert agents["effort"] == "medium" and agents["efforts"] == {"writer": "high"}
    picks = estimate.chosen(settings)
    assert picks["writer"] == ("claude-opus-5-5", "high") and picks["analyst"] == ("claude-opus-5-5", "medium")
    brief = copy.deepcopy(BRIEF)
    brief["agents"].update(default_model="claude-sonnet-5-5", models={"writer": "claude-fable-5-2"}, effort="low",
                           efforts={"writer": "xhigh", "strategist": "high"})
    picks = estimate.chosen(form.resolve(brief)[0])
    assert picks["writer"] == ("claude-fable-5-2", "xhigh") and picks["strategist"] == ("claude-sonnet-5-5", "high")
    assert picks["analyst"] == ("claude-sonnet-5-5", "low")
    # During a run too.
    for key, value in (("agents.default_model", "claude-haiku-5-5"), ("agents.effort", "max"),
                       ("agents.efforts", {"writer": "low"}), ("agents.models", {"analyst": "claude-haiku-5-5"})):
        assert form.check_change(key, value) is None
    assert form.check_change("agents.effort", "extreme") is not None
    assert form.check_change("agents.efforts", {"writer": "extreme"}) is not None
    assert form.check_change("agents.models", {"writer": 5}) is not None


def test_an_effort_the_model_does_not_take_is_warned_about_and_not_sent():
    assert catalog.fault("claude-opus-5-5", "xhigh") is None
    assert "does not accept effort xhigh" in catalog.fault("claude-sonnet-4-6", "xhigh")
    assert "takes no effort setting" in catalog.fault("claude-haiku-4-5", "high")
    assert catalog.fault("some-future-model", "xhigh") is None                 # unknown: sent as set, not second-guessed
    assert catalog.effort_to_send("claude-haiku-4-5", "high") is None
    assert catalog.effort_to_send("claude-sonnet-4-6", "xhigh") is None and catalog.effort_to_send("claude-sonnet-4-6", "max") == "max"
    assert catalog.effort_to_send("claude-opus-5-5", "model_default") is None
    assert catalog.effort_to_send("some-future-model", "max") == "max"
    brief = copy.deepcopy(BRIEF)
    brief["agents"].update(default_model="claude-sonnet-4-6", effort="xhigh", efforts={})
    assert any("does not accept effort xhigh" in w for w in form.warnings(form.resolve(brief)[0]))
    assert not any("effort" in w for w in form.warnings(form.resolve(BRIEF)[0]))


def test_the_request_carries_the_effort_and_the_fallback():
    beta, kwargs = anthropic_api.request("claude-opus-5-5", "high", "default", 16000, "sys", "user")
    assert beta and kwargs["output_config"] == {"effort": "high"}
    assert kwargs["betas"] == ["server-side-fallback-2026-07-01"] and kwargs["fallbacks"] == "default"
    assert kwargs["model"] == "claude-opus-5-5" and kwargs["messages"] == [{"role": "user", "content": "user"}]
    assert "thinking" not in kwargs and "temperature" not in kwargs            # neither is set: both would be refused or redundant
    beta, kwargs = anthropic_api.request("claude-opus-5-5", "high", "off", 16000, "sys", "user")
    assert not beta and "fallbacks" not in kwargs and "betas" not in kwargs
    beta, kwargs = anthropic_api.request("claude-haiku-5-5", "model_default", "default", 16000, "sys", "user")
    assert not beta and "output_config" not in kwargs                           # no server-side fallback for this model
    argv = claude_code.build_argv("claude", "sys", "claude-sonnet-5-5", "xhigh")
    assert argv[argv.index("--effort") + 1] == "xhigh" and argv[argv.index("--model") + 1] == "claude-sonnet-5-5"
    assert "--effort" not in claude_code.build_argv("claude", "sys", "claude-sonnet-5-5", "model_default")


def test_a_call_is_priced_by_the_model_that_answered(monkeypatch):
    fake = types.ModuleType("anthropic")
    for name in ("RateLimitError", "APIStatusError", "APIConnectionError"):
        setattr(fake, name, type(name, (Exception,), {}))
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    sent = {}

    def reply(model, stop="end_turn"):
        return types.SimpleNamespace(stop_reason=stop, model=model, content=[types.SimpleNamespace(type="text", text="{}")],
                                     usage=types.SimpleNamespace(input_tokens=1_000_000, output_tokens=100_000))

    class Endpoint:
        def __init__(self, name, answer):
            self.name, self.answer = name, answer

        def stream(self, **kwargs):          # the reply is streamed and collected
            sent[self.name] = kwargs
            answer = self.answer

            class Stream:
                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

                def get_final_message(self):
                    return answer
            return Stream()
    cfg = types.SimpleNamespace(model=types.SimpleNamespace(max_tokens=64000, prices={}, fallbacks="default", call_timeout_seconds=60),
                                model_for=lambda role: "claude-opus-5-5", effort_for=lambda role: "high")
    client = types.SimpleNamespace(messages=Endpoint("plain", reply("claude-opus-5-5")),
                                   beta=types.SimpleNamespace(messages=Endpoint("beta", reply("claude-opus-4-8"))))
    text, usage = anthropic_api.AnthropicBackend(cfg, client=client).call("writer", "sys", "user", {})
    assert "beta" in sent and "plain" not in sent and sent["beta"]["output_config"] == {"effort": "high"}
    assert usage["model"] == "claude-opus-4-8" and usage["effort"] == "high"
    assert usage["cost_usd"] == pytest.approx(1.0 * 5.00 + 0.1 * 25.00)        # the fallback model's own rates
    # A price of yours wins over the built-in list; a model with no price has no cost.
    cfg.model.prices = {"claude-opus-4-8": {"input": 1.0, "output": 1.0}}
    assert anthropic_api.AnthropicBackend(cfg, client=client).call("writer", "sys", "user", {})[1]["cost_usd"] == pytest.approx(1.1)
    assert catalog.rates("claude-opus-5-5")[0] == {"input": 4.0, "output": 20.0}
    assert catalog.rates("some-future-model") == (None, "no price")
    # A reply that was cut off is still charged.
    client.beta.messages.answer = reply("claude-opus-5-5", stop="max_tokens")
    cfg.model.prices = {}
    with pytest.raises(Exception) as caught:
        anthropic_api.AnthropicBackend(cfg, client=client).call("writer", "sys", "user", {})
    assert caught.value.usage["cost_usd"] == pytest.approx(1.0 * 4.00 + 0.1 * 20.00)


def test_the_plan_shows_the_model_the_effort_and_what_other_models_would_cost(tmp_path, capsys):
    folder = search(tmp_path, agents__backend="anthropic_api", budget__evaluations=100, budget__model_dollars=1000)
    capsys.readouterr()
    assert main(["plan", folder]) == 0
    plan = capsys.readouterr().out
    assert "[claude-opus-5-5, effort high]" in plan and "[claude-opus-5-5, effort medium]" in plan
    assert "from the built-in list of %s" % catalog.AS_OF in plan and "Not counted: the model's own reasoning" in plan
    assert "The same search with another model for every role" in plan
    for model in catalog.OFFERED:
        assert model in plan
    costs = {m: estimate.estimate(form.resolve(dict(copy.deepcopy(BRIEF), agents={"backend": "anthropic_api", "default_model": m}))[0])["dollars"][1]
             for m in catalog.OFFERED}
    assert costs["claude-haiku-5-5"] < costs["claude-sonnet-5-5"] < costs["claude-opus-5-5"] < costs["claude-fable-5-2"]
    capsys.readouterr()
    assert main(["menu", "models"]) == 0
    text = capsys.readouterr().out
    assert "claude-opus-5-5" in text and "$4 in, $20 out per million tokens" in text and catalog.AS_OF in text
    assert main(["menu", "effort"]) == 0
    assert "model_default" in capsys.readouterr().out
