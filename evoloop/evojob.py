"""Helpers for an evaluator (adapter/run.py). No dependencies: `evoloop init` copies this file into
adapter/, so the evaluator can `import evojob` in any environment.

A training run may be ended before it is done: the job reaches its time limit, the cluster preempts it,
or the machine fails. evoloop then submits the run again, uncharged, as long as each start gets further
than the last. For that the evaluator saves its state as it goes and picks it up when it starts again:

    job = evojob.Job()
    state = job.load_state() or {"epoch": 0, "best": None}      # None on the first start
    # ...build the model; if state["epoch"] > 0, load the weights saved under job.checkpoints...
    for epoch in range(state["epoch"] + 1, int(job.allowance) + 1):
        # ...train one epoch, compute the validation score `val`...
        job.report(epoch, val)                                   # progress: early stopping and the status use it
        # ...save the weights under job.checkpoints...
        state = {"epoch": epoch, "best": val if state["best"] is None else max(state["best"], val)}
        job.save_state(state)
        if job.should_stop():                                    # the search asked this run to end: score what there is
            break
        if job.out_of_time():                                    # the time limit is near, or the job was told to end
            job.pause()                                          # leaves; the run is submitted again and continues
    job.finish(score=state["best"], parameters=n)

With this in place a job can ask for a short time limit, which starts sooner on a busy cluster."""
from __future__ import annotations

import json
import math
import os
import signal
import sys
import time
from typing import Any, Dict, Optional

PAUSE_EXIT = 77              # the run saved its state and asks to be continued
MACHINE_EXIT = 75            # the machine failed, not the model: run it again
LARGER_EXIT = 76             # the design needs a larger GPU than the one it was given


class Job:
    def __init__(self, grace_seconds: float = 25.0) -> None:
        env = os.environ
        self.out = env["EVO_OUT_DIR"]
        self.checkpoints = env.get("EVO_CHECKPOINT_DIR") or os.path.join(self.out, "checkpoints")
        self.seed = int(float(env.get("EVO_SEED", "0")))
        self.allowance = float(env.get("EVO_ALLOWANCE", "0") or 0)
        self.data_fraction = float(env.get("EVO_DATA_FRACTION", "1") or 1)
        self.restarts = int(float(env.get("EVO_RESTART_COUNT", "0") or 0))
        self.continue_from = env.get("EVO_CONTINUE_FROM") or None
        self.parent_checkpoints = env.get("EVO_PARENT_CHECKPOINT_DIR") or None
        self.larger_gpu = env.get("EVO_LARGER_GPU") or None
        self.deadline = float(env["EVO_DEADLINE"]) if env.get("EVO_DEADLINE") else None
        os.makedirs(self.out, exist_ok=True)
        os.makedirs(self.checkpoints, exist_ok=True)
        self.told_to_end: Optional[float] = None
        self._grace = grace_seconds
        self._last = time.time()
        self._longest = 0.0
        for name in ("SIGTERM", "SIGUSR1"):
            try:      # a scheduler says a job is about to end with one of these, some seconds before it kills it
                signal.signal(getattr(signal, name), self._told)
            except (ValueError, AttributeError, OSError):
                pass      # not the main thread, or no such signal here: the time limit is still watched

    def _told(self, number: int, frame: Any) -> None:
        if self.told_to_end is None:
            self.told_to_end = time.time()
            try:      # the training loop gets this long to reach out_of_time(); then the process leaves by itself
                signal.signal(signal.SIGALRM, lambda *_: os._exit(128 + number))
                signal.alarm(max(1, int(self._grace)))
            except (ValueError, AttributeError, OSError):
                pass

    # --- state kept between starts -----------------------------------------------------------------
    def path(self, name: str) -> str:
        """A file in the folder kept for this run across starts: put weights and optimizer state there."""
        return os.path.join(self.checkpoints, name)

    def load_state(self) -> Optional[Dict[str, Any]]:
        """What `save_state` last wrote, or None when this run has not saved anything yet."""
        try:
            with open(self.path("state.json"), "r", encoding="utf-8") as handle:
                state = json.load(handle)
        except (OSError, ValueError):
            return None
        return state if isinstance(state, dict) else None

    def save_state(self, state: Dict[str, Any]) -> None:
        """Small facts to continue from (the epoch reached, the best score so far), written in one step so
        that a job killed while saving leaves the earlier state whole. Save the weights before calling it."""
        tmp = self.path("state.json.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        os.replace(tmp, self.path("state.json"))

    # --- talking with the search -------------------------------------------------------------------
    def report(self, step: float, metric: Optional[float] = None, **more: Any) -> None:
        """One line of progress. `metric` is the validation score at this step, when there is one."""
        row: Dict[str, Any] = dict(more, step=step)
        if metric is not None:
            row["metric"] = float(metric)
        with open(os.path.join(self.out, "progress.jsonl"), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        now = time.time()
        self._longest, self._last = max(self._longest, now - self._last), now

    def should_stop(self) -> bool:
        """True when the search asked this run to end early. Finish with the best score so far. The search may
        also lengthen a run while it trains: `allowance` is raised here when it has."""
        try:
            with open(os.path.join(self.out, "control.json"), "r", encoding="utf-8") as handle:
                told = json.load(handle)
            self.allowance = max(self.allowance, float(told.get("allowance") or 0))
            return told.get("action") == "stop"
        except (OSError, ValueError, AttributeError, TypeError):
            return False

    def out_of_time(self) -> bool:
        """True when the job was told to end, or when its time limit would pass before another step like the
        longest so far could finish. Save, then call `pause`."""
        if self.told_to_end is not None:
            return True
        if self.deadline is None:
            return False
        step = max(self._longest, time.time() - self._last)
        return self.deadline - time.time() < 1.5 * step + 60.0

    def pause(self) -> None:
        """Leave now. The run is submitted again and starts where `save_state` left it."""
        sys.stdout.flush()
        sys.exit(PAUSE_EXIT)

    def finish(self, score: Optional[float], valid: bool = True, **fields: Any) -> None:
        """Write the result. A score that is missing or not a finite number makes the run invalid."""
        fine = isinstance(score, (int, float)) and math.isfinite(float(score))
        result = dict(fields, valid=bool(valid and fine), score=float(score) if fine else None)
        if not fine and "reason" not in result:
            result["reason"] = "the score is missing or not a finite number"
        tmp = os.path.join(self.out, "result.json.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(result, handle)
        os.replace(tmp, os.path.join(self.out, "result.json"))
