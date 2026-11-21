"""Skills: what kind of optimisation a search is.

A run type says how to search (the strategy, the schedule). A skill says what the problem is: what may
change, what is measured, what the agents should know about this kind of task, and what the adapter and
the leaderboard need for it. The two are chosen independently, and skills can be combined.

A skill is a folder holding `skill.yaml`. The ones in this package are a library of templates
(`evoloop skills`). A search does not use them in place: when it is confirmed, the skills it names are
copied into the search's own `skills/` folder, and that copy is what the run reads and what you edit.

    name: model-distillation          # specific, lower case with hyphens: <what>-<goal>
    title: Distil a student from a teacher
    summary: one or two lines, shown in listings
    domain: model                     # model, algorithm, pipeline, bioinformatics, ...: for browsing
    objective: a smaller model that matches a larger one
    tags: [distillation, student, teacher, compression]
    version: 1
    authors: [evoloop]
    when: when to choose it, and when not to
    settings: {space: {preset: architecture_and_recipe}}   # laid over the run type's; what you set still wins
    guidance:                         # read by the agents on every call
      all: what holds for every role
      writer: what a writer should try and avoid
      analyst: what the analyst should look for
      strategist: when to change course
    diagnose:                         # shown to the writer and the analyst: what a result says to do next
      - see: the student fits the teacher on training inputs but not on held-out ones
        do: add teacher-labelled data or regularize; do not enlarge the student
    stages:                           # added to the writer's guidance by how much of the budget is spent
      early: explore recipes on one or two student shapes
      late: refine the best student; no new shapes
    needs:
      adapter: [what the adapter has to do or report, in words]
      figures: [parameters]           # figures a result must carry; the report says if none does
      references: [teacher]           # rows the leaderboard should carry; the report says if missing
    combines: [model-size-frontier]   # skills it is meant to be used with
    conflicts: [settings-tuning]      # skills it should not be combined with (the plan warns)

`run.skill` names one skill or several (a list, or names separated by commas). Several are merged in the
order given: settings are laid one over the other, so where two set the same thing the later one stands
and the plan says so; guidance, diagnoses and needs are joined."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

import yaml

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
ROLES = ("all", "writer", "analyst", "strategist", "coordinator", "conductor")
FIELDS = ("name", "title", "summary", "domain", "objective", "tags", "version", "authors", "when", "settings",
          "guidance", "diagnose", "stages", "needs", "combines", "conflicts", "goal", "start", "why", "reading", "instead")
# The first skills had short names; a brief that uses one still works.
ALIASES = {"performance": "model-performance", "distillation": "model-distillation", "tuning": "settings-tuning",
           "efficiency": "model-efficiency", "mechanistic": "model-mechanistic"}
NAME = re.compile(r"[a-z][a-z0-9]*(-[a-z0-9]+)+")
_cache: Dict[str, Tuple[float, Any]] = {}


def names() -> List[str]:
    """The skills of the library in this package, by domain and then by name."""
    try:
        found = [n for n in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, n, "skill.yaml"))]
    except OSError:
        return []
    return sorted(found, key=lambda n: (n.split("-")[0] != "model", n.split("-")[0], n != "model-performance", n))


def wanted(value: Any) -> List[str]:
    """The skill names in `run.skill`: one name, a list, or names separated by commas or plus signs."""
    if isinstance(value, str):
        value = re.split(r"[,+]", value)
    if not isinstance(value, (list, tuple)):
        return []
    out: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip() and item.strip() != "none":
            name = ALIASES.get(item.strip(), item.strip())
            if name not in out:
                out.append(name)
    return out


def find(name: Any, folder: Optional[str] = None) -> Optional[str]:
    """The folder of a skill. The search's own copy (`skills/NAME` under its folder) comes first, then a
    path, then the library in this package."""
    if not isinstance(name, str) or not name.strip():
        return None
    name = ALIASES.get(name.strip(), name.strip())
    tries: List[str] = []
    if os.path.isabs(name):
        tries.append(name)
    else:
        for base in ([folder] if folder else []) + [os.getcwd()]:
            tries += [os.path.join(base, "skills", name), os.path.join(base, name)]
        if os.sep not in name and "/" not in name:
            tries.append(os.path.join(HERE, name))
    for path in tries:
        if os.path.isfile(os.path.join(path, "skill.yaml")):
            return path
    return None


def check(raw: Any) -> Optional[str]:
    """Why a skill file cannot be used, or None."""
    from . import form
    if not isinstance(raw, dict):
        return "skill.yaml must be a mapping"
    extra = set(raw) - set(FIELDS)
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
    diagnose = raw.get("diagnose") or []
    if not isinstance(diagnose, list) or not all(isinstance(d, dict) and set(d) == {"see", "do"}
                                                 and all(isinstance(v, str) for v in d.values()) for d in diagnose):
        return "diagnose must be a list of {see: what the results show, do: what to do about it}"
    stages = raw.get("stages") or {}
    if not isinstance(stages, dict) or set(stages) - {"early", "late"} or not all(isinstance(v, str) for v in stages.values()):
        return "stages must map early and late to text"
    start = raw.get("start") or {}
    if not isinstance(start, dict) or set(start) - {"run_type", "evaluations", "brief"} or not isinstance(start.get("brief") or {}, dict):
        return "start must give run_type, evaluations and, if wanted, brief (further lines of a starting brief)"
    instead = raw.get("instead") or []
    if not isinstance(instead, list) or not all(isinstance(d, dict) and set(d) == {"if", "use"} for d in instead):
        return "instead must be a list of {if: the situation, use: the skill to choose}"
    for key in ("tags", "authors", "combines", "conflicts"):
        if not isinstance(raw.get(key) or [], list) or not all(isinstance(x, str) for x in raw.get(key) or []):
            return "%s must be a list of text" % key
    return None


def load(name: Any, folder: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """One skill: (the skill, None) or (None, why it cannot be used). No skill named: (None, None)."""
    if name in (None, "", "none"):
        return None, None
    path = find(name, folder)
    if path is None:
        return None, "no skill named %r: not in the search's skills/ folder, not a path, and not in the library (%s)" % (
            name, ", ".join(names()))
    file = os.path.join(path, "skill.yaml")
    try:
        stamp = os.path.getmtime(file)
        if file in _cache and _cache[file][0] == stamp:
            return _cache[file][1]
        with open(file, "r", encoding="utf-8") as handle:
            text = handle.read()
        raw = yaml.safe_load(text)
    except (OSError, yaml.YAMLError) as exc:
        return None, "the skill %r cannot be read: %s" % (name, exc)
    fault = check(raw)
    if fault:
        out: Tuple[Optional[Dict[str, Any]], Optional[str]] = (None, "the skill %r cannot be used: %s" % (name, fault))
    else:
        needs = raw.get("needs") or {}
        label = str(raw.get("name") or os.path.basename(path))
        out = ({"name": label, "title": str(raw.get("title") or label), "summary": str(raw.get("summary") or "").strip(),
                "domain": str(raw.get("domain") or label.split("-")[0]), "objective": str(raw.get("objective") or "").strip(),
                "tags": list(raw.get("tags") or []), "version": raw.get("version") or 1,
                "authors": list(raw.get("authors") or []), "when": str(raw.get("when") or "").strip(),
                "settings": raw.get("settings") or {}, "path": path,
                "own": os.path.abspath(path) != os.path.abspath(os.path.join(HERE, os.path.basename(path))),
                "digest": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
                "guidance": {k: v.strip() for k, v in (raw.get("guidance") or {}).items() if v.strip()},
                "diagnose": [{"see": d["see"].strip(), "do": d["do"].strip()} for d in raw.get("diagnose") or []],
                "stages": {k: v.strip() for k, v in (raw.get("stages") or {}).items() if v.strip()},
                "needs": {k: list(needs.get(k) or []) for k in ("adapter", "figures", "references")},
                "goal": str(raw.get("goal") or raw.get("title") or label), "start": raw.get("start") or {},
                "why": " ".join(str(raw.get("why") or "").split()), "reading": " ".join(str(raw.get("reading") or "").split()),
                "instead": [{"if": str(d["if"]), "use": str(d["use"])} for d in raw.get("instead") or []],
                "combines": [ALIASES.get(n, n) for n in raw.get("combines") or []],
                "conflicts": [ALIASES.get(n, n) for n in raw.get("conflicts") or []]}, None)
    _cache[file] = (stamp, out)
    return out


def combine(value: Any, folder: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """The skill a search runs with: the one named in `run.skill`, or several merged in the order given.
    Settings are laid one over the other (the later skill's value stands where two differ); guidance,
    diagnoses and needs are joined, each part under the name of the skill it came from."""
    from . import form
    asked = wanted(value)
    if not asked:
        return None, None
    parts = []
    for name in asked:
        found, fault = load(name, folder)
        if found is None:
            return None, fault
        parts.append(found)
    if len(parts) == 1:
        return dict(parts[0], parts=[parts[0]["name"]], clashes=[], warnings=[], digests={parts[0]["name"]: parts[0]["digest"]}), None
    settings: Dict[str, Any] = {}
    owner: Dict[str, str] = {}
    clashes = []
    for part in parts:
        for path, new in form.flatten(part["settings"]).items():
            if path in owner and form.get(settings, path) != new:
                clashes.append({"setting": path, "from": owner[path], "value": form.get(settings, path),
                                "stands": part["name"], "to": new})
            form.put(settings, path, new)
            owner[path] = part["name"]
    guidance = {}
    for role in ROLES:
        said = ["From the skill %s:\n%s" % (p["name"], p["guidance"][role]) for p in parts if p["guidance"].get(role)]
        if said:
            guidance[role] = "\n\n".join(said)
    stages = {}
    for stage in ("early", "late"):
        said = ["%s: %s" % (p["name"], p["stages"][stage]) for p in parts if p["stages"].get(stage)]
        if said:
            stages[stage] = "\n".join(said)
    needs: Dict[str, List[str]] = {"adapter": [], "figures": [], "references": []}
    for part in parts:
        for kind in needs:
            needs[kind] += [n for n in part["needs"][kind] if n not in needs[kind]]
    chosen = [p["name"] for p in parts]
    warnings = ["the skills %s and %s are marked as not meant to be combined" % (p["name"], other)
                for p in parts for other in p["conflicts"] if other in chosen]
    warnings += ["both %s and %s set %s; the value of %s stands (%r, not %r)" % (
        c["from"], c["stands"], c["setting"], c["stands"], c["to"], c["value"]) for c in clashes]
    return {"name": " + ".join(chosen), "title": " + ".join(p["title"] for p in parts), "parts": chosen,
            "summary": " ".join("%s: %s" % (p["name"], p["summary"]) for p in parts), "settings": settings,
            "guidance": guidance, "stages": stages, "needs": needs, "clashes": clashes, "warnings": warnings,
            "diagnose": [dict(d, skill=p["name"]) for p in parts for d in p["diagnose"]],
            "digests": {p["name"]: p["digest"] for p in parts}, "own": any(p["own"] for p in parts)}, None


def guidance(skill: Optional[Dict[str, Any]], role: str, used: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """What a role is shown of the skill: its name, the guidance for every role and for this one, the
    diagnoses (writer and analyst), and for a writer the advice for this stage of the budget."""
    if not skill:
        return None
    parts = [skill["guidance"].get("all"), skill["guidance"].get(role)]
    text = "\n\n".join(p for p in parts if p)
    out: Dict[str, Any] = {"name": skill["name"]}
    if text:
        out["guidance"] = text
    if role in ("writer", "analyst") and skill.get("diagnose"):
        out["if_you_see"] = skill["diagnose"]
    if role == "writer" and isinstance(used, (int, float)) and skill.get("stages"):
        stage = "early" if used < 0.5 else "late"
        if skill["stages"].get(stage):
            out["at_this_stage"] = skill["stages"][stage]
    return out if len(out) > 1 else None


def checkout(value: Any, folder: str) -> List[str]:
    """Copy the library skills a search names into its own `skills/` folder, where the run reads them and the
    person edits them. One that is there already is left as it is. Returns the names copied."""
    copied = []
    for name in wanted(value):
        if os.path.isabs(name) or os.sep in name or "/" in name:
            continue      # a path of the person's own: used where it is
        target = os.path.join(folder, "skills", name)
        source = os.path.join(HERE, name)
        if os.path.isdir(target) or not os.path.isfile(os.path.join(source, "skill.yaml")):
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copytree(source, target)
        copied.append(name)
    return copied


def index(folder: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every skill of the library (and of a search's own folder), as records a listing or a website can use."""
    found = list(names())
    if folder and os.path.isdir(os.path.join(folder, "skills")):
        found += [n for n in sorted(os.listdir(os.path.join(folder, "skills"))) if n not in found]
    out = []
    for name in found:
        one, _ = load(name, folder)
        if one:
            out.append({"name": one["name"], "title": one["title"], "domain": one["domain"], "objective": one["objective"],
                        "summary": one["summary"], "tags": one["tags"], "version": one["version"], "authors": one["authors"],
                        "when": one["when"], "combines": one["combines"], "conflicts": one["conflicts"],
                        "sets": sorted(_flat(one["settings"])), "needs": one["needs"], "own": one["own"],
                        "digest": one["digest"]})
    return out


def _flat(settings: Dict[str, Any]) -> Dict[str, Any]:
    from . import form
    return form.flatten(settings)


def search(words: str, folder: Optional[str] = None) -> List[Dict[str, Any]]:
    """The skills whose name, title, domain, objective, summary or tags hold every word, best match first."""
    terms = [w for w in re.split(r"\W+", words.lower()) if w]
    scored = []
    for row in index(folder):
        strong = " ".join([row["name"], row["title"], row["domain"], " ".join(row["tags"])]).lower()
        weak = " ".join([row["objective"], row["summary"], row["when"]]).lower()
        if all(t in strong or t in weak for t in terms):
            scored.append((-sum(2 if t in strong else 1 for t in terms), row["name"], row))
    return [row for _, _, row in sorted(scored)]


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


def library_markdown() -> str:
    """The library as a page of the documentation (`evoloop skills --markdown`)."""
    rows = index()
    out = ["# Skill library", "",
           "Every skill that comes with evoloop. This page is written from the skill files themselves "
           "(`evoloop skills --markdown`). Each is a template: a search copies the ones it names into its own "
           "`skills/` folder, and that copy is yours to edit. [Skills](skills.md) explains how they work and how "
           "to write one.", ""]
    domains: List[str] = []
    for row in rows:
        if row["domain"] not in domains:
            domains.append(row["domain"])
    out += ["| Skill | Domain | For |", "|---|---|---|"]
    out += ["| [`%s`](#%s) | %s | %s |" % (r["name"], r["name"], r["domain"], r["objective"] or r["title"]) for r in rows]
    out.append("")
    for domain in domains:
        out += ["## %s" % domain.capitalize(), ""]
        for row in [r for r in rows if r["domain"] == domain]:
            one = load(row["name"])[0] or {}
            out += ["### %s" % row["name"], "", "**%s.** %s" % (row["title"], row["summary"]), ""]
            if row["when"]:
                out += ["*When to choose it.* %s" % " ".join(row["when"].split()), ""]
            out += ["| | |", "|---|---|", "| Tags | %s |" % (", ".join(row["tags"]) or "none"),
                    "| Sets | %s |" % (", ".join("`%s`" % s for s in row["sets"]) or "nothing: guidance only"),
                    "| Guidance for | %s |" % (", ".join(sorted(one.get("guidance") or {})) or "no role"),
                    "| Diagnoses | %d |" % len(one.get("diagnose") or []),
                    "| Needs from the adapter | %s |" % ("; ".join(row["needs"]["adapter"]) or "nothing special").replace("|", "\\|"),
                    "| Goes well with | %s |" % (", ".join("`%s`" % c for c in row["combines"]) or "any"),
                    "| Not with | %s |" % (", ".join("`%s`" % c for c in row["conflicts"]) or "none"), ""]
            if one.get("diagnose"):
                out += ["| If the results show | Then |", "|---|---|"]
                out += ["| %s | %s |" % (d["see"].replace("|", "\\|"), d["do"].replace("|", "\\|")) for d in one["diagnose"]]
                out.append("")
    return "\n".join(out).rstrip() + "\n"


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")

def _brief(tree: Dict[str, Any], indent: int = 0) -> str:
    """A piece of a brief as it would be written by hand: sections as blocks, lists on one line."""
    out = []
    for key, value in tree.items():
        name = key if re.fullmatch(r"[A-Za-z_][\w]*", str(key)) else '"%s"' % key
        if isinstance(value, dict) and value:
            out.append("%s%s:" % ("  " * indent, name))
            out.append(_brief(value, indent + 1))
        else:
            shown = yaml.safe_dump(value, default_flow_style=True).strip().replace("\n...", "")
            if isinstance(value, list):
                shown = "[%s]" % ", ".join("%g" % v if isinstance(v, float) else str(v) for v in value)
            out.append("%s%s: %s" % ("  " * indent, name, shown))
    return "\n".join(out)



def guide_markdown(name: str) -> str:
    """One optimisation goal as a practical page: where to start, why, what the evaluator must report, when to
    choose something else, and how to read the result. Written from the skill's own file."""
    from . import form
    one = load(name)[0]
    start = one["start"]
    brief: Dict[str, Any] = {"run": {"type": start.get("run_type") or "explore_then_exploit", "skill": one["name"]},
                             "budget": {"evaluations": start.get("evaluations") or 100}}
    for key, value in (start.get("brief") or {}).items():
        brief.setdefault(key, {}).update(value) if isinstance(value, dict) else brief.__setitem__(key, value)
    out = ["# %s" % one["goal"], "",
           "Skill `%s` · domain: %s · [the skill in full](../skill-library.md#%s)" % (one["name"], one["domain"], one["name"]), "",
           one["summary"], "", "## Start here", "",
           "Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.", "",
           "```yaml", _brief(brief).rstrip(), "```", "",
           "!!! note \"A starting point\"", "    These settings are a reasoned starting point. They have not been measured against "
           "alternatives; see [Status and limits](../status.md). The numbers in the example (the budget, any limits or "
           "ranges) are placeholders for yours.", ""]
    out += ["## Why this set-up", "", one["why"], ""]
    sets = form.flatten(one["settings"])
    if sets:
        out += ["The skill sets these for you (anything you set in the brief wins):", "", "| Setting | Value |", "|---|---|"]
        out += ["| [`%s`](../fields.md) | `%s` |" % (path, _cell(yaml.safe_dump(value, default_flow_style=True).strip().replace("\n...", "")))
                for path, value in sorted(sets.items())]
        out.append("")
    else:
        out += ["The skill sets nothing itself: the run type and the defaults decide the search, and the skill supplies "
                "the guidance.", ""]
    out += ["## What your evaluator must report", ""]
    needs = one["needs"]
    if needs["adapter"] or needs["figures"] or needs["references"]:
        out += ["- %s" % n for n in needs["adapter"]]
        out += ["- **Required in every result:** `%s`. A search that never sees it is told so in the report." % f for f in needs["figures"]]
        out += ["- **A reference row on the leaderboard for:** %s (`evoloop reference`)." % r for r in needs["references"]]
    else:
        out += ["Nothing beyond the score."]
    out += ["", "How the adapter reports these: [The project's code](../project-contract.md).", ""]
    if one["instead"] or one["conflicts"]:
        out += ["## Choose something else when", "", "| If | Use |", "|---|---|"]
        for row in one["instead"]:
            names_ = wanted(row["use"])
            link = " with ".join("[`%s`](%s.md)" % (n, n) for n in names_)
            out.append("| %s | %s |" % (_cell(row["if"]), link))
        out.append("")
    if one["combines"]:
        out += ["It combines well with %s (`run.skill: [%s, ...]`)." % (
            ", ".join("[`%s`](%s.md)" % (n, n) for n in one["combines"]), one["name"]), ""]
    out += ["## Reading the result", "", one["reading"], "",
            "Where to look: `evoloop leaderboard`, `evoloop show`, and the report "
            "([Records and the study file](../records.md)). To change course while it runs: [Steering a run](../steering.md).", ""]
    out += ["## What the agents are told", ""]
    for role in ("all", "writer", "analyst", "strategist"):
        if one["guidance"].get(role):
            out += ["??? note \"%s\"" % {"all": "Every role", "writer": "The writer", "analyst": "The analyst",
                                           "strategist": "The strategist"}[role]]
            out += ["    " + line if line else "" for line in one["guidance"][role].split("\n")] + [""]
    if one["diagnose"]:
        out += ["| If the results show | Then |", "|---|---|"]
        out += ["| %s | %s |" % (_cell(d["see"]), _cell(d["do"])) for d in one["diagnose"]]
        out.append("")
    if one["stages"]:
        out += ["Early in the budget: %s" % one["stages"].get("early", ""), "", "Late in the budget: %s" % one["stages"].get("late", ""), ""]
    out += ["You can change any of this: the search gets its own copy of the skill in `skills/%s/skill.yaml` "
            "([Skills](../skills.md))." % one["name"], ""]
    return "\n".join(out).rstrip() + "\n"


def guides_index_markdown() -> str:
    rows = [load(n)[0] for n in names()]
    out = ["# What do you want to optimize?", "",
           "Each goal below is a different search, with its own page: a starting configuration, why it fits, what "
           "your evaluator must report, when to choose another, and how to read the result.", ""]
    labels = {"model": "A model", "settings": "Numbers only", "algorithm": "An algorithm", "bioinformatics": "A bioinformatics method",
              "pipeline": "A data pipeline"}
    seen: List[str] = []
    for row in rows:
        if row["domain"] in seen:
            continue
        seen.append(row["domain"])
        out += ["## %s" % labels.get(row["domain"], row["domain"].capitalize()), "", "| I want to | Guide | In one line |", "|---|---|---|"]
        out += ["| %s | [`%s`](%s.md) | %s |" % (r["goal"], r["name"], r["name"], _cell(r["objective"])) for r in rows if r["domain"] == row["domain"]]
        out.append("")
    out += ["## Telling similar goals apart", "",
            "| You have | You want | Use |", "|---|---|---|",
            "| a good model | its learning rate, weight decay or widths set better | [`settings-tuning`](settings-tuning.md) |",
            "| a good model | to change how it trains: the loss, the optimizer, augmentation | [`model-training-recipe`](model-training-recipe.md) |",
            "| a good model | one smaller or faster replacement | [`model-efficiency`](model-efficiency.md) |",
            "| a good model | the best model at each of several sizes | [`model-size-frontier`](model-size-frontier.md) |",
            "| a strong model or ensemble | a small model that keeps its accuracy | [`model-distillation`](model-distillation.md) |",
            "| a task and a baseline | the best score you can get | [`model-performance`](model-performance.md) |",
            "| correct code that is slow | the same output, sooner | [`algorithm-runtime`](algorithm-runtime.md) or [`data-pipeline`](data-pipeline.md) |", "",
            "Goals can be combined ([Skills](../skills.md#combining-skills)), and none of these starting points has been "
            "measured against the others yet ([Status and limits](../status.md)).", ""]
    return "\n".join(out).rstrip() + "\n"


def write_guides(folder: str) -> List[str]:
    os.makedirs(folder, exist_ok=True)
    pages = {"index.md": guides_index_markdown()}
    pages.update({"%s.md" % name: guide_markdown(name) for name in names()})
    for page, text in pages.items():
        with open(os.path.join(folder, page), "w", encoding="utf-8") as handle:
            handle.write(text)
    return sorted(pages)
