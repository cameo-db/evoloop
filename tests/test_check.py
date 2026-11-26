"""`evoloop check`: the evaluator is tried before any search, killed and restarted and asked to stop, so that an
evaluator that begins again or cannot be stopped is found before it costs GPU days (2026-11-26)."""
import os
import shutil

from evoloop import check, evojob
from evoloop.cli import main

from helpers import search

HELPER = os.path.join(os.path.dirname(os.path.abspath(evojob.__file__)), "evojob.py")

GOOD = '''
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evojob
job = evojob.Job()
state = job.load_state() or {"step": 0}
for step in range(state["step"] + 1, int(job.allowance) + 1):
    time.sleep(0.15)
    job.report(step, 1.0 / step)
    state["step"] = step
    job.save_state(state)
    if job.should_stop():
        break
job.finish(score=1.0 / state["step"])
'''

# Begins at step one whenever it is started, and does not read the request to stop.
DEAF = '''
import json, os, time
out = os.environ["EVO_OUT_DIR"]
for step in range(1, int(float(os.environ["EVO_ALLOWANCE"])) + 1):
    time.sleep(0.15)
    with open(os.path.join(out, "progress.jsonl"), "a") as handle:
        handle.write(json.dumps({"step": step, "metric": 1.0 / step}) + "\\n")
with open(os.path.join(out, "result.json"), "w") as handle:
    json.dump({"valid": True, "score": 0.5}, handle)
'''


def evaluator(tmp_path, text, allowance=400, **answers):
    folder = search(tmp_path, evaluation__allowance=allowance, run_command="python adapter/tried.py", **answers)
    shutil.copy(HELPER, os.path.join(folder, "adapter", "evojob.py"))
    with open(os.path.join(folder, "adapter", "tried.py"), "w") as handle:
        handle.write(text)
    return folder


def test_an_evaluator_that_resumes_and_stops_passes(tmp_path):
    said = []
    found = check.run(evaluator(tmp_path, GOOD), wait=60, say=said.append, poll=0.1)
    assert found["ok"] and found["reports"] and found["resumes"] is True and found["stops"] is True and not found["advice"]
    text = "\n".join(said)
    assert "it resumes" in text and "with a score of" in text and said[-2] == "The evaluator does what a search needs."


def test_an_evaluator_that_begins_again_and_cannot_be_stopped_is_told_so(tmp_path):
    said = []
    found = check.run(evaluator(tmp_path, DEAF), wait=4, say=said.append, poll=0.1)
    assert found["ok"] and found["resumes"] is False and found["stops"] is False
    text = "\n".join(said)
    assert "began again at step 1" in text and "it does not resume" in text and "still running after" in text
    assert any("compute.time_limit longer than a whole training run" in a for a in found["advice"])
    assert any("job.should_stop()" in a for a in found["advice"])
    assert "The evaluator runs, with what is said below." in said


def test_a_run_that_pauses_before_it_hears_the_stop_is_not_called_deaf(tmp_path):
    pausing = GOOD.replace("    if job.should_stop():\n        break\n", "    if step == 3:\n        job.pause()\n")
    assert "job.pause()" in pausing
    said = []
    found = check.run(evaluator(tmp_path, pausing), wait=30, say=said.append, poll=0.1)
    assert found["ok"] and found["stops"] is None
    assert "its job ended first" in "\n".join(said) and "asked to be continued" in "\n".join(said)


def test_an_evaluator_that_breaks_fails_the_check(tmp_path, capsys):
    folder = evaluator(tmp_path, "raise SystemExit('the data file is missing')\n")
    assert main(["check", folder, "--wait", "20"]) == 1
    printed = capsys.readouterr().out
    assert "ended without a score" in printed and "the data file is missing" in printed
    assert "The evaluator does not work yet." in printed


def test_a_run_of_seconds_that_reports_nothing_is_fine(tmp_path):
    quick = ('import json, os\nwith open(os.path.join(os.environ["EVO_OUT_DIR"], "result.json"), "w") as h:\n'
             '    json.dump({"valid": True, "score": 0.25}, h)\n')
    said = []
    found = check.run(evaluator(tmp_path, quick), wait=20, say=said.append, poll=0.1)
    assert found["ok"] and found["reports"] is False and found["resumes"] is None and found["stops"] is None
    assert "before it reported any progress" in "\n".join(said)


def test_an_evaluator_that_never_reports_is_asked_to(tmp_path):
    silent = "import time\ntime.sleep(60)\n"
    said = []
    found = check.run(evaluator(tmp_path, silent), wait=2, say=said.append, poll=0.1)
    assert not found["ok"] and found["reports"] is False
    assert any("Report progress while training" in a for a in found["advice"])


def test_the_example_evaluator_is_checked_as_it_is(tmp_path):
    # The demo's evaluator trains in a second or two: whatever the check can test of it, it must not call it broken.
    folder = search(tmp_path, evaluation__allowance=150)
    found = check.run(folder, wait=30, say=lambda line: None, poll=0.05)
    assert found["ok"]
