"""Skills (what kind of optimisation a search is) and the estimator that makes settings moves for the tuning skill."""
import math
import os
import random

import pytest
import yaml

from evoloop import form, interview, menu, skill, tpe
from evoloop.agents import Agents
from evoloop.cli import main
from evoloop.controller import Controller
from evoloop.store import Store

from helpers import EXAMPLE, ask, search
from test_loop import drive, scored
from test_parts import make_view

BASE = {"objective": {"goal": "better", "direction": "maximize"}, "run": {"type": "refine"}, "budget": {"evaluations": 100}}


def resolved(folder=None, **answers):
    brief = {k: dict(v) for k, v in BASE.items()}
    for key, value in answers.items():
        form.put(brief, key.replace("__", "."), value)
    return form.resolve(brief, [], folder)


# --- the skills themselves ------------------------------------------------------------------------
def test_every_built_in_skill_can_be_used_and_says_what_it_is_for():
    assert skill.names() == ["performance", "distillation", "efficiency", "mechanistic", "tuning"]
    for name in skill.names():
        found, fault = skill.load(name)
        assert fault is None and found["name"] == name and len(found["summary"]) > 40
        assert found["guidance"].get("all") and found["guidance"].get("writer")
        assert name in menu.SKILLS and "`%s`" % name in menu.menu_markdown()
    assert skill.load(None) == (None, None) and skill.load("") == (None, None)
    assert "no skill named" in skill.load("nonesuch")[1]


def test_a_skill_is_laid_over_the_run_type_and_under_what_the_person_set():
    plain, _ = resolved()
    assert plain["strategy"]["mechanism"] == "lineage" and plain["_skill"] is None
    settings, sources = resolved(run__skill="efficiency")
    assert settings["strategy"]["mechanism"] == "pareto" and sources["strategy.mechanism"] == "skill efficiency"
    assert settings["strategy"]["second_metric"] == "parameters" and settings["_skill"]["name"] == "efficiency"
    assert settings["space"]["preset"] == "template" and sources["space.preset"] == "run type refine"   # the skill leaves it
    mine, sources = resolved(run__skill="efficiency", strategy__mechanism="archive")
    assert mine["strategy"]["mechanism"] == "archive" and sources["strategy.mechanism"] == "brief"
    tuned, _ = resolved(run__skill="tuning")
    assert tuned["space"]["preset"] == "settings_only" and tuned["variation"]["settings_by"] == "tpe"
    assert tuned["strategist"]["mode"] == "off" and tuned["schedule"]["phases"][0]["local"] == 1.0
    assert any("the efficiency skill needs" in w for w in form.warnings(settings))       # what the adapter must do
    broken, _ = resolved(run__skill="nonesuch")
    assert broken["_skill"] is None and any("no skill named" in w for w in form.warnings(broken))
    lines = form.plan_lines({k: dict(v) for k, v in dict(BASE, run={"type": "refine", "skill": "mechanistic"}).items()})
    assert any(line.startswith("Skill: mechanistic.") for line in lines)
    assert any("From the skill mechanistic:" in line for line in lines)


