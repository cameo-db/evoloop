"""The agent roles, and the one way they are called.

A role is defined by what it reads and what it writes. Each call is a fresh context assembled from the
run's stores; a role has no memory of earlier calls and never talks to another role. Every call is
recorded in the `calls` stream: the sections it was shown with their sizes, the ids of the person's
steering notes it was shown, what it answered, what it cost.

    writer       reads results, lessons, notes       writes designs (every kind of move)
    analyst      reads results                        writes lessons, and questions for the person
    coordinator  reads the options code offers        writes the choice of the next slot (optional)
    assessor     reads one role's record              writes a review of that role, for the person
    strategist   reads the facts of the whole search   writes decisions from a bounded menu, into the ledger
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
list in `followed_notes` the ids of those that shaped your answer; if you set one aside, say why in `reasoning`. \
`direction_from_the_strategist`, when present, is advice from the role that watches the search as a whole: weigh it, \
and where it conflicts with a note from the person, the person's note stands.

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
- `ordered_by_the_person`, when present in the request, is an instruction from the person for this slot: follow it.
- `limits_enforced_by_code`, when present, are hard limits on a design (its size, its speed): one outside them is \
  rejected without a score, so size your design to them. `recent` shows designs that were rejected and why.
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
- When the request has `edit_format: diff`, a block you change only in part may be given under `edits` instead of \
`blocks`: a list of {"block": name, "find": text, "replace": text}. `find` must occur EXACTLY ONCE in that block as \
you were shown it (copy enough of it, character for character, to be unique); edits to one block apply in order. \
Give a block you rewrite in `blocks`, in full. An edit whose `find` does not occur exactly once makes the proposal \
invalid, so when in doubt return the full block.
- `approach`, when present in the request, is a way of working chosen for this slot. Follow it where it does not \
conflict with the slot's instruction; its record is kept, so do not pretend to follow it.
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

`approaches`, when present, are ways of working handed to the writers, one per slot, each with how the designs \
written under it did (`none` is no approach). If the results suggest a way of working that is not there, you may \
add ONE under `new_approach`: a short instruction on how to go about designing (what to look at, what to change \
first, what to avoid), not a particular design. Leave it null when nothing suggests one.

Output: {"reasoning": "...", "note": "...", "followed_notes": [], "lessons": [{"statement": "...", \
"status": "supported | tentative", "evidence": ["R3", "R9"]}], "questions": [{"question": "...", "default": "..."}], \
"new_approach": null}"""

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

STRATEGIST = """## Your role: strategist

You look at the search as a whole, at intervals and whenever it stops gaining, and decide whether it should go on \
as it is. Code gives you the facts: how long since the best score rose, what each mode, move and kind of crossover \
has returned, the population, how varied the recent designs are, the budget left, the agents' spend, and your own \
earlier decisions with what followed them. `menu` lists the actions you may take and their bounds.

Return up to two decisions. `stay` is a decision, and often the right one: a strategy changed every few designs \
never gets a fair test. Change something when the facts show the search is stuck or lopsided: no gain for a long \
stretch, a mode that keeps returning nothing while it holds a large share, crossover of one kind failing while \
another is untried, every recent design of one family. Exploration is part of your brief: do not let the search \
collapse onto the leader while budget remains, and say so when it has.

For each decision give `action`, `args` as the menu describes, `reason` (what in the facts decided it), and \
`expects`: `gain` in noise floors that you expect the best score to rise over the next `within` designs because of \
this. Your expectations are scored against what follows. Small changes are applied at once; large ones wait for \
the person's yes, and the menu says which are which.

Output: {"reasoning": "...", "note": "...", "followed_notes": [], "decisions": [{"action": "shares", "args": \
{"new": 0.5, "cross": 0.2, "local": 0.3}, "reason": "...", "expects": {"gain": 1.0, "within": 15}}]}"""

CONDUCTOR = """## Your role: conductor

You run this search, and the person it is for is talking to you. `message` is what they just said; `conversation` \
is what was said before; `facts` is the state of the search worked out by code; `since_you_last_spoke` is what you \
decided by yourself in the meantime; `waiting_for_them` are decisions of yours that need their yes; `menu` lists \
the actions you may take and their bounds.

Answer them plainly in `reply`, from the facts and the records: what is happening, why, what you intend. If you do \
not know, say so. When they ask for a change, or the facts call for one, put it in `decisions` exactly as a \
strategist would (`action`, `args`, `reason`, `expects`), and say in the reply what you are changing. Code checks \
every decision against the bounds: some are applied at once, some wait for their yes, some are refused; so say \
"I have asked for", not "I have done". When they say yes or no to a waiting decision, put its id in `approve` or \
`decline`. Do not claim anything that is not in `decisions`, `approve` or `decline`. Keep the floors: the budget, \
the limits and the share of new designs are not yours to remove. If what they ask for cannot be done from the menu, \
say what they can do themselves (a setting, a limit, a rehash) and give the command.

Output: {"reasoning": "...", "note": "...", "followed_notes": [], "reply": "...", "decisions": [], "approve": [], \
"decline": []}"""

