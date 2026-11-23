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
# Words in a goal that name the metric being optimized.
METRIC_HINTS = [("spearman_r", r"spearman"), ("pearson_r", r"pearson|correlation"), ("r2", r"\br2\b|r squared|r\^2"),
                ("auroc", r"auroc|\bauc\b"), ("auprc", r"auprc|precision.recall"), ("f1", r"\bf1\b"),
                ("accuracy", r"accurac"), ("mse", r"\bmse\b|mean squared error"), ("perplexity", r"perplexity"),
                ("loss", r"\bloss\b"), ("runtime_s", r"runtime|faster|latency|speed")]
LOWER_IS_BETTER = ("mse", "perplexity", "loss", "runtime_s")

# Words in a goal that point to a kind of optimization, most specific first.
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
SECTIONS = ["Goal", "Data", "Budget", "Search", "Training runs", "Compute", "Agents", "Oversight"]


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
    {"field": "objective.metric", "section": "Goal", "title": "Name of the score", "kind": "text",
     "question": "What is the score called?",
     "why": "The name of the metric your evaluator reports as its score, such as pearson_r or val_loss. It is recorded "
            "with the results and in the study file, so that this search can be compared with others."},
    {"field": "evaluation.metrics", "empty": "nothing tracked beyond the score", "section": "Goal", "title": "Metrics to track", "kind": "text",
     "question": "Which validation metrics should be tracked, and how is each computed?",
     "why": "Give each as `name: how it is computed`, separated by semicolons: the score, and anything else your "
            "evaluator reports on validation data. The agents see these. They are recorded in the study file, and "
            "the report warns if one is missing from the results."},
    {"field": "evaluation.test_metrics", "empty": "no test evaluations", "section": "Goal", "title": "Test evaluations", "kind": "text",
     "question": "Which test evaluations should be run on every design?",
     "why": "Held-out evaluations, each as `name: what it measures`, separated by semicolons. Give as many as you "
            "want to follow. They are never shown to the agents or used for selection. Which evaluations count as "
            "validation and which as test is your decision."},
    {"field": "data.name", "empty": "not recorded", "section": "Data", "title": "Dataset", "kind": "text",
     "question": "What data is the search run on?",
     "why": "A name for the dataset, with an accession if it has one. It is recorded in the study file, so that "
            "results are compared only with results on the same data."},
    {"field": "data.splits", "empty": "not recorded", "section": "Data", "title": "Data split", "kind": "text",
     "question": "How is the data split into training, validation and test sets?",
     "why": "In a sentence, for instance `chromosomes 8 and 9 held out for test, 10 for validation`. The split is "
            "yours to choose. It is recorded in the study file, and it says which data each metric was computed on."},
    {"field": "data.fraction", "section": "Data", "title": "Share of the training data", "kind": "number",
     "question": "What share of the training data should each training run use?",
     "why": "1 uses all of it. A smaller share makes each run cheaper, and the best designs can be trained on all "
            "of the data afterwards. Passed to your evaluator as EVO_DATA_FRACTION."},
    {"field": "budget.evaluations", "section": "Budget", "title": "Models to train", "kind": "number",
     "question": "How many models may be trained in all?",
     "why": "The schedule and the guidance for a small or large search are worked out from it."},
    {"field": "run.type", "section": "Search", "title": "Kind of search", "kind": "choice",
     "question": "How should the search spend its evaluations?",
     "why": "It sets the strategy, the schedule, the harness and the search space unless you set them yourself.",
     "choices": _choices(menu.RUN_TYPES)},
    {"field": "run.skill", "empty": "no skill", "section": "Search", "title": "Kind of optimization", "kind": "choice",
     "question": "Which goal should the agents be given guidance for? (Optional. To combine skills, give their names separated by commas.)",
     "why": "A skill sets what suits one goal and adds guidance to the agent calls. The search runs without one. "
            "You can read and edit the skill file before you confirm.",
     "choices": [{"value": "none", "label": "none", "description": "No skill: the run type and the defaults decide, and the agents see only your task.md and notes."}]
                + _choices(menu.SKILLS), "other": True},
    {"field": "run.description", "section": "Search", "title": "Your own description", "kind": "text",
     "question": "Describe the search you want, in your own words.",
     "why": "With the custom kind the agents read this as your first note.", "when": {"run.type": ["custom"]}},
    {"field": "space.preset", "section": "Search", "title": "What may change", "kind": "choice",
     "question": "Which parts of the code may the search change?",
     "why": "Code enforces it: a design that changes anything else is not run.", "choices": _choices(menu.SPACES)},
    {"field": "limits", "empty": "no limits", "section": "Search", "title": "Hard limits", "kind": "text",
     "question": "Are there hard limits every design must stay within?",
     "why": "Give each as `metric <= value` or `metric >= value`, separated by semicolons, for instance "
            "`parameters <= 2000000; training_minutes <= 30`, or answer `none`. The metric is one your evaluator "
            "reports. Code rejects a design outside a limit: it gets no score and is not charged to the budget."},
    {"field": "harness.autonomy", "empty": "left to the kind of search you chose", "section": "Search", "title": "Agentic or harnessed", "kind": "choice",
     "question": "How much of the search should the agents decide?",
     "why": "The more they decide, the more calls they make. The plan shows the likely cost of each level.",
     "choices": _choices(menu.AUTONOMY)},
    {"field": "evaluation.allowance", "section": "Training runs", "title": "Length of a run", "kind": "number",
     "question": "How long is one training run, in the project's own unit (epochs, steps, seconds)?",
     "why": "Passed to every job as EVO_ALLOWANCE. The usual answer is the length the baseline is trained for now."},
    {"field": "evaluation.noise", "section": "Training runs", "title": "Noise of the score", "kind": "number",
     "question": "How much does the score differ between two fits of the same model?",
     "why": "A difference smaller than this is treated as no difference. Set a small value, or estimate it from a few runs of the baseline."},
    {"field": "evaluation.screen_keep", "section": "Training runs", "title": "Early stopping", "kind": "choice", "other": True,
     "question": "Should weak training runs be stopped early?",
     "why": "Stopping weak runs leaves more of the budget for the rest, at the risk of dropping a design that "
            "starts slowly. It needs your evaluator to report its score as it trains.",
     "choices": [{"value": 0.5, "label": "Stop the weaker half",
                  "description": "New designs are compared halfway through a run and the weaker half stop there. "
                                 "A stopped run is charged half an evaluation."},
                 {"value": 1.0, "label": "No early stopping", "description": "Every run trains to its full length."}]},
    {"field": "baseline.mode", "section": "Training runs", "title": "Baseline", "kind": "choice",
     "question": "What should be done about the baseline?", "why": "It is the reference every gain is measured against.",
     "choices": [{"value": "train", "label": "train", "description": "Fit the code as it stands, inside the search, as the first run."},
                 {"value": "import", "label": "import", "description": "Use a fit you already have (give its folder in baseline.import_from)."},
                 {"value": "skip", "label": "skip", "description": "No baseline: the first designs are compared with each other."}]},
    {"field": "compute.gpus", "section": "Compute", "title": "Jobs at once", "kind": "number",
     "question": "How many models may train at the same time?",
     "why": "The number of training jobs kept running: on a workstation usually its number of GPUs, on a cluster "
            "your share of the queue."},
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


