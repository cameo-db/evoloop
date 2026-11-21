"""Who runs the search: code (the default) or an agent the person talks to."""
import pytest

from evoloop import form, strategist
from evoloop.agents import Agents
from evoloop.cli import main
from evoloop.controller import Controller

from helpers import EXAMPLE, ask, search
from test_loop import drive, scored

QUIET = dict(budget__evaluations=40, evaluation__allowance=150, audit__reviews="none", harness__level="standard",
             strategist__every=500, strategist__plateau=500)


def decisions(controller):
    return [e for e in controller.store.merged_list("ledger") if e["kind"] == "decision"]


def resolved(**answers):
    brief = form.load_brief(EXAMPLE)
    for key, value in answers.items():
        form.put(brief, key.replace("__", "."), value)
    return form.resolve(brief, [])[0]


def test_code_runs_the_search_unless_the_person_chooses_the_agent():
    assert form.DEFAULTS["harness"]["conductor"] == "code"
    assert resolved()["harness"]["conductor"] == "code" and resolved(run__type="discovery")["strategist"]["mode"] == "off"
    chosen = resolved(run__type="discovery", harness__conductor="agent")
    assert chosen["strategist"]["mode"] == "act"                       # an agent that runs the search can change its course
    assert resolved(harness__conductor="agent", strategist__mode="advise")["strategist"]["mode"] == "advise"
    assert form.check_value("harness.conductor", "committee") is not None


def test_there_is_nobody_to_talk_to_when_code_runs_the_search(tmp_path, capsys):
    folder = search(tmp_path, **QUIET)
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 2)
    with pytest.raises(SystemExit) as refused:
        main(["chat", folder, "--name", "t", "how is it going?", "--by", "Ada"])
    assert "harness.conductor=agent" in str(refused.value)
    assert not controller.store.read("chat")
    # The person hands the search to the agent mid-run, and can then talk to it.
    ask(folder, "t", {"kind": "set", "changes": {"harness.conductor": "agent"}, "by": "Ada"})
    controller.turn()
    assert controller.settings["harness"]["conductor"] == "agent"
    capsys.readouterr()
    assert main(["chat", folder, "--name", "t", "how is it going?", "--by", "Ada"]) == 0
    assert "best so far" in capsys.readouterr().out
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)


def test_what_the_person_asks_for_in_a_talk_is_checked_recorded_and_applied(tmp_path, capsys):
    folder = search(tmp_path, harness__conductor="agent", **QUIET)
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 2)
    assert not decisions(controller)
    capsys.readouterr()
    assert main(["chat", folder, "--name", "t", "I want more novel designs, and switch to the archive", "--by", "Ada"]) == 0
    said = capsys.readouterr().out
    assert "asked for: novelty" in said and "asked for: strategy" in said
    controller.turn()
    made = {d["action"]: d for d in decisions(controller)}
    assert made["novelty"]["status"] == "applied" and made["novelty"]["chat"] == "T1"
    assert controller.settings["schedule"]["novelty"] == 0.8
    assert made["strategy"]["status"] == "proposed"                   # a change of strategy still waits for a yes
    assert controller.settings["strategy"]["mechanism"] != "archive"
    talk = controller.store.read("chat")
    assert len(talk) == 1 and talk[0]["by"] == "Ada" and talk[0]["text"].startswith("I want") and talk[0]["reply"]
    # Saying yes in the talk approves what waits, in the person's name.
    assert main(["chat", folder, "--name", "t", "yes, do it", "--by", "Ada"]) == 0
    assert made["strategy"]["id"] in capsys.readouterr().out
    controller.turn()
    made = {d["action"]: d for d in decisions(controller)}
    assert made["strategy"]["status"] == "approved" and made["strategy"]["answered_by"] == "Ada"
    assert controller.settings["strategy"]["mechanism"] == "archive"
    # The strategist's meetings are shown what was said.
    agents = Agents(controller.settings, controller.folder, controller.store, tag="x")
    facts = strategist.facts(controller.store, agents, controller.view(), controller.settings, "test")
    assert [c["they_said"] for c in facts["conversation_with_the_person"]][-1] == "yes, do it"
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)


def test_a_talk_cannot_take_the_search_past_its_bounds(tmp_path):
    folder = search(tmp_path, harness__conductor="agent", **QUIET)
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 1)
    ask(folder, "t", {"kind": "decisions", "by": "Ada", "decisions": [
        {"action": "shares", "args": {"new": 0.0, "cross": 0.2, "local": 0.8}, "reason": "asked", "chat": "T1"},
        {"action": "rewrite_everything", "args": {}, "chat": "T1"}, "not a decision"]})
    controller.turn()
    assert [d["status"] for d in decisions(controller)] == ["refused", "refused"]
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)