ROLES = {"writer": WRITER, "analyst": ANALYST, "coordinator": COORDINATOR, "assessor": ASSESSOR, "translator": TRANSLATOR,
         "strategist": STRATEGIST, "conductor": CONDUCTOR}

# `blocks` and `edits` are read leniently when a design is recorded: a proposal with neither is refused there, with the reason.
PROPOSAL = {"type": "object", "required": [], "properties": {}}
SCHEMAS: Dict[str, Dict[str, Any]] = {
    "writer": {"type": "object", "required": ["proposals"],
               "properties": {"proposals": {"type": "array", "items": PROPOSAL}}},
    "analyst": {"type": "object", "required": ["lessons"], "properties": {"lessons": {"type": "array"}}},
    "coordinator": {"type": "object", "required": ["choice"], "properties": {"choice": {"type": "integer"}}},
    "assessor": {"type": "object", "required": ["assessment"], "properties": {"assessment": {"type": "string"}}},
    "strategist": {"type": "object", "required": ["decisions"], "properties": {"decisions": {"type": "array"}}},
    "conductor": {"type": "object", "required": ["reply"], "properties": {"reply": {"type": "string"}, "decisions": {"type": "array"}}},
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
                               prices=a.get("prices") or {}, backend=a["backend"], fallbacks=a.get("fallbacks") or "off")

    def picked(self, role: str, what: str) -> Any:
        """What was drawn for this call from `agents.writer_mix`, if anything (each call runs in its own thread)."""
        return getattr(self.holder.get("local"), what, None) if role == "writer" else None

    def model_for(self, role: str) -> Any:
        a = self.holder["settings"]["agents"]
        return self.picked(role, "model") or (a.get("models") or {}).get(role) or a.get("default_model")

    def effort_for(self, role: str) -> Any:
        """The effort set for a role, else the one set for every role; None leaves it to the model."""
        a = self.holder["settings"]["agents"]
        return self.picked(role, "effort") or (a.get("efforts") or {}).get(role) or a.get("effort")


class Agents:
    def __init__(self, settings: Dict[str, Any], folder: str, store: Store, backend: Any = None, tag: str = ""):
        self.holder = {"settings": settings, "local": threading.local()}
        self.mixed: Dict[str, int] = {}      # writer calls so far by model, when several models write
        self.folder, self.store = folder, store
        used = store.read("calls")
        for done in used:      # so the shares hold across a restart of the controller
            if done.get("drawn_model"):
                self.mixed[done["drawn_model"]] = self.mixed.get(done["drawn_model"], 0) + 1
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

    def draw_writer(self) -> Optional[Dict[str, Any]]:
        """The model for one writer call when several write (`agents.writer_mix`): by counting, so the realised
        shares follow the shares set, whatever the order the calls come in."""
        mix = [m for m in self.holder["settings"]["agents"].get("writer_mix") or [] if isinstance(m, dict) and m.get("model")]
        if not mix:
            return None
        whole = sum(float(m.get("share") or 0) for m in mix) or 1.0
        with self.lock:
            done = sum(self.mixed.get(m["model"], 0) for m in mix)
            chosen = max(mix, key=lambda m: float(m.get("share") or 0) / whole * (done + 1) - self.mixed.get(m["model"], 0))
            self.mixed[chosen["model"]] = self.mixed.get(chosen["model"], 0) + 1
        return chosen

    def call(self, role: str, context: Dict[str, Any], about: Any = None) -> Dict[str, Any]:
        drawn = self.draw_writer() if role == "writer" else None
        local = self.holder["local"]
        local.model, local.effort = (drawn or {}).get("model"), (drawn or {}).get("effort")
        try:
            return self._call(role, context, about, drawn)
        finally:
            local.model = local.effort = None

    def _call(self, role: str, context: Dict[str, Any], about: Any, drawn: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        why = self.available()
        if why:
            raise AgentsUnavailable(why)
        settings = self.holder["settings"]
        notes = [n for n in settings.get("notes") or [] if not n.get("roles") or role in n["roles"]]
        if notes and role != "translator":
            # What the person wrote and what the strategist wrote are shown apart: one is an instruction, the other advice.
            mine = [{"id": n["id"], "text": n["text"]} for n in notes if n.get("by") != "strategist"]
            theirs = [{"id": n["id"], "text": n["text"]} for n in notes if n.get("by") == "strategist"]
            context = dict(context)
            if mine:
                context["notes_from_the_person"] = mine
            if theirs:
                context["direction_from_the_strategist"] = theirs
        system = CORE + "\n\n" + ROLES[role]
        user = json.dumps(context, indent=1, default=str)
        shown = {key: len(json.dumps(value, default=str)) for key, value in context.items()}
        with self.lock:   # calls are made from several threads: one id each
            self.count += 1
            record: Dict[str, Any] = {"id": "A%d_%s" % (self.count, self.tag) if self.tag else "A%d" % self.count,
                                      "role": role, "about": about, "shown": shown,
                                      "notes_shown": [n["id"] for n in notes] if role != "translator" else []}
            if drawn:
                record["drawn_model"] = drawn["model"]
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
