"""Skills: what kind of optimization a search is.

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
import json
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
_cache: Dict[str, Tuple[Any, Any]] = {}


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
        info = os.stat(file)
        stamp = (info.st_mtime_ns, info.st_size)      # the size too: two edits within one tick of the clock
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
           "`skills/` folder, and that copy is yours to edit. [Edit or write a skill](skills.md) explains how, and "
           "[Skill file format](skill-format.md) is the reference for the file.", ""]
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
            out += ["| | |", "|---|---|", "| File | %s |" % file_links(row["name"]), "| Tags | %s |" % (", ".join(row["tags"]) or "none"),
                    "| Sets | %s |" % (", ".join("`%s`" % s for s in row["sets"]) or "nothing: guidance only"),
                    "| Guidance for | %s |" % (", ".join(sorted(one.get("guidance") or {})) or "no role"),
                    "| Diagnoses | %d, in the guide |" % len(one.get("diagnose") or []),
                    "| Needs from the evaluator | %s |" % ("; ".join(row["needs"]["adapter"]) or "nothing special").replace("|", "\\|"),
                    "| Goes well with | %s |" % (", ".join("`%s`" % c for c in row["combines"]) or "any"),
                    "| Not with | %s |" % (", ".join("`%s`" % c for c in row["conflicts"]) or "none"), ""]
            out += ["[The guide for this goal](guides/%s.md) has the starting brief, the advice the agents are given and the "
                    "diagnoses in full." % row["name"], ""]
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



def _value(value: Any) -> str:
    """A setting's value as a table cell: long lists of text one item to a line, anything else as YAML."""
    if isinstance(value, list) and value and all(isinstance(v, str) for v in value) and max(len(v) for v in value) > 40:
        return "<br>".join("%d. %s" % (i, _cell(v)) for i, v in enumerate(value, 1))
    return "`%s`" % _cell(yaml.safe_dump(value, default_flow_style=True).strip().replace("\n...", ""))


def _listed(text: str) -> str:
    """A skill's text with blank lines around its dash lists, so that a page shows them as lists."""
    out: List[str] = []
    in_list = False
    for line in text.split("\n"):
        item = line.startswith("- ")
        more = in_list and line.startswith("  ") and line.strip() != ""
        if item and not in_list and out and out[-1].strip():
            out.append("")
        if in_list and not item and not more and line.strip():
            out.append("")
        in_list = item or more
        out.append(line)
    return "\n".join(out)