def state(brief: Dict[str, Any], folder: Optional[str] = None) -> Dict[str, Any]:
    """Every question that applies now, with its answer or default, and where the person is in the list."""
    settings, sources = form.resolve(brief, folder=folder)
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


def metrics_from_text(text: str) -> Any:
    """`name: how it is computed; name: ...` (or one to a line) as a mapping. Text with no colon is returned as it
    is, so that the check can say what is wrong with it."""
    out: Dict[str, str] = {}
    for part in [p.strip() for p in text.replace("\n", ";").split(";") if p.strip()]:
        if ":" not in part:
            return text
        name, about = part.split(":", 1)
        out[name.strip()] = about.strip()
    return out


def limits_from_text(text: str) -> Any:
    """`parameters <= 2000000; training_minutes <= 30` as {metric: {max: x}}; `none` as no limits. Text that does
    not read as limits is returned as it is, so that the check can say what would be accepted."""
    import re
    if text.strip().lower() in ("none", "no", "no limits", "-"):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for part in [p.strip() for p in text.replace("\n", ";").split(";") if p.strip()]:
        said = re.match(r"^([A-Za-z_][\w.]*)\s*(<=|>=|<|>|at most|at least|max|min)\s*([-+0-9.eE_,]+)$", part)
        try:
            number = float(said.group(3).replace(",", "").replace("_", "")) if said else None
        except ValueError:
            number = None
        if number is None:
            return text
        side = "max" if said.group(2) in ("<=", "<", "at most", "max") else "min"
        out.setdefault(said.group(1), {})[side] = int(number) if number.is_integer() else number
    return out


