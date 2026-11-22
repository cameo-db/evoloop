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
    assert skill.names() == ["model-performance", "model-distillation", "model-efficiency", "model-ensemble-members",
                             "model-finetuning", "model-mechanistic", "model-size-frontier", "model-training-recipe",
                             "algorithm-runtime", "bioinformatics-algorithm", "data-pipeline", "settings-tuning",
                             "settings-tuning-bayesian"]
    for name in skill.names():
        found, fault = skill.load(name)
        assert fault is None and found["name"] == name and len(found["summary"]) > 40
        assert found["guidance"].get("all") and found["guidance"].get("writer") and found["guidance"].get("analyst")
        assert len(found["diagnose"]) >= 4 and set(found["stages"]) == {"early", "late"}       # what a result says to do; by stage
        assert found["title"] and found["objective"] and found["when"] and len(found["tags"]) >= 4 and found["domain"]
        assert skill.NAME.fullmatch(name), name                                                # specific, so the library can grow
        assert all(other in skill.names() for other in found["combines"] + found["conflicts"]), name
        assert name in menu.SKILLS and "`%s`" % name in menu.menu_markdown()
    assert skill.load(None) == (None, None) and skill.load("") == (None, None)
    assert "no skill named" in skill.load("nonesuch")[1]


def test_a_skill_is_laid_over_the_run_type_and_under_what_the_person_set():
    plain, _ = resolved()
    assert plain["strategy"]["mechanism"] == "lineage" and plain["_skill"] is None
    settings, sources = resolved(run__skill="efficiency")
    assert settings["strategy"]["mechanism"] == "pareto" and sources["strategy.mechanism"] == "skill model-efficiency"
    assert settings["strategy"]["second_metric"] == "parameters" and settings["_skill"]["name"] == "model-efficiency"
    assert settings["space"]["preset"] == "architecture_and_recipe" and sources["space.preset"] == "skill model-efficiency"
    assert settings["population"]["lineages"] == 3 and sources["population.lineages"] == "run type refine"      # what the skill leaves alone
    mine, sources = resolved(run__skill="efficiency", strategy__mechanism="archive")
    assert mine["strategy"]["mechanism"] == "archive" and sources["strategy.mechanism"] == "brief"
    tuned, _ = resolved(run__skill="tuning")
    assert tuned["space"]["preset"] == "settings_only" and tuned["variation"]["settings_by"] == "agent"     # an agent tunes
    assert resolved(run__skill="settings-tuning-bayesian")[0]["variation"]["settings_by"] == "tpe"               # or none does
    assert tuned["strategist"]["mode"] == "off" and tuned["schedule"]["phases"][0]["local"] == 1.0
    assert any("the skill needs" in w for w in form.warnings(settings))       # what the adapter must do
    broken, _ = resolved(run__skill="nonesuch")
    assert broken["_skill"] is None and any("no skill named" in w for w in form.warnings(broken))
    lines = form.plan_lines({k: dict(v) for k, v in dict(BASE, run={"type": "refine", "skill": "mechanistic"}).items()})
    assert any(line.startswith("Skill: model-mechanistic.") for line in lines)
    assert any("From the skill model-mechanistic:" in line for line in lines)


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
    assert skill.guidance(settings["_skill"], "writer")["guidance"] == "Prefer depthwise layers."
    assert "guidance" not in skill.guidance(settings["_skill"], "analyst")          # only the diagnoses are left for it
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
    assert told["name"] == "model-distillation" and "teacher-labelled augmentation" in told["guidance"]
    assert any("from scratch" in d["see"] for d in told["if_you_see"]) and "at_this_stage" not in told   # no stage without the budget
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
    assert controller.settings["_skill"]["name"] == "model-efficiency" and controller.settings["strategy"]["mechanism"] == "pareto"
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)


