"""Setting up by question and answer: the same questions in a terminal, for an agent, and as an HTML form."""
import copy
import json
import os
import re

import pytest

from evoloop import form, formpage, interview
from evoloop.cli import main

from helpers import EXAMPLE


@pytest.fixture(autouse=True)
def bare_machine(monkeypatch):
    """A machine with no Slurm, no GPU tool and no agent login, so that what is suggested does not depend on where the tests run."""
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def blank(tmp_path):
    folder = str(tmp_path / "s")
    os.makedirs(folder)
    form.save_brief(folder, copy.deepcopy(form.BLANK))
    return folder


def test_every_question_says_where_it_stands_and_gives_choices_as_choices():
    now = interview.state({})
    assert now["done"] == 0 and now["next"]["number"] == 1 and now["next"]["of"] == now["total"]
    assert [s["name"] for s in now["sections"]] == [s for s in interview.SECTIONS if any(q["section"] == s for q in now["questions"])]
    for q in now["questions"]:
        assert q["section"] in interview.SECTIONS and q["why"] and q["number"] >= 1
        if q["kind"] == "choice":
            assert len(q["choices"]) >= 2 and all(c["description"] for c in q["choices"])
    assert set(form.REQUIRED) <= {q["field"] for q in interview.QUESTIONS}        # nothing required is left unasked
    assert all(form.known(q["field"]) for q in interview.QUESTIONS)


def test_only_the_questions_that_apply_are_asked():
    brief = copy.deepcopy(form.BLANK)
    fields = lambda b: [q["field"] for q in interview.state(b)["questions"]]      # noqa: E731
    assert "compute.partition" not in fields(brief) and "run.description" not in fields(brief)
    form.put(brief, "compute.scheduler", "slurm")
    form.put(brief, "run.type", "custom")
    assert {"compute.partition", "compute.qos", "run.description"} <= set(fields(brief))
    form.put(brief, "agents.backend", "stub")
    assert not {"agents.default_model", "agents.effort", "budget.model_dollars"} & set(fields(brief))
    form.put(brief, "agents.backend", "anthropic_api")
    assert {"agents.default_model", "agents.effort", "budget.model_dollars"} <= set(fields(brief))
    form.put(brief, "agents.backend", "stub")       # with the stub there is nothing to cap, so the cap is not an open question
    assert "budget.model_dollars" not in [q["field"] for q in form.questions(brief)]


def answerer(said, replies):
    def ask(prompt):
        question = [line for line in said if line.endswith("?")][-1]
        for key, queue in replies.items():
            if key in question:
                return queue.pop(0) if len(queue) > 1 else queue[0]
        raise AssertionError("no reply prepared for: %s" % question)
    return ask


def test_the_terminal_walk_through(tmp_path):
    folder = blank(tmp_path)
    said = []
    replies = {"What is being improved": ["Find a better model."], "higher score better": ["1"], "may be trained in all": ["30"],
               "What kind of search": [""], "Which parts of the code": ["wrong", ""], "How much of the search": ["b", "3"],
               "How long is one training run": ["25"], "differ between two fits": ["0.01"], "about the baseline": [""],
               "at the same time": ["4"], "Where do the training jobs run": [""], "How are the agents called": [""],
               "When should the agents be reviewed": ["q"]}
    assert not interview.run(folder, answerer(said, replies), said.append)
    text = "\n".join(said)
    assert "Saved." in text and "Question 1 of" in text and "·  Goal" in text and "·  Budget" in text
    assert "Not accepted: answer with a number from 1 to" in text               # a wrong answer is asked again
    assert "<- suggested" in text and "suggested because with about 30 models" in text and "<- default" in text
    assert "left to the kind of search" in text
    brief = form.load_brief(folder)
    stated = form.given(brief)
    assert stated["objective.goal"] == "Find a better model." and stated["objective.direction"] == "maximize"
    assert stated["run.type"] == "refine"                                # Enter accepted the suggestion, which is now the answer
    assert stated["harness.autonomy"] == "agentic"                       # "b" went back a question, then came forward again
    assert "space.preset" not in stated and "space.preset" in brief["status"]["asked"]   # Enter kept a default: nothing written
    assert stated["budget.evaluations"] == 30 and stated["evaluation.allowance"] == 25 and stated["evaluation.noise"] == 0.01
    assert stated["baseline.mode"] == "train" and stated["compute.gpus"] == 4
    assert stated["compute.scheduler"] == "local" and stated["agents.backend"] == "stub"
    said.clear()
    assert interview.run(folder, lambda prompt: "", said.append)                # goes on from where it stopped
    assert "All" in said[-1] and interview.state(form.load_brief(folder))["next"] is None
    assert form.questions(form.load_brief(folder)) == []


def test_a_suggestion_is_shown_but_is_not_an_answer_until_it_is_left_or_picked(tmp_path, capsys):
    folder = blank(tmp_path)
    assert main(["brief", folder, "--suggest", "objective.direction=minimize", "--suggest", "evaluation.noise=0.004",
                 "--because", "the task text calls the score a loss"]) == 0
    brief = form.load_brief(folder)
    assert "objective.direction" not in form.given(brief)                       # proposed, not answered
    assert [q["field"] for q in form.questions(brief)].count("objective.direction") == 1   # still an open question
    with pytest.raises(SystemExit):
        main(["brief", folder, "--confirm", "Ada"])
    with pytest.raises(SystemExit):
        main(["brief", folder, "--suggest", "objective.direction=sideways"])   # a suggestion is checked like an answer
    capsys.readouterr()
    main(["brief", folder, "--answer", "objective.goal=g", "--next"])
    q = json.loads(capsys.readouterr().out)["question"]
    assert q["field"] == "objective.direction" and q["suggested"] == {"value": "minimize", "why": "the task text calls the score a loss", "by": "an agent"}
    assert main(["brief", folder, "--keep", "objective.direction"]) == 0        # the person left it: accepted
    assert form.given(form.load_brief(folder))["objective.direction"] == "minimize"
    assert main(["brief", folder, "--answer", "evaluation.noise=0.01"]) == 0     # or gave their own
    assert form.given(form.load_brief(folder))["evaluation.noise"] == 0.01