def record(brief: Dict[str, Any], field: str, value: Any) -> Optional[str]:
    """Put an answer in the brief (or, with KEEP, note that its default was seen and left). Returns a fault or None."""
    asked = brief.setdefault("status", {}).setdefault("asked", [])
    hint = ((brief.get("status") or {}).get("suggested") or {}).get(field)
    if field in ("evaluation.metrics", "evaluation.test_metrics") and isinstance(value, str) and value != KEEP:
        value = metrics_from_text(value)      # typed as `name: how it is computed; name: ...`
    if field == "limits" and isinstance(value, str) and value != KEEP:
        value = limits_from_text(value)       # typed as `metric <= value; metric >= value`, or `none`
    if field in ("evaluation.screen_keep", "data.fraction") and isinstance(value, str) and value != KEEP:
        try:
            value = 1.0 if value.strip().lower() in ("none", "no", "off") else float(value)
        except ValueError:
            pass
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
    for field, value in form.flatten({k: v for k, v in answers.items() if k not in ("status", "skill_files")}).items():
        if value in form.EMPTY:
            continue
        fault = record(brief, field, value)
        (refused if fault else done).append("%s: %s" % (field, fault) if fault else field)
    for field in (answers.get("status") or {}).get("asked") or []:      # defaults the person saw and left
        if form.known(field):
            record(brief, field, KEEP)
    return done, refused


def shown(value: Any, empty: str = "none") -> str:
    """A value as the person would type it: metrics as `name: how`, limits as `metric <= x`, nothing as words."""
    if value in (None, "", {}, []):
        return empty
    if isinstance(value, dict) and all(isinstance(v, str) for v in value.values()):
        return "; ".join("%s: %s" % (k, v) for k, v in value.items())
    if isinstance(value, dict) and all(isinstance(v, dict) and set(v) <= {"max", "min"} for v in value.values()):
        return "; ".join("%s %s %g" % (m, "<=" if side == "max" else ">=", x) for m, b in value.items() for side, x in sorted(b.items()))
    return str(value)


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
    if current in (None, "", {}, []) and not q["required"]:
        lines.append("  default: %s" % q.get("empty", "none"))
    elif q["kind"] != "choice" and current is not None:
        lines.append("  %s: %s" % (word, shown(current)))
    if hint:
        lines.append("  suggested because %s. Enter accepts it; or give your own answer." % hint["why"])
    return lines


