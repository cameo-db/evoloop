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
import shlex
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
    from . import interview
    if args.importing:
        answers = read_json(args.importing)
        if not isinstance(answers, dict):
            with open(args.importing, encoding="utf-8") as handle:
                answers = yaml.safe_load(handle)
        if not isinstance(answers, dict):
            raise SystemExit("%s does not hold a mapping of answers" % args.importing)
        done, refused = interview.merge(brief, answers)
        form.save_brief(folder, brief)
        out("recorded: %s" % (", ".join(done) or "nothing"))
        for item in refused:
            out("not accepted: %s" % item)
    if args.suggest:
        for field, value in parse_pairs(args.suggest).items():
            fault = interview.suggest(brief, field, value, args.because or "the agent judged it likely", by="an agent")
            if fault:
                raise SystemExit(fault)
        form.save_brief(folder, brief)
    if args.infer or args.next:
        made = interview.infer(folder, brief)
        form.save_brief(folder, brief)
        if args.infer:
            out("suggested: %s" % (", ".join("%s=%s" % kv for kv in made.items()) or "nothing new"))
    if args.keep:
        for field in args.keep:
            fault = interview.record(brief, field, interview.KEEP)
            if fault:
                raise SystemExit(fault)
        form.save_brief(folder, brief)
    if args.next:
        now = interview.state(brief)
        q = now["next"]
        out(json.dumps({"done": now["done"], "total": now["total"], "sections": now["sections"],
                        "question": None if q is None else {k: q[k] for k in (
                            "field", "number", "of", "section", "title", "question", "why", "kind", "choices", "default", "suggested",
                            "default_from", "required") if k in q},
                        "how_to_answer": "evoloop brief DIR --answer FIELD=VALUE, or --keep FIELD to leave the default; then --next again"
                        if q else "all done: evoloop plan DIR, then evoloop brief DIR --confirm NAME"}, indent=1, default=str))
        return 0
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


def cmd_setup(args: Any) -> int:
    """The questions one at a time in the terminal."""
    from . import interview
    folder = os.path.abspath(args.dir)
    try:
        brief = form.load_brief(folder)
        interview.infer(folder, brief)
        form.save_brief(folder, brief)
        interview.run(folder, input, out)
    except (EOFError, KeyboardInterrupt):
        out("\nStopped. What you answered is saved; run `evoloop setup` again to go on.")
    return 0


def cmd_form(args: Any) -> int:
    """The questions as a self-contained HTML form."""
    from . import formpage, interview
    folder = os.path.abspath(args.dir)
    path = args.out or os.path.join(folder, "setup_form.html")
    seeded = form.load_brief(folder)
    interview.infer(folder, seeded)
    form.save_brief(folder, seeded)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(formpage.fragment(form.load_brief(folder), download=False) if args.fragment
                     else formpage.document(form.load_brief(folder)))
    out("wrote %s" % path)
    out("Open it in a browser (copy it to your own machine if this is a server), answer, save the answers file it gives "
        "you as answers.json, then: evoloop brief %s --import answers.json" % args.dir)
    return 0


def cmd_plan(args: Any) -> int:
    brief = form.load_brief(os.path.abspath(args.dir))
    from . import estimate
    folder = os.path.abspath(args.dir)
    for line in form.plan_lines(brief, folder=folder) + estimate.lines(brief, folder):
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


