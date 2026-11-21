"""Skills: what kind of optimisation a search is.

A run type says how to search (the strategy, the schedule). A skill says what the problem is: what may
change, what is measured, what the agents should know about this kind of task, and what the adapter and
the leaderboard need for it. The two are chosen independently.

A skill is a folder holding `skill.yaml`:

    name: efficiency
    summary: one line, shown in the menu
    settings: {strategy: {mechanism: pareto}, ...}     # laid over the run type's; what you set still wins
    guidance:                                          # read by the agents on every call
      all: what holds for every role
      writer: what a writer should try and avoid
      analyst: what the analyst should look for
      strategist: when to change course
    needs:
      adapter: [what the adapter has to do or report, in words]
      figures: [parameters]                            # figures a result must carry; the report says if none does
      references: [teacher]                            # rows the leaderboard should carry; the report says if missing

The built-in skills are in this package (`evoloop skills`). `run.skill` names one of them, or gives the
path of a folder of your own; `evoloop skills NAME --copy DIR` writes a built-in one out to start from."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import yaml

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
ROLES = ("all", "writer", "analyst", "strategist", "coordinator", "conductor")
_cache: Dict[str, Tuple[float, Any]] = {}


def names() -> List[str]:
    try:
        found = sorted(n for n in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, n, "skill.yaml")))
    except OSError:
        return []
    return sorted(found, key=lambda n: (n != "performance", n))     # the plain one first


def find(name: Any, folder: Optional[str] = None) -> Optional[str]:
    """The folder of a skill: a built-in name, or a path (absolute, or under the search's folder or its `skills/`)."""
    if not isinstance(name, str) or not name.strip():
        return None
    name = name.strip()
    tries = [os.path.join(HERE, name)] if os.sep not in name and "/" not in name else []
    if os.path.isabs(name):
        tries.append(name)
    else:
        for base in ([folder] if folder else []) + [os.getcwd()]:
            tries += [os.path.join(base, name), os.path.join(base, "skills", name)]
    for path in tries:
        if os.path.isfile(os.path.join(path, "skill.yaml")):
            return path
    return None


def check(raw: Any) -> Optional[str]:
    """Why a skill file cannot be used, or None."""
    from . import form
    if not isinstance(raw, dict):
        return "skill.yaml must be a mapping"
    extra = set(raw) - {"name", "summary", "settings", "guidance", "needs"}
    if extra:
        return "skill.yaml has unknown entries: %s" % ", ".join(sorted(extra))
    settings = raw.get("settings") or {}
    if not isinstance(settings, dict):
        return "settings must be a mapping"
    known = form.flatten(form.DEFAULTS)
    for path, value in form.flatten(settings).items():
        if path not in known:
            return "settings names %s, which is not a field of the brief" % path
        if path.startswith("run.") or not form.is_live(path) or form.starts_period(path):
            return ("settings may only set what can change during a run; %s defines the problem or the meaning of a "
                    "score, so it belongs in the brief" % path)
        fault = form.check_value(path, value)
        if fault:
            return fault
    guidance = raw.get("guidance") or {}
    if not isinstance(guidance, dict) or set(guidance) - set(ROLES) or not all(isinstance(v, str) for v in guidance.values()):
        return "guidance must map %s to text" % ", ".join(ROLES)
    needs = raw.get("needs") or {}
    if not isinstance(needs, dict) or set(needs) - {"adapter", "figures", "references"} or not all(
            isinstance(v, list) and all(isinstance(x, str) for x in v) for v in needs.values()):
        return "needs must map adapter, figures and references to lists of text"
    return None


def load(name: Any, folder: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(the skill, None) or (None, why it cannot be used). No skill named: (None, None)."""
    if name in (None, "", "none"):
        return None, None
    path = find(name, folder)
    if path is None:
        return None, "no skill named %r: not a built-in one (%s) and no folder with a skill.yaml" % (name, ", ".join(names()))
    file = os.path.join(path, "skill.yaml")
    try:
        stamp = os.path.getmtime(file)
        if file in _cache and _cache[file][0] == stamp:
            return _cache[file][1]
        with open(file, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return None, "the skill %r cannot be read: %s" % (name, exc)
    fault = check(raw)
    if fault:
        out: Tuple[Optional[Dict[str, Any]], Optional[str]] = (None, "the skill %r cannot be used: %s" % (name, fault))
    else:
        needs = raw.get("needs") or {}
        out = ({"name": str(raw.get("name") or os.path.basename(path)), "summary": str(raw.get("summary") or "").strip(),
                "settings": raw.get("settings") or {}, "path": path,
                "guidance": {k: v.strip() for k, v in (raw.get("guidance") or {}).items() if v.strip()},
                "needs": {k: list(needs.get(k) or []) for k in ("adapter", "figures", "references")}}, None)
    _cache[file] = (stamp, out)
    return out


def guidance(skill: Optional[Dict[str, Any]], role: str) -> Optional[str]:
    """What a role is told: the part for every role, then its own."""
    if not skill:
        return None
    parts = [skill["guidance"].get("all"), skill["guidance"].get(role)]
    text = "\n\n".join(p for p in parts if p)
    return text or None


def summaries() -> Dict[str, str]:
    return {name: (load(name)[0] or {}).get("summary", "") for name in names()}


def missing(skill: Optional[Dict[str, Any]], view: Any, references: List[Dict[str, Any]]) -> List[str]:
    """What the skill needs and the run does not have yet: figures no result carries, rows the leaderboard lacks."""
    if not skill:
        return []
    from .strategies import measure
    out = []
    scored = view.scored()
    if len(scored) >= 3:
        for figure in skill["needs"]["figures"]:
            if not any(measure(view, c["id"], figure) is not None for c in scored):
                out.append("the %s skill needs `%s` in the results, and no run has reported it" % (skill["name"], figure))
    labels = " | ".join(str(r.get("label") or "").lower() for r in references)
    for row in skill["needs"]["references"]:
        if row.lower() not in labels:
            out.append("the %s skill expects a reference row for: %s (add it with `evoloop reference ... --label \"%s\"`)" % (
                skill["name"], row, row))
    return out
