"""The site file: what is particular to the machine a search runs on.

Every cluster is set up differently: its partitions, its QoS names, which GPUs it has, how an environment is
activated, what an account must be charged to, what is not allowed. None of that belongs in a search's brief,
which should move between machines. It goes in a site file, written once per machine:

    name: our-cluster
    compute:                       # defaults for the compute settings of every search on this machine
      scheduler: slurm
      partition: gpu
      qos: [{name: normal, max_jobs: 8}, {name: low}]
      gpu_type: a100
      time_limit: "1-00:00:00"
      setup: ["module load cuda/12", "source ~/envs/train/bin/activate"]
      extra_sbatch: ["--account=mylab"]
    rules:                         # shown in the plan, and to an agent helping to set up a search
      - "Do not train on the login node: every design runs as a job."
    forbid:                        # refused by code, whoever asks
      qos: [urgent]
      partition: [debug]

It is looked for, in order: `site.yaml` in the search folder; the file named by the environment variable
EVOLOOP_SITE (`none` switches site files off); `~/.config/evoloop/site.yaml`. Its `compute` values come right
after the defaults, so a brief that sets something itself still wins. `evoloop site --detect` drafts one from
what the machine reports."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

FIELDS = ("name", "compute", "rules", "forbid", "notes")
_cache: Dict[str, Tuple[float, Any]] = {}


def find(folder: Optional[str] = None) -> Optional[str]:
    named = os.environ.get("EVOLOOP_SITE")
    if named == "none":
        return None
    tries = [os.path.join(folder, "site.yaml")] if folder else []
    if named:
        tries.append(os.path.expanduser(named))
    tries.append(os.path.join(os.path.expanduser("~"), ".config", "evoloop", "site.yaml"))
    for path in tries:
        if os.path.isfile(path):
            return path
    return None


def check(raw: Any) -> Optional[str]:
    from . import form
    if not isinstance(raw, dict):
        return "the site file must be a mapping"
    extra = set(raw) - set(FIELDS)
    if extra:
        return "the site file has unknown entries: %s" % ", ".join(sorted(extra))
    compute = raw.get("compute") or {}
    if not isinstance(compute, dict):
        return "compute must be a mapping"
    for key, value in compute.items():
        if key not in form.DEFAULTS["compute"]:
            return "compute.%s is not a compute setting (see `evoloop menu fields`)" % key
        fault = form.check_value("compute.%s" % key, value)
        if fault:
            return fault
    if not isinstance(raw.get("rules") or [], list) or not all(isinstance(r, str) for r in raw.get("rules") or []):
        return "rules must be a list of text"
    forbid = raw.get("forbid") or {}
    if not isinstance(forbid, dict) or set(forbid) - {"qos", "partition"} or not all(
            isinstance(v, list) and all(isinstance(x, str) for x in v) for v in forbid.values()):
        return "forbid must map qos and partition to lists of names"
    return None


def load(folder: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """(the site, None), (None, why its file cannot be used), or (None, None) when there is no site file."""
    path = find(folder)
    if path is None:
        return None, None
    try:
        stamp = os.path.getmtime(path)
        if path in _cache and _cache[path][0] == stamp:
            return _cache[path][1]
        with open(path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        return None, "the site file %s cannot be read: %s" % (path, exc)
    fault = check(raw)
    if fault:
        out: Tuple[Optional[Dict[str, Any]], Optional[str]] = (None, "the site file %s cannot be used: %s" % (path, fault))
    else:
        forbid = raw.get("forbid") or {}
        out = ({"name": str(raw.get("name") or "this machine"), "path": path, "compute": raw.get("compute") or {},
                "rules": list(raw.get("rules") or []),
                "forbid": {"qos": list(forbid.get("qos") or []), "partition": list(forbid.get("partition") or [])}}, None)
    _cache[path] = (stamp, out)
    return out


def names_of(value: Any) -> List[str]:
    """The QoS or partition names in a setting: one name, or a list of names or of {name: ...}."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v.get("name")) if isinstance(v, dict) else str(v) for v in value]
    return []


def forbidden(site: Optional[Dict[str, Any]], key: str, value: Any) -> Optional[str]:
    """Why this machine does not allow a compute setting to take this value, or None."""
    if not site:
        return None
    kind = {"compute.qos": "qos", "compute.partition": "partition"}.get(key)
    if not kind:
        return None
    hit = [n for n in names_of(value) if n in site["forbid"][kind]]
    return ("the %s %s is not to be used on %s (its site file, %s, forbids it)" % (kind, ", ".join(hit), site["name"], site["path"])
            if hit else None)


def fault(site: Optional[Dict[str, Any]], settings: Dict[str, Any]) -> Optional[str]:
    for key in ("compute.qos", "compute.partition"):
        why = forbidden(site, key, settings["compute"].get(key.split(".")[1]))
        if why:
            return why
    return None


