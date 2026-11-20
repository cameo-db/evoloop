"""The loop.

One controller per run. Each turn it reads the person's requests into the ledger, works out the settings
in force, follows the running jobs, and, when a job slot is free and the budget allows, has one more
design written: the schedule picks the kind of slot, the strategy picks the parents, a writer (or code)
makes the design, code checks it, and it is submitted. A design is written only when it can run.

Everything the controller knows is in the run's stores, so it can be stopped and started again at any
point, and a change of strategy, schedule, harness or search space takes effect at the next design."""
from __future__ import annotations

import concurrent.futures
import json
import os
import random
import signal
import time
from typing import Any, Dict, List, Optional, Tuple

from . import audit, form, jobs, report, schedule, space, strategies, strategist, study
from .agents import AgentError, Agents, AgentsUnavailable
from .design import Designer
from .store import ENDED, SCORED, Store, View, read_json, write_json

STALL = 8   # designs refused in a row, with nothing running, before the run stops as stalled


class Controller:
    def __init__(self, folder: str, name: str, backend: Any = None, agent_backend: Any = None, poll: Optional[float] = None):
        self.folder = os.path.abspath(folder)
        self.name = name
        self.run_dir = os.path.join(self.folder, "runs", name)
        self.store = Store(self.run_dir)
        self.brief = form.load_brief(self.folder)
        self.info = read_json(os.path.join(self.run_dir, "run.json"), {}) or {}
        if self.info.get("brief"):
            self.brief = self.info["brief"]   # a run keeps the brief it started with; changes go through the ledger
        self.settings, self.sources = form.resolve(self.brief, self.store.merged_list("ledger"))
        self.agents = Agents(self.settings, self.folder, self.store, backend=agent_backend)
        self.designer = Designer(self.folder, self.run_dir, self.store, self.agents, seed=int(self.settings["evaluation"]["seed"]))
        self.backend = backend or jobs.make(self.settings)
        self.poll_seconds = poll if poll is not None else (20.0 if self.backend.name == "slurm" else 1.0)
        self.rng = random.Random(1000 + int(self.settings["evaluation"]["seed"]))
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=int(self.settings["agents"]["max_concurrent_calls"]))
        self.designing: List[Tuple[concurrent.futures.Future, str, Dict[str, Any]]] = []
        self.side: List[Tuple[str, concurrent.futures.Future, int]] = []
        self.pending: List[Dict[str, Any]] = []
        self.refused = 0
        self.blocked: Optional[str] = None          # a job could not be submitted
        self.agent_block: Optional[str] = None      # no agent call can be made
        self.submit_failures = 0
        self.retry_after = 0.0
        self.draining = False
        self.stop_now = False
        self.started = time.time()
        self.state = read_json(os.path.join(self.run_dir, "controller.json"), {}) or {}
        self.state.setdefault("analysed", 0)
        self.state.setdefault("reviewed", [])
        self.state.setdefault("rechecked", 0)
        self.state.setdefault("period", 0)
        self.state.setdefault("screen", {})
        self.state.setdefault("forced", [])
        self.state.setdefault("met_at", 0)
        self.state.setdefault("governed_at", 0)

    # --- starting --------------------------------------------------------------------------------
    def begin(self) -> None:
        """Start a new run: freeze the brief and the base, record the person's own words, queue the baseline."""
        if self.info:
            return
        if not form.confirmed(self.brief):
            raise form.BriefError("the brief is not confirmed (run `evoloop brief --confirm NAME` after reading `evoloop plan`)")
        self.info = {"name": self.name, "started": time.strftime("%Y-%m-%d %H:%M"), "brief": self.brief,
                     "frozen": space.frozen_hash(os.path.join(self.folder, "base"), os.path.join(self.folder, "adapter")),
                     "status": "running"}
        write_json(os.path.join(self.run_dir, "run.json"), self.info)
        by = (self.brief.get("status") or {}).get("confirmed_by")
        self.ledger({"kind": "init", "by": by, "run_type": self.settings["run"]["type"],
                     "strategy": self.settings["strategy"]["mechanism"], "harness": self.settings["harness"]["level"]})
        if self.settings["run"]["description"]:
            self.ledger({"kind": "note", "by": by, "text": self.settings["run"]["description"], "roles": [],
                         "status": "active", "reason": "the person's own description of the search"})
        view = self.view()
        mode = self.settings["baseline"]["mode"]
        if mode != "skip":
            run = self.designer.baseline(view, self.settings)
            if mode == "import":
                result = read_json(os.path.join(str(self.settings["baseline"]["import_from"]), "result.json"))
                if not isinstance(result, dict):
                    raise form.BriefError("baseline.import_from has no result.json")
                run["charge"] = 0.0
                self.store.append("runs", run)
                self.finish(run, {"state": "ended", "exit": 0}, result=result)
            else:
                self.queue(run)

    def check_frozen(self) -> None:
        now = space.frozen_hash(os.path.join(self.folder, "base"), os.path.join(self.folder, "adapter"))
        if self.info.get("frozen") and now != self.info["frozen"]:
            raise RuntimeError("the frozen code of this run has changed since it started (base/ or adapter/). "
                               "Scores before and after would not be comparable; start a new run, or restore the files.")

    # --- the stores ------------------------------------------------------------------------------
    def view(self) -> View:
        return View.load(self.store, self.settings)

    def ledger(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        entry = dict(entry, id="S%d" % (len(self.store.read("ledger")) + 1))
        entry.setdefault("at_evaluations", len([r for r in self.store.merged("runs").values()
                                                if r["performance"].get("status") in SCORED]))
        return self.store.append("ledger", entry)

    def update(self, run_id: str, **fields: Any) -> None:
        self.store.append("runs", dict(fields, id=run_id))

    def queue(self, run: Dict[str, Any]) -> None:
        """A run the loop makes itself (the baseline, a re-check, a reference for a new period): recorded at
        once under the next free id, so that no design written meanwhile can take the same id, then started
        when a slot is free."""
        run["id"] = "R%d" % (len(self.store.merged("runs")) + 1)
        self.store.append("runs", run)
        self.pending.append(run)

    def read_inbox(self) -> None:
        """The person's requests, written by `evoloop set`, `note`, `stop`, `review`. Each becomes a ledger
        entry, applied or refused with the reason. A refused request changes nothing and the run goes on."""
        folder = os.path.join(self.run_dir, "requests")
        if not os.path.isdir(folder):
            return
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if not name.endswith(".json") or not os.path.isfile(path):
                continue
            request = read_json(path, {}) or {}
            try:
                self.take(request)
            except Exception as exc:   # a request that cannot be carried out is refused on the record; the run goes on
                self.ledger({"kind": str(request.get("kind") or "request"), "by": request.get("by"), "status": "refused",
                             "why": "%s: %s" % (type(exc).__name__, exc), "request": request})
            os.makedirs(os.path.join(folder, "done"), exist_ok=True)
            os.replace(path, os.path.join(folder, "done", "%d_%s" % (int(time.time()), name)))

    def take(self, request: Dict[str, Any]) -> None:
        who, why = request.get("by"), request.get("reason")
        kind = request.get("kind")
        if kind == "set":
            for key, value in (request.get("changes") or {}).items():
                fault = form.check_change(key, value)
                old = form.get(self.settings, key)
                entry = {"kind": "set", "key": key, "value": value, "old": old, "by": who, "reason": why,
                         "status": "refused" if fault else "applied", "why": fault}
                if not fault and form.starts_period(key) and self.settings["evaluation"]["on_length_change"] != "compare_anyway":
                    entry["new_period"] = True
                before = form.flatten({k: v for k, v in self.settings.items() if not k.startswith("_") and k != "notes"})
                entry = self.ledger(entry)
                self.refresh()   # so that the next change records the value this one left
                after = form.flatten({k: v for k, v in self.settings.items() if not k.startswith("_") and k != "notes"})
                also = {k: [before.get(k), v] for k, v in after.items() if k != key and before.get(k) != v}
                if also:   # a change of the budget or the run type moves the settings that follow from it: say which
                    self.store.append("ledger", {"id": entry["id"], "also_changed": also})
        elif kind == "note":
            self.ledger({"kind": "note", "text": str(request.get("text") or ""), "roles": request.get("roles") or [],
                         "by": who, "reason": why, "status": "active", "from_review": request.get("from_review")})
        elif kind == "withdraw":
            target = request.get("id")
            found = any(e.get("id") == target and e.get("kind") == "note" for e in self.store.read("ledger"))
            if found:
                self.store.append("ledger", {"id": target, "status": "withdrawn", "withdrawn_by": who})
            self.ledger({"kind": "withdraw", "target": target, "by": who, "reason": why,
                         "status": "applied" if found else "refused", "why": None if found else "no note has that id"})
        elif kind == "stop":
            if request.get("run"):
                self.stop_run(str(request["run"]), who, why)
            else:
                self.draining = True
                self.ledger({"kind": "stop", "drain": True, "by": who, "reason": why, "status": "applied"})
        elif kind in ("approve", "decline"):
            self.answer(str(request.get("id")), kind == "approve", who, why)
        elif kind == "review":
            self.state["review_now"] = request.get("roles") or "all"
            self.ledger({"kind": "review", "by": who, "reason": why, "roles": request.get("roles") or "all", "status": "applied"})
        else:
            raise ValueError("unknown kind of request: %r" % kind)

    def refresh(self) -> None:
        self.settings, self.sources = form.resolve(self.brief, self.store.merged_list("ledger"))
        self.agents.update(self.settings)

    # --- jobs ------------------------------------------------------------------------------------
    def out_dir(self, run: Dict[str, Any]) -> str:
        return os.path.join(self.run_dir, "out", run["id"])

    def checkpoint_dir(self, run: Dict[str, Any]) -> str:
        return os.path.join(self.run_dir, "checkpoints", "%s_s%s_p%s" % (run["candidate"], run["seed"], run.get("period", 0)))

    def submit(self, run: Dict[str, Any]) -> None:
        out, work = self.out_dir(run), os.path.join(self.run_dir, "work", run["id"])
        os.makedirs(out, exist_ok=True)
        os.makedirs(self.checkpoint_dir(run), exist_ok=True)
        if not os.path.isdir(work):
            space.materialize(os.path.join(self.folder, "base"), os.path.join(self.folder, "adapter"),
                              self.designer.blocks(run["candidate"]), work)
        env = jobs.environment(run, out, self.checkpoint_dir(run), self.settings)
        try:
            job = self.backend.submit(run, work, env, self.settings)
        except Exception as exc:
            # Tried again after a pause; after three failures in a row the run stops as paused, with the reason.
            self.update(run["id"], performance={"status": "designed"}, submit_error=str(exc)[:300])
            self.submit_failures += 1
            self.retry_after = time.time() + 60.0
            self.blocked = "a job could not be submitted: %s" % str(exc)[:200]
            return
        self.submit_failures, self.blocked = 0, None
        self.update(run["id"], job=job, allowance=float(run.get("allowance") or self.settings["evaluation"]["allowance"]),
                    performance={"status": "queued"})

    def stop_run(self, run_id: str, who: Any, why: Any) -> None:
        run = self.store.merged("runs").get(run_id)
        if run is None or run["performance"].get("status") in ENDED:
            self.ledger({"kind": "stop", "run": run_id, "by": who, "reason": why, "status": "refused",
                         "why": "no such run in flight"})
            return
        if not run.get("job"):   # recorded but not started: it is withdrawn, uncharged
            self.pending = [p for p in self.pending if p["id"] != run_id]
            self.update(run_id, charge=0.0, performance={"status": "not_run", "reason": "withdrawn by %s before it started" % who})
        else:
            jobs.tell(self.out_dir(run), "stop")
            self.update(run_id, stopped_by={"who": who, "why": why, "t": time.time()})
        self.ledger({"kind": "stop", "run": run_id, "by": who, "reason": why, "status": "applied"})

    def follow(self, view: View) -> None:
        for run in view.in_flight():
            if not run.get("job"):
                if run["performance"].get("status") == "designed" and run["id"] not in [p["id"] for p in self.pending]:
                    self.pending.append(run)   # recorded but never submitted: a controller that stopped in between
                continue
            told = self.backend.state(run)
            status = run["performance"].get("status")
            stopped = run.get("stopped_by")
            if told["state"] == "waiting":
                if stopped:   # stopped before it ever started: taken out of the queue
                    self.backend.cancel(run)
                    self.update(run["id"], charge=0.0, performance={
                        "status": "not_run", "reason": "stopped by %s while waiting in the queue" % stopped.get("who")})
                continue
            if told["state"] == "running":
                if status != "running":
                    self.update(run["id"], performance={"status": "running"}, running_since=time.time())
                self.screen(run, view)
                if stopped and time.time() - stopped["t"] > 300:
                    self.backend.cancel(run)
                continue
            if told["state"] == "machine" and not stopped:
                restarts = int(run.get("restarts") or 0)
                if restarts < int(self.settings["compute"]["infrastructure_retries"]):
                    # The machine, not the model: run it again, uncharged. Bounded, so it cannot loop.
                    self.update(run["id"], restarts=restarts + 1, job=None, performance={"status": "designed"},
                                machine_endings=(run.get("machine_endings") or []) + [told.get("why")])
                    self.pending.append(dict(run, job=None, restarts=restarts + 1))
                else:
                    self.finish(run, {"state": "ended", "exit": None}, reason="the machine ended this run %d times: %s" % (
                        restarts + 1, told.get("why")))
                continue
            self.finish(run, told)

    def finish(self, run: Dict[str, Any], told: Dict[str, Any], result: Any = None, reason: Optional[str] = None) -> None:
        out = self.out_dir(run)
        result = result if result is not None else read_json(os.path.join(out, "result.json"))
        perf: Dict[str, Any] = {}
        diag = (result or {}).get("diagnostics") if isinstance(result, dict) else None
        diag = diag if isinstance(diag, dict) else {}
        score = (result or {}).get("score") if isinstance(result, dict) else None
        ok = isinstance(result, dict) and result.get("valid") and isinstance(score, (int, float)) and score == score \
            and abs(score) != float("inf")
        since = run.get("running_since") or (run.get("job") or {}).get("started")
        if ok:
            cut = run.get("screened") or run.get("stopped_by")
            perf.update(status="stopped_early" if cut else "done", score=float(score),
                        valid={k: v for k, v in diag.items() if k != "hidden" and isinstance(v, (int, float)) and not isinstance(v, bool)},
                        test=diag.get("hidden") if isinstance(diag.get("hidden"), dict) else None,
                        parameters=diag.get("parameters", result.get("parameters")),
                        best_epoch=result.get("best_epoch", diag.get("best_epoch")),
                        epochs_run=result.get("epochs_run", diag.get("epochs_run")),
                        signature=result.get("signature") if isinstance(result.get("signature"), list) else None,
                        inference_speed=result.get("inference_speed"), resource_used=result.get("resource_used"))
        elif told.get("exit") == jobs.CHECK_EXIT:
            perf.update(status="invalid", reason="the quick check failed; the design was not trained",
                        log=jobs.tail(out))
        else:
            stopped = run.get("stopped_by")
            perf.update(status="failed", reason=reason or (
                "stopped by %s before it gave a result" % stopped.get("who") if stopped else None) or (
                diag.get("error") if diag else None) or ("no result.json (exit %s)" % told.get("exit")), log=jobs.tail(out))
            if stopped:
                perf["status"] = "not_run"   # the person's stop, not the design's failure
        ended = time.time()
        try:   # a job can start and end between two looks at the queue: its own records give the times
            with open(os.path.join(out, "starts.jsonl"), "r", encoding="utf-8") as handle:
                since = json.loads(handle.readline())["t"]
            ended = os.path.getmtime(os.path.join(out, "result.json"))
        except (OSError, ValueError, KeyError):
            pass
        if since:
            perf["training_minutes"] = round(max(0.0, ended - float(since)) / 60.0, 3)
        fields: Dict[str, Any] = {"performance": perf, "ended": time.time()}
        if isinstance(result, dict) and isinstance(result.get("captured"), dict):
            fields["captured"] = result["captured"]   # what the job read from the objects it built, and its environment
        if run.get("screened"):
            fields["charge"] = float(self.settings["evaluation"]["screen_fraction"])
        if perf["status"] == "not_run":
            fields["charge"] = 0.0
        self.update(run["id"], **fields)

    def screen(self, run: Dict[str, Any], view: View) -> None:
        """A new design's first run is compared, part way, with the new designs before it at the same point.
        One clearly in the lower part is stopped there and charged for what it ran."""
        ev = self.settings["evaluation"]
        fraction, keep = float(ev["screen_fraction"]), float(ev["screen_keep"])
        if not 0 < fraction < 1 or keep >= 1 or run.get("purpose", "search") != "search" or run.get("screened") \
                or run["history"].get("mode") not in ("new", "novel") or run["id"] in self.state["screen"]:
            return
        target = fraction * float(run.get("allowance") or ev["allowance"])
        rows = [r for r in jobs.read_progress(self.out_dir(run)) if r["step"] >= target]
        if not rows:
            return
        mine = view.sign * float(rows[0]["metric"])
        pool = sorted(self.state["screen"].values())
        self.state["screen"][run["id"]] = mine
        if len(pool) < int(ev["screen_min_pool"]):
            return
        cutoff = pool[int(len(pool) * (1 - keep))]   # the score that the kept share of earlier designs reached
        if mine < cutoff - view.noise:
            jobs.tell(self.out_dir(run), "stop")
            self.update(run["id"], screened={"at": target, "metric": rows[0]["metric"], "cutoff": view.sign * cutoff})

    # --- designing -------------------------------------------------------------------------------
    def capacity(self) -> int:
        compute = self.settings["compute"]
        cap = int(compute["gpus"] or 1)
        return min(cap, int(compute["max_running"])) if compute.get("max_running") else cap

    def spent(self, view: View) -> float:
        """Evaluations charged: every scored run, and runs that failed or failed the quick check beyond the
        allowance of uncounted ones, so that a search whose designs all break still comes to an end."""
        unscored = sum(1 for r in view.runs.values() if r["performance"].get("status") in ("failed", "invalid")
                       and r.get("purpose", "search") in ("search", "trial"))
        return view.charged() + max(0, unscored - int(self.settings["budget"]["max_uncounted_failures"]))

    def unscored_streak(self, view: View) -> int:
        """How many of the most recent designs in a row ended without a score."""
        streak = 0
        for run in sorted(view.ended(), key=lambda r: r.get("ended", 0), reverse=True):
            if run.get("purpose", "search") not in ("search", "trial"):
                continue
            if run["performance"].get("status") not in ("failed", "invalid"):
                break
            streak += 1
        return streak

    def passed(self, view: View) -> bool:
        threshold = self.settings["objective"].get("success_threshold")
        best = view.best()
        return threshold is not None and best is not None and best["value"] >= view.sign * float(threshold)

    def start(self, view: View) -> None:
        if self.blocked and self.submit_failures < 3 and time.time() >= self.retry_after:
            self.blocked = None   # try the submission again
        in_flight = view.in_flight()
        # A run that is recorded but not yet submitted holds no slot: it is what the free slots are for.
        started = [r for r in in_flight if r.get("job")]
        free = self.capacity() - len(started) - len(self.designing)
        while self.pending and free > 0 and not self.draining and not self.blocked:
            run = self.pending.pop(0)
            if run["id"] not in view.runs:
                self.store.append("runs", run)
            self.submit(run)
            free -= 1
        if free <= 0 or self.draining or self.pending or self.blocked or self.passed(view):
            return
        budget = float(self.settings["budget"]["evaluations"] or 0)
        committed = self.spent(view) + len(in_flight) + len(self.designing)
        # On a busy cluster nothing more is written while `compute.max_waiting` jobs await their first start.
        waiting = sum(1 for r in in_flight if r["performance"].get("status") == "queued") if self.backend.name == "slurm" else 0
        new_period = any(r.get("purpose") == "reference" for r in in_flight) and not view.scored()
        strategy = strategies.make(self.settings)
        while free > 0 and committed < budget and waiting < int(self.settings["compute"]["max_waiting"]) and not new_period \
                and not self.agents.available() and self.refused < STALL and self.unscored_streak(view) < STALL:
            planned = [mode for _, mode, _ in self.designing]
            # What is being written now is not in the results yet: the strategy is told, so that two slots
            # opened together do not go to the same lineage and parent.
            settings = dict(self.settings, _designing=[making for _, _, making in self.designing])
            mode = schedule.next_mode(view, settings, planned)
            # Slots the strategist ordered come first, when their mode is possible now.
            forced = self.state["forced"]
            while forced and not schedule.available(view, settings).get(forced[0]["mode"]):
                forced.pop(0)
            if forced:
                mode = forced[0]["mode"]
                settings = dict(settings, _forced=True)   # an ordered slot is not turned into a trial run
            options = None
            if settings["harness"]["coordinator"] == "agent" and not forced \
                    and not strategist.reserve_reached(self.agents, settings):
                can = schedule.available(view, settings)
                want = schedule.shares(view, settings)
                modes = [m for m in form.MODES if can[m] and want[m] > 0] or [mode]
                options = [strategy.choose(view, m, settings, self.rng) for m in modes]
                for option, m in zip(options, modes):
                    option["share_owed"] = round(want.get(m, 0.0), 3)
                request = options[modes.index(mode)] if mode in modes else options[0]
            else:
                request = strategy.choose(view, mode, settings, self.rng)
            if forced:
                request["forced_by"], request["force_kind"] = forced[0].get("decision"), forced[0].get("kind")
                forced[0]["left"] -= 1
                if forced[0]["left"] <= 0:
                    forced.pop(0)
            future = self.pool.submit(self.write, request, options, view, settings)
            self.designing.append((future, request["mode"], {k: request.get(k) for k in (
                "mode", "lineage", "parents", "island", "purpose")}))
            free -= 1
            committed += 1

    def write(self, request: Dict[str, Any], options: Any, view: View, settings: Dict[str, Any]) -> Dict[str, Any]:
        """In a worker: the coordinator's choice when there is one, then the design."""
        if options and len(options) > 1:
            shadow = options.index(request)
            try:
                reply = self.agents.call("coordinator", {
                    "objective": settings["objective"], "budget_used": round(schedule.fraction_used(view, settings), 3),
                    "options": [{"index": i, "mode": o["mode"], "parents": o.get("parents"), "why": o.get("why"),
                                 "share_owed": o.get("share_owed")} for i, o in enumerate(options)],
                    "code_would_choose": shadow, "returns_so_far": schedule.credit(view),
                    "leaderboard": [self.designer.summary(view, c["id"]) for c in view.scored()[:8]]}, about="next slot")
                choice = reply.get("choice")
                if isinstance(choice, int) and 0 <= choice < len(options):
                    request = options[choice]
                    request["coordinator"] = {"call": reply.get("_call"), "chose": choice, "code_would_choose": shadow}
            except AgentError:
                pass   # the schedule's choice stands
        return self.designer.propose(self.designer.prepare(request, view, settings))

    def collect(self, view: View) -> View:
        still = []
        for future, mode, making in self.designing:
            if not future.done():
                still.append((future, mode, making))
                continue
            try:
                request = future.result()
            except Exception as exc:   # a fault in the loop's own code: recorded, never silent
                request = {"mode": mode, "move": None, "refuse": "the designer raised %s: %s" % (type(exc).__name__, exc)}
            try:
                run, why = self.designer.commit(request, view, self.settings)
            except Exception as exc:   # a reply of an unexpected shape must not end the run
                run, why = None, "the design could not be recorded (%s: %s)" % (type(exc).__name__, exc)
            if run is None:
                if request.get("agents_unavailable"):
                    self.agent_block = why
                else:
                    self.refused += 1
                    self.store.append("runs", {
                        "id": "R%d" % (len(view.runs) + 1), "candidate": None, "purpose": "not_run", "charge": 0.0,
                        "period": view.period, "seed": None, "history": {"lineage": None, "mode": request.get("mode"),
                                                                           "move": request.get("move"), "call": request.get("call")},
                        "performance": {"status": "not_run", "reason": why[:600]}})
            else:
                self.refused = 0
                if request.get("coordinator"):
                    run["history"]["coordinator"] = request["coordinator"]
                self.store.append("runs", run)
                if self.draining:
                    self.pending.append(run)   # written before the stop was asked: kept, and started if the run goes on
                else:
                    self.submit(run)
            view = self.view()
        self.designing = still
        return view

    # --- housekeeping ----------------------------------------------------------------------------
    def housekeeping(self, view: View) -> None:
        for kind, future, since in self.side:
            if kind == "analyst" and future.done():
                try:
                    done = future.result()
                except Exception:
                    done = False
                if not done:   # the call failed: those results are shown again at the next analysis
                    self.state["analysed"] = min(int(self.state["analysed"]), since)
        # A finished meeting of the strategist stays until its decisions are taken up, further down.
        self.side = [item for item in self.side if not item[1].done() or item[0] == "strategist"]
        scored = [r for r in view.runs.values() if r["performance"].get("status") in SCORED]
        designs = [r for r in scored if r.get("purpose", "search") in ("search", "trial", "baseline")]
        budget = float(self.settings["budget"]["evaluations"] or 0)
        room = self.spent(view) + len(view.in_flight()) + len(self.designing) < budget
        # A change of the run's length begins a new period: the leaders are fitted again, or continued.
        period = int(self.settings["_period"])
        if period > int(self.state["period"]):
            old = View.load(self.store, dict(self.settings, _period=int(self.state["period"])))
            ev = self.settings["evaluation"]
            how = ev["on_length_change"]
            can_continue = not ev["schedule_depends_on_length"] and ev["keep_checkpoints"]
            leaders, seen = [], set()
            for cand in old.scored():
                if cand["lineage"] not in seen:
                    seen.add(cand["lineage"])
                    leaders.append(cand["id"])
            for cand in leaders[:int(ev["leaders_refit"])]:
                # The reference is fitted with the seed in force now, and continues the candidate's latest checkpoint.
                latest = [old.runs[r] for r in old.cands[cand]["runs"] if old.counts(old.runs[r])][-1]
                run = self.designer.again(view, cand, "reference", int(ev["seed"]), self.settings, period=period)
                if how == "continue" or (how == "auto" and can_continue):
                    run["continue_from"] = self.checkpoint_dir(latest)
                self.queue(run)
            self.ledger({"kind": "period", "period": period, "leaders": leaders[:int(ev["leaders_refit"])],
                         "how": "continued from checkpoints" if (how == "continue" or (how == "auto" and can_continue))
                         else "fitted again"})
            self.state["period"] = period
            write_json(os.path.join(self.run_dir, "controller.json"), self.state)   # so a restart does not queue them twice
        self.strategy_turn(view, room)
        level = self.settings["harness"]["level"]
        # The leader is partly the luckiest fit. The full harness fits it again on a new seed every 20 designs
        # unless `evaluation.recheck_every` says otherwise; a re-check is charged like any run.
        every = int(self.settings["evaluation"]["recheck_every"] or 0) or (20 if level == "full" else 0)
        if every > 0 and len(designs) // every > int(self.state["rechecked"]) and view.best() and room:
            self.state["rechecked"] = len(designs) // every
            leader = view.best()
            run = self.designer.again(view, leader["id"], "recheck", int(self.settings["evaluation"]["seed"]) + len(leader["runs"]),
                                      self.settings)
            self.queue(run)
        every = int(self.settings["harness"]["analyst_every"] or 0)
        seen = [r for r in view.ended() if r["performance"].get("status") != "not_run"]
        if level != "minimal" and every > 0 and len(seen) - int(self.state["analysed"]) >= every \
                and not any(item[0] == "analyst" for item in self.side) and not self.agents.available() \
                and not strategist.reserve_reached(self.agents, self.settings):
            since = int(self.state["analysed"])
            self.state["analysed"] = len(seen)
            self.side.append(("analyst", self.pool.submit(audit.analyse, self.store, self.agents, self.designer, view,
                                                          self.settings, since), since))
        done = schedule.fraction_used(view, self.settings)
        for point in form.review_points(self.settings):
            if point < 1.0 and done >= point and point not in self.state["reviewed"]:
                self.state["reviewed"].append(point)
                self.review(view, "at %d%% of the budget" % round(100 * point))
        asked = self.state.pop("review_now", None)
        if asked:
            self.review(view, "asked for by the person", asked if isinstance(asked, list) else None)

    # --- the strategist and the spend governor ---------------------------------------------------
    def strategy_turn(self, view: View, room: bool) -> None:
        s = self.settings["strategist"]
        # Decisions of a meeting that has ended are checked and applied here, on the controller's own thread.
        for kind, future, _ in self.side:
            if kind == "strategist" and future.done():
                try:
                    decisions = future.result()
                except Exception as exc:   # a fault in a meeting is on the record, never silent
                    decisions = []
                    self.ledger({"kind": "decision", "by": strategist.BY, "action": None, "status": "refused",
                                 "why": "the meeting failed: %s: %s" % (type(exc).__name__, exc)})
                for decision in decisions:
                    self.decide(decision, view)
                    view = self.view()
        self.side = [item for item in self.side if not (item[0] == "strategist" and item[1].done())]
        # Earlier decisions are scored once enough designs have followed them.
        for entry in self.store.merged_list("ledger"):
            if entry.get("kind") == "decision" and entry.get("status") in ("applied", "approved") and not entry.get("outcome"):
                outcome = strategist.score(view, entry, int(s["horizon"]))
                if outcome:
                    self.store.append("ledger", {"id": entry["id"], "outcome": outcome})
        scored = len(strategist.designs(view))
        # The spend governor: when the run is heading past the cap, one step cheaper, at most every ten designs.
        if scored - int(self.state["governed_at"]) >= 10:
            step = strategist.govern(self.agents, view, self.settings, self.store)
            if step:
                self.state["governed_at"] = scored
                self.ledger({"kind": "set", "key": step["key"], "value": step["value"], "old": form.get(self.settings, step["key"]),
                             "by": strategist.GOVERNOR, "reason": step["reason"], "status": "applied"})
                self.refresh()
        if s["mode"] == "off" or not room or self.draining or any(item[0] == "strategist" for item in self.side) \
                or self.agents.available() or strategist.reserve_reached(self.agents, self.settings):
            return
        since = scored - int(self.state["met_at"])
        stuck = strategist.since_gain(view)
        why = None
        if since >= int(s["every"]):
            why = "%d designs since the last meeting" % since
        elif stuck >= int(s["plateau"]) and since >= max(3, int(s["plateau"]) // 2):
            why = "no rise in the best score for %d designs" % stuck
        if why and scored >= 3:
            self.state["met_at"] = scored
            self.side.append(("strategist", self.pool.submit(strategist.meet, self.store, self.agents, view,
                                                             dict(self.settings), why), 0))

    def decide(self, decision: Dict[str, Any], view: View) -> None:
        """One decision of the strategist: refused, applied, or held for the person. Always on the record."""
        fault, effects, wait = strategist.work_out(decision, view, self.settings, self.store.merged_list("ledger"))
        best = view.best()
        entry = {"kind": "decision", "by": strategist.BY, "action": decision.get("action"), "args": decision.get("args"),
                 "reason": str(decision.get("reason") or "")[:600], "expects": decision.get("expects")
                 if isinstance(decision.get("expects"), dict) else None, "call": decision.get("call"),
                 "best_before": view.display(best["value"]) if best else None, "effects": effects}
        if fault:
            self.ledger(dict(entry, status="refused", why=fault))
        elif wait:
            self.ledger(dict(entry, status="proposed", why=wait))
        else:
            entry = self.ledger(dict(entry, status="applied"))
            self.enact(entry["id"], effects)

    def enact(self, decision_id: str, effects: Dict[str, Any]) -> None:
        for key, value in (effects.get("sets") or {}).items():
            self.ledger({"kind": "set", "key": key, "value": value, "old": form.get(self.settings, key), "by": strategist.BY,
                         "decision": decision_id, "status": "applied"})
            self.refresh()
        if effects.get("force"):
            self.state["forced"].append(dict(effects["force"], decision=decision_id))
        if effects.get("lineage"):
            self.ledger(dict(effects["lineage"], kind="lineage", by=strategist.BY, decision=decision_id, status="applied"))
        if effects.get("note"):
            standing = [e for e in self.store.merged_list("ledger") if e.get("kind") == "note" and e.get("by") == strategist.BY
                        and e.get("status") == "active"]
            for old in standing[:max(0, len(standing) - 2)]:   # at most three of its notes stand at once
                self.store.append("ledger", {"id": old["id"], "status": "withdrawn", "withdrawn_by": strategist.BY})
            self.ledger({"kind": "note", "text": effects["note"], "roles": ["writer"], "by": strategist.BY,
                         "decision": decision_id, "status": "active"})
        if effects.get("question"):
            self.store.append("questions", dict(effects["question"], id="Q%d" % (len(self.store.read("questions")) + 1),
                                                status="open", **{"from": strategist.BY}))
        self.refresh()

    def answer(self, decision_id: str, yes: bool, who: Any, why: Any) -> None:
        """The person's yes or no to a decision that was held for them."""
        held = [e for e in self.store.merged_list("ledger") if e.get("id") == decision_id and e.get("kind") == "decision"]
        if not held or held[0].get("status") != "proposed":
            self.ledger({"kind": "approve" if yes else "decline", "target": decision_id, "by": who, "status": "refused",
                         "why": "no decision with that id is waiting"})
            return
        self.store.append("ledger", {"id": decision_id, "status": "approved" if yes else "declined", "answered_by": who,
                                     "answer_reason": why, "t_answered": time.time()})
        if yes:
            # Scored from now, not from when it was proposed.
            best = self.view().best()
            self.store.append("ledger", {"id": decision_id, "t": time.time(),
                                         "best_before": self.view().display(best["value"]) if best else None})
            self.enact(decision_id, held[0].get("effects") or {})
        self.ledger({"kind": "approve" if yes else "decline", "target": decision_id, "by": who, "reason": why, "status": "applied"})

    def review(self, view: View, why: str, roles: Any = None) -> None:
        if self.agents.available() or strategist.reserve_reached(self.agents, self.settings):
            return
        self.side.append(("review", self.pool.submit(audit.review, self.store, self.agents, view, self.settings, why, roles), 0))

    # --- the loop --------------------------------------------------------------------------------
    def finished(self, view: View) -> Optional[str]:
        started = [r for r in view.in_flight() if r.get("job")]
        # A run recorded but never started does not keep a draining or blocked search alive: it starts when the run goes on.
        idle = not started and not self.designing and (not self.pending or self.draining or bool(self.blocked))
        budget = float(self.settings["budget"]["evaluations"] or 0)
        if self.stop_now:
            return "interrupted"
        hours = self.settings["budget"].get("wall_clock_hours")
        if hours and time.time() - self.started > float(hours) * 3600:
            self.draining = True
        if not idle:
            return None
        if self.draining:
            return "stopped by the person" if any(e.get("kind") == "stop" and e.get("drain") for e in self.store.read("ledger")) \
                else "the wall-clock limit was reached"
        if self.passed(view):
            return "the success threshold was passed"
        if self.spent(view) >= budget:
            return "the budget of %d evaluations is spent" % budget
        if self.blocked and self.submit_failures < 3:
            return None   # a submission is tried again after a pause
        if self.blocked or self.agents.available():
            return "paused: %s" % (self.blocked or self.agents.available() or self.agent_block)
        if self.refused >= STALL:
            return "stalled: %d designs in a row could not be run" % self.refused
        if self.unscored_streak(view) >= STALL:
            return "stalled: the last %d designs all failed or failed the quick check" % self.unscored_streak(view)
        return None

    def turn(self) -> Optional[str]:
        self.read_inbox()
        self.refresh()
        view = self.view()
        self.follow(view)
        view = self.collect(self.view())
        self.housekeeping(view)
        self.start(view)
        view = self.view()
        write_json(os.path.join(self.run_dir, "controller.json"), self.state)
        report.status(self, view)
        return self.finished(view)

    def run(self, max_seconds: Optional[float] = None) -> str:
        self.begin()
        self.check_frozen()
        self.blocked, self.agent_block, self.submit_failures, self.refused = None, None, 0, 0
        previous = {}
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                previous[sig] = signal.signal(sig, lambda *_: setattr(self, "stop_now", True))
            except ValueError:
                pass   # not in the main thread (a test)
        reason = None
        try:
            while reason is None:
                reason = self.turn()
                if reason is None:
                    if max_seconds is not None and time.time() - self.started > max_seconds:
                        reason = "interrupted"
                        break
                    time.sleep(self.poll_seconds)
        finally:
            for kind, future, _ in self.side:
                try:
                    future.result(timeout=5 if reason == "interrupted" else 600)
                except Exception:
                    pass
            self.backend.shutdown()
            self.pool.shutdown(wait=False)
            for sig, handler in previous.items():
                signal.signal(sig, handler)
        self.end(reason)
        return reason

    def end(self, reason: str) -> None:
        view = self.view()
        ended = not reason.startswith(("interrupted", "paused"))
        if ended and 1.0 in form.review_points(self.settings) and "end" not in self.state["reviewed"] and not self.agents.available():
            self.state["reviewed"].append("end")
            try:
                audit.review(self.store, self.agents, view, self.settings, "at the end of the run")
            except Exception:
                pass
        self.info.update(status="ended" if ended else "stopped", reason=reason, ended=time.strftime("%Y-%m-%d %H:%M"))
        write_json(os.path.join(self.run_dir, "run.json"), self.info)
        write_json(os.path.join(self.run_dir, "controller.json"), self.state)
        report.status(self, view, reason=reason)
        report.write(self, view, reason)
        study.write(self, view)
