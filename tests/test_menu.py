"""The menu and the documentation's reference pages cannot drift from what the brief accepts."""
import os
import re

from evoloop import form, menu
from evoloop.cli import main

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_option_and_every_field_is_explained():
    assert menu.missing() == []
    assert all(len(words) >= 8 for words in menu.FIELDS.values())


def test_the_reference_pages_are_what_the_code_writes():
    # Regenerate with: evoloop menu --markdown > docs/menu.md ; evoloop menu fields --markdown > docs/fields.md
    for page, text in (("menu.md", menu.menu_markdown()), ("fields.md", menu.fields_markdown())):
        with open(os.path.join(ROOT, "docs", page), encoding="utf-8") as handle:
            assert handle.read() == text, "docs/%s is stale: regenerate it" % page


def test_the_menu_command(capsys):
    assert main(["menu"]) == 0
    text = capsys.readouterr().out
    for name in list(form.MECHANISMS) + list(form.CROSS_KINDS) + list(form.RUN_TYPES) + list(form.SPACES):
        assert name in text
    assert "strategy.mechanism = \"archive\"" in text            # what the survey run type sets
    assert "about 30 evaluations" in text and "schedule.novelty = 0.3   [yes]" in text
    assert "evaluation.allowance = null   [yes, and a new period begins]" in text
    assert "objective.direction = null   [no]" in text
    assert main(["menu", "crossover"]) == 0
    only = capsys.readouterr().out
    assert "block_swap" in only and "RUN TYPES" not in only and "FIELDS" not in only


def test_every_page_in_the_navigation_exists_and_links_resolve():
    with open(os.path.join(ROOT, "mkdocs.yml"), encoding="utf-8") as handle:
        pages = re.findall(r":\s*([\w-]+\.md)\s*$", handle.read(), flags=re.M)
    assert len(pages) >= 11
    for page in pages:
        path = os.path.join(ROOT, "docs", page)
        assert os.path.isfile(path), page
        with open(path, encoding="utf-8") as handle:
            for target in re.findall(r"\]\(([\w-]+\.md)(?:#[\w-]+)?\)", handle.read()):
                assert os.path.isfile(os.path.join(ROOT, "docs", target)), "%s links to %s" % (page, target)
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as handle:
        for target in re.findall(r"\]\((docs/[\w-]+\.md)\)", handle.read()):
            assert os.path.isfile(os.path.join(ROOT, target)), target


def test_the_docs_name_only_fields_and_commands_that_exist():
    paths = set(form.flatten(form.DEFAULTS))
    groups = {p.split(".")[0] for p in paths}
    commands = {"init", "example", "brief", "plan", "menu", "guide", "run", "status", "report", "study", "set", "note",
                "withdraw", "steer", "stop", "review", "approve", "decline", "lineage", "estimate", "setup", "form",
                "rehash", "force", "import", "reference", "leaderboard", "show", "controller", "chat", "skills", "site"}
    for name in sorted(os.listdir(os.path.join(ROOT, "docs"))) + ["../README.md"]:
        if not name.endswith(".md"):
            continue
        with open(os.path.join(ROOT, "docs", name), encoding="utf-8") as handle:
            text = handle.read()
        for field in re.findall(r"`([a-z_]+\.[a-z_]+)`", text):
            if field.split(".")[0] in groups and field.split(".")[1] not in ("md", "json", "jsonl", "py", "yaml"):
                assert field in paths, "%s names the field %s, which does not exist" % (name, field)
        code = "\n".join(re.findall(r"```[a-z]*\n(.*?)```", text, flags=re.S))      # command lines in code blocks
        named = re.findall(r"^evoloop +([a-z]+)", code, flags=re.M) + re.findall(r"`evoloop +([a-z]+)", text)
        for command in named:
            assert command in commands, "%s names the command %s, which does not exist" % (name, command)


def test_the_plan_explorer_shows_what_the_code_would_do():
    import json
    data = menu.plans()
    assert data["run_types"] == list(form.RUN_TYPES) and len(data["plans"]) == len(data["run_types"]) * len(data["skills"]) * 4 * 3
    plain = data["plans"]["explore_then_exploit|||100"]
    assert plain["strategy"] == "lineage" and plain["phases"][0][:2] == [0.6, 0.65] and plain["calls"]["writer"] > 50
    tuned = data["plans"]["settings_only|settings-tuning-bayesian|agentic|100"]
    assert tuned["calls"] == {} and tuned["settings_by"] == "tpe" and tuned["space"] == "settings_only"   # agent-free at every level
    led = data["plans"]["settings_only|settings-tuning||100"]
    assert led["settings_by"] == "agent" and led["calls"]["writer"] > 50 and "strategist" not in led["calls"]
    small = data["plans"]["explore_then_exploit|model-efficiency||100"]
    assert small["strategy"] == "pareto" and small["second"] == "parameters" and any("skill needs" in data["warnings"][i] for i in small["warn"])
    with open(os.path.join(ROOT, "docs", "assets", "plans.json"), encoding="utf-8") as handle:
        assert json.load(handle) == json.loads(menu.plans_json()), "docs/assets/plans.json is stale: evoloop menu --plans > docs/assets/plans.json"
