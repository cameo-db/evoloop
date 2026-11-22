# Run on a cluster

A search is described in two files. The *brief* says what to optimize and how to search, and should
move between machines unchanged. The *site file* says what is particular to one machine: its
scheduler, its queues, its GPUs, how an environment is activated, and what is not allowed there. Every
cluster differs in these, even two that both run Slurm. `evoloop plan` combines the two and shows what
will run and where.

## The site file

```
evoloop site --detect                                          # prints a draft from what this machine reports
evoloop site --detect --write ~/.config/evoloop/site.yaml      # or writes it
```

Detection only asks questions (`sinfo`, `sacctmgr`, `scontrol`, `nvidia-smi`); nothing is submitted. It
finds whether the machine has Slurm, the partitions and which have GPUs, the GPU types, the QoS names
and the longest time a partition allows. It cannot know what your group's account is, how you activate
your environment, or which queues you should avoid. Those you fill in:

```yaml
name: our-cluster
compute:
  scheduler: slurm
  partition: gpu
  qos: [{name: normal, max_jobs: 8}, {name: low}]     # in order of preference; each job goes to the first with room
  gpu_type: a100
  time_limit: "1-00:00:00"
  setup:                       # shell lines run first in every job
    - module load cuda/12
    - source ~/envs/train/bin/activate
  extra_sbatch:                # further sbatch options your site needs
    - "--account=mylab"
rules:                         # shown in every plan, and to an agent helping to set up a search
  - "Do not train on the login node: every design runs as a job."
  - "Scratch files go under /scratch/$USER, not /tmp."
forbid:                        # refused by code, whoever asks
  qos: [urgent]                # for instance a QoS that preempts other people's jobs
  partition: [debug]
```

| Part | What it does |
|---|---|
| `compute` | defaults for the [compute settings](fields.md) of every search on this machine. A brief that sets one itself still wins |
| `rules` | text. Printed at the top of every plan, so that you and an agent helping you both see them |
| `forbid` | QoS and partition names that are never used. A brief that asks for one does not start, and a change during a run that asks for one is refused and recorded |

Where it is looked for, in order:

1. `site.yaml` in the search's own folder;
2. the file named by the environment variable `EVOLOOP_SITE` (`none` switches site files off);
3. `~/.config/evoloop/site.yaml`.

`evoloop site` shows the one in use and what it sets. `evoloop plan` says where designs will run
("Runs on: Slurm, one job per design, partition gpu, qos normal, low, 8 at once (site file:
our-cluster)") and lists the site's rules.

## Machine-specific settings

| What differs | Where it goes |
|---|---|
| the scheduler | `compute.scheduler`: `slurm` or `local` |
| the queue | `compute.partition`, `compute.qos` (one name, or a list in order of preference with a cap on each) |
| the hardware | `compute.gpu_type`, `compute.gpus_per_job`, `compute.cpus_per_job`, `compute.mem_gb` |
| time limits | `compute.time_limit`; a job that hits it is started again from its checkpoint, a limited number of times |
| the environment | `compute.setup`: module loads, activating an environment, exporting paths |
| accounts, reservations, constraints, anything else | `compute.extra_sbatch`: any option `sbatch` accepts, one per line |
| how many jobs you may hold | `compute.gpus` (how many train at once), `compute.max_waiting` (how many may queue unstarted) |
| what must not be done | `rules` (for people and agents) and `forbid` (for code) |
| login-node rules | run the controller itself as a job: `evoloop controller` writes the script, and it requeues itself at its time limit |
| preemption | each design is its own job, submitted with `--requeue`; a preempted job keeps its id and resumes from its checkpoint |

## With an agent

An agent helping you can do this for you: ask it to run `evoloop site --detect`, read the draft with
you, and ask you only for what the machine cannot report (the account, the environment, the queues to
avoid). Once the file exists, the agent sees the site's rules in every plan.

## Not supported

- Schedulers other than Slurm. PBS, LSF and Grid Engine are not built in. `evoloop site --detect`
  says so when it finds `qsub` or `bsub`. Adding one means writing a backend with three operations
  (submit a job, ask its state, cancel it) beside the Slurm one in `evoloop/jobs.py`. On such a machine
  today, evoloop can still run designs as local processes inside one allocation you hold
  (`compute.scheduler: local`).
- Cloud and container platforms (Kubernetes, batch services): not built in, for the same reason.
- Detection is a draft. It reads what the scheduler reports and has only been tested against made-up
  scheduler output, not on a real cluster. Expect to correct it.
- Rules are text. Only `forbid` is enforced by code; a rule such as "scratch goes under /scratch"
  is for you and the agent to follow.
