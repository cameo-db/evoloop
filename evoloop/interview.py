"""Setting up a search by question and answer: one list of questions, three ways to answer it.

    evoloop setup DIR          in a terminal: one question at a time, numbered choices, Enter for the default
    evoloop brief DIR --next   for an agent in a chat: the next question as JSON, with its choices and
                               where it stands in the list, to be asked one at a time
    evoloop form DIR           a self-contained HTML form to fill in a browser; it gives back a small file
                               that `evoloop brief DIR --import FILE` reads

All three walk the same questions in the same order, by section, and each says where you are: "question 6
of 17, Budget". A question with choices is always given as choices, each with a line on what it means, and
the default is marked. Only the questions that apply are asked: the model is not asked for with the stub,
the Slurm partition not on one machine. Leaving a question at its default records nothing but that you saw
it, so the brief holds only what you chose."""
from __future__ import annotations

import copy
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import form, menu
from .model import catalog

KEEP = "__keep__"       # the answer "leave it at the default"
# Words in a goal that point to a kind of optimisation, most specific first.
SKILL_HINTS = [("model-distillation", r"distil\w*|student|teacher"),
               ("model-ensemble-members", r"ensembl\w*"),
               ("model-size-frontier", r"pareto|trade-?offs?|frontier|range of sizes|across sizes|family of models|at each size"),
               ("model-finetuning", r"fine-?tun\w*|pretrained|pre-trained|foundation model"),
               ("model-mechanistic", r"interpretab\w*|mechanis\w*|biophysic\w*|motif\w*|kinetic\w*|thermodynamic\w*"),
               ("settings-tuning", r"hyper-?param\w*|\btun(e|ing)\b|learning rate"),
               ("model-training-recipe", r"recipe|optimi[sz]er|augmentation|regulari[sz]ation|loss function"),
               ("data-pipeline", r"pipeline|\betl\b|preprocessing"),
               ("bioinformatics-algorithm", r"bioinformatic\w*|aligner|alignment|variant call\w*|peak call\w*|assembl\w*"),
               ("algorithm-runtime", r"\balgorithm\b|run ?time|\bcode\b"),
               ("model-efficiency", r"smaller|faster|efficien\w*|compress\w*|lightweight|fewer parameters|\bspeed\b")]
SECTIONS = ["Goal", "Budget", "Search", "Training runs", "Compute", "Agents", "Oversight"]


def _choices(entries: Dict[str, str], only: Any = None) -> List[Dict[str, str]]:
    return [{"value": name, "label": name, "description": words} for name, words in entries.items()
            if only is None or name in only]