def test_best_guesses_from_the_machine_the_folder_and_the_answers(tmp_path, monkeypatch):
    folder = str(tmp_path / "ex")
    import shutil as real
    real.copytree(EXAMPLE, folder)
    brief = {"budget": {"evaluations": 200}, "agents": {"backend": "anthropic_api"}}
    made = interview.infer(folder, brief)
    assert made["compute.scheduler"] == "local" and made["baseline.mode"] == "train"
    assert made["run.type"] == "explore_then_exploit" and made["budget.model_dollars"] >= 1
    assert "agents.backend" not in made and "budget.evaluations" not in made    # never over what was answered
    assert "objective.goal" not in made and "evaluation.noise" not in made      # nothing is guessed without evidence
    why = brief["status"]["suggested"]["budget.model_dollars"]["why"]
    assert why.startswith("the estimate for this search runs to about $")
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/" + name if name in ("sbatch", "claude") else None)
    fresh = {}
    made = interview.infer(folder, fresh)
    assert made["compute.scheduler"] == "slurm" and made["agents.backend"] == "claude_code" and "compute.gpus" not in made


def test_an_agent_gets_one_question_at_a_time(tmp_path, capsys):
    folder = blank(tmp_path)
    seen, q = [], True
    answers = {"objective.goal": "better", "objective.direction": "minimize", "budget.evaluations": 50, "evaluation.allowance": 10,
               "evaluation.noise": 0.02, "compute.gpus": 2, "agents.backend": "anthropic_api"}
    for _ in range(40):
        capsys.readouterr()
        assert main(["brief", folder, "--next"]) == 0
        reply = json.loads(capsys.readouterr().out)
        q = reply["question"]
        if q is None:
            break
        seen.append(q["field"])
        assert reply["total"] == q["of"] and q["number"] <= q["of"] and "how_to_answer" in reply
        if q["field"] in answers:
            assert main(["brief", folder, "--answer", "%s=%s" % (q["field"], answers[q["field"]])]) == 0
        else:
            assert (q["suggested"] or not q["required"]) and main(["brief", folder, "--keep", q["field"]]) == 0
    assert q is None and len(seen) == len(set(seen)) >= 12                         # each asked once, in order
    assert seen[0] == "objective.goal" and seen.index("run.type") > seen.index("budget.evaluations")
    assert seen.index("budget.model_dollars") > seen.index("agents.backend")
    assert reply["done"] == reply["total"] and reply["how_to_answer"].startswith("all done")
    stated = form.given(form.load_brief(folder))
    assert stated["run.type"] == "explore_then_exploit" and stated["budget.model_dollars"] >= 1    # suggestions the person left
    assert main(["brief", folder, "--confirm", "Ada"]) == 0


def test_the_html_form_and_its_answers_file(tmp_path, capsys):
    folder = blank(tmp_path)
    assert main(["brief", folder, "--suggest", "objective.direction=maximize", "--because", "accuracy is reported"]) == 0
    assert main(["form", folder]) == 0
    page = open(os.path.join(folder, "setup_form.html"), encoding="utf-8").read()
    assert page.startswith("<!doctype html>") and page.count("<title>") == 1 and page.index("<title>") < page.index("</head>")
    assert "http://" not in page and "https://" not in page                        # nothing is loaded from anywhere
    data = json.loads(re.search(r"const DATA = (\{.*?\});\nconst DOWNLOAD", page, re.S).group(1))
    assert [q["field"] for q in data["questions"]] == interview.FIELDS and data["sections"] == interview.SECTIONS
    assert data["phases"]["explore_then_exploit"][0]["new"] == 0.65 and len(data["phases"]["refine"]) == 1
    by = {q["field"]: q for q in data["questions"]}
    assert by["objective.direction"]["suggested"]["why"] == "accuracy is reported"
    assert by["compute.scheduler"]["suggested"]["value"] == "local" and by["objective.goal"]["suggested"] is None
    assert "prefers-color-scheme: dark" in page and 'data-theme="dark"' in page
    # What the form hands back: the answers, and the defaults the person saw and left.
    answers = {"objective": {"goal": "better", "direction": "maximize"}, "run": {"type": "refine"},
               "budget": {"evaluations": 80}, "evaluation": {"allowance": 20, "noise": 0.01}, "baseline": {"mode": "train"},
               "compute": {"gpus": 2}, "agents": {"backend": "stub"}, "bogus": {"field": 1},
               "status": {"asked": ["space.preset", "audit.reviews"]}}
    path = str(tmp_path / "answers.json")
    json.dump(answers, open(path, "w"))
    capsys.readouterr()
    assert main(["brief", folder, "--import", path]) == 0
    out = capsys.readouterr().out
    assert "recorded: " in out and "not accepted: bogus.field" in out
    brief = form.load_brief(folder)
    assert form.given(brief)["run.type"] == "refine" and "space.preset" in brief["status"]["asked"]
    assert form.questions(brief) == [] and interview.state(brief)["done"] >= 9
    # A fragment for a host that wraps pages itself, with no download link (such hosts block downloads).
    fragment = formpage.fragment(form.load_brief(EXAMPLE), download=False)
    assert fragment.startswith("<title>") and "<html" not in fragment and "const DOWNLOAD = false;" in fragment