def cmd_skills(args: Any) -> int:
    """The skills: what kinds of optimisation there are, one in full, or one written out as a folder to edit."""
    from . import skill as skills
    if not args.skill:
        out("Skills (set one with run.skill; it is independent of the run type):")
        for name, summary in skills.summaries().items():
            out("")
            out("  %s" % name)
            out("      %s" % summary)
        out("")
        out("evoloop skills NAME shows one in full; evoloop skills NAME --copy DIR writes it out to edit.")
        return 0
    found, fault = skills.load(args.skill, args.dir)
    if found is None:
        raise SystemExit(fault or "name a skill")
    if args.copy:
        if os.path.exists(args.copy):
            raise SystemExit("%s exists already" % args.copy)
        shutil.copytree(found["path"], args.copy)
        out("written to %s; edit skill.yaml there and set run.skill to that path" % args.copy)
        return 0
    with open(os.path.join(found["path"], "skill.yaml"), "r", encoding="utf-8") as handle:
        sys.stdout.write(handle.read())
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
    if args.json:
        out(json.dumps(snap, indent=1, default=str))
        return 0
    budget, agents, runs = snap["budget"], snap["agents"], snap["runs"]
    out("Run %s: %s  (as of %s)" % (snap["run"], snap.get("ended") or "going", snap["updated"]))
    out("  Models: %s of %s spent (%d%%). Training now: %d. Waiting for a slot: %d. Being written: %d." % (
        budget["spent"], budget["evaluations"], round(100 * budget["fraction"]), runs.get("running", 0),
        runs.get("queued", 0) + runs.get("designed", 0), snap["designing"]))
    best = snap.get("best")
    out("  Best: %s" % ("%s (%s), score %s" % (best["candidate"], best["family"], format(best["score"], ".6g")) if best else "none yet"))
    out("  Ended without a score: %d failed, %d invalid or rejected, %d refused before running." % (
        runs.get("failed", 0), runs.get("invalid", 0), runs.get("not_run", 0)))
    spend = snap.get("spend") or {}
    line = "  Agents: $%.2f over %d calls" % (agents["dollars"], agents["calls"])
    if agents.get("cap_dollars") is not None:
        line += " of a cap of $%.2f" % float(agents["cap_dollars"])
    if spend.get("projected") is not None:
        line += "; heading for about $%.2f" % spend["projected"]
    out(line + ".")
    kind = snap["strategy"]
    out("  Search: %s, %s strategy, %s harness. Mix now: %s." % (kind["run_type"], kind["mechanism"], kind["harness"], ", ".join(
        "%s %d%%" % (m, round(100 * s)) for m, s in snap["shares_now"].items() if s > 0)))
    if agents.get("blocked"):
        out("  HELD UP: %s" % agents["blocked"])
    if snap.get("decisions_waiting"):
        out("  Waiting for your yes or no: %s (see `evoloop report`)." % ", ".join(snap["decisions_waiting"]))
    for q in snap.get("open_questions") or []:
        out("  Question for you: %s (default: %s)" % (q.get("question"), q.get("default")))
    for note in snap.get("notes_in_force") or []:
        out("  Note in force (%s): %s" % (note["id"], note["text"]))
    return 0


def cmd_show(args: Any) -> int:
    """One run: where it came from, what its design changed against its parent, how it ended."""
    controller = offline(args)
    controller.refresh()
    controller.pool.shutdown(wait=False)
    view = controller.view()
    run = view.runs.get(args.run) or (view.run_of(args.run) if args.run in view.cands else None)
    if run is None:
        raise SystemExit("no run or design %s in %s" % (args.run, args.name))
    h, perf = run["history"], run["performance"]
    out("%s  design %s  model %s  recipe %s  lineage %s" % (run["id"], run.get("candidate"), run.get("model"), run.get("recipe"), h.get("lineage")))
    out("  Came from: %s%s%s" % (h.get("move"), " of %s" % h["parent"] if h.get("parent") else "",
                               " with %s" % h["second_parent"]["run"] if h.get("second_parent") else ""))
    out("  Why this slot: %s" % h.get("why_this_slot"))
    for key in ("hypothesis", "predicted_effect", "change_summary"):
        if h.get(key):
            out("  %s: %s" % (key.replace("_", " ").capitalize(), h[key]))
    if h.get("forecast"):
        out("  Forecast: %+.2f noise floors, %d%% likely to beat its reference" % (h["forecast"]["gain"], round(100 * h["forecast"]["probability_better"])))
    out("  Ended: %s%s" % (perf.get("status"), ", score %s" % format(perf["score"], ".6g") if isinstance(perf.get("score"), (int, float)) else ""))
    if perf.get("reason"):
        out("  Reason: %s" % perf["reason"])
    for part in ("valid", "test"):
        if perf.get(part):
            out("  %s: %s" % (part.capitalize(), ", ".join("%s %s" % (k, format(v, ".5g") if isinstance(v, float) else v) for k, v in perf[part].items())))
    if run.get("variables"):
        out("  Job variables: %s" % run["variables"])
    if run.get("candidate"):
        mine = controller.designer.blocks(run["candidate"])
        parent = view.runs.get(h.get("parent") or "")
        theirs = controller.designer.blocks(parent["candidate"]) if parent and parent.get("candidate") else space.full(controller.designer.table, {})
        text = space.diff(theirs, mine, limit=20000)
        out("\n  What it changed against %s:" % (parent["id"] if parent else "the base code"))
        out(text if text else "  (nothing)")
    if perf.get("log"):
        out("\n  End of its log:\n%s" % perf["log"])
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


