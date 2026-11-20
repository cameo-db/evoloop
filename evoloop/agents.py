"""The agent roles, and the one way they are called.

A role is defined by what it reads and what it writes. Each call is a fresh context assembled from the
run's stores; a role has no memory of earlier calls and never talks to another role. Every call is
recorded in the `calls` stream: the sections it was shown with their sizes, the ids of the person's
steering notes it was shown, what it answered, what it cost.

    writer       reads results, lessons, notes       writes designs (every kind of move)
    analyst      reads results                        writes lessons, and questions for the person
    coordinator  reads the options code offers        writes the choice of the next slot (optional)
    assessor     reads one role's record              writes a review of that role, for the person
    translator   reads the person's words             writes proposed ledger entries, for the person to confirm"""
from __future__ import annotations

import json
import os
import threading
import time
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from .model.base import BudgetExceeded, ModelClient, ModelError, QuotaExhausted, StubBackend, validate
from .store import Store, write_json

CORE = """You are one role inside evoloop, a system that improves a project by evolutionary search. The project \
has frozen code and a few marked blocks that may change, and a command that trains a candidate and returns a score. \
Code does the bookkeeping (selection, schedule, budget, checks); language-model roles like you make the judgments. \
Each call is a fresh context built from the run's records: you have no memory of earlier calls and you never talk to \
another role. Scores are noisy: a difference smaller than the noise floor is no difference.

`notes_from_the_person`, when present, are standing instructions from the person the search is for. Follow them, and \
list in `followed_notes` the ids of those that shaped your answer; if you set one aside, say why in `reasoning`.

Return exactly one JSON object and nothing else. Put `reasoning` first (three to six plain sentences on what you \
weighed), then `note` (one sentence, at most 30 words, on what you chose and why)."""

WRITER = """## Your role: writer

You write designs. The request names the kind of slot:

- mode `new`: a fresh design from a family the search has not covered. Use `families` and `thin_cells` to see what \
is missing, and aim there.
- mode `novel`: a design unlike anything tried. You are shown `inspirations`: designs that were rarely built on. \
Build from them or against them; do not return a variant of the leader.
- mode `local`, move `edit`: ONE attributable change to the parent's structure, so that the result has one cause. \
`step` says how large: `small` (a careful adjustment), `normal`, or `bold` (a larger single change).
- mode `local`, move `settings`: change only values in the `params` blocks.
- mode `local`, move `ablation`: remove one component from the parent and change nothing else.
- mode `cross`, move `graft`: you are shown `gene`, the change that gained most in the donor's history. Apply that \
one change to the first parent and change nothing else.
- mode `cross`, move `hybrid`: write one design from the two parents and say in `parts_from` which parts came \
from each.

Rules, and why:

- Only the blocks listed in `blocks_you_may_change` can change; everything else is frozen and verified.
- Return the FULL new contents of each block you change and omit the others; an omitted block is taken from the \
first parent (or, with no parent, from the current leader, so that a new design runs with settings already found).
- A `params` block is exactly one assignment of a dict literal of numbers, booleans or strings.
- Do not repeat a design in `leaderboard` or `recent`; an exact copy is refused unrun.
- Give `family`: a short label for the kind of approach, reused only when the approach really is of that kind.
- Give `expected_gain`: `gain` is how many noise floors above (positive) or below the reference you expect this to \
score, your honest middle estimate; `probability_better` is your chance, 0 to 1, that it beats the reference. The \
reference is the parent, or the leader when there is no parent. These are scored against the result.
- When `number_of_proposals` is above 1, return that many DIFFERENT proposals. One will be chosen to run, by your \
forecast and by how far each is from what has been tried.

Output: {"reasoning": "...", "note": "...", "followed_notes": [], "proposals": [{"name": "short name", \
"family": "label", "hypothesis": "...", "predicted_effect": "...", "expected_gain": {"gain": 0.0, \
"probability_better": 0.5}, "change_summary": "one line", "parts_from": null, "blocks": {"block_name": \
"full new contents"}}]}"""

ANALYST = """## Your role: analyst

You read the results since the last analysis and write what the search has learned. A lesson is `supported` only \
when the same change did the same thing in two different lineages; otherwise it is `tentative`, an idea worth \
testing and never a constraint. Cite run ids as evidence. If something needs the person's decision, add a question \
with the default you would take; the run does not wait for the answer.

Output: {"reasoning": "...", "note": "...", "followed_notes": [], "lessons": [{"statement": "...", \
"status": "supported | tentative", "evidence": ["R3", "R9"]}], "questions": [{"question": "...", "default": "..."}]}"""

COORDINATOR = """## Your role: coordinator

Code has worked out the options for the next slot: one per kind of move that is possible now, each with the parents \
it would use and the share of the schedule it is owed. `code_would_choose` is what the schedule alone picks. Choose \
one option by its index. Depart from the schedule only for a reason in the results, and say it.

Output: {"reasoning": "...", "note": "...", "followed_notes": [], "choice": 0}"""

