"""The site file: what is particular to the machine, kept out of the brief."""
import os

import pytest
import yaml

from evoloop import form, site
from evoloop.cli import main
from evoloop.controller import Controller

from helpers import ask, search
from test_loop import drive, scored

SITE = {"name": "our-cluster",
        "compute": {"scheduler": "local", "partition": "gpu", "qos": [{"name": "normal", "max_jobs": 4}, {"name": "low"}],
                    "setup": ["module load cuda"], "extra_sbatch": ["--account=lab"], "time_limit": "0-12:00:00"},
        "rules": ["Do not train on the login node."], "forbid": {"qos": ["urgent"], "partition": ["debug"]}}


def put_site(folder, **changes):
    with open(os.path.join(folder, "site.yaml"), "w", encoding="utf-8") as handle:
        yaml.safe_dump(dict(SITE, **changes), handle)
    os.utime(os.path.join(folder, "site.yaml"), (1, os.path.getmtime(os.path.join(folder, "site.yaml")) + 7))


def test_the_machine_s_settings_come_from_its_site_file_and_the_brief_still_wins(tmp_path, monkeypatch):
    folder = search(tmp_path)
    monkeypatch.delenv("EVOLOOP_SITE")
    monkeypatch.setenv("HOME", str(tmp_path))                 # no site file of the machine running the tests
    brief = form.load_brief(folder)
    plain, _ = form.resolve(brief, [], folder)
    assert plain["_site"] is None and plain["compute"]["partition"] is None
    put_site(folder)
    settings, sources = form.resolve(brief, [], folder)
    assert settings["_site"]["name"] == "our-cluster" and settings["compute"]["partition"] == "gpu"
    assert sources["compute.partition"] == "site our-cluster" and settings["compute"]["setup"] == ["module load cuda"]
    assert settings["compute"]["gpus"] == 3 and sources["compute.gpus"] == "brief"                 # the brief's own value stands
    form.put(brief, "compute.partition", "bigmem")
    assert form.resolve(brief, [], folder)[0]["compute"]["partition"] == "bigmem"
    glance = "\n".join(form.at_a_glance(settings))
    assert "(site file: our-cluster)" in glance and "Site rule:       Do not train on the login node." in glance
    # Elsewhere: named by the environment, then in the home folder; `none` switches site files off.
    os.remove(os.path.join(folder, "site.yaml"))
    home = tmp_path / ".config" / "evoloop"
    home.mkdir(parents=True)
    (home / "site.yaml").write_text(yaml.safe_dump(dict(SITE, name="home-cluster")))
    assert form.resolve(brief, [], folder)[0]["_site"]["name"] == "home-cluster"
    named = tmp_path / "elsewhere.yaml"
    named.write_text(yaml.safe_dump(dict(SITE, name="named-cluster")))
    monkeypatch.setenv("EVOLOOP_SITE", str(named))
    assert form.resolve(brief, [], folder)[0]["_site"]["name"] == "named-cluster"
    monkeypatch.setenv("EVOLOOP_SITE", "none")
    assert form.resolve(brief, [], folder)[0]["_site"] is None


def test_what_a_machine_forbids_is_refused_by_code(tmp_path, monkeypatch):
    monkeypatch.delenv("EVOLOOP_SITE")
    monkeypatch.setenv("HOME", str(tmp_path))
    folder = search(tmp_path, budget__evaluations=30, evaluation__allowance=150, audit__reviews="none", harness__level="minimal")
    put_site(folder)
    controller = Controller(folder, "t", poll=0.2)
    drive(controller, lambda v: len(scored(v)) >= 1)
    ask(folder, "t", {"kind": "set", "changes": {"compute.qos": "urgent"}, "by": "Ada"})
    ask(folder, "t", {"kind": "set", "changes": {"compute.qos": [{"name": "low"}, {"name": "urgent"}]}, "by": "Ada"})
    ask(folder, "t", {"kind": "set", "changes": {"compute.qos": "low"}, "by": "Ada"})
    controller.turn()
    sets = [e for e in controller.store.merged_list("ledger") if e["kind"] == "set"]
    assert [e["status"] for e in sets] == ["refused", "refused", "applied"] and "forbids it" in sets[0]["why"]
    assert controller.settings["compute"]["qos"] == "low"
    ask(folder, "t", {"kind": "stop", "by": "Ada"})
    controller.run(max_seconds=120)
    # A brief that asks for it does not start.
    other = search(tmp_path / "b", compute__partition="debug")
    put_site(other)
    with pytest.raises(form.BriefError) as refused:
        Controller(other, "t", poll=0.2).begin()
    assert "partition debug is not to be used on our-cluster" in str(refused.value)
    # A site file that cannot be used stops the run too, with the reason; it is never half-applied.
    for bad, said in (({"compute": {"queue": "x"}}, "not a compute setting"), ({"forbid": {"account": ["x"]}}, "forbid must map"),
                      ({"colour": "blue"}, "unknown entries")):
        assert said in site.check(dict(SITE, **bad))


def test_a_site_file_is_drafted_from_what_the_machine_reports(tmp_path, capsys, monkeypatch):
    answers = {"scontrol": "ClusterName             = bigiron\nOther = 1\n",
               "sinfo": "cpu*|up|7-00:00:00|(null)|40\ngpu|up|2-00:00:00|gpu:a100:4|10\ngpu|up|2-00:00:00|gpu:v100:8|6\ndebug|down|1:00:00|gpu:2|1\n",
               "sacctmgr": "normal\nlow\nurgent\n", "nvidia-smi": ""}
    found = site.detect(run=lambda argv: answers.get(argv[0]), which=lambda name: "/usr/bin/" + name if name in ("sbatch",) else None)
    assert found["scheduler"] == "slurm" and found["name"] == "bigiron" and found["qos"] == ["low", "normal", "urgent"]
    assert [p["name"] for p in found["partitions"]] == ["cpu", "gpu", "debug"] and found["gpu_types"] == ["a100", "v100"]
    text = site.draft(found)
    made = yaml.safe_load(text)
    assert site.check(made) is None                                            # the draft is itself a usable site file
    assert made["compute"]["partition"] == "gpu" and made["compute"]["scheduler"] == "slurm" and made["name"] == "bigiron"
    assert "a100, v100" in text and "low, normal, urgent" in text and made["compute"]["time_limit"] == "2-00:00:00"
    alone = site.detect(run=lambda argv: "GPU 0: X\nGPU 1: X\n" if argv[0] == "nvidia-smi" else None,
                        which=lambda name: "/usr/bin/" + name if name in ("nvidia-smi", "qsub") else None)
    assert alone["scheduler"] == "local" and alone["local_gpus"] == 2 and "qsub" in alone["notes"][0]
    assert yaml.safe_load(site.draft(alone))["compute"] == {"scheduler": "local", "gpus": 2}
    monkeypatch.setenv("HOME", str(tmp_path))
    assert main(["site"]) == 0 and "No site file is in use" in capsys.readouterr().out