def skill_step(folder: str, brief: Dict[str, Any], ask: Callable[[str], str], say: Callable[[str], None],
               edit: Optional[Callable[[str], bool]] = None) -> None:
    """After the skill is chosen: give the search its own copies, show what they set, and let the person edit
    them, or merge several into one file, before going on."""
    from . import skill as skills
    while True:
        chosen = form.given(brief).get("run.skill")
        skills.checkout(chosen, folder)
        rows = skills.state(chosen, folder)
        if not rows:
            return
        say("")
        say("  This search has its own copy of %s, yours to edit:" % ("the skill" if len(rows) == 1 else "each skill"))
        for row in rows:
            say("    %s   (%s)" % (row["file"] or row["name"], skills.KINDS[row["kind"]]))
            if row["fault"]:
                say("      NOT USABLE: %s" % row["fault"])
        lines = skills.sets(chosen, folder)
        say("  It sets: %s" % ("; ".join(lines) if lines else "no settings; it only adds text to the agent calls"))
        found, _ = skills.combine(chosen, folder)
        for note in (found or {}).get("warnings") or []:
            say("  Note: %s" % note)
        say("  Enter = go on    e = edit %s now%s" % (
            "it" if len(rows) == 1 else "them", "    m = merge them into one file" if len(rows) > 1 else ""))
        reply = ask("> ").strip().lower()
        if reply == "e":
            for row in rows:
                if row["file"] and not (edit and edit(row["file"])):
                    say("  No editor could be opened (set EDITOR). Edit %s in another window, then press Enter." % row["file"])
                    ask("> ")
            continue
        if reply == "m" and len(rows) > 1:
            name = ask("  A name for the merged skill (lower case, hyphens; for instance my-students) > ").strip()
            file, fault = skills.merge(chosen, name, folder)
            if file is None:
                say("  Not merged: %s" % fault)
                continue
            record(brief, "run.skill", name)
            form.save_brief(folder, brief)
            say("  Merged into %s; the search now uses that one file." % file)
            continue
        if any(row["fault"] for row in rows):
            say("  A skill above cannot be used as it is. Fix the file (e), or go back (b at the next question) and choose another.")
        return


def run(folder: str, ask: Callable[[str], str], say: Callable[[str], None],
        edit: Optional[Callable[[str], bool]] = None) -> bool:
    """The terminal walk-through. Returns True when every question has been dealt with."""
    brief = form.load_brief(folder)
    say("Setting up the search in %s. Enter keeps the default; b goes back; q saves and stops." % folder)
    back: List[str] = []
    position: Optional[str] = None
    while True:
        infer(folder, brief)      # best guesses from what is known so far
        now = state(brief, folder)
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
        if q["field"] == "run.skill":
            skill_step(folder, brief, ask, say, edit)
    form.save_brief(folder, brief)
    say("")
    say("All %d questions are done. Next: `evoloop plan %s`, then `evoloop brief %s --confirm \"Your Name\"`." % (
        state(brief, folder)["total"], folder, folder))
    return True


