"""The brief: what is asked, where each setting comes from, what may change during a run."""
import copy

import pytest

from evoloop import form


def filled():
    brief = copy.deepcopy(form.BLANK)
    for key, value in {"objective.goal": "g", "objective.direction": "maximize", "run.type": "explore_then_exploit",
                       "budget.evaluations": 100, "evaluation.allowance": 10, "evaluation.noise": 0.01,
                       "baseline.mode": "train", "compute.gpus": 2, "agents.backend": "stub",
                       "budget.model_dollars": 0}.items():
        form.put(brief, key, value)
    return brief


def test_empty_required_fields_become_questions():
    asks = form.questions(copy.deepcopy(form.BLANK))
    assert {a["field"] for a in asks} == set(form.REQUIRED)
    assert all(a["required"] and a["question"] for a in asks)
    assert form.questions(filled()) == []


def test_custom_run_type_asks_for_a_description():
    brief = filled()
    form.put(brief, "run.type", "custom")
    assert [a["field"] for a in form.questions(brief)] == ["run.description"]


def test_a_setting_says_where_it_came_from():
    brief = filled()
    form.put(brief, "population.lineages", 5)
    settings, sources = form.resolve(brief)
    assert settings["population"]["lineages"] == 5 and sources["population.lineages"] == "brief"
    assert sources["variation.proposals_per_slot"].startswith("guidance for about 100")
    assert sources["strategy.tournament_size"] == "default"
    form.put(brief, "run.type", "survey")
    settings, sources = form.resolve(brief)
    assert settings["strategy"]["mechanism"] == "archive" and sources["strategy.mechanism"] == "run type survey"


@pytest.mark.parametrize("evaluations,mechanism,proposals", [(30, "greedy", 4), (100, "lineage", 3), (300, "lineage", 2),
                                                             (2000, "archive", 1)])
def test_guidance_by_budget(evaluations, mechanism, proposals):
    brief = filled()
    form.put(brief, "budget.evaluations", evaluations)
    form.put(brief, "run.type", "custom")
    form.put(brief, "run.description", "my own")
    settings, _ = form.resolve(brief)
    assert settings["strategy"]["mechanism"] == mechanism       # with no run type to say otherwise, the guidance decides
    assert settings["variation"]["proposals_per_slot"] == proposals


@pytest.mark.parametrize("evaluations", [30, 100, 300, 2000])
def test_a_named_run_type_keeps_its_strategy_at_any_budget(evaluations):
    brief = filled()
    form.put(brief, "budget.evaluations", evaluations)
    settings, sources = form.resolve(brief)
    assert settings["strategy"]["mechanism"] == "lineage" and settings["harness"]["level"] == "full"
    assert sources["strategy.mechanism"] == "run type explore_then_exploit"
    suggested = form.guidance_for(evaluations)[1].get("strategy", {}).get("mechanism")
    assert any("guidance suggests" in w for w in form.warnings(settings)) == bool(suggested and suggested != "lineage")


def test_values_of_the_wrong_kind_are_refused():
    assert form.check_change("evaluation.seed", "abc") is not None
    assert form.check_change("evaluation.seed", 3) is None
    assert form.check_change("evaluation.screen_keep", 0) is not None
    assert form.check_change("variation.step_adaptation", "yes") is not None
    assert form.check_change("crossover.kinds", "graft") is not None
    assert form.check_change("compute.time_limit", 30) is not None
    assert form.check_change("compute.qos", [{"name": "a", "max_jobs": 4}, {"name": "b"}]) is None
    assert form.check_change("notes", ["x"]) is not None                 # notes are made with `evoloop note`
    for dead in ("strategy.inner", "compute.python", "audit.scorecard", "audit.review_on_stall"):
        assert not form.known(dead)


def test_an_unpriced_model_is_warned_about():
    brief = filled()
    form.put(brief, "agents.backend", "anthropic_api")
    form.put(brief, "agents.default_model", "some-model")
    form.put(brief, "budget.model_dollars", 50)
    assert any("no price is given for some-model" in w for w in form.warnings(form.resolve(brief)[0]))
    form.put(brief, "agents.prices", {"some-model": {"input": 3, "output": 15}})
    assert not any("no price" in w for w in form.warnings(form.resolve(brief)[0]))


