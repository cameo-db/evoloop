"""Does the evaluator do what a search needs? One training run of the code as it stands, interrupted on purpose.

    1. It is started, and its first progress report is awaited.
    2. It is killed, as a preemption or a time limit kills a job, and started again. Does it go on from where
       it was, or begin again?
    3. It is asked to stop. How long until it ends, and does it still write its score?

No agent is called and nothing is charged. The run goes where the search's jobs go: this machine, or Slurm.
Most of what goes wrong in a long search on a shared cluster is one of these three, and each costs GPU days
when it is found during the search instead of before it."""
from __future__ import annotations

import os
import shutil
import time
from typing import Any, Callable, Dict, List, Optional

from . import form, jobs, space
from .store import read_json


def steps(out: str) -> List[float]:
    return [float(r["step"]) for r in jobs.read_progress(out, every=True) if isinstance(r.get("step"), (int, float))]


def result_of(out: str) -> Optional[Dict[str, Any]]:
    result = read_json(os.path.join(out, "result.json"))
    return result if isinstance(result, dict) else None


def scored(result: Optional[Dict[str, Any]]) -> bool:
    return bool(result) and bool(result.get("valid")) and isinstance(result.get("score"), (int, float))


def run(folder: str, wait: float = 1800.0, say: Callable[[str], None] = print, poll: Optional[float] = None) -> Dict[str, Any]:
    """Run the check and say what was found. Returns the findings: `ok` (the evaluator can be used), and for
    each of `reports`, `resumes` and `stops` True, False, or None when it could not be told."""
    folder = os.path.abspath(folder)
    settings = form.resolve(form.load_brief(folder), folder=folder)[0]
    if not settings["evaluation"]["allowance"]:
        raise form.BriefError("the length of a training run is not set yet: answer evaluation.allowance first")
    if jobs.in_block(settings["compute"]) and not os.environ.get("SLURM_JOB_ID"):
        raise form.BriefError("this search holds one block of GPUs: run the check inside a job that has a GPU")
    backend = jobs.make(settings)
    poll = poll if poll is not None else (15.0 if backend.name == "slurm" else 1.0)
    root = os.path.join(folder, "check")
    shutil.rmtree(root, ignore_errors=True)
    out, kept, work = os.path.join(root, "out"), os.path.join(root, "checkpoints"), os.path.join(root, "work")
    for path in (out, kept):
        os.makedirs(path)
    base = os.path.join(folder, "base")
    space.materialize(base, os.path.join(folder, "adapter"), space.full(space.table(base), {}), work)
    job: Dict[str, Any] = {"id": "check", "seed": int(settings["evaluation"]["seed"] or 0), "restarts": 0}
    found: Dict[str, Any] = {"ok": False, "reports": None, "resumes": None, "stops": None, "advice": []}

    def start() -> None:
        job["job"] = backend.submit(job, work, jobs.environment(job, out, kept, settings), settings)

    last: Dict[str, Any] = {}

    def going() -> bool:
        last.clear()
        last.update(backend.state(job))
        return last["state"] in ("waiting", "running")

    def until(met: Callable[[], bool], seconds: float) -> bool:
        """Wait for `met`, for the job to end, or for the time to pass. True when `met` came about."""
        end = time.time() + seconds
        while time.time() < end:
            if met():
                return True
            if not going():
                return met()
            time.sleep(poll)
        return met()

    def close(line: str) -> Dict[str, Any]:
        if going():
            backend.cancel(job)
        say(line)
        for advice in found["advice"]:
            say("  - " + advice)
        say("Its files are in %s." % root)
        return found

    say("Evaluator check for %s: one training run of the code as it stands, interrupted on purpose. Nothing is charged." % folder)
    began = time.time()
    start()
    # A report with a step above zero: something has been trained, so there is something to lose and to resume.
    found["reports"] = until(lambda: any(s > 0 for s in steps(out)), wait)
    if not found["reports"]:
        if going():
            say("  started               no progress report in %d s" % wait)
            found["advice"].append("Report progress while training (`job.report(step, score)`), at least every few minutes: "
                                   "early stopping, the status and a clean stop all depend on it. Or give the check longer "
                                   "with --wait.")
            return close("The check could not go on: the evaluator did not report progress in time.")
        result = result_of(out)
        if scored(result):
            found["ok"] = True
            say("  started               finished in %d s with a score of %s, before it reported any progress"
                % (time.time() - began, result["score"]))
            found["advice"].append("A run this short needs no more. For runs of minutes or longer, report progress so that "
                                   "weak designs can be stopped part way and an interrupted run can go on.")
            return close("The evaluator runs. Stopping and resuming were not tested: it ended before either could be.")
        say("  started               ended without a score%s" % ("" if result is None else ": result.json says %s" % str(result)[:200]))
        say("  the end of its log:\n%s" % jobs.tail(out))
        found["advice"].append("Run it by hand as in docs/evaluator.md (Testing by hand) and make it write result.json with "
                               "`valid` and `score`.")
        return close("The evaluator does not work yet.")
    first = time.time() - began
    say("  started               reported step %g after %d s" % (max(steps(out)), first))

    # 2. killed and started again
    backend.cancel(job)
    until(lambda: not going(), 180)
    reached, before = max(steps(out)), len(steps(out))
    job["restarts"] = 1
    start()
    until(lambda: len(steps(out)) > before, wait)
    new = steps(out)[before:]
    positive = [s for s in new if s > 0]
    if not new:
        say("  killed and restarted  it reported nothing after the restart%s" % ("" if going() else ", and ended"))
        if not going():
            say("  the end of its log:\n%s" % jobs.tail(out))
            found["advice"].append("It ran the first time and not the second: look at how it handles the files a killed "
                                   "run leaves in EVO_CHECKPOINT_DIR.")
            return close("The evaluator does not survive being started again.")
    elif positive and min(positive) > reached:
        found["resumes"] = True
        say("  killed and restarted  went on at step %g (it had reached step %g): it resumes" % (min(positive), reached))
    else:
        found["resumes"] = False
        say("  killed and restarted  began again at step %g (it had reached step %g): it does not resume" % (new[0], reached))
        found["advice"].append("A job that reaches its time limit or is preempted will lose its work. Save the state after "
                               "every step and load it at the start (the template from `evoloop init` does, with "
                               "adapter/evojob.py), or set compute.time_limit longer than a whole training run.")

    # 3. asked to stop
    if not going():
        result = result_of(out)
        found["ok"] = scored(result)
        return close("The evaluator %s. Stopping was not tested: the run ended first." % (
            "runs" if found["ok"] else "ended without a score after the restart"))
    asked = time.time()
    jobs.tell(out, "stop")
    until(lambda: not going(), wait)
    took = time.time() - asked
    result = result_of(out)
    if last.get("state") in ("waiting", "running"):      # as last seen: a job that has ended is not asked about again
        found["stops"] = False
        say("  asked to stop         still running after %d s" % took)
        found["advice"].append("Read control.json at every progress report and finish when it says stop "
                               "(`job.should_stop()`), still writing the result. Otherwise a design that is stopped early "
                               "is killed and loses its score.")
    elif last.get("state") == "machine" and not scored(result):
        # Its job ended for the machine's reasons (its time ran out, or the run paused to be continued) before the
        # stop was seen. In a search it would be started again; here that says nothing about stopping.
        say("  asked to stop         its job ended first (%s), so stopping was not tested" % last.get("why"))
        found["advice"].append("Check again with a time limit that leaves room for a few progress reports.")
    elif scored(result):
        found["stops"] = True
        say("  asked to stop         ended %d s later with a score of %s" % (took, result["score"]))
    else:
        found["stops"] = False
        say("  asked to stop         ended %d s later without a score" % took)
        found["advice"].append("When asked to stop, write result.json with the best score so far. Otherwise a design that is "
                               "stopped early loses the score it had reached.")
    found["ok"] = True      # it trains, reports and survives a restart; what is missing is said above
    whole = found["resumes"] and found["stops"]
    return close("The evaluator does what a search needs." if whole else "The evaluator runs, with what is said below.")