# field, section, short title, the question, why it is asked, kind, choices, and when it applies.
QUESTIONS: List[Dict[str, Any]] = [
    {"field": "objective.goal", "section": "Goal", "title": "Goal", "kind": "text",
     "question": "What is being improved, and why?",
     "why": "Every agent reads this on every call. One or two sentences."},
    {"field": "objective.direction", "section": "Goal", "title": "Direction of the score", "kind": "choice",
     "question": "Is a higher score better, or a lower one?", "why": "Selection turns on it.",
     "choices": [{"value": "maximize", "label": "Higher is better", "description": "maximize: accuracy, correlation, R squared."},
                 {"value": "minimize", "label": "Lower is better", "description": "minimize: a loss or an error."}]},
    {"field": "budget.evaluations", "section": "Budget", "title": "Models to train", "kind": "number",
     "question": "How many models may be trained in all?",
     "why": "The schedule and the guidance for a small or large search are worked out from it."},
    {"field": "run.type", "section": "Search", "title": "Kind of search", "kind": "choice",
     "question": "What kind of search do you want?",
     "why": "It sets the strategy, the schedule, the harness and the search space unless you set them yourself.",
     "choices": _choices(menu.RUN_TYPES)},
    {"field": "run.skill", "section": "Search", "title": "Kind of optimisation", "kind": "choice",
     "question": "What kind of optimisation is this? (To combine skills, give their names separated by commas.)",
     "why": "It sets what suits the task (what is open, how designs are selected) and gives the agents guidance for it. "
            "Independent of the kind of search.",
     "choices": _choices(menu.SKILLS), "other": True},
    {"field": "run.description", "section": "Search", "title": "Your own description", "kind": "text",
     "question": "Describe the search you want, in your own words.",
     "why": "With the custom kind the agents read this as your first note.", "when": {"run.type": ["custom"]}},
    {"field": "space.preset", "section": "Search", "title": "What may change", "kind": "choice",
     "question": "Which parts of the code may the search change?",
     "why": "Code enforces it: a design that changes anything else is not run.", "choices": _choices(menu.SPACES)},
    {"field": "harness.autonomy", "section": "Search", "title": "Agentic or harnessed", "kind": "choice",
     "question": "How much of the search should the agents decide?",
     "why": "The more they decide, the more calls they make. The plan shows the likely cost of each level.",
     "choices": _choices(menu.AUTONOMY)},
    {"field": "evaluation.allowance", "section": "Training runs", "title": "Length of a run", "kind": "number",
     "question": "How long is one training run, in the project's own unit (epochs, steps, seconds)?",
     "why": "It is passed to every job."},
    {"field": "evaluation.noise", "section": "Training runs", "title": "Noise of the score", "kind": "number",
     "question": "How much does the score differ between two fits of the same model?",
     "why": "A difference smaller than this is treated as no difference. A measured seed-to-seed spread is best."},
    {"field": "baseline.mode", "section": "Training runs", "title": "Baseline", "kind": "choice",
     "question": "What should be done about the baseline?", "why": "It is the reference every gain is measured against.",
     "choices": [{"value": "train", "label": "train", "description": "Fit the code as it stands, inside the search, as the first run."},
                 {"value": "import", "label": "import", "description": "Use a fit you already have (give its folder in baseline.import_from)."},
                 {"value": "skip", "label": "skip", "description": "No baseline: the first designs are compared with each other."}]},
    {"field": "compute.gpus", "section": "Compute", "title": "Jobs at once", "kind": "number",
     "question": "How many models may train at the same time?", "why": "The number of jobs kept running."},
    {"field": "compute.scheduler", "section": "Compute", "title": "Where jobs run", "kind": "choice",
     "question": "Where do the training jobs run?", "why": "On a cluster each run is its own job.",
     "choices": [{"value": "local", "label": "local", "description": "Processes on this machine."},
                 {"value": "slurm", "label": "slurm", "description": "Each run its own Slurm job, requeued if preempted."}]},
    {"field": "compute.partition", "section": "Compute", "title": "Slurm partition", "kind": "text",
     "question": "Which Slurm partition?", "why": "Passed to sbatch.", "when": {"compute.scheduler": ["slurm"]}},
    {"field": "compute.qos", "section": "Compute", "title": "Slurm QoS", "kind": "text",
     "question": "Which Slurm QoS?", "why": "Passed to sbatch. Leave it empty if your cluster needs none.",
     "when": {"compute.scheduler": ["slurm"]}},
    {"field": "agents.backend", "section": "Agents", "title": "Agent backend", "kind": "choice",
     "question": "How are the agents called?", "why": "It decides who writes the designs and what it costs.",
     "choices": [{"value": "stub", "label": "stub", "description": "No model call and no cost: a dry run that shows the setup works."},
                 {"value": "anthropic_api", "label": "anthropic_api", "description": "The Anthropic API, billed by the token."},
                 {"value": "claude_code", "label": "claude_code", "description": "The Claude Code command line on this machine, under its own login."}]},
    {"field": "agents.default_model", "section": "Agents", "title": "Model", "kind": "choice", "other": True,
     "question": "Which model should the agents run on?",
     "why": "One model for every role; a model per role can be set later (agents.models).",
     "choices": _choices(menu.MODELS, catalog.OFFERED), "when_not": {"agents.backend": ["stub"]}},
    {"field": "agents.effort", "section": "Agents", "title": "Effort", "kind": "choice",
     "question": "How hard should the model reason?",
     "why": "Reasoning is billed as output, so higher effort costs more. The writer runs at high unless you set agents.efforts.",
     "choices": _choices(menu.EFFORT), "when_not": {"agents.backend": ["stub"]}},
    {"field": "budget.model_dollars", "section": "Agents", "title": "Agent spend cap", "kind": "number",
     "question": "What is the most the agents may cost, in dollars?",
     "why": "No agent call is made once it is reached; the run then waits for you to raise it.",
     "when_not": {"agents.backend": ["stub"]}},
    {"field": "audit.reviews", "section": "Oversight", "title": "Reviews of the agents", "kind": "choice",
     "question": "When should the agents be reviewed?",
     "why": "A review is a written assessment of each role, for you. Each costs one call per role.",
     "choices": _choices(menu.REVIEWS)},
]
FIELDS = [q["field"] for q in QUESTIONS]


