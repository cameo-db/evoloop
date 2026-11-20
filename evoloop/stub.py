"""The built-in stub: stands in for every agent role so that a search can be dry-run with no model call.

It knows nothing about the project. The writer returns the parent's blocks with a number nudged (and a
comment line in a structure block, so that each design is a different text). The designs are not good
ideas; the point is that every path of the loop runs, at no cost, before any agent is paid."""
from __future__ import annotations

import re
from typing import Any, Dict

NUMBER = re.compile(r"(?<![\w.])(\d+\.\d+|\d+)(?![\w.])")


def nudge(text: str, which: int, factor: float) -> str:
    found = list(NUMBER.finditer(text))
    if not found:
        return text
    m = found[which % len(found)]
    old = m.group(1)
    new = repr(round(float(old) * factor, 6)) if "." in old else str(max(1, int(round(int(old) * factor))) + (which % 2))
    return text[:m.start(1)] + new + text[m.end(1):]


class GenericStub:
    def __init__(self) -> None:
        self.calls = 0

    def respond(self, role: str, context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        base = {"reasoning": "stub", "note": "stub reply %d" % self.calls, "followed_notes": [
            n["id"] for n in context.get("notes_from_the_person") or []]}
        if role == "writer":
            return dict(base, proposals=[self.proposal(context, i) for i in range(int(
                (context.get("request") or {}).get("number_of_proposals") or 1))])
        if role == "analyst":
            return dict(base, lessons=[], questions=[])
        if role == "strategist":
            return dict(base, decisions=[{"action": "stay", "args": {}, "reason": "stub", "expects": {"gain": 0.0, "within": 10}}])
        if role == "coordinator":
            return dict(base, choice=int(context.get("code_would_choose") or 0))
        if role == "assessor":
            return dict(base, assessment="Stub review: no judgment was made.", strengths=[], weaknesses=[], suggestions=[])
        return dict(base, changes=[], notes=[{"text": str(context.get("words") or ""), "roles": []}], not_covered=[])

    def proposal(self, context: Dict[str, Any], index: int) -> Dict[str, Any]:
        request = context.get("request") or {}
        open_blocks = context.get("blocks_you_may_change") or {}
        source = ((context.get("parents") or [{}])[0].get("blocks")) or context.get("starting_blocks") or {}
        n = self.calls * 7 + index
        blocks: Dict[str, str] = {}
        params = [b for b, info in open_blocks.items() if info["kind"] == "params" and b in source]
        structure = [b for b, info in open_blocks.items() if info["kind"] == "structure" and b in source]
        if request.get("move") == "settings" or not structure:
            for name in params[:1]:
                blocks[name] = nudge(source[name], n, 1.3 if n % 2 else 0.75)
        else:
            name = structure[n % len(structure)]
            blocks[name] = "# stub variant %d\n" % n + nudge(source[name], n, 1.2 if n % 2 else 0.85)
        family = "stub_family_%d" % (n % 5) if request.get("mode") in ("new", "novel") else None
        return {"name": "stub_%d" % n, "family": family, "hypothesis": "A nudged number changes the score.",
                "predicted_effect": "small", "expected_gain": {"gain": 0.0, "probability_better": 0.5},
                "change_summary": "nudged one number", "blocks": blocks}
