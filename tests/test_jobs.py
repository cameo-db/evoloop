"""How jobs are obtained and kept going: a GPU for each local job, one job per design or one block of
GPUs on a cluster, and a training run as a chain of short jobs that continue from a checkpoint."""
import json
import os
import shutil
import time

import pytest

from evoloop import evojob, form, jobs
from evoloop.cli import main
from evoloop.controller import Controller
from evoloop.store import SCORED

from helpers import run, search

HELPER = os.path.join(os.path.dirname(os.path.abspath(evojob.__file__)), "evojob.py")

# Six steps, in three starts: it saves after each step and leaves after the second and the fourth.
CHAIN = '''
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evojob
job = evojob.Job()
state = job.load_state() or {"step": 0}
for step in range(state["step"] + 1, 7):
    job.report(step, 1.0 / step)
    state["step"] = step
    job.save_state(state)
    if step in (2, 4):
        job.pause()
job.finish(score=1.0 / state["step"], diagnostics={"starts": job.restarts + 1})
'''


def test_a_slurm_time_limit_in_seconds():
    assert [jobs.seconds(t) for t in ("30", "90:30", "2:00:00", "1-12", "1-00:00:00")] == [1800, 5430, 7200, 129600, 86400]
    assert jobs.seconds("soon") is None and jobs.seconds(None) is None


def test_each_local_job_gets_a_gpu_of_its_own():
    backend = jobs.Local(gpus=["0", "1"])
    assert backend.take_gpus("R1", 1) == ["0"] and backend.take_gpus("R2", 1) == ["1"]
    assert backend.take_gpus("R3", 1) == ["0"]          # more jobs than GPUs: the least used one is shared
    backend.held.pop("R1")
    backend.held.pop("R3")
    assert backend.take_gpus("R4", 1) == ["0"]
    assert backend.take_gpus("R5", 0) == []             # a CPU job is given none
    assert jobs.Local(gpus=[]).take_gpus("R1", 1) == []  # nor is any job on a machine without GPUs


def test_a_local_job_is_started_on_its_gpu(tmp_path):
    settings = {"compute": {"gpus_per_job": 1, "larger_gpu_type": None, "cpus_per_job": 1},
                "evaluation": {"allowance": 1, "variables": {}, "quick_check": None}, "data": {"fraction": 1.0},
                "run_command": "echo $CUDA_VISIBLE_DEVICES > $EVO_OUT_DIR/gpu"}
    backend = jobs.Local(gpus=["3", "5"])
    for name in ("R1", "R2"):
        out = tmp_path / name
        out.mkdir()
        run_ = {"id": name, "seed": 0}
        job = backend.submit(run_, str(tmp_path), jobs.environment(run_, str(out), str(out), settings), settings)
        assert job["gpus"] == [{"R1": "3", "R2": "5"}[name]]
    for _ in range(100):
        if all(p.poll() is not None for p in backend.procs.values()):
            break
        time.sleep(0.05)
    assert (tmp_path / "R1" / "gpu").read_text().strip() == "3" and (tmp_path / "R2" / "gpu").read_text().strip() == "5"


def test_the_gpus_of_a_block_are_the_ones_the_job_was_given(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "2,3")
    assert jobs.local_gpus() == ["2", "3"]
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    assert jobs.local_gpus() == []


def test_a_slurm_job_is_told_when_it_ends(tmp_path, monkeypatch):
    settings = {"compute": {"gpu_type": None, "larger_gpu_type": None, "gpus_per_job": 1, "cpus_per_job": 2, "mem_gb": 8,
                            "time_limit": "2:00:00", "partition": None, "qos": None, "setup": [], "extra_sbatch": []},
                "evaluation": {"allowance": 10, "variables": {}, "quick_check": None}, "data": {"fraction": 1.0},
                "run_command": "python adapter/run.py"}
    backend = jobs.Slurm()
    monkeypatch.setattr(backend, "sh", lambda args: "123")
    run_ = {"id": "R1", "seed": 0}
    backend.submit(run_, str(tmp_path), jobs.environment(run_, str(tmp_path), str(tmp_path), settings), settings)
    assert "export EVO_DEADLINE=$(( $(date +%s) + 7200 ))" in (tmp_path / "job.sbatch").read_text()


def test_a_pause_and_a_time_limit_are_the_machine_not_the_model(monkeypatch):
    backend = jobs.Slurm()
    monkeypatch.setattr(backend, "refresh", lambda: None)
    backend.seen = {}
    for told in ("FAILED|77:0\n", "TIMEOUT|0:0\n", "PREEMPTED|0:0\n"):
        monkeypatch.setattr(backend, "sh", lambda args, told=told: told)
        assert backend.state({"job": {"job_id": "9", "submitted": 0}})["state"] == "machine"


def chained(tmp_path, text, **answers):
    folder = search(tmp_path, audit__reviews="none", limits={}, evaluation__screen_keep=1.0, **answers)
    shutil.copy(HELPER, os.path.join(folder, "adapter", "evojob.py"))
    with open(os.path.join(folder, "adapter", "chain.py"), "w") as handle:
        handle.write(text)
    return folder