def cmd_chat(args: Any) -> int:
    """Talk with the agent that runs the search. It answers from the run's records, and what it decides in
    answer goes to the controller as requests, checked like any other decision and recorded."""
    from . import strategist
    from .agents import AgentError, Agents
    controller = offline(args)
    controller.refresh()
    controller.pool.shutdown(wait=False)
    if controller.settings["harness"]["conductor"] != "agent":
        raise SystemExit("this search is run by code, so there is no agent to talk to. To hand it to one: "
                         "evoloop set %s --name %s harness.conductor=agent --by NAME" % (args.dir, args.name))
    agents = Agents(controller.settings, controller.folder, controller.store, tag="chat%d" % int(time.time()))

    def say(text: str) -> None:
        controller.refresh()
        store, view, settings = controller.store, controller.view(), controller.settings
        ledger = store.merged_list("ledger")
        talks = store.read("chat")
        last = talks[-1]["t"] if talks else 0
        mine = [e for e in ledger if e.get("kind") == "decision" and e.get("action")]
        waiting = [{"id": e["id"], "action": e["action"], "args": e.get("args"), "why_it_waits": e.get("why")}
                   for e in mine if e.get("status") == "proposed"]
        context = {"objective": settings["objective"], "message": text,
                   "conversation": [{"they_said": c.get("text"), "you_said": c.get("reply")} for c in talks][-8:],
                   "facts": strategist.facts(store, agents, view, settings, "the person is talking to you"),
                   "menu": strategist.menu(settings), "waiting_for_them": waiting,
                   "since_you_last_spoke": [{"id": e["id"], "action": e["action"], "args": e.get("args"), "status": e.get("status"),
                                             "reason": e.get("reason")} for e in mine if e.get("t", 0) > last][-10:],
                   "the_run_is": (read_json(os.path.join(controller.run_dir, "run.json"), {}) or {}).get("status")}
        try:
            answer = agents.call("conductor", context, about="chat")
        except AgentError as exc:
            raise SystemExit("the conductor could not be reached: %s" % exc)
        number = "T%d" % (len(talks) + 1)
        decisions = [dict(d, chat=number) for d in answer.get("decisions") or [] if isinstance(d, dict)]
        ids = {w["id"] for w in waiting}
        yes = [i for i in answer.get("approve") or [] if i in ids]
        no = [i for i in answer.get("decline") or [] if i in ids and i not in yes]
        store.append("chat", {"id": number, "by": args.by, "text": text, "reply": answer.get("reply"), "decisions": decisions,
                              "approve": yes, "decline": no, "call": answer.get("_call")})
        out(str(answer.get("reply") or ""))
        if decisions:
            request(args, {"kind": "decisions", "decisions": decisions})
        for kind, which in (("approve", yes), ("decline", no)):
            for one in which:
                time.sleep(0.002)
                request(args, {"kind": kind, "id": one})
        for d in decisions:
            out("  asked for: %s %s" % (d.get("action"), json.dumps(d.get("args"), default=str)))
        for one in yes:
            out("  your yes to %s is recorded" % one)
        for one in no:
            out("  your no to %s is recorded" % one)
        if decisions or yes or no:
            out("  (checked and applied at the controller's next turn; `evoloop report` shows what became of each)")

    if args.message:
        say(args.message)
        return 0
    out("Talking with the conductor of %s. An empty line ends the talk." % args.name)
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        say(text)
    return 0


def cmd_rehash(args: Any) -> int:
    request(args, {"kind": "rehash", "moves_scores": bool(args.moves_scores)})
    out("requested: the change to base/ or adapter/ is recorded as meant%s. The run goes on at its next turn, or when it is "
        "started again." % ("; a new period begins" if args.moves_scores else ""))
    return 0


def cmd_force(args: Any) -> int:
    request(args, {"kind": "force", "mode": args.mode, "count": args.count, "instruction": args.instruction,
                   "move": args.kind})
    out("requested: the next %d slot(s) go to %s%s" % (args.count, args.mode, " (%s)" % args.kind if args.kind else ""))
    return 0