ASSESSOR = """## Your role: assessor

You review one role of the search for the person it is run for, like a consultant's review. You are shown the \
role's scorecard and its calls in order, each with what it stated, and what happened afterwards. Judge the role on \
what it could have known. Separate calibration (were its forecasts right) from choice (did what it chose pay). \
Small samples prove little: give counts. Do not praise, and do not hedge beyond the evidence. Each suggestion must \
be a specific change to the role's instructions or to what it is shown, and name the scorecard figure it should move.

Output: {"reasoning": "...", "note": "...", "assessment": "three to six sentences", "strengths": [], \
"weaknesses": [], "suggestions": [{"change": "...", "figure": "..."}]}"""

TRANSLATOR = """## Your role: translator

The person has written, in their own words, what they want from the search or how they want it changed. Turn it \
into entries for the steering ledger. You are shown `settings` (every setting with its current value) and \
`changeable` (those that may change now). Use `changes` for what a setting expresses, each with the sentence of \
the person's that it comes from; use `notes` for guidance that agents should read; put under `not_covered` \
anything you could not express, in the person's words. Translate what was said and nothing else: never set a \
value the person did not ask for. Nothing you return is applied until the person confirms it.

Output: {"reasoning": "...", "note": "...", "changes": [{"key": "schedule.novelty", "value": 0.6, "from": \
"..."}], "notes": [{"text": "...", "roles": ["writer"]}], "not_covered": []}"""

ROLES = {"writer": WRITER, "analyst": ANALYST, "coordinator": COORDINATOR, "assessor": ASSESSOR, "translator": TRANSLATOR}

PROPOSAL = {"type": "object", "required": ["blocks"], "properties": {"blocks": {"type": "object"}}}
SCHEMAS: Dict[str, Dict[str, Any]] = {
    "writer": {"type": "object", "required": ["proposals"],
               "properties": {"proposals": {"type": "array", "items": PROPOSAL}}},
    "analyst": {"type": "object", "required": ["lessons"], "properties": {"lessons": {"type": "array"}}},
    "coordinator": {"type": "object", "required": ["choice"], "properties": {"choice": {"type": "integer"}}},
    "assessor": {"type": "object", "required": ["assessment"], "properties": {"assessment": {"type": "string"}}},
    "translator": {"type": "object", "required": ["changes", "notes"],
                   "properties": {"changes": {"type": "array"}, "notes": {"type": "array"}}},
}


class AgentError(Exception):
    pass


class AgentsUnavailable(AgentError):
    """No call can be made now: the spend cap is reached, or the account's limit refused a call."""


class _BackendConfig:
    """What the model backends read, taken from the settings in force at the time of the call, so that
    the model behind a role can be changed while a run is going."""

    def __init__(self, holder: Dict[str, Any], folder: str):
        self.holder, self.project_dir = holder, folder

    @property
    def model(self) -> Any:
        a = self.holder["settings"]["agents"]
        return SimpleNamespace(call_timeout_seconds=a["call_timeout_seconds"], max_tokens=a["max_tokens"],
                               prices=a.get("prices") or {}, backend=a["backend"])

    def model_for(self, role: str) -> Any:
        a = self.holder["settings"]["agents"]
        return (a.get("models") or {}).get(role) or a.get("default_model")