def guide_markdown(name: str) -> str:
    """One skill as a page: how to use it, exactly what it sets, what it tells each agent, what the scoring script
    must report, and the file itself. Everything on the page is read from the skill's file."""
    from . import form
    one = load(name)[0]
    start = one["start"]
    brief: Dict[str, Any] = {"run": {"skill": one["name"], "type": start.get("run_type") or "explore_then_exploit"},
                             "budget": {"evaluations": start.get("evaluations") or 100}}
    for key, value in (start.get("brief") or {}).items():
        brief.setdefault(key, {}).update(value) if isinstance(value, dict) else brief.__setitem__(key, value)
    preview = '<a href="../../which-search/?goal=%s&run=%s#preview-a-search">Preview the resulting search</a>' % (
        one["name"], brief["run"]["type"])
    out = ["# %s" % one["goal"], "",
           "Skill `%s`. %s" % (one["name"], one["summary"]), "",
           "File: %s. A search copies this file to `mysearch/skills/%s/skill.yaml` when you choose the skill, and "
           "reads that copy. [Edit it during setup](../skills.md)." % (file_links(one["name"]), one["name"]), "",
           "## When to use", "", one["when"] or one["summary"], ""]
    out += ["## Usage", "",
            "[Use this skill in setup](../setting-up.md#3-answer-the-setup-questions) · "
            "[Combine it with another skill](../skills.md#combining-skills) · %s" % preview, "",
            "In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or "
            "ranges are placeholders.", "", "```yaml", _brief(brief).rstrip(), "```", ""]
    sets = form.flatten(one["settings"])
    out += ["## Settings", ""]
    if sets:
        out += ["A skill's settings override the run type's and the autonomy level's. Settings in your brief override "
                "the skill's.", "", "| Setting | Value |", "|---|---|"]
        out += ["| [`%s`](../fields.md#%s) | %s |" % (path, path.replace(".", "-"), _value(value)) for path, value in sorted(sets.items())]
        out.append("")
    else:
        out += ["Nothing. This skill only supplies instructions; the run type and the defaults set the search.", ""]
    out += ["## Agent guidance", "",
            "This text is added to every call to the role named. It is taken from the skill's file.", ""]
    labels = {"all": "Every role", "writer": "Writer", "analyst": "Analyst", "strategist": "Strategist",
              "coordinator": "Coordinator", "conductor": "Conductor"}
    for role in ROLES:
        if one["guidance"].get(role):
            out += ['=== "%s"' % labels[role], ""]
            out += ["    " + line if line else "" for line in _listed(one["guidance"][role]).split("\n")] + [""]
    if one["diagnose"]:
        out += ["The writer and the analyst are also given these rules:", "", "| If the results show | Then |", "|---|---|"]
        out += ["| %s | %s |" % (_cell(d["see"]), _cell(d["do"])) for d in one["diagnose"]]
        out.append("")
    if one["stages"]:
        out += ["And the writer is told, in the first half of the budget: \"%s\" In the second half: \"%s\"" % (
            one["stages"].get("early", ""), one["stages"].get("late", "")), ""]
    out += ["## Evaluator requirements", ""]
    needs = one["needs"]
    if needs["adapter"] or needs["figures"] or needs["references"]:
        out += ["- %s" % n for n in needs["adapter"]]
        out += ["- `%s` in every result. The report warns if no result has it." % f for f in needs["figures"]]
        out += ["- A leaderboard row for %s, added with `evoloop reference`. The report warns if it is missing." % r
                for r in needs["references"]]
    else:
        out += ["The score only."]
    out += ["", "[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)", ""]
    out += ["## Reading the results", "", one["reading"], ""]
    if one["why"]:
        out += ["## Rationale", "", one["why"], ""]
    if one["instead"] or one["combines"]:
        out += ["## Related skills", ""]
        if one["instead"]:
            out += ["| If | Use |", "|---|---|"]
            for row in one["instead"]:
                names_ = [n for n in wanted(row["use"]) if n != one["name"]] or wanted(row["use"])
                both = len(wanted(row["use"])) > len(names_)
                link = ("add " if both else "") + " with ".join("[`%s`](%s.md)" % (n, n) for n in names_) + (" to this one" if both else "")
                out.append("| %s | %s |" % (_cell(row["if"]), link))
            out.append("")
        if one["combines"]:
            out += ["Can be combined with %s: `run.skill: [%s, %s]`." % (
                ", ".join("[`%s`](%s.md)" % (n, n) for n in one["combines"]), one["name"], one["combines"][0]), ""]
    with open(os.path.join(one["path"], "skill.yaml"), "r", encoding="utf-8") as handle:
        text = handle.read().rstrip()
    out += ["## Skill file", "", "%s" % file_links(one["name"]), "", "```yaml", text, "```", ""]
    return "\n".join(out).rstrip() + "\n"


def write_guides(folder: str) -> List[str]:
    os.makedirs(folder, exist_ok=True)
    pages: Dict[str, str] = {}
    pages.update({"%s.md" % name: guide_markdown(name) for name in names()})
    for page, text in pages.items():
        with open(os.path.join(folder, page), "w", encoding="utf-8") as handle:
            handle.write(text)
    return sorted(pages)


REPO = "https://github.com/cameo-db/evoloop/blob/main/evoloop"
RAW = "https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop"


def file_links(name: str) -> str:
    """Where a library skill's file is: in the repository, and as a plain file to download."""
    return "[`evoloop/skills/%s/skill.yaml`](%s/skills/%s/skill.yaml) ([raw](%s/skills/%s/skill.yaml))" % (
        name, REPO, name, RAW, name)


def table_markdown() -> str:
    """Every library skill with what it sets, read from the files: the table on the documentation's front page."""
    from . import form
    out = ["| Skill | Goal | Parent selection | What may change | Other settings it changes | File |", "|---|---|---|---|---|---|"]
    for name in names():
        one = load(name)[0]
        sets = form.flatten(one["settings"])
        other = sorted(k for k in sets if k not in ("strategy.mechanism", "space.preset"))
        out.append("| [`%s`](guides/%s.md) | %s | %s | %s | %s | [skill.yaml](%s/skills/%s/skill.yaml) |" % (
            name, name, _cell(one["goal"]),
            "`%s`" % sets["strategy.mechanism"] if "strategy.mechanism" in sets else "not set",
            "`%s`" % sets["space.preset"] if "space.preset" in sets else "not set",
            ", ".join("`%s`" % k for k in other) or "none", REPO, name))
    return "\n".join(out) + "\n"


# --- the search's own copies: what is there, how it differs from the library, several merged into one ------------

class _Block(yaml.SafeDumper):
    """Writes text of several lines as a block, so that a merged skill reads like one written by hand."""


def _text(dumper: yaml.Dumper, value: str) -> Any:
    if "\n" in value:
        value = "\n".join(line.rstrip() for line in value.split("\n"))
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", value)