def payload(brief: Dict[str, Any], folder: Optional[str] = None) -> Dict[str, Any]:
    """What the HTML form needs: every question (the form itself decides which apply as answers change),
    the current answers, the defaults, and the schedule each kind of search runs."""
    settings, sources = form.resolve(brief, folder=folder)
    stated = form.given(brief)
    shares = {}
    for name in form.RUN_TYPES:
        variant = copy.deepcopy(brief)
        form.put(variant, "run.type", name)
        shares[name] = form.resolve(variant, folder=folder)[0]["schedule"]["phases"]
    questions = []
    for q in QUESTIONS:
        field = q["field"]
        required = field in form.REQUIRED or field == "run.description"
        questions.append(dict(copy.deepcopy(q), required=required,
                              suggested=None if field in stated else ((brief.get("status") or {}).get("suggested") or {}).get(field),
                              default=None if required and field not in stated else form.get(settings, field)))
    from . import skill as skills
    return {"questions": questions, "answers": {f: stated[f] for f in FIELDS if f in stated}, "sections": SECTIONS,
            "phases": shares, "goal": settings["objective"]["goal"] or "", "skills": skills.texts(folder)}


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
            else:
                found["compute.gpus"] = (1, "no GPU was found on this machine: one job at a time")
        if "compute.gpus" not in found:
            found["compute.gpus"] = (4, "a modest share of a shared cluster; the queue decides how many run at once")
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
    if goal:      # the kind of optimization, from the words of the goal
        for name, words in SKILL_HINTS:
            said = re.search(words, goal)
            if said:
                found["run.skill"] = (name, "the goal says \"%s\"" % said.group(0))
                break
        else:
            found["run.skill"] = ("model-performance", "the goal names no other kind of optimization than a better score")
    if stated.get("run.type") == "settings_only":
        found["run.skill"] = ("settings-tuning", "a search over settings alone: the estimator in code makes the moves, at no agent cost")
    budget = stated.get("budget.evaluations")
    if isinstance(budget, (int, float)) and budget > 0:
        label = form.guidance_for(budget)[0]
        if budget < 45:
            found["run.type"] = ("refine", "with %s models there is no room for a population: a careful search near the baseline" % label)
        else:
            found["run.type"] = ("explore_then_exploit", "the usual choice at %s models: explore first, then work on what was found" % label)
    else:
        found["run.type"] = ("explore_then_exploit", "the usual choice: explore first, then work on what was found")
    # What is optimized and what is tracked. The name of the score comes from the words of the goal; with a name,
    # the least worth tracking is the score on validation data and a held-out copy of it.
    metric = stated.get("objective.metric")
    if not metric and goal:
        for name, words in METRIC_HINTS:
            said = re.search(words, goal)
            if said:
                metric = name
                found["objective.metric"] = (name, "the goal says \"%s\"" % said.group(0))
                if "objective.direction" not in found:
                    found["objective.direction"] = ("minimize" if name in LOWER_IS_BETTER else "maximize",
                                                    "%s is %s when it is better" % (name, "lower" if name in LOWER_IS_BETTER else "higher"))
                break
    if metric and metric != "score":
        bare = re.sub(r"^(val|valid|validation)[_ ]", "", str(metric))      # val_accuracy is accuracy, on validation data
        found["evaluation.metrics"] = ({metric: "%s on the validation data: the score" % bare},
                                       "the score is the least to track; add every other validation metric your evaluator reports")
        found["evaluation.test_metrics"] = ({"test_%s" % bare: "%s on the held-out test data" % bare},
                                            "a held-out copy of the score is the usual minimum; add every other test "
                                            "evaluation you want to follow")
    found["evaluation.noise"] = (0.001, "a small value, to start with: raise it if lineages stall straight after one high "
                                        "score, or estimate it from a few runs of the baseline")
    if not isinstance(budget, (int, float)):
        found["budget.evaluations"] = (100, "the size the default settings are tuned for")
    earlier = status.get("suggested") or {}

    def likely(field: str) -> Any:
        """The answer, or failing that the suggestion: what the search will most likely be set to."""
        if field in stated:
            return stated[field]
        return found[field][0] if field in found else (earlier.get(field) or {}).get("value")

    kind = likely("run.type")
    if kind == "settings_only":
        found["harness.autonomy"] = ("harnessed", "a search over settings alone needs no agent to steer it")
    elif kind:
        found["harness.autonomy"] = ("guided", "the middle level, and what this kind of search uses unless told otherwise: "
                                               "code runs the schedule and the strategist may adjust it within bounds")
    if likely("agents.backend") in ("anthropic_api", "claude_code") and "budget.model_dollars" not in stated:
        from . import estimate
        sketch = copy.deepcopy(brief)      # the search as it would be if every suggestion were accepted
        for field in ("budget.evaluations", "run.type", "agents.backend", "harness.autonomy", "run.skill"):
            if field not in stated and likely(field) is not None:
                form.put(sketch, field, likely(field))
        try:
            est = estimate.estimate(form.resolve(sketch, folder=folder)[0], folder)
        except Exception:      # an estimate is a convenience here: a half-filled brief may not resolve
            est = {"dollars": None}
        if est["dollars"]:
            cap = max(1, int(est["dollars"][2] + 0.999))
            found["budget.model_dollars"] = (cap, "the estimate for this search runs to about $%.2f at its upper end" % est["dollars"][2])
    made = {}
    for field, (value, why) in found.items():
        if field in stated or (earlier.get(field) or {}).get("by", "evoloop") != "evoloop":
            continue      # an answer stands, and so does a suggestion an agent or the person made
        if suggest(brief, field, value, why, by="evoloop") is None:
            made[field] = value
    return made
