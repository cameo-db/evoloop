"""Defects found in real searches (2026-11-25): an answer with a colon, reviews after the budget was raised, an
imported score with no metric, a crashed design that could not be trained again, questions that could not be
answered, and a stop that cut off a slow evaluator."""
import json
import os
import time

from evoloop import report, study
from evoloop.cli import main, parse_pairs
from evoloop.controller import Controller, STOP_GRACE
from evoloop.store import SCORED

from helpers import ask, run, search

SMALL = dict(evaluation__allowance=150, audit__reviews="none", harness__level="minimal")


def test_an_answer_with_a_colon_is_a_sentence(tmp_path):
    read = parse_pairs(["objective.goal=Improve the fit: keep the size", "task.note=a: b: c", "budget.evaluations=40",
                        "limits={parameters: {max: 5}}", "compute.qos=[{name: a, max_jobs: 2}, {name: b}]",
                        "evaluation.metrics=val_r: Pearson r"])
    assert read["objective.goal"] == "Improve the fit: keep the size" and read["task.note"] == "a: b: c"
    assert read["budget.evaluations"] == 40 and read["limits"] == {"parameters": {"max": 5}}
    assert read["compute.qos"] == [{"name": "a", "max_jobs": 2}, {"name": "b"}]
    assert read["evaluation.metrics"] == {"val_r": "Pearson r"}                  # a field that holds a mapping still takes one
    folder = str(tmp_path / "s")
    assert main(["init", folder]) == 0
    assert main(["brief", folder, "--answer", "objective.goal=Lower the error: without more constants"]) == 0
    from evoloop import form
    assert form.given(form.load_brief(folder))["objective.goal"] == "Lower the error: without more constants"


def reviews_of(controller):
    seen = []
    controller.review = lambda view, why, roles=None, asked=False: seen.append((why, round(view.charged())))
    return seen


def test_a_larger_budget_brings_the_later_reviews_again(tmp_path):
    folder = search(tmp_path, budget__evaluations=4, evaluation__allowance=150, audit__reviews=[0.5, 0.75],
                    harness__level="minimal", compute__gpus=1, baseline__mode="skip")
    controller = Controller(folder, "t", poll=0.1)
    first = reviews_of(controller)
    controller.run(max_seconds=200)
    assert first == [("at 50% of the budget", 2), ("at 75% of the budget", 3)]
    ask(folder, "t", {"kind": "set", "changes": {"budget.evaluations": 12}, "by": "Ada"})
    again = Controller(folder, "t", poll=0.1)
    later = reviews_of(again)
    again.run(max_seconds=300)
    # Four evaluations were spent and reviewed. Of the new budget of twelve, half is six and three quarters is nine.
    assert later == [("at 50% of the budget", 6), ("at 75% of the budget", 9)]


def test_a_run_kept_from_before_is_not_reviewed_twice(tmp_path):
    folder = search(tmp_path, budget__evaluations=4, evaluation__allowance=150, audit__reviews=[0.5],
                    harness__level="minimal", compute__gpus=1, baseline__mode="skip")
    controller, _ = run(folder)
    state = os.path.join(controller.run_dir, "controller.json")
    with open(state) as handle:
        kept = json.load(handle)
    kept.pop("review_at")                                                        # as an earlier version left it
    with open(state, "w") as handle:
        json.dump(kept, handle)
    ask(folder, "t", {"kind": "set", "changes": {"budget.evaluations": 6}, "by": "Ada"})
    again = Controller(folder, "t", poll=0.1)
    later = reviews_of(again)
    again.run(max_seconds=200)
    assert later == []                                                           # half of six is three, which lies behind


def test_an_imported_score_says_what_it_measured(tmp_path):
    assert study.score_there(0.76, "pearson_r", "K562 ATAC-seq") == (
        "Its score there was 0.76 pearson_r on K562 ATAC-seq, as that search's evaluator computed it: it is not a score "
        "of this search.")
    assert "in a metric that search did not name" in study.score_there(0.76, None, None)
    source = search(tmp_path / "a", budget__evaluations=3, objective__metric="val_mse", data__name="the toy curve", **SMALL)
    earlier, _ = run(source, name="one")
    folder = search(tmp_path / "b", budget__evaluations=2, baseline__mode="skip", **SMALL)
    ask(folder, "t", {"kind": "import", "source": earlier.run_dir, "top": 1, "by": "Ada"})
    controller, _ = run(folder)
    brought = [r for r in controller.store.merged("runs").values() if (r["history"].get("imported_from") or {}).get("run")]
    assert brought and brought[0]["history"]["imported_from"]["metric_there"] == "val_mse"
    assert brought[0]["history"]["imported_from"]["data_there"] == "the toy curve"
    assert "val_mse on the toy curve" in brought[0]["history"]["change_summary"]
    assert "not a score of this search" in brought[0]["history"]["change_summary"]