def cmd_import(args: Any) -> int:
    source = os.path.abspath(args.source)
    if not os.path.isfile(os.path.join(source, "runs.jsonl")):
        raise SystemExit("%s is not a run folder (give the path that holds runs.jsonl, e.g. DIR/runs/NAME)" % source)
    request(args, {"kind": "import", "source": source, "candidates": args.designs or None, "top": args.top})
    out("requested: %s of %s, to be fitted in this run" % (", ".join(args.designs) if args.designs else "the top %d" % args.top, source))
    return 0


def cmd_reference(args: Any) -> int:
    """A row on the leaderboard for a model that is not part of the search: a published baseline, an earlier run's best."""
    rows = []
    if args.source:
        source = os.path.abspath(args.source)
        theirs = Store(source)
        brief = (read_json(os.path.join(source, "run.json"), {}) or {}).get("brief") or {}
        old = View.load(theirs, form.resolve(brief, theirs.merged_list("ledger"))[0])
        for cand in old.scored()[:args.top]:
            perf = old.run_of(cand["id"])["performance"]
            rows.append({"label": "%s %s" % (os.path.basename(source), cand["id"]), "score": old.display(cand["value"]),
                         "valid": perf.get("valid"), "test": perf.get("test"), "parameters": perf.get("parameters"),
                         "note": cand["family"], "source": source})
    else:
        if not args.label or args.score is None:
            raise SystemExit("give --label and --score, or --from-run PATH")
        figures = parse_pairs(args.metric or [])
        rows.append({"label": args.label, "score": args.score, "note": args.note, "parameters": figures.pop("parameters", None),
                     "valid": {k[6:]: v for k, v in figures.items() if k.startswith("valid.")},
                     "test": {k[5:]: v for k, v in figures.items() if k.startswith("test.")}})
    for row in rows:
        time.sleep(0.002)
        request(args, dict(row, kind="reference"))
    out("requested: %d reference row(s): %s" % (len(rows), ", ".join(r["label"] for r in rows)))
    return 0


def cmd_leaderboard(args: Any) -> int:
    from . import report
    controller = offline(args)
    controller.refresh()
    controller.pool.shutdown(wait=False)
    settings = controller.settings
    rows = report.leaderboard(controller.view(), args.top or int(settings["report"]["top"]),
                              args.columns or settings["report"]["columns"], controller.store.read("references"))
    out("\n".join(report.table(rows)))
    return 0


CONTROLLER = '''#!/bin/bash
#SBATCH --job-name=evoloop_{name}
#SBATCH --output={log}
#SBATCH --open-mode=append
#SBATCH --requeue
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time={time}
#SBATCH --signal=B:USR1@180
{extra}
# The controller of the search {name}. It is light: it follows the training jobs, which are jobs of their own and
# go on whatever happens to this one. Shortly before its time limit Slurm signals it; it then stops cleanly and
# puts itself back in the queue, and when it starts again it finds its jobs by their ids. It requeues itself
# only then, never after ending by itself (budget spent, paused, stalled) and never after a crash.
{setup}
requeue() {{
  kill -TERM "$child" 2>/dev/null; wait "$child"
  echo "[controller] time limit near: requeueing"; scontrol requeue "$SLURM_JOB_ID"
}}
trap requeue USR1
{python} -m evoloop run {dir} --name {name} &
child=$!
wait "$child"
'''