def test_a_skill_of_your_own_is_a_folder_you_can_copy_and_edit(tmp_path, capsys):
    folder = str(tmp_path)
    assert main(["skills"]) == 0
    listed = capsys.readouterr().out
    assert all(name in listed for name in skill.names())
    assert main(["skills", "distillation"]) == 0 and "teacher" in capsys.readouterr().out
    own = os.path.join(folder, "skills", "mine")
    assert main(["skills", "efficiency", "--copy", own]) == 0
    with pytest.raises(SystemExit):
        main(["skills", "efficiency", "--copy", own])                     # never written over
    with open(os.path.join(own, "skill.yaml"), encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    raw.update(name="mine", guidance={"writer": "Prefer depthwise layers."})
    raw["settings"]["strategy"]["second_metric"] = "examples_per_s"
    with open(os.path.join(own, "skill.yaml"), "w", encoding="utf-8") as handle:
        yaml.safe_dump(raw, handle)
    for given in ("mine", "skills/mine", own):                              # by name, by relative path, by full path
        settings, sources = resolved(folder, run__skill=given)
        assert settings["_skill"]["name"] == "mine" and settings["strategy"]["second_metric"] == "examples_per_s"
        assert sources["strategy.second_metric"] == "skill mine"
    assert skill.guidance(settings["_skill"], "writer") == "Prefer depthwise layers."
    assert skill.guidance(settings["_skill"], "analyst") is None
    # A skill may not set what defines the problem, or name a field that does not exist, or a value that is refused.
    for bad, said in (({"evaluation": {"allowance": 5}}, "belongs in the brief"), ({"objective": {"direction": "minimize"}}, "belongs in the brief"),
                      ({"strategy": {"mechanism": "magic"}}, "strategy.mechanism"), ({"nothing": {"here": 1}}, "not a field"),
                      ({"run": {"type": "survey"}}, "belongs in the brief")):
        raw["settings"] = bad
        with open(os.path.join(own, "skill.yaml"), "w", encoding="utf-8") as handle:
            yaml.safe_dump(raw, handle)
        os.utime(os.path.join(own, "skill.yaml"), (1, random.random() * 1e9))
        found, fault = skill.load("mine", folder)
        assert found is None and said in fault, fault
    assert skill.check({"guidance": {"janitor": "x"}}) and skill.check({"needs": {"adapter": "not a list"}}) and skill.check([])


# --- in a search ----------------------------------------------------------------------------------
class Listener:
    def __init__(self):
        self.heard = {}

    def call(self, role, system, user, schema, context):
        self.heard[role] = context
        return {"reasoning": "r", "note": "n", "proposals": [], "lessons": [], "questions": [], "changes": [], "notes": [],
                "not_covered": []}, {"cost_usd": 0.0}


def test_the_agents_are_told_what_the_skill_asks_of_their_role(tmp_path):
    settings, _ = resolved(run__skill="distillation", agents__backend="stub")
    backend = Listener()
    agents = Agents(settings, str(tmp_path), Store(str(tmp_path)), backend=backend)
    for role in ("writer", "analyst", "translator"):
        agents.call(role, {})
    told = backend.heard["writer"]["skill"]
    assert told["name"] == "distillation" and "teacher-labelled augmentation" in told["guidance"]
    assert "from-scratch" in backend.heard["analyst"]["skill"]["guidance"] and "teacher-labelled" not in backend.heard["analyst"]["skill"]["guidance"]
    assert "skill" not in backend.heard["translator"]
    plain, _ = resolved(agents__backend="stub")
    agents.update(plain)
    agents.call("writer", {})
    assert "skill" not in backend.heard["writer"]


def test_a_run_will_not_start_on_a_skill_that_cannot_be_used(tmp_path):
    folder = search(tmp_path, run__skill="nonesuch")
    with pytest.raises(form.BriefError) as refused:
        Controller(folder, "t", poll=0.1).begin()
    assert "no skill named" in str(refused.value)


def test_the_skill_can_be_changed_during_a_run_and_a_bad_one_is_refused(tmp_path):
    folder = search(tmp_path, budget__evaluations=40, evaluation__allowance=150, audit__reviews="none", harness__level="minimal")
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 2)
    assert controller.settings["_skill"] is None
    ask(folder, "t", {"kind": "set", "changes": {"run.skill": "nonesuch"}, "by": "Ada"})
    ask(folder, "t", {"kind": "set", "changes": {"run.skill": "efficiency"}, "by": "Ada"})
    controller.turn()
    sets = [e for e in controller.store.merged_list("ledger") if e["kind"] == "set"]
    assert [e["status"] for e in sets] == ["refused", "applied"] and "no skill named" in sets[0]["why"]
    assert sets[1]["also_changed"]["strategy.mechanism"] == ["lineage", "pareto"]       # what moved with it is on record
    assert controller.settings["_skill"]["name"] == "efficiency" and controller.settings["strategy"]["mechanism"] == "pareto"
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)


def test_the_report_says_what_the_skill_still_lacks():
    rows = [("R%d" % i, "L1", "new", None, 0.5 + i / 100, "a") for i in range(1, 5)]
    view = make_view(rows)
    wants, _ = skill.load("efficiency")
    assert any("`parameters`" in line for line in skill.missing(wants, view, []))
    for run in view.runs.values():
        run["performance"]["parameters"] = 1000
    assert skill.missing(wants, type(view)(view.runs, view.models, {}, "maximize", 0.01, 0), []) == []
    taught, _ = skill.load("distillation")
    lacking = skill.missing(taught, view, [{"label": "Teacher ensemble (5 models)"}])
    assert len(lacking) == 1 and "from scratch" in lacking[0]
    assert skill.missing(taught, view, [{"label": "teacher"}, {"label": "student from scratch"}]) == []
    assert skill.missing(None, view, []) == []


