"""The metric a search optimizes has a name, and the metrics to track are declared: both reach the study file."""
import json
import os

from evoloop import form, interview, report
from evoloop.cli import main

from helpers import search
from test_on_the_fly import run


def test_set_up_asks_what_the_score_is_called_and_what_to_track():
    fields = [q["field"] for q in interview.QUESTIONS]
    at = fields.index("objective.direction")
    assert fields[at + 1:at + 3] == ["objective.metric", "evaluation.metrics"]          # asked straight after the direction
    brief = {"objective": {"goal": "better", "direction": "maximize"}}
    assert interview.record(brief, "objective.metric", "pearson_r") is None
    assert interview.record(brief, "evaluation.metrics", "pearson_r: Pearson r per peak; count_r2: R2 of log counts") is None
    assert brief["evaluation"]["metrics"] == {"pearson_r": "Pearson r per peak", "count_r2": "R2 of log counts"}
    assert interview.record(brief, "evaluation.metrics", "just some words") is not None  # not a list of name: definition
    assert form.check_value("evaluation.metrics", {"auroc": {"definition": "area under the ROC curve", "direction": "maximize", "split": "test"}}) is None
    assert form.check_value("evaluation.metrics", {"auroc": {"direction": "maximize"}}) is not None
    assert form.check_value("evaluation.metrics", {"auroc": ""}) is not None


def test_the_plan_says_what_is_optimized_and_tracked():
    base = {"objective": {"goal": "better", "direction": "maximize"}, "run": {"type": "refine"}, "budget": {"evaluations": 100}}
    unnamed = "\n".join(form.at_a_glance(form.resolve(base)[0]))
    assert "Score:           not named (set objective.metric" in unnamed and "higher is better" in unnamed
    named = dict(base, objective=dict(base["objective"], metric="pearson_r"),
                 evaluation={"metrics": {"pearson_r": "Pearson r per peak", "count_r2": "R2 of log counts"}})
    assert "Score:           pearson_r, higher is better; also tracked: count_r2" in "\n".join(form.at_a_glance(form.resolve(named)[0]))


def test_the_study_file_names_the_metric_and_the_report_says_when_a_tracked_one_is_missing(tmp_path):
    folder = search(tmp_path, budget__evaluations=7, evaluation__allowance=150, audit__reviews="none", strategist__mode="off",
                    objective__metric="valid_mse",
                    evaluation__metrics={"valid_mse": "mean squared error on the validation points",
                                         "test_mse": {"definition": "mean squared error on held-out points", "split": "test"},
                                         "calibration": "a metric the evaluator does not report"})
    controller, _ = run(folder, name="m")
    assert main(["study", folder, "--name", "m"]) == 0
    with open(os.path.join(folder, "runs", "m", "study.json"), encoding="utf-8") as handle:
        study = json.load(handle)
    evaluation = study["experiment"]["evaluation"]
    assert evaluation["primary_metric"] == "valid_mse" and study["experiment"]["objective"]["optimize"]["metric"] == "valid_mse"
    assert set(evaluation["metrics"]) == {"valid_mse", "test_mse", "calibration"}
    notes = report.untracked(controller.settings, controller.view())
    assert len(notes) == 1 and "`calibration`" in notes[0]                               # test_mse is reported; the score is the score