_Block.add_representer(str, _text)


def file_of(name: str, folder: Optional[str] = None) -> Optional[str]:
    path = find(name, folder)
    return os.path.join(path, "skill.yaml") if path else None


def _read(path: Optional[str]) -> Optional[str]:
    try:
        with open(path or "", "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def state(value: Any, folder: Optional[str] = None) -> List[Dict[str, Any]]:
    """For each skill named: the file a search in `folder` reads, and whether it is the library's, the search's own
    unchanged copy of it, an edited copy, or a skill that is not in the library at all."""
    out = []
    for name in wanted(value):
        file = file_of(name, folder)
        library = _read(os.path.join(HERE, os.path.basename(name), "skill.yaml"))
        mine = _read(file)
        if file is None:
            kind = "missing"
        elif os.path.abspath(os.path.dirname(file)) == os.path.abspath(os.path.join(HERE, os.path.basename(name))):
            kind = "library"
        elif library is None:
            kind = "own"
        else:
            kind = "copy" if mine == library else "edited"
        _, fault = load(name, folder)
        out.append({"name": name, "file": file, "kind": kind, "fault": fault})
    return out


KINDS = {"library": "the library's file; your search gets its own copy when you choose the skill",
         "copy": "your search's copy, the same as the library's", "edited": "your search's copy, edited",
         "own": "your own skill", "missing": "not found"}


def differs(name: str, folder: Optional[str] = None) -> Optional[List[str]]:
    """The lines by which the search's copy of a skill differs from the library's: None when the library has no
    skill of that name, an empty list when the two are the same."""
    import difflib
    library = _read(os.path.join(HERE, os.path.basename(ALIASES.get(name, name)), "skill.yaml"))
    mine = _read(file_of(name, folder))
    if library is None or mine is None:
        return None
    return [line.rstrip("\n") for line in difflib.unified_diff(
        library.splitlines(), mine.splitlines(), "library", "yours", lineterm="", n=1)]


def sets(value: Any, folder: Optional[str] = None) -> List[str]:
    """`setting = value` for everything the named skills set, as one search would have them."""
    from . import form
    found, _ = combine(value, folder)
    return ["%s = %s" % (k, json.dumps(v, default=str)) for k, v in sorted(form.flatten((found or {}).get("settings") or {}).items())]


def merged_yaml(value: Any, name: str, folder: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Several skills written out as one skill file: (the text, None) or (None, why not). A search run with the
    merged file has the settings and shows the agents the text that it would have with the skills combined."""
    found, fault = combine(value, folder)
    if found is None:
        return None, fault or "name the skills to merge"
    if len(found["parts"]) < 2:
        return None, "name at least two skills to merge; to edit one, edit the search's copy of it"
    parts = [load(n, folder)[0] for n in found["parts"]]
    union = lambda key: [x for i, x in enumerate(sum((p[key] for p in parts), [])) if x not in sum((p[key] for p in parts), [])[:i]]
    raw: Dict[str, Any] = {
        "name": name, "title": found["title"], "summary": found["summary"], "domain": parts[0]["domain"],
        "objective": "; ".join(p["objective"] for p in parts if p["objective"]), "tags": union("tags"), "version": 1,
        "authors": union("authors"), "when": "\n".join("%s: %s" % (p["name"], p["when"]) for p in parts if p["when"]),
        "settings": found["settings"], "guidance": found["guidance"],
        "diagnose": [{"see": d["see"], "do": d["do"]} for d in found["diagnose"]], "stages": found["stages"],
        "needs": found["needs"], "conflicts": [c for c in union("conflicts") if c not in found["parts"]]}
    raw = {k: v for k, v in raw.items() if v not in (None, "", [], {})}
    fault = check(raw)
    if fault:
        return None, fault
    head = ["# %s: merged from %s. This file is yours to edit." % (name, " + ".join(found["parts"]))]
    if found["clashes"]:
        head.append("# Where two of them set the same thing, the later one's value was kept:")
        head += ["#   %s: %r (%s), not %r (%s)" % (c["setting"], c["to"], c["stands"], c["value"], c["from"]) for c in found["clashes"]]
    return "\n".join(head) + "\n" + yaml.dump(raw, Dumper=_Block, sort_keys=False, width=110, allow_unicode=True), None


OWN_NAME = re.compile(r"[a-z0-9][a-z0-9_-]*")


def merge(value: Any, name: str, folder: str) -> Tuple[Optional[str], Optional[str]]:
    """Write the named skills as one skill, `skills/NAME/skill.yaml` in the search folder: (the file, None) or
    (None, why not). Nothing that is there already is written over."""
    if not OWN_NAME.fullmatch(name or ""):
        return None, "give the merged skill a name in lower case, with digits, hyphens or underscores (for instance my-students)"
    if name in names() or name in ALIASES:
        return None, "%s is a skill of the library; give the merged skill a name of its own" % name
    target = os.path.join(folder, "skills", name)
    if os.path.exists(target):
        return None, "%s exists already" % target
    text, fault = merged_yaml(value, name, folder)
    if text is None:
        return None, fault
    os.makedirs(target)
    file = os.path.join(target, "skill.yaml")
    with open(file, "w", encoding="utf-8") as handle:
        handle.write(text)
    return file, None


def write_edited(name: str, text: str, folder: str) -> Optional[str]:
    """Save an edited skill file (from the set-up form) as the search's copy. Returns why not, or None."""
    name = ALIASES.get(name, name)
    if not OWN_NAME.fullmatch(name or ""):
        return "%r is not the name of a skill" % name
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return "the edited skill %s is not valid YAML: %s" % (name, exc)
    fault = check(raw)
    if fault:
        return "the edited skill %s cannot be used: %s" % (name, fault)
    target = os.path.join(folder, "skills", name)
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, "skill.yaml"), "w", encoding="utf-8") as handle:
        handle.write(text if text.endswith("\n") else text + "\n")
    return None


