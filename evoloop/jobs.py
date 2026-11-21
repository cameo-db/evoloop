"""Running a design: one job per training run, on this machine or through Slurm.

The contract with the project's code is the one of the earlier evoloop, so an existing adapter works
unchanged. The run command starts in a working copy (the base with the design's blocks spliced in, and
the adapter) with EVO_OUT_DIR, EVO_SEED, EVO_ALLOWANCE, EVO_CHECKPOINT_DIR, EVO_RESTART_COUNT set, and
with EVO_CONTINUE_FROM when it is to continue an earlier run's checkpoint. It writes `result.json`
({"valid", "score", "diagnostics", ...}) and may write `progress.jsonl`; it reads `control.json`.

A backend answers `state(run)` with one of: waiting, running, ended, machine (the machine, not the
model, ended it: run it again, uncharged). On Slurm each run is its own job, submitted with --requeue and
followed by its job id, so the controller can stop and start again without touching the jobs."""
from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from .store import read_json, write_json

MACHINE_EXIT = 75            # EX_TEMPFAIL: the adapter says the machine failed
CHECK_EXIT = 97              # the quick check failed and the design was not trained
LARGER_EXIT = 76             # the adapter says the design needs a larger GPU than the one it was given
CREDENTIALS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
INFRASTRUCTURE = ("NODE_FAIL", "BOOT_FAIL", "PREEMPTED", "DEADLINE", "TIMEOUT")
ACTIVE = ("PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "SUSPENDED", "REQUEUED", "REQUEUE_HOLD", "RESIZING",
          "SIGNALING", "STAGE_OUT", "STOPPED")


def environment(run: Dict[str, Any], out_dir: str, checkpoint_dir: str, settings: Dict[str, Any]) -> Dict[str, str]:
    env = {"EVO_OUT_DIR": out_dir, "EVO_SEED": str(run["seed"]), "EVO_CHECKPOINT_DIR": checkpoint_dir,
           "EVO_ALLOWANCE": str(run.get("allowance") or settings["evaluation"]["allowance"]),
           "EVO_RUN_ID": run["id"], "EVO_DATA_FRACTION": str(settings["data"]["fraction"]), "EVO_CPUS": str(settings["compute"]["cpus_per_job"]), "PYTHONUNBUFFERED": "1"}
    for name, value in (settings["evaluation"].get("variables") or {}).items():   # the adapter's own knobs, as the person set them
        env[str(name)] = str(value)
    if run.get("continue_from"):
        env["EVO_CONTINUE_FROM"] = run["continue_from"]
    if larger_available(run, settings["compute"]):
        # The adapter may exit LARGER_EXIT when the design is too large for the GPU it got: it is then moved to this type.
        env["EVO_LARGER_GPU"] = str(settings["compute"]["larger_gpu_type"])
    return env


def gpu_type_for(run: Dict[str, Any], compute: Dict[str, Any]) -> Optional[str]:
    """The GPU type this run asks for: the larger type once it was moved there, else the search's own (empty: any)."""
    return run.get("gpu_type") or compute.get("gpu_type") or None


def larger_available(run: Dict[str, Any], compute: Dict[str, Any]) -> bool:
    """Whether a design too large for its GPU can still be moved to a larger one."""
    larger = compute.get("larger_gpu_type")
    return bool(larger) and gpu_type_for(run, compute) != larger


def command(settings: Dict[str, Any]) -> str:
    """The quick check, when there is one, then the run command. A failed check exits 97 and trains nothing."""
    run = settings["run_command"]
    check = settings["evaluation"].get("quick_check")
    return "%s || exit %d\n%s" % (check, CHECK_EXIT, run) if check else run


def clean_env(extra: Dict[str, str]) -> Dict[str, str]:
    """Designs are model-written code: credentials do not go into their environment."""
    env = {k: v for k, v in os.environ.items() if not any(word in k.upper() for word in CREDENTIALS)}
    env.update(extra)
    return env


