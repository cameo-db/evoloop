"""The level of autonomy (harnessed, guided, agentic), and the estimate of what the agents will cost."""
import copy
import os

from evoloop import estimate, form
from evoloop.cli import main
from evoloop.store import Store

from helpers import EXAMPLE, search

BRIEF = {"objective": {"goal": "g", "direction": "maximize"}, "run": {"type": "explore_then_exploit"},
         "budget": {"evaluations": 100, "model_dollars": 500}, "evaluation": {"allowance": 10, "noise": 0.01},
         "baseline": {"mode": "skip"}, "compute": {"gpus": 4},
         "agents": {"backend": "anthropic_api", "default_model": "m", "prices": {"m": {"input": 3.0, "output": 15.0}}}}


def at(level, **extra):
    brief = copy.deepcopy(BRIEF)
    form.put(brief, "harness.autonomy", level)
    for key, value in extra.items():
        form.put(brief, key.replace("__", "."), value)
    return form.resolve(brief)


def test_what_each_level_sets():
    harnessed, sources = at("harnessed")
    assert (harnessed["harness"]["coordinator"], harnessed["strategist"]["mode"], harnessed["variation"]["settings_by"],
            harnessed["variation"]["proposals_per_slot"]) == ("code", "off", "sampler", 1)
    assert sources["strategist.mode"] == "autonomy harnessed"
    guided, _ = at("guided")
    assert (guided["harness"]["coordinator"], guided["strategist"]["mode"], guided["strategist"]["ask_first"]) == ("code", "act", ["strategy"])
    agentic, _ = at("agentic")
    assert (agentic["harness"]["coordinator"], agentic["strategist"]["mode"], agentic["strategist"]["ask_first"],
            agentic["variation"]["proposals_per_slot"]) == ("agent", "act", [], 3)
    assert agentic["strategist"]["min_new_share"] == 0.10            # the floor on exploration stays at every level
    # Left empty, the run type decides; what the brief sets itself is kept at every level.
    assert form.resolve(BRIEF)[1]["strategist.mode"] == "run type explore_then_exploit"
    kept, sources = at("agentic", strategist__mode="advise")
    assert kept["strategist"]["mode"] == "advise" and sources["strategist.mode"] == "brief"
    assert form.check_change("harness.autonomy", "agentic") is None and form.check_change("harness.autonomy", "wild") is not None


def test_more_autonomy_means_more_calls_and_the_estimate_says_how_many():
    levels = estimate.by_level(BRIEF)
    calls = {level: est["calls"][1] for level, est in levels.items()}
    assert calls["harnessed"] < calls["guided"] < calls["agentic"]
    dollars = {level: est["dollars"][1] for level, est in levels.items()}
    assert 0 < dollars["harnessed"] < dollars["guided"] < dollars["agentic"]
    assert set(levels["harnessed"]["roles"]) == {"writer", "analyst", "assessor"}
    assert set(levels["agentic"]["roles"]) == {"writer", "coordinator", "analyst", "strategist", "assessor"}
    agentic = levels["agentic"]
    assert agentic["roles"]["coordinator"]["calls"][0] == 100            # one a design
    assert agentic["roles"]["strategist"]["calls"] == [10.0, 15.0, 20.0]  # every 10 designs, more on plateaus
    for est in levels.values():                                           # every figure is a range, low <= expected <= high
        for row in est["roles"].values():
            assert row["calls"][0] <= row["calls"][1] <= row["calls"][2]
            assert row["dollars"][0] <= row["dollars"][1] <= row["dollars"][2]


def test_the_count_of_writer_calls_follows_the_schedule():
    settings, _ = at("harnessed", crossover__kinds=["block_swap"])
    share = estimate.mix(settings)
    assert abs(sum(share.values()) - 1.0) < 1e-9
    assert abs(share["new"] + share["novel"] - (0.6 * 0.65 + 0.4 * 0.15)) < 1e-9
    writer = estimate.calls(settings)["writer"][0]
    # New designs, and the local moves an agent writes (edits and ablations): block swaps and sampled settings need no call.
    local = share["local"] * (0.5 + 0.15)
    assert abs(writer - 100 * (share["new"] + share["novel"] + local)) < 1e-6