def test_a_training_run_can_be_a_chain_of_short_jobs(tmp_path):
    # No restart without progress is allowed here, and every run still takes its three starts: one that got further
    # than the last is always followed by another.
    folder = chained(tmp_path, CHAIN, budget__evaluations=3, evaluation__allowance=6, compute__gpus=2,
                     compute__infrastructure_retries=0, run_command="python adapter/chain.py")
    controller, reason = run(folder, seconds=180)
    assert reason == "the budget of 3 evaluations is spent"
    scored = [r for r in controller.store.merged("runs").values() if r["performance"].get("status") in SCORED]
    assert len(scored) == 3
    for one in scored:
        assert one["restarts"] == 2 and one["stalled"] == 0 and one["reached"] == 4.0
        with open(os.path.join(controller.out_dir(one), "result.json")) as handle:
            assert json.load(handle)["diagnostics"]["starts"] == 3
        steps = [row["step"] for row in jobs.read_progress(controller.out_dir(one))]
        assert steps == [1, 2, 3, 4, 5, 6]               # it went on from its checkpoint: no step was trained twice


def test_a_run_that_gets_no_further_is_not_started_for_ever(tmp_path):
    folder = chained(tmp_path, "import sys\nsys.exit(77)\n", budget__evaluations=1, evaluation__allowance=6, compute__gpus=1,
                     compute__infrastructure_retries=2, budget__max_uncounted_failures=0, run_command="python adapter/chain.py")
    controller, reason = run(folder, seconds=120)
    failed = [r for r in controller.store.merged("runs").values() if r["performance"].get("status") == "failed"]
    assert failed and all(r["restarts"] == 2 for r in failed)
    assert "without it getting past step 0" in failed[0]["performance"]["reason"]


def test_the_helper_keeps_state_and_watches_the_clock(tmp_path, monkeypatch):
    monkeypatch.setenv("EVO_OUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("EVO_CHECKPOINT_DIR", str(tmp_path / "kept"))
    monkeypatch.setenv("EVO_ALLOWANCE", "5")
    monkeypatch.setenv("EVO_DEADLINE", str(time.time() + 3600))
    job = evojob.Job()
    assert job.load_state() is None and not job.out_of_time() and not job.should_stop()
    job.save_state({"step": 3, "best": 0.5})
    job.report(3, 0.5, parameters=10)
    assert evojob.Job().load_state() == {"step": 3, "best": 0.5}
    assert jobs.reached(job.out) == 3.0
    with open(os.path.join(job.out, "control.json"), "w") as handle:
        json.dump({"action": "stop", "allowance": 8}, handle)
    assert job.should_stop() and job.allowance == 8
    job.deadline = time.time() + 30                      # less than a step and a minute away
    assert job.out_of_time()
    with pytest.raises(SystemExit) as left:
        job.pause()
    assert left.value.code == jobs.PAUSE_EXIT == evojob.PAUSE_EXIT
    job.finish(score=float("nan"), parameters=10)
    with open(os.path.join(job.out, "result.json")) as handle:
        result = json.load(handle)
    assert result["valid"] is False and result["score"] is None and result["parameters"] == 10


def test_init_gives_an_evaluator_that_resumes(tmp_path):
    folder = str(tmp_path / "s")
    assert main(["init", folder]) == 0
    with open(os.path.join(folder, "adapter", "run.py")) as handle:
        text = handle.read()
    assert "job.load_state()" in text and "job.out_of_time()" in text and "job.pause()" in text
    compile(text, "run.py", "exec")
    with open(os.path.join(folder, "adapter", "evojob.py")) as theirs, open(HELPER) as ours:
        assert theirs.read() == ours.read()


def test_a_block_of_gpus_is_one_job_with_the_designs_inside(tmp_path, monkeypatch, capsys):
    folder = search(tmp_path, compute__scheduler="slurm", compute__allocation="block", compute__gpus=4,
                    compute__gpu_type="a100", compute__partition="gpu", compute__time_limit="8:00:00",
                    compute__cpus_per_job=4, compute__mem_gb=16)
    settings = form.resolve(form.load_brief(folder), folder=folder)[0]
    assert isinstance(jobs.make(settings), jobs.Local) and not jobs.make(settings).own_python
    assert isinstance(jobs.make(dict(settings, compute=dict(settings["compute"], allocation="per_design"))), jobs.Slurm)
    plan = "\n".join(form.plan_lines(form.load_brief(folder), folder=folder))
    assert "Slurm, one job that holds every GPU, partition gpu, 4 at once, 8:00:00 per job" in plan
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    with pytest.raises(RuntimeError, match="evoloop controller"):
        Controller(folder, "b").run(max_seconds=5)       # not from a terminal: the block is a job
    assert main(["controller", folder, "--name", "b"]) == 0
    with open(os.path.join(folder, "run_controller_b.sbatch")) as handle:
        script = handle.read()
    for line in ("#SBATCH --gres=gpu:a100:4", "#SBATCH --partition=gpu", "#SBATCH --time=8:00:00",
                 "#SBATCH --cpus-per-task=18", "#SBATCH --mem=68G", "export EVO_DEADLINE=$(( $(date +%s) + 28560 ))"):
        assert line in script


def test_one_job_per_design_keeps_a_light_controller(tmp_path):
    folder = search(tmp_path, compute__scheduler="slurm", compute__gpus=4, compute__partition="gpu")
    plan = "\n".join(form.plan_lines(form.load_brief(folder), folder=folder))
    assert "one job per design, submitted as GPUs come free" in plan
    assert main(["controller", folder, "--name", "p", "--partition", "cpu"]) == 0
    with open(os.path.join(folder, "run_controller_p.sbatch")) as handle:
        script = handle.read()
    assert "--gres" not in script and "#SBATCH --partition=cpu" in script and "#SBATCH --cpus-per-task=2" in script
    assert "EVO_DEADLINE" not in script
