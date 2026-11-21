"""The commands.

Setting up:   init, example, brief, plan, guide
Running:      run (also continues a stopped run), status, report, study
Steering:     set, note, withdraw, steer, stop, review     (each becomes an entry in the run's ledger)

A steering command does not touch the run directly: it leaves a request that the controller reads on its
next turn, checks, and records as applied or refused. So the same commands work on a run that is going
and on one that is stopped, and everything that changed the run is in one place."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from typing import Any, Dict, List

import yaml

from . import form, space
from .store import Store, View, read_json, write_json

TASK = """# Task

Say here what the problem is, what each marked block is for, and what a good solution looks like. Every
agent reads this file on every call; agents see it, the open blocks and the visible results, and nothing
else of your code.
"""

ADAPTER = '''"""How one design is run. Started in a working copy of base/ with the design's blocks spliced in.

Reads EVO_OUT_DIR, EVO_SEED, EVO_ALLOWANCE, EVO_CHECKPOINT_DIR (and EVO_CONTINUE_FROM, when the run is to
continue an earlier checkpoint); writes result.json; may append to progress.jsonl and read control.json."""
import json
import os

out = os.environ["EVO_OUT_DIR"]
seed = int(os.environ.get("EVO_SEED", "0"))
allowance = float(os.environ["EVO_ALLOWANCE"])

# TODO: call the project's own training here, for `allowance` of its unit, with `seed`.
# During training, report progress so that weak new designs can be stopped part way:
#   {"step": n, "metric": validation_score}  appended to progress.jsonl, then read control.json and stop
#   promptly, still writing the result, if it says {"action": "stop"}.

result = {
    "valid": False,                      # True when the run produced a score
    "score": None,                       # the number the search optimises (validation)
    "diagnostics": {                     # numbers here are shown to the agents...
        "hidden": {},                    # ...except this part: put test-set results here
    },
    "parameters": None,                  # trainable parameter count
    "signature": None,                   # optional: a list of numbers saying where this model's errors fall
    "inference_speed": None,             # optional: {"examples_per_s": n}
    "captured": {},                      # optional: {"environment": {...}, "training": {"loss": ..., ...}} read
}                                        # from the objects the script built, for the study file
with open(os.path.join(out, "result.json"), "w") as handle:
    json.dump(result, handle)
'''


def out(text: str = "") -> None:
    sys.stdout.write(text + "\n")


def run_dir(args: Any) -> str:
    path = os.path.join(os.path.abspath(args.dir), "runs", args.name)
    if not os.path.isdir(path):
        raise SystemExit("no run named %s under %s" % (args.name, args.dir))
    return path


def request(args: Any, body: Dict[str, Any]) -> str:
    folder = os.path.join(run_dir(args), "requests")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%d_%s.json" % (int(time.time() * 1000), body["kind"]))
    write_json(path, dict(body, by=args.by, reason=getattr(args, "reason", None)))
    return path


def parse_pairs(pairs: List[str]) -> Dict[str, Any]:
    changes = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit("expected KEY=VALUE, got %r" % pair)
        key, value = pair.split("=", 1)
        loaded = yaml.safe_load(value)
        if isinstance(loaded, bool) and value.strip().lower() not in ("true", "false") \
                and not isinstance(form.flatten(form.DEFAULTS).get(key.strip()), bool):
            loaded = value.strip()   # YAML reads off, on, yes and no as booleans; here they are words
        changes[key.strip()] = loaded
    return changes


def cmd_init(args: Any) -> int:
    folder = os.path.abspath(args.dir)
    os.makedirs(folder, exist_ok=True)
    made = []
    if not os.path.exists(os.path.join(folder, "brief.yaml")):
        form.save_brief(folder, json.loads(json.dumps(form.BLANK)))
        made.append("brief.yaml")
    if not os.path.exists(os.path.join(folder, "task.md")):
        with open(os.path.join(folder, "task.md"), "w", encoding="utf-8") as handle:
            handle.write(TASK)
        made.append("task.md")
    if args.source and not os.path.isdir(os.path.join(folder, "base")):
        shutil.copytree(os.path.abspath(args.source), os.path.join(folder, "base"),
                        ignore=shutil.ignore_patterns("__pycache__", ".git", "runs"))
        made.append("base/ (a snapshot of %s)" % args.source)
    if not os.path.isdir(os.path.join(folder, "adapter")):
        os.makedirs(os.path.join(folder, "adapter"))
        with open(os.path.join(folder, "adapter", "run.py"), "w", encoding="utf-8") as handle:
            handle.write(ADAPTER)
        made.append("adapter/run.py")
    out("made: %s" % (", ".join(made) or "nothing (all present)"))
    out("next: mark the blocks in base/ (EVOLVE-BLOCK-START name=... kind=structure|params role=...), write task.md and "
        "adapter/run.py, then `evoloop brief %s`" % args.dir)
    return 0


def cmd_example(args: Any) -> int:
    source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples", "symbolic_regression")
    if os.path.exists(args.dir):
        raise SystemExit("%s exists" % args.dir)
    shutil.copytree(source, args.dir, ignore=shutil.ignore_patterns("__pycache__"))
    out("copied the example to %s; confirm its brief with `evoloop brief %s --confirm NAME`" % (args.dir, args.dir))
    return 0


def cmd_brief(args: Any) -> int:
    folder = os.path.abspath(args.dir)
    brief = form.load_brief(folder)
    if args.answer:
        for key, value in parse_pairs(args.answer).items():
            fault = form.check_value(key, value)
            if fault:
                raise SystemExit(fault)
            form.put(brief, key, value)
            asked = brief.setdefault("status", {}).setdefault("asked", [])
            if key not in asked:
                asked.append(key)
        save = True
    else:
        save = False
    if save:
        form.save_brief(folder, brief)
    if args.confirm:
        try:
            form.confirm(folder, args.confirm)
        except form.BriefError as exc:
            raise SystemExit(str(exc))
        out("confirmed by %s" % args.confirm)
        return 0
    asks = form.questions(brief, everything=args.all)
    if args.questions:
        out(json.dumps(asks, indent=1, default=str))
        return 0
    faults = form.problems(brief)
    for fault in faults:
        out("problem: %s" % fault)
    for ask in asks:
        if ask["required"] or args.all:
            out("%s %s\n    %s%s" % ("ASK " if ask["required"] else "    ", ask["field"], ask["question"],
                                    "\n    choices: " + ", ".join(map(str, ask["choices"])) if ask["choices"] else ""))
    if not any(a["required"] for a in asks) and not faults:
        out("nothing left to ask. Read `evoloop plan %s`, then confirm with `evoloop brief %s --confirm NAME`." % (args.dir, args.dir)
            if not form.confirmed(brief) else "the brief is complete and confirmed by %s." % brief["status"]["confirmed_by"])
    return 0


def cmd_plan(args: Any) -> int:
    brief = form.load_brief(os.path.abspath(args.dir))
    from . import estimate
    folder = os.path.abspath(args.dir)
    for line in form.plan_lines(brief) + estimate.lines(brief, folder):
        out(line)
    asks = [a["field"] for a in form.questions(brief)]
    if asks:
        out("\nStill to ask: %s" % ", ".join(asks))
    return 0


def cmd_estimate(args: Any) -> int:
    """What the agents will cost: before a run from the brief; during one, from its own calls so far."""
    from . import estimate
    folder = os.path.abspath(args.dir)
    if not args.name:
        brief = form.load_brief(folder)
        lines = estimate.lines(brief, folder)
        for line in lines or ["give budget.evaluations in the brief first"]:
            out(line)
        return 0
    controller = offline(args)
    controller.refresh()
    controller.pool.shutdown(wait=False)
    view, settings = controller.view(), controller.settings
    seen = estimate.measured(controller.store)
    left = max(0.0, float(settings["budget"]["evaluations"] or 0) - view.charged())
    rest = estimate.estimate(dict(settings, budget=dict(settings["budget"], evaluations=left)), folder, seen)
    out("Spent so far: $%.2f over %d calls, %s of %s designs." % (controller.agents.dollars, controller.agents.count,
                                                                 format(view.charged(), "g"), settings["budget"]["evaluations"]))
    for role, row in sorted(seen.items()):
        out("  %-12s %d calls, $%.4f a call" % (role, row["calls"], row["dollars_per_call"]))
    out("For the %s designs still to come:" % format(left, "g"))
    for role, row in rest["roles"].items():
        out("  %-12s %s calls, %s  [%s]" % (role, estimate.span(row["calls"]), estimate.span(row["dollars"], "$", 2), row["from"]))
    if rest["dollars"]:
        total = [controller.agents.dollars + d for d in rest["dollars"]]
        cap = settings["budget"]["model_dollars"]
        out("The run as a whole: %s%s." % (estimate.span(total, "$", 2), " against a cap of $%.2f" % float(cap) if cap is not None else ""))
    return 0


def cmd_guide(args: Any) -> int:
    for limit, label, overlay in form.GUIDANCE:
        if args.evaluations and form.guidance_for(args.evaluations)[0] != label:
            continue
        out("%s evaluations:" % label)
        for key, value in form.flatten(overlay).items():
            out("  %s = %s" % (key, json.dumps(value)))
    out("\nRun types: %s" % ", ".join(form.RUN_TYPES))
    return 0


def menu_topics() -> List[str]:
    from . import menu
    return menu.TOPICS


def cmd_menu(args: Any) -> int:
    from . import menu
    if args.markdown:
        sys.stdout.write(menu.fields_markdown() if args.topic in ("fields", "defaults") else menu.menu_markdown())
    else:
        sys.stdout.write(menu.text(args.topic))
    return 0


def cmd_run(args: Any) -> int:
    from .controller import Controller
    controller = Controller(args.dir, args.name)
    try:
        reason = controller.run(max_seconds=args.max_seconds)
    except (form.BriefError, RuntimeError) as exc:
        raise SystemExit(str(exc))
    out("run %s: %s" % (args.name, reason))
    out("report: %s" % os.path.join(controller.run_dir, "report.md"))
    return 0


def offline(args: Any) -> Any:
    """A controller object for reading a run, with nothing started."""
    from .controller import Controller
    run_dir(args)
    return Controller(args.dir, args.name)


def cmd_status(args: Any) -> int:
    snap = read_json(os.path.join(run_dir(args), "status.json"))
    if snap is None:
        raise SystemExit("the run has written no status yet")
    out(json.dumps(snap, indent=1, default=str))
    return 0


def cmd_report(args: Any) -> int:
    from . import report
    controller = offline(args)
    controller.refresh()
    view = controller.view()
    info = controller.info
    out("\n".join(report.lines(controller, view, info.get("reason") if info.get("status") != "running" else None)))
    controller.pool.shutdown(wait=False)
    return 0


def cmd_study(args: Any) -> int:
    from . import study
    controller = offline(args)
    controller.refresh()
    view = controller.view()
    path = study.write(controller, view)
    out("wrote %s" % path)
    out(study.star(read_json(path)))
    controller.pool.shutdown(wait=False)
    return 0


def cmd_set(args: Any) -> int:
    changes = parse_pairs(args.pairs)
    for key, value in changes.items():
        fault = form.check_change(key, value)
        if fault:
            raise SystemExit(fault)
    request(args, {"kind": "set", "changes": changes})
    out("requested: %s. Applied to the next design; recorded in the ledger with your name." % ", ".join(
        "%s=%r" % kv for kv in changes.items()))
    periods = [k for k in changes if form.starts_period(k)]
    if periods:
        out("note: %s changes what a score means. A new period begins: the leaders are fitted again (or continued) and "
            "earlier scores stop deciding selection." % ", ".join(periods))
    return 0


def cmd_note(args: Any) -> int:
    request(args, {"kind": "note", "text": args.text, "roles": args.roles or [], "from_review": args.from_review})
    out("requested: a note for %s. The agents read it on every call from now on." % (", ".join(args.roles or []) or "every role"))
    return 0


def cmd_withdraw(args: Any) -> int:
    request(args, {"kind": "withdraw", "id": args.id})
    out("requested: withdraw %s" % args.id)
    return 0


def cmd_stop(args: Any) -> int:
    request(args, {"kind": "stop", "run": args.run})
    out("requested: stop %s" % (args.run or "the search once the running jobs finish"))
    return 0


def cmd_lineage(args: Any) -> int:
    if bool(args.retire) == bool(args.revive):
        raise SystemExit("give one of --retire ID or --revive ID")
    request(args, {"kind": "lineage", "lineage": args.retire or args.revive, "to": "retired" if args.retire else "revived"})
    out("requested: lineage %s %s" % (args.retire or args.revive, "retired" if args.retire else "brought back"))
    return 0


def cmd_answer(args: Any) -> int:
    request(args, {"kind": args.command, "id": args.id})
    out("requested: %s %s" % (args.command, args.id))
    return 0


def cmd_review(args: Any) -> int:
    request(args, {"kind": "review", "roles": args.roles or "all"})
    out("requested: a review of the agents now")
    return 0


def cmd_steer(args: Any) -> int:
    """The person's words, turned into ledger entries by the translator, shown back, applied only with --yes.
    The proposal that was shown is kept; `--yes` applies that one, and makes no second call that could differ."""
    from .agents import Agents
    path = os.path.join(run_dir(args), "steer_pending.json")
    if args.yes:
        shown = read_json(path)
        if not shown or shown.get("words") != args.words:
            raise SystemExit("nothing has been shown for these words yet: run the command without --yes first, read what "
                             "it proposes, then run it again with --yes")
        if shown["changes"]:
            request(args, {"kind": "set", "changes": shown["changes"]})
        for note in shown["notes"]:
            time.sleep(0.002)
            request(args, {"kind": "note", "text": note["text"], "roles": note.get("roles") or []})
        os.remove(path)
        out("requested, exactly as shown. The controller applies it on its next turn.")
        return 0
    controller = offline(args)
    controller.refresh()
    controller.pool.shutdown(wait=False)
    flat = form.flatten({k: v for k, v in controller.settings.items() if not k.startswith("_") and k != "notes"})
    agents = Agents(controller.settings, controller.folder, controller.store, tag="steer%d" % int(time.time()))
    try:
        reply = agents.call("translator", {
            "words": args.words, "settings": flat,
            "changeable": [k for k in flat if form.is_live(k) or form.starts_period(k)]}, about="steer")
    except Exception as exc:
        raise SystemExit("the translator could not be called: %s" % exc)
    changes, refused = {}, []
    for change in reply.get("changes") or []:
        if not isinstance(change, dict) or "key" not in change:
            continue
        fault = form.check_change(change["key"], change.get("value"))
        if fault:
            refused.append("%s (%s)" % (change["key"], fault))
        else:
            changes[change["key"]] = change.get("value")
            out("change: %s = %r   (was %r; from: %s)" % (change["key"], change.get("value"), flat.get(change["key"]),
                                                          change.get("from")))
    notes = [{"text": str(n["text"]), "roles": n.get("roles") or []} for n in reply.get("notes") or []
             if isinstance(n, dict) and n.get("text")]
    for note in notes:
        out("note to %s: %s" % (", ".join(note["roles"]) or "every role", note["text"]))
    for item in refused:
        out("cannot be done: %s" % item)
    for item in reply.get("not_covered") or []:
        out("not covered: %s" % item)
    write_json(path, {"words": args.words, "changes": changes, "notes": notes})
    out("\nnothing was changed. Run the same command with --yes to apply exactly the above.")
    return 0



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evoloop", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, fn: Any, help_text: str, named: bool = False, by: bool = False) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.set_defaults(fn=fn)
        if name not in ("guide", "menu"):
            p.add_argument("dir", help="the search folder")
        if named:
            p.add_argument("--name", required=True, help="the run")
        if by:
            p.add_argument("--by", required=True, help="the person asking; recorded in the ledger")
            p.add_argument("--reason", default=None)
        return p

    p = add("init", cmd_init, "make a search folder")
    p.add_argument("--source", help="the project's code, copied to base/")
    add("example", cmd_example, "copy the built-in example to a new folder")
    p = add("brief", cmd_brief, "what the brief still lacks; record answers; confirm")
    p.add_argument("--questions", action="store_true", help="the open questions as JSON, for an agent to ask the person")
    p.add_argument("--all", action="store_true", help="every field, not only the required ones")
    p.add_argument("--answer", action="append", metavar="FIELD=VALUE")
    p.add_argument("--confirm", metavar="NAME")
    add("plan", cmd_plan, "the settings the brief leads to, each with where it came from")
    p = add("estimate", cmd_estimate, "what the agents will cost, at each level of autonomy; with --name, from a run's own calls")
    p.add_argument("--name", default=None, help="a run: project its remaining cost from what its calls have cost")
    p = add("guide", cmd_guide, "guidance by size of budget")
    p.add_argument("evaluations", nargs="?", type=int)
    p = add("menu", cmd_menu, "every choice a run can make, the presets, and every field of the brief")
    p.add_argument("topic", nargs="?", default="all", choices=menu_topics())
    p.add_argument("--markdown", action="store_true", help="as a page of the documentation (topics: all, fields)")
    p = add("run", cmd_run, "start a run, or continue a stopped one", named=True)
    p.add_argument("--max-seconds", type=float, default=None)
    add("status", cmd_status, "the run's status", named=True)
    add("report", cmd_report, "the run's report", named=True)
    add("study", cmd_study, "write the run as a study file (CAMEO format 0.4)", named=True)
    p = add("set", cmd_set, "change settings of a run", named=True, by=True)
    p.add_argument("pairs", nargs="+", metavar="KEY=VALUE")
    p = add("note", cmd_note, "a standing note the agents read", named=True, by=True)
    p.add_argument("text")
    p.add_argument("--roles", nargs="*")
    p.add_argument("--from-review", default=None, metavar="ID", help="the review whose suggestion this note adopts, e.g. V3")
    p = add("withdraw", cmd_withdraw, "withdraw a note", named=True, by=True)
    p.add_argument("--id", required=True)
    p = add("steer", cmd_steer, "say what you want in your own words; shown back before anything changes", named=True, by=True)
    p.add_argument("words")
    p.add_argument("--yes", action="store_true")
    p = add("stop", cmd_stop, "stop the search once running jobs finish, or stop one run", named=True, by=True)
    p.add_argument("--run")
    p = add("lineage", cmd_lineage, "set a lineage aside, or bring one back (lineage strategy)", named=True, by=True)
    p.add_argument("--retire", metavar="ID")
    p.add_argument("--revive", metavar="ID")
    for name, words in (("approve", "say yes to a decision of the strategist that waits for you"),
                        ("decline", "say no to a decision of the strategist that waits for you")):
        p = add(name, cmd_answer, words, named=True, by=True)
        p.add_argument("--id", required=True, help="the decision, e.g. S14")
    p = add("review", cmd_review, "have the assessor review the agents now", named=True, by=True)
    p.add_argument("--roles", nargs="*")
    return parser


def main(argv: Any = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.fn(args) or 0)
    except form.BriefError as exc:
        raise SystemExit(str(exc))