def _run(argv: List[str]) -> Optional[str]:
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def detect(run: Callable[[List[str]], Optional[str]] = _run, which: Callable[[str], Optional[str]] = shutil.which) -> Dict[str, Any]:
    """What this machine reports about itself: the scheduler, its partitions, QoS names and GPU types. Only
    queries are made (sinfo, sacctmgr, scontrol, nvidia-smi); nothing is submitted."""
    found: Dict[str, Any] = {"scheduler": "local", "name": socket.gethostname().split(".")[0], "partitions": [], "qos": [],
                             "gpu_types": [], "local_gpus": 0, "other_schedulers": [c for c in ("qsub", "bsub") if which(c)],
                             "notes": []}
    listed = run(["nvidia-smi", "-L"]) if which("nvidia-smi") else None
    found["local_gpus"] = len([line for line in (listed or "").splitlines() if line.strip().startswith("GPU ")])
    if not which("sbatch"):
        if found["other_schedulers"]:
            found["notes"].append("this machine has %s: evoloop submits to Slurm or runs locally; another scheduler needs a "
                                  "backend of its own (see the documentation)" % ", ".join(found["other_schedulers"]))
        return found
    found["scheduler"] = "slurm"
    config = run(["scontrol", "show", "config"]) or ""
    for line in config.splitlines():
        if line.strip().startswith("ClusterName"):
            found["name"] = line.split("=", 1)[1].strip()
    for line in (run(["sinfo", "-h", "-o", "%P|%a|%l|%G|%D"]) or "").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5:
            continue
        name, default = parts[0].rstrip("*"), parts[0].endswith("*")
        types = sorted({g.split(":")[1] for g in parts[3].split(",") if g.startswith("gpu:") and len(g.split(":")) >= 3
                        and not g.split(":")[1].isdigit()})
        row = next((p for p in found["partitions"] if p["name"] == name), None)
        if row is None:
            row = {"name": name, "default": default, "up": parts[1] == "up", "time_limit": parts[2], "gpus": False, "gpu_types": []}
            found["partitions"].append(row)
        row["gpus"] = row["gpus"] or "gpu" in parts[3]
        row["gpu_types"] = sorted(set(row["gpu_types"]) | set(types))
        found["gpu_types"] = sorted(set(found["gpu_types"]) | set(types))
    found["qos"] = sorted({line.strip() for line in (run(["sacctmgr", "-nP", "show", "qos", "format=Name"]) or "").splitlines()
                           if line.strip()})
    if not found["partitions"]:
        found["notes"].append("sinfo listed no partition: fill in compute.partition by hand")
    return found


def draft(found: Dict[str, Any]) -> str:
    """A site file drafted from what was detected, with what could not be known left for the person."""
    lines = ["# Site file for evoloop: what is particular to this machine. Drafted from what the machine reports;",
             "# check every line. Keep it at ~/.config/evoloop/site.yaml (every search here then uses it), or as",
             "# site.yaml in one search's folder.",
             "name: %s" % found["name"], "compute:", "  scheduler: %s" % found["scheduler"]]
    if found["scheduler"] == "slurm":
        with_gpus = [p for p in found["partitions"] if p["gpus"] and p["up"]]
        pick = (with_gpus or [p for p in found["partitions"] if p["default"]] or found["partitions"] or [None])[0]
        lines.append("  partition: %s%s" % (pick["name"] if pick else "null", "        # partitions here: %s" % ", ".join(
            "%s%s" % (p["name"], " (GPUs)" if p["gpus"] else "") for p in found["partitions"]) if found["partitions"] else ""))
        lines.append("  qos: null%s" % ("              # QoS names here: %s" % ", ".join(found["qos"]) if found["qos"] else
                                        "              # a name, or a list in order of preference"))
        lines.append("  gpu_type: null%s" % ("         # GPU types here: %s" % ", ".join(found["gpu_types"]) if found["gpu_types"] else ""))
        if pick and pick.get("time_limit") and pick["time_limit"] != "infinite":
            lines.append("  time_limit: \"%s\"   # the most this partition allows; a shorter limit often starts sooner" % pick["time_limit"])
        lines += ["  setup: []              # shell lines run first in every job: module loads, activating an environment",
                  "  extra_sbatch: []       # further sbatch options your site needs, e.g. \"--account=mylab\"",
                  "rules:", "  - \"Do not train on the login node: every design runs as a job.\"",
                  "forbid:", "  qos: []                # QoS names never to be used here (for instance one that preempts other people's jobs)",
                  "  partition: []"]
    else:
        lines.append("  gpus: %s%s" % (found["local_gpus"] or 1, "                # GPUs seen on this machine" if found["local_gpus"]
                                       else "                # how many designs may train at once here"))
        lines += ["rules: []", "forbid: {qos: [], partition: []}"]
    lines += ["# %s" % note for note in found["notes"]]
    return "\n".join(lines) + "\n"