def test_the_report_says_what_the_skill_still_lacks():
    rows = [("R%d" % i, "L1", "new", None, 0.5 + i / 100, "a") for i in range(1, 5)]
    view = make_view(rows)
    wants, _ = skill.load("efficiency")
    assert any("`parameters`" in line for line in skill.missing(wants, view, []))
    for run in view.runs.values():
        run["performance"]["parameters"] = 1000
    measured = type(view)(view.runs, view.models, {}, "maximize", 0.01, 0)
    assert len(skill.missing(wants, measured, [])) == 2                               # the teacher and from-scratch rows are still missing
    assert skill.missing(wants, measured, [{"label": "teacher"}, {"label": "student from scratch"}]) == []
    taught, _ = skill.load("distillation")
    lacking = skill.missing(taught, view, [{"label": "Teacher ensemble (5 models)"}])
    assert len(lacking) == 1 and "from scratch" in lacking[0]
    assert skill.missing(taught, view, [{"label": "teacher"}, {"label": "student from scratch"}]) == []
    assert skill.missing(None, view, []) == []


def test_setup_suggests_a_skill_from_the_words_of_the_goal(tmp_path):
    folder = search(tmp_path)
    for goal, wanted in (("Distil the ensemble into a small student.", "model-distillation"),
                         ("Speed up this algorithm at the same output.", "algorithm-runtime"),
                         ("A family of models across sizes, the best at each.", "model-size-frontier"),
                         ("Improve the peak calling method.", "bioinformatics-algorithm"),
                         ("Make the preprocessing pipeline cheaper.", "data-pipeline"),
                         ("Fine-tune the pretrained model.", "model-finetuning"),
                         ("Members for an ensemble.", "model-ensemble-members"),
                         ("A better loss function and augmentation.", "model-training-recipe"),
                         ("Tune the learning rate and weight decay.", "settings-tuning"),
                         ("Make the model faster at the same accuracy.", "model-efficiency"),
                         ("An interpretable model whose filters are motifs.", "model-mechanistic"),
                         ("A biophysical model of binding.", "model-mechanistic"),
                         ("Get the best correlation on held-out data.", "model-performance")):
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
    folder = search(tmp_path, budget__evaluations=16, evaluation__allowance=150, run__skill="settings-tuning-bayesian", space__preset=None)
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


# --- the library: combining, a search's own copies, finding -----------------------------------------
def test_skills_are_merged_in_the_order_given_and_the_plan_says_where_they_differ():
    assert skill.wanted("distillation, model-size-frontier") == ["model-distillation", "model-size-frontier"]
    assert skill.wanted(["efficiency", "efficiency", "none"]) == ["model-efficiency"] and skill.wanted(None) == []
    settings, sources = resolved(run__skill=["model-distillation", "model-size-frontier"])
    both = settings["_skill"]
    assert both["name"] == "model-distillation + model-size-frontier" and both["parts"] == ["model-distillation", "model-size-frontier"]
    assert settings["space"]["preset"] == "architecture_and_recipe" and settings["strategy"]["mechanism"] == "archive"   # one from each
    assert sources["strategy.mechanism"] == "skill model-distillation + model-size-frontier"
    told = skill.guidance(both, "writer", used=0.8)
    assert "From the skill model-distillation:" in told["guidance"] and "From the skill model-size-frontier:" in told["guidance"]
    assert {d["skill"] for d in told["if_you_see"]} == {"model-distillation", "model-size-frontier"}
    assert "model-size-frontier:" in told["at_this_stage"] and "Improve the best design in each band" in told["at_this_stage"]
    assert "Put at least two designs" in skill.guidance(both, "writer", used=0.1)["at_this_stage"]
    assert both["needs"]["figures"] == ["parameters"] and both["needs"]["references"] == ["teacher", "from scratch"]
    assert both["clashes"] and both["clashes"][0]["setting"] == "report.columns" or not both["clashes"]
    # Two skills that set the same thing differently: the later stands, and the plan says so.
    clash, _ = resolved(run__skill="model-efficiency, model-size-frontier")
    assert clash["strategy"]["mechanism"] == "archive"
    notes = form.warnings(clash)
    assert any("strategy.mechanism" in n and "model-size-frontier stands" in n for n in notes)
    assert any("not meant to be combined" in n for n in notes)
    swapped, _ = resolved(run__skill="model-size-frontier, model-efficiency")
    assert swapped["strategy"]["mechanism"] == "pareto"
    assert "no skill named" in skill.combine("model-efficiency, nonesuch")[1]
    assert form.check_value("run.skill", ["a", "b"]) is None and form.check_value("run.skill", [1]) is not None


