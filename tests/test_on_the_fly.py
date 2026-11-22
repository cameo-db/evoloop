"""The adjustments people make while a search is going: job variables, a fix to the adapter, limits, designs
from an earlier run, slots ordered by hand, a controller job, a leaderboard with reference rows."""
import json
import os

import pytest

from evoloop import form, jobs, report
from evoloop.cli import main
from evoloop.controller import Controller
from evoloop.store import SCORED

from helpers import ask, run, search
from test_loop import Recorder, drive, scored


def finish(folder, controller):
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    for r in controller.view().in_flight():
        ask(folder, "t", {"kind": "stop", "run": r["id"], "by": "Ada"})
    return controller.run(max_seconds=120)


def test_job_variables_reach_the_jobs_and_a_change_begins_a_new_period(tmp_path):
    folder = search(tmp_path, budget__evaluations=16, evaluation__allowance=150, audit__reviews="none", strategist__mode="off",
                    evaluation__variables={"PATIENCE": 3, "MIN_GAIN": 0.005}, evaluation__leaders_refit=2)
    controller = Controller(folder, "t", poll=0.2)
    env = jobs.environment({"id": "R1", "seed": 0}, "/out", "/ckpt", controller.settings)
    assert env["PATIENCE"] == "3" and env["MIN_GAIN"] == "0.005" and env["EVO_ALLOWANCE"] == "150"
    drive(controller, lambda v: len(scored(v)) >= 5)
    assert main(["set", folder, "--name", "t", 'evaluation.variables={"PATIENCE": 10, "MIN_GAIN": 0.001}', "--by", "Ada"]) == 0
    drive(controller, lambda v: v.period == 1 and len(v.scored()) >= 2)
    view = controller.view()
    old = [r for r in view.runs.values() if r.get("period", 0) == 0 and r.get("variables")]
    new = [r for r in view.runs.values() if r.get("period") == 1 and r.get("variables")]
    assert old and all(r["variables"]["PATIENCE"] == 3 for r in old)
    assert new and all(r["variables"]["PATIENCE"] == 10 for r in new)                 # each run records what it ran with
    assert [r for r in view.runs.values() if r["purpose"] == "reference"]              # the leaders were fitted again
    assert form.check_change("evaluation.variables", {"EVO_SEED": 1}) is not None      # the loop's own names are not yours
    assert form.check_change("evaluation.variables", {"bad name": 1}) is not None
    finish(folder, controller)


def test_a_fix_to_the_adapter_during_a_run(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, evaluation__allowance=150, audit__reviews="none", strategist__mode="off")
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 4)
    with open(os.path.join(folder, "adapter", "check.py"), "a") as handle:
        handle.write("\n# a fix made while the run was going\n")
    controller.code_checked = 0                       # the code is looked at again (every minute in a real run)
    before = len(controller.view().runs)
    reason = drive(controller, lambda v: False)      # until the run comes to rest by itself
    assert reason.startswith("paused: the frozen code") and "evoloop rehash" in reason        # nothing new starts; it says what to do
    assert len(controller.view().runs) <= before + controller.capacity()
    # Recorded as meant: the run goes on, here from a stop.
    assert main(["rehash", folder, "--name", "t", "--by", "Ada", "--reason", "quick check was too strict"]) == 0
    again = Controller(folder, "t", poll=0.2)
    assert again.run(max_seconds=200).startswith("the budget")
    entry = [e for e in again.store.merged_list("ledger") if e["kind"] == "rehash"][0]
    assert entry["status"] == "applied" and entry["old"] != entry["new"] and entry["by"] == "Ada" and not entry["new_period"]
    assert again.settings["_period"] == 0
    # A second rehash with nothing changed is refused; one that moves scores begins a new period.
    ask(folder, "t", {"kind": "rehash", "by": "Ada"})
    with open(os.path.join(folder, "adapter", "check.py"), "a") as handle:
        handle.write("# another\n")
    third = Controller(folder, "t", poll=0.2)
    third.read_inbox()
    assert [e["status"] for e in third.store.merged_list("ledger") if e["kind"] == "rehash"] == ["applied", "applied"]
    with open(os.path.join(folder, "adapter", "check.py"), "a") as handle:
        handle.write("# and one that changes scores\n")
    ask(folder, "t", {"kind": "rehash", "by": "Ada", "moves_scores": True})
    ask(folder, "t", {"kind": "rehash", "by": "Ada"})
    third.read_inbox()
    third.refresh()
    statuses = [(e["status"], bool(e.get("new_period"))) for e in third.store.merged_list("ledger") if e["kind"] == "rehash"]
    assert statuses[-2:] == [("applied", True), ("refused", False)] and third.settings["_period"] == 1
    third.pool.shutdown(wait=False)