class Local:
    """Jobs as processes on this machine."""
    name = "local"

    def __init__(self) -> None:
        self.procs: Dict[str, subprocess.Popen] = {}
        self.cancelled: Dict[str, int] = {}

    @staticmethod
    def end(proc: subprocess.Popen) -> None:
        """Stop the job and everything it started: the job is the leader of its own process group."""
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    def submit(self, run: Dict[str, Any], workdir: str, env: Dict[str, str], settings: Dict[str, Any]) -> Dict[str, Any]:
        log = open(os.path.join(env["EVO_OUT_DIR"], "job.log"), "ab")
        # The controller's own Python comes first on the path, so `python` in the run command is the one in use.
        path = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")
        self.procs[run["id"]] = subprocess.Popen(["bash", "-c", command(settings)], cwd=workdir, env=clean_env(
            dict(env, EVO_RESTART_COUNT=str(run.get("restarts") or 0), PATH=path)), stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True)
        return {"backend": "local", "pid": self.procs[run["id"]].pid, "started": time.time()}

    def state(self, run: Dict[str, Any]) -> Dict[str, Any]:
        proc = self.procs.get(run["id"])
        if proc is None:
            if run["id"] in self.cancelled:   # it was cancelled here: it ended, the machine did not fail
                return {"state": "ended", "exit": self.cancelled[run["id"]]}
            # The controller was restarted: a local process does not outlive it.
            return {"state": "machine", "why": "the controller restarted and local jobs do not outlive it"}
        code = proc.poll()
        if code is None:
            return {"state": "running"}
        self.procs.pop(run["id"], None)
        if code == MACHINE_EXIT:
            return {"state": "machine", "why": "the run exited %d (the machine failed)" % MACHINE_EXIT}
        if code == LARGER_EXIT:
            return {"state": "larger"}
        return {"state": "ended", "exit": code}

    def cancel(self, run: Dict[str, Any]) -> None:
        proc = self.procs.pop(run["id"], None)
        if proc is not None:
            if proc.poll() is None:
                self.end(proc)
            self.cancelled[run["id"]] = -signal.SIGTERM

    def shutdown(self) -> None:
        for proc in self.procs.values():
            if proc.poll() is None:
                self.end(proc)