def applies(question: Dict[str, Any], values: Dict[str, Any]) -> bool:
    for field, wanted in (question.get("when") or {}).items():
        if values.get(field) not in wanted:
            return False
    for field, unwanted in (question.get("when_not") or {}).items():
        if values.get(field) in unwanted:
            return False
    return True


def state(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Every question that applies now, with its answer or default, and where the person is in the list."""
    settings, sources = form.resolve(brief)
    stated = form.given(brief)
    seen = set((brief.get("status") or {}).get("asked") or [])
    values = {field: form.get(settings, field) for field in FIELDS}
    out = []
    for q in QUESTIONS:
        if not applies(q, values):
            continue
        field = q["field"]
        required = field in form.REQUIRED or (field == "run.description")
        default = None if required and field not in stated else values[field]
        answered = field in stated
        done = answered or (field in seen and not required)
        hint = None if answered else ((brief.get("status") or {}).get("suggested") or {}).get(field)
        out.append(dict(copy.deepcopy(q), required=required, answered=answered, done=done,
                        value=stated.get(field), default=default, suggested=hint,
                        default_from=None if answered or default is None else sources.get(field, "default")))
    for index, q in enumerate(out):
        q["number"], q["of"] = index + 1, len(out)
    todo = [q for q in out if not q["done"]]
    return {"questions": out, "total": len(out), "done": len(out) - len(todo), "next": todo[0] if todo else None,
            "sections": [{"name": name, "total": sum(1 for q in out if q["section"] == name),
                          "done": sum(1 for q in out if q["section"] == name and q["done"])}
                         for name in SECTIONS if any(q["section"] == name for q in out)]}


def parse(question: Dict[str, Any], text: str) -> Any:
    """An answer as typed, turned into a value. Raises ValueError with what would be accepted."""
    text = text.strip()
    if question["kind"] == "number":
        try:
            number = float(text)
        except ValueError:
            raise ValueError("a number is needed")
        return int(number) if number.is_integer() else number
    if question["kind"] == "choice":
        choices = question["choices"]
        if text.isdigit() and 1 <= int(text) <= len(choices):
            return choices[int(text) - 1]["value"]
        for choice in choices:
            if text.lower() in (str(choice["value"]).lower(), str(choice["label"]).lower()):
                return choice["value"]
        if question.get("other") and text:
            return text
        raise ValueError("answer with a number from 1 to %d, or one of: %s" % (
            len(choices), ", ".join(str(c["value"]) for c in choices)))
    if not text:
        raise ValueError("an answer is needed")
    return text


def record(brief: Dict[str, Any], field: str, value: Any) -> Optional[str]:
    """Put an answer in the brief (or, with KEEP, note that its default was seen and left). Returns a fault or None."""
    asked = brief.setdefault("status", {}).setdefault("asked", [])
    hint = ((brief.get("status") or {}).get("suggested") or {}).get(field)
    if value == KEEP and hint is not None and field not in form.given(brief):
        value = hint["value"]          # leaving a suggestion as it is accepts it: the person saw it
    if value == KEEP:
        if (field in form.REQUIRED or field == "run.description") and field not in form.given(brief):
            return "%s has no default: an answer is needed" % field
    else:
        fault = form.check_value(field, value)
        if fault:
            return fault
        form.put(brief, field, value)
    if field not in asked:
        asked.append(field)
    return None


def merge(brief: Dict[str, Any], answers: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Answers from a file (the HTML form's, or any nested mapping of fields) into the brief: (set, refused)."""
    done, refused = [], []
    for field, value in form.flatten({k: v for k, v in answers.items() if k != "status"}).items():
        if value in form.EMPTY:
            continue
        fault = record(brief, field, value)
        (refused if fault else done).append("%s: %s" % (field, fault) if fault else field)
    for field in (answers.get("status") or {}).get("asked") or []:      # defaults the person saw and left
        if form.known(field):
            record(brief, field, KEEP)
    return done, refused


def card(q: Dict[str, Any]) -> List[str]:
    """One question as text, the same way every time: where you are, the question, why, the choices."""
    lines = ["", "Question %d of %d  ·  %s" % (q["number"], q["of"], q["section"]), q["question"], "  (%s)" % q["why"]]
    hint = q.get("suggested") if not q["answered"] else None
    current = q["value"] if q["answered"] else (hint["value"] if hint else q["default"])
    word = "your answer" if q["answered"] else ("suggested" if hint else "default")
    if q["kind"] == "choice":
        for index, choice in enumerate(q["choices"], 1):
            mark = "  <- %s" % word if choice["value"] == current else ""
            lines.append("  %d. %s%s" % (index, choice["label"], mark))
            lines.append("       %s" % choice["description"])
        if q.get("other"):
            lines.append("  or type another value")
    if current is None and not q["required"]:
        lines.append("  default: left to the kind of search you chose")
    elif q["kind"] != "choice" and current is not None:
        lines.append("  %s: %s" % (word, current))
    if hint:
        lines.append("  suggested because %s. Enter accepts it; or give your own answer." % hint["why"])
    return lines


def run(folder: str, ask: Callable[[str], str], say: Callable[[str], None]) -> bool:
    """The terminal walk-through. Returns True when every question has been dealt with."""
    brief = form.load_brief(folder)
    say("Setting up the search in %s. Enter keeps the default; b goes back; q saves and stops." % folder)
    back: List[str] = []
    position: Optional[str] = None
    while True:
        infer(folder, brief)      # best guesses from what is known so far
        now = state(brief)
        q = next((x for x in now["questions"] if x["field"] == position), None) if position else now["next"]
        if q is None:
            break
        for line in card(q):
            say(line)
        has_default = q["answered"] or not q["required"]      # Enter leaves it as it is
        reply = ask("> ").strip()
        if reply.lower() == "q":
            form.save_brief(folder, brief)
            say("Saved. %d of %d done; run `evoloop setup` again to go on." % (now["done"], now["total"]))
            return False
        if reply.lower() == "b":
            position = back.pop() if back else q["field"]
            continue
        if reply == "" and (has_default or q.get("suggested")):
            fault = record(brief, q["field"], KEEP)
        else:
            try:
                fault = record(brief, q["field"], parse(q, reply))
            except ValueError as exc:
                fault = str(exc)
        if fault:
            say("  Not accepted: %s" % fault)
            position = q["field"]
            continue
        back.append(q["field"])
        position = None
        form.save_brief(folder, brief)
    form.save_brief(folder, brief)
    say("")
    say("All %d questions are done. Next: `evoloop plan %s`, then `evoloop brief %s --confirm \"Your Name\"`." % (
        state(brief)["total"], folder, folder))
    return True


def payload(brief: Dict[str, Any]) -> Dict[str, Any]:
    """What the HTML form needs: every question (the form itself decides which apply as answers change),
    the current answers, the defaults, and the schedule each kind of search runs."""
    settings, sources = form.resolve(brief)
    stated = form.given(brief)
    shares = {}
    for name in form.RUN_TYPES:
        variant = copy.deepcopy(brief)
        form.put(variant, "run.type", name)
        shares[name] = form.resolve(variant)[0]["schedule"]["phases"]
    questions = []
    for q in QUESTIONS:
        field = q["field"]
        required = field in form.REQUIRED or field == "run.description"
        questions.append(dict(copy.deepcopy(q), required=required,
                              suggested=None if field in stated else ((brief.get("status") or {}).get("suggested") or {}).get(field),
                              default=None if required and field not in stated else form.get(settings, field)))
    return {"questions": questions, "answers": {f: stated[f] for f in FIELDS if f in stated}, "sections": SECTIONS,
            "phases": shares, "goal": settings["objective"]["goal"] or ""}


def as_json(value: Any) -> str:
    return json.dumps(value, indent=1, default=str)


def suggest(brief: Dict[str, Any], field: str, value: Any, why: str, by: str = "an agent") -> Optional[str]:
    """Propose an answer for the person to accept or change. A suggestion is never an answer: it is shown,
    preselected and with its reason, and becomes an answer only when the person leaves it or picks it."""
    if field not in FIELDS and not form.known(field):
        return "%s is not a field of the brief" % field
    fault = form.check_value(field, value)
    if fault:
        return fault
    brief.setdefault("status", {}).setdefault("suggested", {})[field] = {"value": value, "why": str(why).rstrip("."), "by": by}
    return None


def infer(folder: str, brief: Dict[str, Any]) -> Dict[str, Any]:
    """Best guesses from the machine, the search folder and the answers so far, as suggestions. Nothing is
    suggested for a question that already has an answer, and nothing is guessed where there is no evidence
    (the goal, the length of a run, the noise): those are asked plainly."""
    import os
    import re
    import shutil
    import subprocess
    from . import space
    stated = form.given(brief)
    status = brief.setdefault("status", {})
    found: Dict[str, Tuple[Any, str]] = {}
    if not status.get("machine_looked_at"):
        status["machine_looked_at"] = True
        if shutil.which("sbatch"):
            found["compute.scheduler"] = ("slurm", "this machine has Slurm (sbatch is on the path)")
        else:
            found["compute.scheduler"] = ("local", "there is no Slurm on this machine")
            try:
                listed = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=10)
                count = len([line for line in listed.stdout.splitlines() if line.startswith("GPU ")]) if listed.returncode == 0 else 0
            except (OSError, subprocess.SubprocessError):
                count = 0
            if count:
                found["compute.gpus"] = (count, "nvidia-smi lists %d GPU%s here" % (count, "" if count == 1 else "s"))
        if shutil.which("claude"):
            found["agents.backend"] = ("claude_code", "the claude command is on this machine's path")
        elif os.environ.get("ANTHROPIC_API_KEY"):
            found["agents.backend"] = ("anthropic_api", "ANTHROPIC_API_KEY is set here")
        else:
            found["agents.backend"] = ("stub", "no agent login or key was found here, and a dry run costs nothing")
        found["baseline.mode"] = ("train", "the usual choice: the code as it stands is fitted first, as the reference")
        try:
            table = space.table(os.path.join(folder, "base"))
            structure = [b for b in table.values() if b["kind"] == "structure"]
            recipe = [b for b in structure if b["role"] in form.DEFAULTS["space"]["recipe_roles"]]
            if not structure:
                found["space.preset"] = ("settings_only", "only settings blocks are marked in the code")
            elif recipe and len(recipe) < len(structure):
                found["space.preset"] = ("open_architecture", "model and recipe blocks are both marked; the usual start is the "
                                         "architecture alone, with the recipe opened later")
        except (space.SpaceError, OSError):
            pass
        try:
            task = space.read(os.path.join(folder, "task.md")).lower()
            low = re.search(r"lower (is|are|scores? (is|are)) better|minimi[sz]e", task)
            high = re.search(r"higher (is|are|scores? (is|are)) better|maximi[sz]e", task)
            if bool(low) != bool(high):
                found["objective.direction"] = ("minimize" if low else "maximize", "task.md says \"%s\"" % (low or high).group(0))
        except OSError:
            pass
    goal = str(stated.get("objective.goal") or "").lower()
    if goal:      # the kind of optimisation, from the words of the goal
        for name, words in SKILL_HINTS:
            said = re.search(words, goal)
            if said:
                found["run.skill"] = (name, "the goal says \"%s\"" % said.group(0))
                break
        else:
            found["run.skill"] = ("model-performance", "the goal names no other kind of optimisation than a better score")
    if stated.get("run.type") == "settings_only":
        found["run.skill"] = ("settings-tuning", "a search over settings alone: the estimator in code makes the moves, at no agent cost")
    budget = stated.get("budget.evaluations")
    if isinstance(budget, (int, float)) and budget > 0:
        label = form.guidance_for(budget)[0]
        if budget < 45:
            found["run.type"] = ("refine", "with %s models there is no room for a population: a careful search near the baseline" % label)
        else:
            found["run.type"] = ("explore_then_exploit", "the usual choice at %s models: explore first, then work on what was found" % label)
        backend = stated.get("agents.backend")
        if backend in ("anthropic_api", "claude_code"):
            from . import estimate
            est = estimate.estimate(form.resolve(brief)[0], folder)
            if est["dollars"]:
                cap = max(1, int(est["dollars"][2] + 0.999))
                found["budget.model_dollars"] = (cap, "the estimate for this search runs to about $%.2f at its upper end" % est["dollars"][2])
    made = {}
    for field, (value, why) in found.items():
        if field not in stated and suggest(brief, field, value, why, by="evoloop") is None:
            made[field] = value
    return made