def test_a_search_gets_its_own_copy_of_each_skill_and_reads_that(tmp_path, capsys):
    folder = search(tmp_path)
    brief = form.load_brief(folder)
    form.put(brief, "run.skill", "model-efficiency, model-distillation")
    form.save_brief(folder, brief)
    assert main(["brief", folder, "--confirm", "Ada"]) == 0
    said = capsys.readouterr().out
    assert "its own copy of: model-efficiency, model-distillation" in said
    own = os.path.join(folder, "skills", "model-efficiency", "skill.yaml")
    assert os.path.isfile(own) and os.path.isfile(os.path.join(folder, "skills", "model-distillation", "skill.yaml"))
    assert skill.checkout("model-efficiency", folder) == []                       # never copied over an edited one
    assert skill.find("model-efficiency", folder) == os.path.dirname(own)        # the search's copy comes first
    assert skill.load("model-efficiency", folder)[0]["own"] and not skill.load("model-efficiency")[0]["own"]
    with open(own, encoding="utf-8") as handle:
        text = handle.read()
    with open(own, "w", encoding="utf-8") as handle:
        handle.write(text.replace("Design the student for efficiency;", "Never use attention. Design the student for efficiency;"))
    assert "Never use attention." in skill.load("model-efficiency", folder)[0]["guidance"]["writer"]
    assert "Never use attention." not in skill.load("model-efficiency")[0]["guidance"]["writer"]      # the library is untouched


def test_an_edit_to_a_skill_during_a_run_goes_on_the_record(tmp_path):
    folder = search(tmp_path, budget__evaluations=40, evaluation__allowance=150, audit__reviews="none", harness__level="minimal",
                    run__skill="model-performance")
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 2)
    own = os.path.join(folder, "skills", "model-performance", "skill.yaml")
    assert os.path.isfile(own)                                                   # copied when the run began
    assert not [e for e in controller.store.merged_list("ledger") if e["kind"] == "skill"]
    with open(own, encoding="utf-8") as handle:
        text = handle.read()
    with open(own, "w", encoding="utf-8") as handle:
        handle.write(text.replace("The aim is the best validation score.", "The aim is the best validation score. No attention."))
    os.utime(own, (1, 12345.0))
    controller.turn()
    edits = [e for e in controller.store.merged_list("ledger") if e["kind"] == "skill"]
    assert len(edits) == 1 and edits[0]["skills"] == ["model-performance"]
    assert edits[0]["before"]["model-performance"] != edits[0]["after"]["model-performance"]
    assert "No attention." in controller.settings["_skill"]["guidance"]["all"]
    controller.turn()
    assert len([e for e in controller.store.merged_list("ledger") if e["kind"] == "skill"]) == 1     # once per edit
    ask(folder, "t", {"kind": "set", "changes": {"run.skill": "model-performance, model-training-recipe"}, "by": "Ada"})
    controller.turn()
    assert os.path.isdir(os.path.join(folder, "skills", "model-training-recipe"))
    assert len([e for e in controller.store.merged_list("ledger") if e["kind"] == "skill"]) == 1     # a change of skills is a `set`
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)
    with open(os.path.join(folder, "runs", "t", "report.md"), encoding="utf-8") as handle:
        assert "the skill file(s) model-performance changed" in handle.read()


