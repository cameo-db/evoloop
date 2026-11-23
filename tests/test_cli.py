"""The commands, as a person or an agent would use them."""
import json
import os

import pytest

from evoloop import form
from evoloop.cli import main
from evoloop.controller import Controller

from helpers import search


def test_init_then_questions_then_confirm(tmp_path, capsys):
    source = tmp_path / "code"
    source.mkdir()
    (source / "m.py").write_text("# EVOLVE-BLOCK-START name=net kind=structure role=trunk\nX = 1\n# EVOLVE-BLOCK-END\n")
    folder = str(tmp_path / "s")
    assert main(["init", folder, "--source", str(source)]) == 0
    assert os.path.isfile(os.path.join(folder, "brief.yaml")) and os.path.isfile(os.path.join(folder, "base", "m.py"))
    capsys.readouterr()
    main(["brief", folder, "--questions"])
    asks = json.loads(capsys.readouterr().out)
    assert {a["field"] for a in asks} == set(form.REQUIRED)       # every empty required field is asked, none is guessed
    with pytest.raises(SystemExit):
        main(["brief", folder, "--confirm", "Ada"])                  # not while a question is open
    with pytest.raises(SystemExit):
        main(["brief", folder, "--answer", "objective.direction=upwards"])
    answers = ["objective.goal=better", "objective.direction=maximize", "run.type=refine", "budget.evaluations=30",
               "evaluation.allowance=5", "evaluation.noise=0.01", "baseline.mode=skip", "compute.gpus=1",
               "agents.backend=stub", "budget.model_dollars=0"]
    args = ["brief", folder]
    for answer in answers:
        args += ["--answer", answer]
    assert main(args) == 0
    brief = form.load_brief(folder)
    assert set(brief["status"]["asked"]) == set(form.REQUIRED)       # what the person was asked is on record
    capsys.readouterr()
    main(["plan", folder])
    plan = capsys.readouterr().out
    assert "From the brief (what you set):" in plan and "From the run type refine:" in plan
    assert "From the guidance for about 30 evaluations:" in plan and "From the default:" in plan
    with pytest.raises(SystemExit) as stop:                      # nor while a question has not been put to the person
        main(["brief", folder, "--confirm", "Ada"])
    assert "have not been put to the person" in str(stop.value) and "evaluation.test_metrics" in str(stop.value)
    capsys.readouterr()
    assert main(["brief", folder, "--confirm", "Ada", "--accept-defaults"]) == 0
    assert "accepted without asking:" in capsys.readouterr().out
    assert form.confirmed(form.load_brief(folder))


def test_steering_commands_reach_the_ledger(tmp_path, capsys):
    folder = search(tmp_path, budget__evaluations=6, evaluation__allowance=150, audit__reviews="none")
    assert main(["run", folder, "--name", "r", "--max-seconds", "200"]) == 0
    with pytest.raises(SystemExit):
        main(["set", folder, "--name", "r", "data.accession=x", "--by", "Ada"])       # refused at once, with the reason
    assert main(["set", folder, "--name", "r", "budget.evaluations=9", "schedule.novelty=0.7", "--by", "Ada", "--reason", "more"]) == 0
    assert main(["note", folder, "--name", "r", "Keep forms short.", "--roles", "writer", "--by", "Ada"]) == 0
    capsys.readouterr()
    assert main(["steer", folder, "--name", "r", "make it more novel", "--by", "Ada"]) == 0
    shown = capsys.readouterr().out
    assert "change: schedule.novelty = 0.8" in shown and "nothing was changed" in shown
    assert main(["steer", folder, "--name", "r", "make it more novel", "--by", "Ada", "--yes"]) == 0
    assert main(["run", folder, "--name", "r", "--max-seconds", "200"]) == 0           # the stopped run goes on
    controller = Controller(folder, "r")
    controller.refresh()
    ledger = controller.store.read("ledger")
    sets = {(e["key"], e["value"]) for e in ledger if e["kind"] == "set" and e["status"] == "applied"}
    assert {("budget.evaluations", 9), ("schedule.novelty", 0.7), ("schedule.novelty", 0.8)} <= sets
    assert controller.settings["schedule"]["novelty"] == 0.8 and len(controller.settings["notes"]) == 2
    assert controller.spent(controller.view()) >= 9
    assert any(c["role"] == "translator" for c in controller.store.read("calls"))
    capsys.readouterr()
    assert main(["report", folder, "--name", "r"]) == 0
    report = capsys.readouterr().out
    assert "schedule.novelty: 0.7 -> 0.8" in report and "Keep forms short." in report
    assert main(["study", folder, "--name", "r"]) == 0
    assert "No star: data.accession is empty" in capsys.readouterr().out
    assert main(["status", folder, "--name", "r"]) == 0
    controller.pool.shutdown(wait=False)


def test_guide(capsys):
    assert main(["guide", "100"]) == 0
    text = capsys.readouterr().out
    assert "about 100 evaluations" in text and "about 30" not in text and "Run types:" in text
