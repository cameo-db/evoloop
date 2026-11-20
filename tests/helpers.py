"""Shared by the tests: a copy of the example with its brief confirmed, and a way to run it."""
import os
import shutil

from evoloop import form
from evoloop.controller import Controller

EXAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evoloop", "examples",
                       "symbolic_regression")


def search(tmp_path, **answers):
    folder = str(tmp_path / "search")
    shutil.copytree(EXAMPLE, folder, ignore=shutil.ignore_patterns("__pycache__"))
    brief = form.load_brief(folder)
    for key, value in answers.items():
        form.put(brief, key.replace("__", "."), value)
    form.save_brief(folder, brief)
    form.confirm(folder, "Tester")
    return folder


def run(folder, name="t", seconds=240):
    controller = Controller(folder, name, poll=0.2)
    reason = controller.run(max_seconds=seconds)
    return controller, reason


def ask(folder, name, body):
    """Leave a request for the controller, as the steering commands do."""
    import json
    import time
    inbox = os.path.join(folder, "runs", name, "requests")
    os.makedirs(inbox, exist_ok=True)
    with open(os.path.join(inbox, "%d_%s.json" % (int(time.time() * 1e6), body["kind"])), "w") as handle:
        json.dump(body, handle)