def test_limits_are_enforced_and_a_rejected_design_is_not_a_failure(tmp_path):
    folder = search(tmp_path, budget__evaluations=14, evaluation__allowance=150, audit__reviews="none", strategist__mode="off",
                    limits={"n_constants": {"max": 4}}, variation__proposals_per_slot=1, population__trial_runs=1)
    recorder = Recorder(folder)
    controller = Controller(folder, "t", poll=0.2, agent_backend=recorder)
    reason = controller.run(max_seconds=240)
    assert reason.startswith("the budget"), reason                                    # rejections do not stall the run
    view = controller.view()
    rejected = [r for r in view.runs.values() if r["performance"].get("rejected")]
    assert len(rejected) >= 2 and all(r["performance"]["status"] == "invalid" for r in rejected)
    assert all("n_constants is" in r["performance"]["reason"] and "above the limit of 4" in r["performance"]["reason"] for r in rejected)
    assert all(r["performance"]["valid"]["n_constants"] <= 4 for r in view.runs.values() if r["performance"].get("status") in SCORED)
    # Rejected designs are not charged: the spend is what the scored runs cost (a run stopped at the screen costs half).
    assert controller.spent(view) == sum(float(r.get("charge", 1.0)) for r in view.runs.values() if r["performance"].get("status") in SCORED)
    stopped_early = [r for r in rejected if r.get("rejecting")]
    assert stopped_early                                                               # seen on a progress line, not trained to the end
    assert any('"limits_enforced_by_code"' in user and '"max": 4' in user for role, user in recorder.seen if role == "writer")
    assert any("rejected: n_constants" in user for role, user in recorder.seen if role == "writer")    # writers see why
    # The limit can be moved during a run, and a bad one is refused.
    assert form.check_change("limits", {"n_constants": {"max": 8}}) is None
    assert form.check_change("limits", {"n_constants": 8}) is not None
    row = report.leaderboard(view, 50)
    assert all(r["kind"] in ("design", "baseline") for r in row) and "baseline" in [r["kind"] for r in row]