class Agents:
    def __init__(self, settings: Dict[str, Any], folder: str, store: Store, backend: Any = None, tag: str = ""):
        self.holder = {"settings": settings}
        self.folder, self.store = folder, store
        used = store.read("calls")
        self.dollars = sum(float(c.get("cost_usd") or 0.0) for c in used)
        self.count = len(used)
        self.lock = threading.Lock()
        self.unpriced = 0
        self.tag = tag   # set for calls made outside the controller (the `steer` command), so ids cannot collide
        a = settings["agents"]
        cfg = _BackendConfig(self.holder, folder)
        if backend is None:
            if a["backend"] == "stub":
                path = a.get("stub_module")
                if path:
                    backend = StubBackend(path if os.path.isabs(path) else os.path.join(folder, path))
                else:
                    from .stub import GenericStub
                    backend = StubBackend(None, module=GenericStub())
            elif a["backend"] == "anthropic_api":
                from .model.anthropic_api import AnthropicBackend
                backend = AnthropicBackend(cfg)
            else:
                from .model.claude_code import ClaudeCodeBackend
                backend = ClaudeCodeBackend(cfg)
        # No retry loop on refused calls: a refusal for the account's limit pauses every call until it resets.
        self.client = ModelClient(backend, max_concurrent=int(a["max_concurrent_calls"]), max_calls=None,
                                  calls_used=self.count, max_retries=int(a["max_retries"]))

    def update(self, settings: Dict[str, Any]) -> None:
        self.holder["settings"] = settings

    def available(self) -> Optional[str]:
        """Why no call can be made now, or None."""
        budget = self.holder["settings"]["budget"]
        cap = budget.get("model_dollars")
        if cap is not None and self.holder["settings"]["agents"]["backend"] != "stub" and self.dollars >= float(cap):
            return "the agent spend cap of $%.2f is reached ($%.2f spent)" % (float(cap), self.dollars)
        if budget.get("model_calls") is not None and self.count >= int(budget["model_calls"]):
            return "the cap of %d agent calls is reached" % int(budget["model_calls"])
        if cap is not None and self.unpriced >= 3:
            return ("the backend reports no cost for its calls, so the spend cap of $%.2f cannot be kept: give "
                    "agents.prices for the model in use, or cap the calls with budget.model_calls" % float(cap))
        if self.client.paused() > 0:
            return "agent calls are paused for the account's limit (%s)" % self.client.pause_reason[:120]
        return None

    def call(self, role: str, context: Dict[str, Any], about: Any = None) -> Dict[str, Any]:
        why = self.available()
        if why:
            raise AgentsUnavailable(why)
        settings = self.holder["settings"]
        notes = [n for n in settings.get("notes") or [] if not n.get("roles") or role in n["roles"]]
        if notes and role != "translator":
            context = dict(context, notes_from_the_person=[{"id": n["id"], "text": n["text"]} for n in notes])
        system = CORE + "\n\n" + ROLES[role]
        user = json.dumps(context, indent=1, default=str)
        shown = {key: len(json.dumps(value, default=str)) for key, value in context.items()}
        with self.lock:   # calls are made from several threads: one id each
            self.count += 1
            record: Dict[str, Any] = {"id": "A%d_%s" % (self.count, self.tag) if self.tag else "A%d" % self.count,
                                      "role": role, "about": about, "shown": shown,
                                      "notes_shown": [n["id"] for n in notes] if role != "translator" else []}
        started = time.time()
        usage: Dict[str, Any] = {}
        try:
            output, usage = self.client.complete_with_usage(role, system, user, SCHEMAS[role], context)
            faults = validate(output, SCHEMAS[role])
            if faults:
                raise ModelError("the reply does not fit the role's format: %s" % "; ".join(faults[:3]))
        except QuotaExhausted as exc:
            with self.lock:
                self.count -= 1
            raise AgentsUnavailable(str(exc))
        except BudgetExceeded as exc:
            raise AgentsUnavailable(str(exc))
        except ModelError as exc:
            # A reply that was paid for and could not be used is still paid for.
            usage = getattr(exc, "usage", None) or usage or {}
            self.charge(usage)
            self.store.append("calls", dict(record, error=str(exc)[:500], seconds=round(time.time() - started, 2),
                                            cost_usd=usage.get("cost_usd"), model=usage.get("model")))
            raise AgentError("%s call failed: %s" % (role, exc))
        self.charge(usage)
        kept = {k: v for k, v in output.items() if k not in ("proposals",)}
        if role == "writer":
            kept["proposals"] = [{k: v for k, v in p.items() if k != "blocks"} for p in output.get("proposals") or []
                                 if isinstance(p, dict)]
        self.store.append("calls", dict(record, output=kept, seconds=round(usage.get("seconds") or 0.0, 2),
                                        cost_usd=usage.get("cost_usd"), model=usage.get("model"),
                                        tokens={"in": usage.get("input_tokens"), "out": usage.get("output_tokens")}))
        # The whole reply, the code of every proposal included, chosen or not.
        os.makedirs(os.path.join(self.store.dir, "replies"), exist_ok=True)
        write_json(os.path.join(self.store.dir, "replies", record["id"] + ".json"), output)
        output["_call"] = record["id"]
        return output

    def charge(self, usage: Dict[str, Any]) -> None:
        with self.lock:
            cost = usage.get("cost_usd")
            if cost is None and usage and self.holder["settings"]["agents"]["backend"] != "stub":
                self.unpriced += 1   # the backend gave no cost: the dollar cap cannot see this call
            self.dollars += float(cost or 0.0)


def spend(store: Store) -> Dict[str, Dict[str, float]]:
    """Agent cost by role: calls, dollars, seconds, failures."""
    out: Dict[str, Dict[str, float]] = {}
    for call in store.read("calls"):
        row = out.setdefault(call.get("role") or "?", {"calls": 0, "dollars": 0.0, "seconds": 0.0, "failed": 0})
        row["calls"] += 1
        row["dollars"] += float(call.get("cost_usd") or 0.0)
        row["seconds"] += float(call.get("seconds") or 0.0)
        row["failed"] += 1 if call.get("error") else 0
    return out