class Slurm:
    """Each run its own Slurm job, followed by its job id."""
    name = "slurm"

    def __init__(self, squeue_seconds: float = 30.0) -> None:
        self.squeue_seconds = squeue_seconds
        self.seen: Dict[str, str] = {}
        self.asked = 0.0

    def sh(self, argv: List[str], timeout: float = 60.0) -> str:
        env = {k: v for k, v in os.environ.items() if not k.startswith("SLURM_") or k == "SLURM_CONF"}
        done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
        if done.returncode != 0:
            raise RuntimeError("%s failed: %s" % (argv[0], (done.stderr or done.stdout).strip()[:300]))
        return done.stdout

    def pick_qos(self, compute: Dict[str, Any]) -> Optional[str]:
        """The first QoS with room: `qos` may be one name or a list in order of preference,
        [{name: a, max_jobs: 8}, {name: b}]; the last takes the rest."""
        qos = compute.get("qos")
        if not isinstance(qos, list):
            return qos
        entries = [q if isinstance(q, dict) else {"name": q} for q in qos]
        try:
            mine = self.sh(["squeue", "--me", "-h", "-o", "%q"]).split()
        except Exception:
            mine = []
        for entry in entries[:-1]:
            if entry.get("max_jobs") is None or mine.count(entry["name"]) < int(entry["max_jobs"]):
                return entry["name"]
        return entries[-1]["name"] if entries else None

    def submit(self, run: Dict[str, Any], workdir: str, env: Dict[str, str], settings: Dict[str, Any]) -> Dict[str, Any]:
        compute = settings["compute"]
        out = env["EVO_OUT_DIR"]
        qos = self.pick_qos(compute)
        lines = ["#!/bin/bash", "#SBATCH --job-name=evo_%s" % run["id"], "#SBATCH --output=%s" % os.path.join(out, "job.log"),
                 "#SBATCH --open-mode=append", "#SBATCH --requeue", "#SBATCH --export=NONE",
                 "#SBATCH --cpus-per-task=%d" % int(compute["cpus_per_job"]), "#SBATCH --mem=%dG" % int(compute["mem_gb"]),
                 "#SBATCH --time=%s" % compute["time_limit"]]
        if compute.get("partition"):
            lines.append("#SBATCH --partition=%s" % compute["partition"])
        if qos:
            lines.append("#SBATCH --qos=%s" % qos)
        if int(compute.get("gpus_per_job") or 0) > 0:
            gpu_type = gpu_type_for(run, compute)
            gres = "gpu:%s:%d" % (gpu_type, int(compute["gpus_per_job"])) if gpu_type else "gpu:%d" % int(compute["gpus_per_job"])
            lines.append("#SBATCH --gres=%s" % gres)
        lines.extend("#SBATCH %s" % extra for extra in compute.get("extra_sbatch") or [])
        lines.append("set -u")
        lines.extend("export %s=%s" % (k, shlex.quote(v)) for k, v in sorted(env.items()))
        # Slurm counts its own requeues of this job; the controller adds the times it started the run again itself.
        lines.append("export EVO_RESTART_COUNT=$(( ${SLURM_RESTART_COUNT:-0} + %d ))" % int(run.get("restarts") or 0))
        lines.append("export PATH=%s" % shlex.quote(os.environ.get("PATH", "/usr/bin:/bin")))
        lines.append('echo "{\\"t\\": $(date +%%s), \\"node\\": \\"$(hostname)\\", \\"restart\\": $EVO_RESTART_COUNT, '
                     '\\"gpu\\": \\"$(command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi --query-gpu=name,memory.total '
                     '--format=csv,noheader 2>/dev/null | grep -iv failed | head -1)\\"}" >> %s' % shlex.quote(os.path.join(out, "starts.jsonl")))
        lines.extend(compute.get("setup") or [])
        lines.append("cd %s" % shlex.quote(workdir))
        lines.append(command(settings))
        script = os.path.join(out, "job.sbatch")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        job_id = self.sh(["sbatch", "--parsable", script]).strip().split(";")[0]
        self.asked = 0.0
        return {"backend": "slurm", "job_id": job_id, "qos": qos, "submitted": time.time()}

    def refresh(self) -> None:
        if time.time() - self.asked < self.squeue_seconds:
            return
        try:
            text = self.sh(["squeue", "--me", "-h", "-o", "%i %T"])
        except Exception:
            return   # Slurm did not answer: keep what was last seen
        self.seen = dict(line.split()[:2] for line in text.splitlines() if len(line.split()) >= 2)
        self.asked = time.time()

    def state(self, run: Dict[str, Any]) -> Dict[str, Any]:
        self.refresh()
        job_id = str((run.get("job") or {}).get("job_id"))
        seen = self.seen.get(job_id)
        if seen in ("PENDING", "CONFIGURING", "REQUEUED", "REQUEUE_HOLD"):
            return {"state": "waiting"}
        if seen in ACTIVE:
            return {"state": "running"}
        if seen is None and time.time() - float((run.get("job") or {}).get("submitted") or 0) < self.squeue_seconds:
            return {"state": "waiting"}
        try:
            fields = self.sh(["sacct", "-j", job_id, "-n", "-P", "-X", "-o", "State,ExitCode"]).strip().splitlines()
            state, exit_code = (fields[0].split("|") + ["0:0"])[:2] if fields else ("UNKNOWN", "0:0")
        except Exception:
            state, exit_code = "UNKNOWN", "0:0"
        state = state.split()[0] if state else "UNKNOWN"
        code = int(exit_code.split(":")[0] or 0) if exit_code.split(":")[0].isdigit() else 0
        if state in ACTIVE:
            return {"state": "running"}
        if state in INFRASTRUCTURE or code == MACHINE_EXIT:
            return {"state": "machine", "why": "Slurm ended the job as %s (exit %d)" % (state, code)}
        if code == LARGER_EXIT:
            return {"state": "larger"}
        return {"state": "ended", "exit": code, "slurm_state": state}

    def cancel(self, run: Dict[str, Any]) -> None:
        job_id = (run.get("job") or {}).get("job_id")
        if job_id:
            try:
                self.sh(["scancel", str(job_id)])
            except Exception:
                pass

    def shutdown(self) -> None:
        """Nothing: the jobs go on, and the controller reattaches to them when it starts again."""


def make(settings: Dict[str, Any]) -> Any:
    return Slurm() if settings["compute"]["scheduler"] == "slurm" else Local()


def read_progress(out_dir: str, every: bool = False) -> List[Dict[str, Any]]:
    """The progress lines of a run. By default only those that carry a score; with `every`, cost-only lines too."""
    rows = []
    try:
        with open(os.path.join(out_dir, "progress.jsonl"), "r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and (every or (isinstance(row.get("metric"), (int, float)) and "step" in row)):
                    rows.append(row)
    except OSError:
        pass
    return rows


def tell(out_dir: str, action: str, allowance: Optional[float] = None) -> None:
    told = read_json(os.path.join(out_dir, "control.json"), {}) or {}
    told["action"] = action
    if allowance is not None:
        told["allowance"] = allowance
    write_json(os.path.join(out_dir, "control.json"), told)


def tail(out_dir: str, lines: int = 12) -> str:
    try:
        with open(os.path.join(out_dir, "job.log"), "r", encoding="utf-8", errors="replace") as handle:
            return "".join(handle.readlines()[-lines:])[-1500:]
    except OSError:
        return ""