def test_designs_from_an_earlier_run_and_reference_rows(tmp_path, capsys):
    folder = search(tmp_path, budget__evaluations=7, evaluation__allowance=150, audit__reviews="none", strategist__mode="off")
    first, _ = run(folder, name="one")
    best = [c["id"] for c in first.view().scored()[:2]]
    second = Controller(folder, "t", poll=0.2)
    second.begin()
    source = os.path.join(folder, "runs", "one")
    assert main(["import", folder, "--name", "t", "--from-run", source, "--top", "2", "--by", "Ada"]) == 0
    assert main(["reference", folder, "--name", "t", "--label", "published model", "--score", "0.5", "--metric", "test.test_mse=0.6",
                 "--metric", "parameters=7", "--note", "from the paper", "--by", "Ada"]) == 0
    assert main(["reference", folder, "--name", "t", "--from-run", source, "--top", "1", "--by", "Ada"]) == 0
    with pytest.raises(SystemExit):
        main(["import", folder, "--name", "t", "--from-run", folder, "--by", "Ada"])            # not a run folder
    reason = second.run(max_seconds=240)
    assert reason.startswith("the budget")
    view = second.view()
    imported = [r for r in view.runs.values() if r["purpose"] == "import"]
    assert len(imported) == 2 and all(r["performance"]["status"] in SCORED for r in imported)   # fitted here, scored here
    assert {r["history"]["imported_from"]["candidate"] for r in imported} == set(best)
    assert all(r["history"]["mode"] is None and r["history"]["lineage"] for r in imported)
    assert any(r["history"].get("parent") in {i["id"] for i in imported} for r in view.runs.values())     # and built on
    entry = [e for e in second.store.merged_list("ledger") if e["kind"] == "import"][0]
    assert entry["status"] == "applied" and len(entry["imported"]) == 2 and entry["by"] == "Ada"
    capsys.readouterr()
    assert main(["leaderboard", folder, "--name", "t", "--top", "5", "--columns", "test.test_mse", "valid.n_constants"]) == 0
    board = capsys.readouterr().out
    assert "| reference | published model |" in board and "| reference | one %s |" % best[0] in board and "| baseline |" in board
    assert "test.test_mse" in board and "0.6" in board
    assert main(["status", folder, "--name", "t"]) == 0
    status = capsys.readouterr().out
    assert "Models: 7" in status and "Best: " in status and "Agents: $0.00" in status and "{" not in status.split("\n")[0]
    assert main(["status", folder, "--name", "t", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["run"] == "t"
    child = [r for r in view.runs.values() if r["history"].get("parent") and r.get("candidate")][0]
    assert main(["show", folder, "--name", "t", child["id"]]) == 0
    shown = capsys.readouterr().out
    assert "Came from:" in shown and "What it changed against %s" % child["history"]["parent"] in shown and "+" in shown


def test_slots_ordered_by_the_person(tmp_path):
    folder = search(tmp_path, budget__evaluations=24, evaluation__allowance=150, audit__reviews="none", strategist__mode="off",
                    crossover__kinds=["hybrid"], schedule__phases=[{"until": 1.0, "new": 0.5, "cross": 0.0, "local": 0.5}])
    recorder = Recorder(folder)
    controller = Controller(folder, "t", poll=0.2, agent_backend=recorder)
    drive(controller, lambda v: len(scored(v)) >= 6)
    assert not [r for r in controller.view().runs.values() if r["history"].get("mode") == "cross"]     # the schedule has none
    assert main(["force", folder, "--name", "t", "--mode", "cross", "--kind", "hybrid", "--count", "3", "--by", "Ada",
                 "--instruction", "Keep the sine term of the first parent."]) == 0
    with pytest.raises(SystemExit):
        main(["force", folder, "--name", "t", "--mode", "sideways", "--by", "Ada"])
    drive(controller, lambda v: len([r for r in v.runs.values() if r["history"].get("forced_by")]) >= 3)
    forced = [r for r in controller.view().runs.values() if r["history"].get("forced_by")]
    assert len(forced) == 3 and all(r["history"]["mode"] == "cross" and r["history"]["move"] == "hybrid" for r in forced)
    entry = [e for e in controller.store.merged_list("ledger") if e["kind"] == "force"][0]
    assert entry["by"] == "Ada" and entry["count"] == 3 and all(r["history"]["forced_by"] == entry["id"] for r in forced)
    assert sum(1 for role, user in recorder.seen if role == "writer" and "Keep the sine term of the first parent." in user) == 3
    finish(folder, controller)


def test_the_controller_job_script(tmp_path, capsys):
    folder = search(tmp_path)
    assert main(["controller", folder, "--name", "r1", "--partition", "cpuq", "--qos", "normal", "--time", "0-12:00:00",
                 "--setup", "source ~/envs/x/bin/activate", "--python", "python3"]) == 0
    text = open(os.path.join(folder, "run_controller_r1.sbatch")).read()
    for needed in ("#SBATCH --requeue", "#SBATCH --signal=B:USR1@180", "#SBATCH --partition=cpuq", "#SBATCH --qos=normal",
                   "#SBATCH --time=0-12:00:00", "source ~/envs/x/bin/activate", "trap requeue USR1",
                   'scontrol requeue "$SLURM_JOB_ID"', "python3 -m evoloop run", "--name r1 &", 'wait "$child"'):
        assert needed in text, needed
    assert text.index("trap requeue USR1") < text.index("-m evoloop run")
    assert "sbatch " in capsys.readouterr().out


def test_replies_are_streamed_and_long_enough_for_several_designs():
    assert form.DEFAULTS["agents"]["max_tokens"] == 64000
    source = open(os.path.join(os.path.dirname(form.__file__), "model", "anthropic_api.py")).read()
    assert "messages.stream(**kwargs)" in source and "get_final_message()" in source and ".create(" not in source