def texts(folder: Optional[str] = None) -> Dict[str, str]:
    """The file of every skill a search in `folder` could name (its own copies first), for the set-up form."""
    out = {}
    for row in index(folder):
        text = _read(file_of(row["name"], folder))
        if text:
            out[row["name"]] = text
    return out


def told(skill: Optional[Dict[str, Any]]) -> List[str]:
    """What a skill adds to the agent calls, role by role, as lines of a plan."""
    if not skill:
        return []
    out: List[str] = []
    labels = {"all": "Every role that is given the skill (writer, analyst, strategist, coordinator, conductor)"}
    for role in ROLES:
        text = skill["guidance"].get(role)
        if text:
            out += ["", "  %s:" % labels.get(role, "The %s, in addition" % role)] + ["    " + line for line in text.split("\n")]
    if skill.get("diagnose"):
        out += ["", "  Writer and analyst, if the results show:"]
        out += ["    - %s -> %s" % (d["see"], d["do"]) for d in skill["diagnose"]]
    for stage, label in (("early", "first half of the budget"), ("late", "second half of the budget")):
        if skill.get("stages", {}).get(stage):
            out += ["", "  Writer, in the %s:" % label] + ["    " + line for line in skill["stages"][stage].split("\n")]
    return out


# --- a skill of the person's own, from an empty template -----------------------------------------------------------

TEMPLATE = """# {name}: a skill of your own. It does not have to resemble a library skill.
# A skill does two things: its settings are applied to the search, and its guidance is added to the agent
# calls. Every entry is optional. Delete what you do not need.
name: {name}
title: One line saying what this skill is for
summary: One or two sentences, shown in listings and in the plan.

# Search settings this skill applies. Any setting that can change during a run may go here; the run type
# decides the rest. For example:
#   settings:
#     strategy: {{mechanism: pareto, second_metric: parameters, second_direction: minimize}}
settings: {{}}

# Text added to the agent calls. `all` goes to every role, the others to one role.
guidance:
  all: |
    Say what this search is for and what counts as success.
  writer: |
    Say what to try first, what to avoid, and what must not change.

# Rules for the writer and the analyst: what a result means, and what to do about it. For example:
#   diagnose:
#     - see: "training loss falls and validation loss does not"
#       do: "regularize before adding capacity"
diagnose: []

# Advice to the writer in the first and the second half of the budget. For example:
#   stages: {{early: "Try several kinds of design.", late: "Refine the two best."}}
stages: {{}}

# What the evaluator must report for this skill to work. For example:
#   needs: {{figures: [parameters], references: ["teacher"]}}
needs: {{}}
"""


def new(name: str, folder: str) -> Tuple[Optional[str], Optional[str]]:
    """Write an empty skill of the person's own, `skills/NAME/skill.yaml` in the search folder: (the file, None) or
    (None, why not). Nothing that is there already is written over."""
    if not OWN_NAME.fullmatch(name or ""):
        return None, "give the skill a name in lower case, with digits, hyphens or underscores (for instance my-skill)"
    if name in names() or name in ALIASES:
        return None, "%s is a skill of the library; give yours a name of its own, or copy that one with --copy" % name
    target = os.path.join(folder, "skills", name)
    if os.path.exists(target):
        return None, "%s exists already" % target
    os.makedirs(target)
    file = os.path.join(target, "skill.yaml")
    with open(file, "w", encoding="utf-8") as handle:
        handle.write(TEMPLATE.format(name=name))
    return file, None