def test_default_schedule_is_the_agreed_one():
    settings, _ = form.resolve(filled())
    early, late = settings["schedule"]["phases"]
    assert (early["until"], early["new"], early["cross"], early["local"]) == (0.6, 0.65, 0.10, 0.25)
    assert (late["new"], late["cross"], late["local"]) == (0.15, 0.25, 0.60)


def test_the_ledger_overrides_the_brief_and_counts_periods():
    brief = filled()
    ledger = [{"kind": "set", "key": "schedule.novelty", "value": 0.9, "by": "P", "id": "S1", "status": "applied"},
              {"kind": "set", "key": "evaluation.allowance", "value": 20, "by": "P", "id": "S2", "status": "applied",
               "new_period": True},
              {"kind": "set", "key": "population.lineages", "value": 2, "by": "P", "id": "S3", "status": "refused"},
              {"kind": "note", "text": "no attention", "id": "S4", "status": "active"},
              {"kind": "note", "text": "old", "id": "S5", "status": "withdrawn"}]
    settings, sources = form.resolve(brief, ledger)
    assert settings["schedule"]["novelty"] == 0.9 and "S1" in sources["schedule.novelty"]
    assert settings["_period"] == 1 and settings["evaluation"]["allowance"] == 20
    assert settings["population"]["lineages"] != 2
    assert [n["id"] for n in settings["notes"]] == ["S4"]


def test_what_may_change_during_a_run():
    assert form.check_change("schedule.novelty", 0.5) is None
    assert form.check_change("budget.evaluations", 300) is None
    assert form.check_change("strategy.mechanism", "archive") is None
    assert form.check_change("space.preset", "module") is None
    assert form.check_change("compute.time_limit", "1-00:00:00") is None
    assert form.check_change("evaluation.allowance", 50) is None and form.starts_period("evaluation.allowance")
    assert "cannot change during a run" in form.check_change("objective.direction", "minimize")
    assert "cannot change during a run" in form.check_change("data.accession", "x")
    assert form.check_change("schedule.novelty", 3) is not None
    assert form.check_change("no.such.setting", 1) is not None


def test_phases_must_sum_to_one():
    assert form.check_phases([{"until": 1.0, "new": 0.5, "cross": 0.2, "local": 0.3}]) is None
    assert form.check_phases([{"until": 1.0, "new": 0.5, "cross": 0.2, "local": 0.2}]) is not None
    assert form.check_phases([{"until": 0.5, "new": 1, "cross": 0, "local": 0}]) is not None


def test_review_schedule_options():
    for name, points in (("none", []), ("halfway", [0.5, 1.0]), ("thirds", [0.33, 0.67, 1.0]),
                         ("quarterly", [0.25, 0.5, 0.75, 1.0])):
        brief = filled()
        form.put(brief, "audit.reviews", name)
        assert form.review_points(form.resolve(brief)[0]) == points
    brief = filled()
    form.put(brief, "audit.reviews", [0.4, 0.1])
    assert form.review_points(form.resolve(brief)[0]) == [0.1, 0.4]
    assert form.check_value("audit.reviews", "weekly") is not None


def test_warnings_flag_mismatches_without_refusing():
    brief = filled()
    form.put(brief, "budget.evaluations", 30)
    form.put(brief, "run.type", "survey")
    notes = form.warnings(form.resolve(brief)[0])
    assert any("archive" in n for n in notes)
    assert form.problems(brief) == []


def test_unknown_field_is_a_problem_and_confirmation_tracks_the_content(tmp_path):
    brief = filled()
    form.save_brief(str(tmp_path), brief)
    confirmed = form.confirm(str(tmp_path), "Ada")
    assert form.confirmed(confirmed)
    form.put(confirmed, "budget.evaluations", 200)
    assert not form.confirmed(confirmed)     # changed after it was agreed
    form.put(brief, "nonsense.field", 1)
    assert form.problems(brief) == ["nonsense.field is not a field of the brief"]