def test_the_library_can_be_listed_searched_and_read_by_a_program(tmp_path, capsys):
    import json
    assert [r["name"] for r in skill.search("pareto")][:1] == ["model-size-frontier"] or "model-size-frontier" in [
        r["name"] for r in skill.search("pareto")]
    assert [r["name"] for r in skill.search("faster pipeline")][0] == "data-pipeline"
    assert [r["name"] for r in skill.search("bioinformatics")][0] == "bioinformatics-algorithm"
    assert skill.search("zzzz") == []
    assert main(["skills"]) == 0
    listed = capsys.readouterr().out
    assert "MODEL" in listed and "BIOINFORMATICS" in listed and "data-pipeline" in listed
    assert main(["skills", "--search", "student teacher"]) == 0 and "model-distillation" in capsys.readouterr().out
    assert main(["skills", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert len(rows) == 13 and set(rows[0]) >= {"name", "title", "domain", "objective", "tags", "version", "sets", "needs", "digest"}
    page = skill.library_markdown()
    assert all("### %s" % name in page for name in skill.names()) and "The guide for this goal" in page
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "skill-library.md"),
              encoding="utf-8") as handle:
        assert handle.read() == page, "docs/skill-library.md is stale: regenerate it with `evoloop skills --markdown`"


def test_every_goal_has_a_guide_that_matches_its_skill(tmp_path):
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "guides")
    written = skill.write_guides(str(tmp_path))
    assert written == sorted("%s.md" % name for name in skill.names())
    for page in written:
        with open(os.path.join(str(tmp_path), page), encoding="utf-8") as fresh, open(os.path.join(root, page), encoding="utf-8") as kept:
            assert kept.read() == fresh.read(), "docs/guides/%s is stale: regenerate with `evoloop skills --guides docs/guides`" % page
    for name in skill.names():
        one = skill.load(name)[0]
        assert one["goal"] and one["why"] and one["reading"] and one["start"].get("run_type") in form.RUN_TYPES, name
        assert all(n in skill.names() for row in one["instead"] for n in skill.wanted(row["use"])), name
        page = skill.guide_markdown(name)
        for part in ("## What a good result looks like", "## Start here", "skill: %s" % name, "## Why this set-up", "## What your evaluator must report",
                     "set up this search", "Preview this search", "## What the agents are told"):
            assert part in page, (name, part)
    with open(os.path.join(os.path.dirname(root), "..", "mkdocs.yml"), encoding="utf-8") as handle:
        nav = handle.read()
    assert all("guides/%s.md" % name in nav for name in skill.names())            # every guide can be reached


def test_the_decision_page_and_the_readme_list_the_whole_library_and_say_it_can_grow():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for page in (os.path.join(root, "docs", "which-search.md"), os.path.join(root, "README.md")):
        with open(page, encoding="utf-8") as handle:
            text = handle.read()
        assert all("`%s`" % name in text for name in skill.names()), page            # every goal can be found
    with open(os.path.join(root, "docs", "skills.md"), encoding="utf-8") as handle:
        text = handle.read()
    assert "Writing your own" in text and "Adding a skill to the library" in text and "Combining skills" in text
    with open(os.path.join(root, "README.md"), encoding="utf-8") as handle:
        assert "study.json" in handle.read()                                          # and how the result is kept


def test_the_tuning_skill_has_an_agent_choose_each_trial(tmp_path):
    folder = search(tmp_path, budget__evaluations=10, evaluation__allowance=150, run__skill="settings-tuning", space__preset=None)
    controller = Controller(folder, "t", poll=0.1)
    assert controller.settings["variation"]["settings_by"] == "agent" and controller.settings["strategist"]["mode"] == "off"
    assert controller.run(max_seconds=300)
    runs = [r for r in controller.view().runs.values() if r.get("purpose", "search") in ("search", "trial")]
    writers = [c for c in controller.store.read("calls") if c["role"] == "writer"]
    assert writers and all("skill" in c["shown"] for c in writers)                # every trial was chosen by an agent shown the skill
    assert {r["history"]["move"] for r in runs if r["history"].get("move")} == {"settings_move"}
    assert len({r["model"] for r in runs}) == 1                                   # the structure never changed
    with open(os.path.join(folder, "runs", "t", "report.md"), encoding="utf-8") as handle:
        assert "Skill: settings-tuning." in handle.read()


def test_shrinking_a_model_is_set_up_as_distillation():
    one = skill.load("model-efficiency")[0]
    assert one["settings"]["space"]["preset"] == "architecture_and_recipe"       # the student and how it is trained are both searched
    assert one["needs"]["references"] == ["teacher", "from scratch"]
    assert "teacher" in one["guidance"]["all"] and "student" in one["guidance"]["writer"]