def cmd_controller(args: Any) -> int:
    """A Slurm job script that runs the search and requeues itself at its time limit."""
    folder = os.path.abspath(args.dir)
    path = args.out or os.path.join(folder, "run_controller_%s.sbatch" % args.name)
    extra = ["#SBATCH --partition=%s" % args.partition] if args.partition else []
    extra += ["#SBATCH --qos=%s" % args.qos] if args.qos else []
    text = CONTROLLER.format(name=args.name, log=os.path.join(folder, "controller_%s.log" % args.name), time=args.time,
                             extra="\n".join(extra), setup="\n".join(args.setup or []), python=args.python or sys.executable,
                             dir=shlex.quote(folder))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    out("wrote %s" % path)
    out("Start the search with: sbatch %s" % path)
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
        if name not in ("guide", "menu", "skills"):
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
    p.add_argument("--next", action="store_true", help="the next question as JSON, with its choices and where it stands in the list")
    p.add_argument("--keep", action="append", metavar="FIELD", help="leave a question as shown: accept its suggestion, or its default")
    p.add_argument("--suggest", action="append", metavar="FIELD=VALUE", help="propose an answer for the person to accept or change")
    p.add_argument("--because", metavar="WHY", help="the reason for the suggestions given with --suggest")
    p.add_argument("--infer", action="store_true", help="suggest answers from this machine, the folder and the answers so far")
    p.add_argument("--import", dest="importing", metavar="FILE", help="read answers from a file (the HTML form's, or any mapping of fields)")
    add("setup", cmd_setup, "answer the questions one at a time in the terminal")
    p = add("form", cmd_form, "write the questions as a self-contained HTML form")
    p.add_argument("--out", metavar="FILE")
    p.add_argument("--fragment", action="store_true", help=argparse.SUPPRESS)
    add("plan", cmd_plan, "the settings the brief leads to, each with where it came from")
    p = add("estimate", cmd_estimate, "what the agents will cost, at each level of autonomy; with --name, from a run's own calls")
    p.add_argument("--name", default=None, help="a run: project its remaining cost from what its calls have cost")
    p = add("skills", cmd_skills, "the kinds of optimisation a search can be set up for")
    p.add_argument("skill", nargs="?", help="a built-in skill or the path of a skill folder; leave out for the list")
    p.add_argument("--copy", metavar="DIR", help="write the skill out as a folder to edit")
    p.add_argument("--dir", default=None, help="the search folder, to find a skill of your own by a relative path")
    p = add("guide", cmd_guide, "guidance by size of budget")
    p.add_argument("evaluations", nargs="?", type=int)
    p = add("menu", cmd_menu, "every choice a run can make, the presets, and every field of the brief")
    p.add_argument("topic", nargs="?", default="all", choices=menu_topics())
    p.add_argument("--markdown", action="store_true", help="as a page of the documentation (topics: all, fields)")
    p = add("run", cmd_run, "start a run, or continue a stopped one", named=True)
    p.add_argument("--max-seconds", type=float, default=None)
    p = add("status", cmd_status, "where the run stands, in a few lines", named=True)
    p.add_argument("--json", action="store_true", help="everything, as JSON")
    p = add("leaderboard", cmd_leaderboard, "the best designs, the baseline and the reference rows", named=True)
    p.add_argument("--top", type=int)
    p.add_argument("--columns", nargs="*", metavar="COLUMN", help="valid.<metric>, test.<metric>, speed, best_epoch, epochs_run")
    p = add("show", cmd_show, "one run in full: where it came from, what changed, how it ended", named=True)
    p.add_argument("run", metavar="RUN", help="a run id (R12) or a design id (C9)")
    p = add("controller", cmd_controller, "write a Slurm job script that runs the search and requeues itself", named=True)
    p.add_argument("--partition")
    p.add_argument("--qos")
    p.add_argument("--time", default="1-00:00:00")
    p.add_argument("--python")
    p.add_argument("--setup", action="append", metavar="LINE", help="a shell line to run first, e.g. activating an environment")
    p.add_argument("--out", metavar="FILE")
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
    p = add("chat", cmd_chat, "talk with the agent that runs the search (harness.conductor: agent)", named=True, by=True)
    p.add_argument("message", nargs="?", help="one message; leave it out to talk back and forth")
    p = add("rehash", cmd_rehash, "record that a change to base/ or adapter/ during a run is meant", named=True, by=True)
    p.add_argument("--moves-scores", action="store_true", help="scores before and after are not comparable: begin a new period")
    p = add("force", cmd_force, "order the next slots yourself: a mode, a kind, an instruction", named=True, by=True)
    p.add_argument("--mode", required=True, choices=list(form.MODES))
    p.add_argument("--kind", choices=list(form.CROSS_KINDS + form.LOCAL_MOVES))
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--instruction", help="what the writers of those slots must do")
    p = add("import", cmd_import, "bring designs from an earlier run into this one, to be fitted here", named=True, by=True)
    p.add_argument("--from-run", dest="source", required=True, metavar="PATH", help="the earlier run's folder (DIR/runs/NAME)")
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--designs", nargs="*", metavar="ID", help="these designs (C12 ...) in place of the top ones")
    p = add("reference", cmd_reference, "add a model to compare with to the leaderboard", named=True, by=True)
    p.add_argument("--label")
    p.add_argument("--score", type=float)
    p.add_argument("--metric", action="append", metavar="NAME=VALUE", help="valid.<metric>, test.<metric> or parameters")
    p.add_argument("--note")
    p.add_argument("--from-run", dest="source", metavar="PATH", help="take the top designs of an earlier run as reference rows")
    p.add_argument("--top", type=int, default=3)
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