def test_a_design_that_crashed_can_be_trained_again(tmp_path):
    flag = str(tmp_path / "repaired")
    folder = search(tmp_path, budget__evaluations=1, budget__max_uncounted_failures=0, baseline__mode="skip",
                    run_command="test -f %s && python adapter/run.py" % flag, **SMALL)
    controller, _ = run(folder)
    failed = [r for r in controller.store.merged("runs").values() if r["performance"].get("status") == "failed"]
    assert len(failed) == 1 and not [r for r in controller.store.merged("runs").values() if r["performance"].get("status") in SCORED]
    open(flag, "w").close()                                                      # the evaluator is repaired
    ask(folder, "t", {"kind": "rerun", "run": failed[0]["id"], "by": "Ada", "reason": "the evaluator was fixed"})
    again, _ = run(folder)
    runs = again.store.merged("runs")
    new = [r for r in runs.values() if r["history"].get("rerun_of") == failed[0]["id"]]
    assert len(new) == 1 and new[0]["candidate"] == failed[0]["candidate"] and new[0]["seed"] == failed[0]["seed"]
    assert new[0]["performance"]["status"] in SCORED and new[0]["charge"] == 1.0
    assert again.view().cands[failed[0]["candidate"]]["value"] is not None       # the design has its score now
    done = [e for e in again.store.merged_list("ledger") if e.get("kind") == "rerun"]
    assert done[-1]["status"] == "applied" and done[-1]["as"] == new[0]["id"]
    # A design that has a score is not trained again this way, by its run id or by its own.
    ask(folder, "t", {"kind": "rerun", "run": failed[0]["candidate"], "by": "Ada"})
    third, _ = run(folder)
    refused = [e for e in third.store.merged_list("ledger") if e.get("kind") == "rerun"][-1]
    assert refused["status"] == "refused" and "has a score" in refused["why"]
    assert len(third.store.merged("runs")) == len(runs)


def test_a_question_can_be_answered_or_closed(tmp_path):
    folder = search(tmp_path, budget__evaluations=2, baseline__mode="skip", **SMALL)
    controller, _ = run(folder)
    for text in ("Is the score there the same metric?", "Should larger models be tried?"):
        controller.store.append("questions", {"id": "Q%d" % (len(controller.store.read("questions")) + 1), "question": text,
                                              "default": "assume not", "from": "analyst", "status": "open"})
    assert main(["reply", folder, "--name", "t", "--id", "Q1", "No: it was measured on other peaks.", "--by", "Ada"]) == 0
    assert main(["reply", folder, "--name", "t", "--id", "Q2", "--by", "Ada"]) == 0                   # closed, unanswered
    assert main(["reply", folder, "--name", "t", "--id", "Q9", "nothing", "--by", "Ada"]) == 0
    again, _ = run(folder)
    asked = again.store.merged("questions")
    assert asked["Q1"]["status"] == "answered" and asked["Q1"]["answer"] == "No: it was measured on other peaks."
    assert asked["Q2"]["status"] == "dismissed"
    notes = [e for e in again.store.merged_list("ledger") if e.get("kind") == "note" and e.get("answers") == "Q1"]
    assert len(notes) == 1 and notes[0]["status"] == "active" and notes[0]["roles"] == []
    assert "Is the score there the same metric?" in notes[0]["text"] and "other peaks" in notes[0]["text"]
    assert [e for e in again.store.merged_list("ledger") if e.get("kind") == "reply" and e.get("status") == "refused"]
    with open(os.path.join(again.run_dir, "report.md")) as handle:
        assert "Questions for you" not in handle.read()                          # none is open any more


def test_a_stopped_run_is_given_the_time_its_evaluator_needs(tmp_path):
    folder = search(tmp_path, budget__evaluations=2, baseline__mode="skip", **SMALL)
    controller, _ = run(folder)
    out = tmp_path / "slow"
    out.mkdir()
    controller.out_dir = lambda run_: str(out)
    now = time.time()
    assert controller.stop_grace({"id": "R9", "running_since": now - 6000}) == STOP_GRACE          # it has reported nothing
    with open(out / "progress.jsonl", "w") as handle:
        for step in (1, 2, 3):
            handle.write(json.dumps({"step": step, "metric": 0.1}) + "\n")
    # Three reports in the 6,000 seconds since it started: it reports every 2,000 or so, and hears of a stop then.
    grace = controller.stop_grace({"id": "R9", "running_since": now - 6000})
    assert 3900 < grace < 4100
    assert controller.stop_grace({"id": "R9", "running_since": now - 60}) == STOP_GRACE              # a quick one: five minutes
    # After a restart only the reports of this start count.
    assert 11900 < controller.stop_grace({"id": "R9", "running_since": now - 6000, "reports_at_start": 2}) < 12100
