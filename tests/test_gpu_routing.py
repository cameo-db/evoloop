"""A design too large for the GPU it got is moved to `compute.larger_gpu_type`, uncharged, once (2026-11-21)."""
from evoloop import jobs
from evoloop.store import SCORED

from helpers import run, search

# Exits 76 while the job is told it may ask for a larger GPU, else trains as usual.
ASKS_FOR_LARGER = '[ -n "${EVO_LARGER_GPU:-}" ] && exit 76; python adapter/run.py'


def test_the_type_a_run_asks_for():
    compute = {"gpu_type": None, "larger_gpu_type": "h100"}
    assert jobs.gpu_type_for({}, compute) is None
    assert jobs.larger_available({}, compute)
    assert jobs.gpu_type_for({"gpu_type": "h100"}, compute) == "h100"
    assert not jobs.larger_available({"gpu_type": "h100"}, compute)
    assert not jobs.larger_available({}, {"gpu_type": "v100", "larger_gpu_type": None})


def test_the_job_script_asks_for_the_larger_type(tmp_path, monkeypatch):
    settings = {"compute": {"gpu_type": None, "larger_gpu_type": "h100", "gpus_per_job": 1, "cpus_per_job": 2, "mem_gb": 8,
                            "time_limit": "1:00:00", "partition": "gpuq", "qos": None, "setup": [], "extra_sbatch": []},
                "evaluation": {"allowance": 10, "variables": {}, "quick_check": None}, "data": {"fraction": 1.0},
                "run_command": "python adapter/run.py"}
    backend = jobs.Slurm()
    monkeypatch.setattr(backend, "sh", lambda args: "123")
    texts = []
    for run_ in ({"id": "R1", "seed": 0}, {"id": "R2", "seed": 0, "gpu_type": "h100"}):
        out = tmp_path / run_["id"]
        out.mkdir()
        env = jobs.environment(run_, str(out), str(out), settings)
        backend.submit(run_, str(tmp_path), env, settings)
        texts.append((out / "job.sbatch").read_text())
    assert "--gres=gpu:1\n" in texts[0] and "EVO_LARGER_GPU=h100" in texts[0]
    assert "--gres=gpu:h100:1" in texts[1] and "EVO_LARGER_GPU" not in texts[1]


def test_a_slurm_exit_76_is_a_move_not_a_failure(monkeypatch):
    backend = jobs.Slurm()
    monkeypatch.setattr(backend, "refresh", lambda: None)
    backend.seen = {}
    monkeypatch.setattr(backend, "sh", lambda args: "FAILED|76:0\n")
    assert backend.state({"job": {"job_id": "9", "submitted": 0}})["state"] == "larger"


def test_every_design_moves_once_and_is_charged_once(tmp_path):
    folder = search(tmp_path, budget__evaluations=4, evaluation__allowance=150, compute__gpus=2, audit__reviews="none",
                    compute__larger_gpu_type="big", run_command=ASKS_FOR_LARGER)
    controller, reason = run(folder, seconds=180)
    assert reason == "the budget of 4 evaluations is spent"
    runs = list(controller.store.merged("runs").values())
    scored = [r for r in runs if r["performance"].get("status") in SCORED]
    assert len(scored) == 4
    assert all(r.get("gpu_type") == "big" and r["moved_to_larger_gpu"]["to"] == "big" for r in scored)
    assert not any(r["performance"].get("status") == "failed" for r in runs)


def test_with_no_larger_type_the_exit_is_a_failure(tmp_path):
    folder = search(tmp_path, budget__evaluations=2, evaluation__allowance=150, compute__gpus=1, audit__reviews="none",
                    run_command="exit 76")
    controller, reason = run(folder, seconds=120)
    failed = [r for r in controller.store.merged("runs").values() if r["performance"].get("status") == "failed"]
    assert failed and not any(r.get("moved_to_larger_gpu") for r in failed)