def test_setup_suggests_a_skill_from_the_words_of_the_goal(tmp_path):
    folder = search(tmp_path)
    for goal, wanted in (("Distil the ensemble into a small student.", "distillation"),
                         ("Tune the learning rate and weight decay.", "tuning"),
                         ("Make the model faster at the same accuracy.", "efficiency"),
                         ("An interpretable model whose filters are motifs.", "mechanistic"),
                         ("A biophysical model of binding.", "mechanistic"),
                         ("Get the best correlation on held-out data.", "performance")):
        brief = form.load_brief(folder)
        form.put(brief, "objective.goal", goal)
        made = interview.infer(folder, brief)
        assert made.get("run.skill") == wanted, (goal, made.get("run.skill"))
    asked = [q for q in interview.QUESTIONS if q["field"] == "run.skill"][0]
    assert [c["value"] for c in asked["choices"]] == skill.names()


# --- the estimator --------------------------------------------------------------------------------
def test_the_estimator_finds_good_settings_faster_than_chance():
    def score(s):       # best at lr = 0.001 and width = 64, with dropout off
        return -(math.log10(s["fit.lr"]) + 3.0) ** 2 - ((s["net.width"] - 64) / 32.0) ** 2 - (0.5 if s["net.dropout"] else 0.0)
    start = {"fit.lr": 0.1, "net.width": 256, "net.dropout": True}
    ranges = {"fit.lr": [1e-5, 1.0], "net.width": [8, 512]}
    rng = random.Random(0)
    history = [(dict(start), score(start))]
    lines = []
    for _ in range(70):
        new, how = tpe.suggest(start, history, rng, ranges)
        lines.append(how)
        assert isinstance(new["net.width"], int) and 8 <= new["net.width"] <= 512 and 1e-5 <= new["fit.lr"] <= 1.0
        assert isinstance(new["net.dropout"], bool)
        history.append((new, score(new)))
    early = max(v for _, v in history[1:tpe.STARTUP])
    late = sorted(v for _, v in history[-20:])
    assert "prior" in lines[0] and "densities" in lines[-1]
    assert late[10] > early                           # the middle of the late draws beats the best of the first, random ones
    assert max(v for _, v in history) > -0.15           # and it gets close to the best there is (0)
    best = max(history, key=lambda item: item[1])[0]
    assert 2e-4 < best["fit.lr"] < 5e-3 and 40 <= best["net.width"] <= 96 and best["net.dropout"] is False


def test_the_estimator_copes_with_what_it_is_given():
    rng = random.Random(1)
    new, _ = tpe.suggest({"a.zero": 0.0, "a.neg": -2.0, "a.name": "relu", "a.n": 3}, [], rng)
    assert isinstance(new["a.zero"], float) and new["a.name"] == "relu" and isinstance(new["a.n"], int) and new["a.n"] >= 1
    history = [({"a.name": "relu", "a.n": 3}, 0.1), ({"a.name": "gelu", "a.n": 4}, 0.9), ({"a.n": "broken"}, float("nan"))] * 5
    seen = {tpe.suggest({"a.name": "relu", "a.n": 3}, history, random.Random(i))[0]["a.name"] for i in range(30)}
    assert "gelu" in seen                                # a text value is drawn from those seen, the better one more often
    assert form.check_value("space.ranges", {"fit.lr": [1e-5, 0.1]}) is None
    assert form.check_value("space.ranges", {"fit.lr": [0.1, 1e-5]}) is not None
    assert form.check_value("variation.settings_by", "tpe") is None


def test_the_tuning_skill_searches_settings_without_calling_an_agent(tmp_path):
    folder = search(tmp_path, budget__evaluations=16, evaluation__allowance=150, run__skill="tuning", space__preset=None)
    controller = Controller(folder, "t", poll=0.1)
    assert controller.settings["space"]["preset"] == "settings_only" and controller.settings["variation"]["settings_by"] == "tpe"
    assert controller.run(max_seconds=300)
    runs = [r for r in controller.view().runs.values() if r.get("purpose", "search") in ("search", "trial")]
    assert len(scored(controller.view())) >= 12
    assert controller.store.read("calls") == []                                  # nothing was asked of a model
    assert {r["history"]["move"] for r in runs} == {"settings_move"}
    assert len({r["model"] for r in runs}) == 1                                  # the structure never changed
    assert len({str(sorted(r["settings"].items())) for r in runs}) == len(runs)  # and every design has its own settings
    assert any("densities" in str(r["history"].get("predicted_effect")) for r in runs)