def test_without_a_price_the_estimate_gives_tokens_and_says_so():
    brief = copy.deepcopy(BRIEF)
    brief["agents"]["prices"] = {}
    est = estimate.estimate(form.resolve(brief)[0])
    assert est["dollars"] is None and not est["priced"] and est["tokens"][1] > 0
    text = "\n".join(estimate.lines(brief))
    assert "no price given" in text and "Give agents.prices" in text


def test_the_estimate_is_sized_from_the_search_folder(tmp_path):
    settings = form.resolve(BRIEF)[0]
    typical = estimate.estimate(settings)
    measured = estimate.estimate(settings, EXAMPLE)                      # a small project: far smaller calls
    assert measured["roles"]["writer"]["from"] == "sizes of the folder"
    assert measured["roles"]["writer"]["tokens_in_per_call"] < typical["roles"]["writer"]["tokens_in_per_call"]
    assert estimate.sizes(EXAMPLE, settings)["blocks"] == 1


def test_a_runs_own_calls_replace_the_guess(tmp_path):
    store = Store(str(tmp_path))
    for _ in range(5):
        store.append("calls", {"role": "writer", "cost_usd": 0.20, "tokens": {"in": 9000, "out": 2000}})
    seen = estimate.measured(store)
    assert seen["writer"]["calls"] == 5 and abs(seen["writer"]["dollars_per_call"] - 0.20) < 1e-9
    est = estimate.estimate(form.resolve(BRIEF)[0], None, seen)
    row = est["roles"]["writer"]
    assert row["from"] == "this run's 5 calls so far" and row["tokens_in_per_call"] == 9000
    assert abs(row["dollars"][1] - row["calls"][1] * 0.20) < 0.02
    assert est["roles"]["analyst"]["from"] != row["from"]                # roles with no calls yet keep the guess


def test_the_plan_and_the_estimate_command_show_the_levels_side_by_side(tmp_path, capsys):
    folder = search(tmp_path, agents__backend="anthropic_api", agents__default_model="m", budget__evaluations=100,
                    agents__prices={"m": {"input": 3.0, "output": 15.0}}, budget__model_dollars=1)
    capsys.readouterr()
    assert main(["plan", folder]) == 0
    plan = capsys.readouterr().out
    assert "What the agents will cost (an estimate, for 100 designs):" in plan
    assert "The same search at each level of autonomy" in plan
    for level in estimate.LEVELS:
        assert level in plan
    assert "above your cap of $1.00" in plan
    assert main(["estimate", folder]) == 0
    assert "harnessed" in capsys.readouterr().out
    # With the stub there is nothing to pay, and the plan says so.
    stub = search(tmp_path / "s")
    capsys.readouterr()
    main(["plan", stub])
    assert "What the agents will cost: nothing." in capsys.readouterr().out
    # During a run: what its calls have cost, and the rest projected from them.
    assert main(["run", stub, "--name", "r", "--max-seconds", "120"]) == 0
    capsys.readouterr()
    assert main(["estimate", stub, "--name", "r"]) == 0
    text = capsys.readouterr().out
    assert "Spent so far: $0.00" in text and "designs still to come" in text


def test_autonomy_can_change_during_a_run_and_the_ledger_says_what_moved(tmp_path):
    from evoloop.controller import Controller
    from helpers import ask
    folder = search(tmp_path, budget__evaluations=12, evaluation__allowance=150, audit__reviews="none")
    controller = Controller(folder, "t", poll=0.2)
    controller.begin()
    ask(folder, "t", {"kind": "set", "changes": {"harness.autonomy": "harnessed"}, "by": "Ada"})
    controller.turn()
    assert controller.settings["strategist"]["mode"] == "off" and controller.settings["variation"]["settings_by"] == "sampler"
    entry = [e for e in controller.store.merged_list("ledger") if e["kind"] == "set"][0]
    assert entry["also_changed"]["strategist.mode"] == ["act", "off"]
    ask(folder, "t", {"kind": "set", "changes": {"harness.autonomy": "agentic"}, "by": "Ada"})
    controller.turn()
    assert controller.settings["harness"]["coordinator"] == "agent" and controller.settings["strategist"]["mode"] == "act"
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)
