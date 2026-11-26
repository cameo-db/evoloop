# Run on a cluster

A search is described in two files. The *brief* says what to optimize and how to search, and should
move between machines unchanged. The *site file* says what is particular to one machine: its
scheduler, its queues, its GPUs, how an environment is activated, and what is not allowed there. Every
cluster differs in these, even two that both run Slurm. `evoloop plan` combines the two and shows what
will run and where.

## Setup by an agent

An agent can work out a machine for you. Open the repository in Claude Code on the cluster and ask it
to set evoloop up there. It runs `evoloop site --detect`, which only queries the scheduler and submits
nothing, reads the draft with you, and asks for the three things the machine cannot report: the
account to charge, how your environment is activated, and which queues to avoid. It then writes the
site file and proves it with a dry run. From then on the site's rules are printed in every plan, where
you and the agent both see them.

Slurm and local processes are built in. On a machine with another scheduler (PBS, LSF, Grid Engine,
Kubernetes, a cloud batch service), ask the agent to add it. A scheduler is one class in
[`evoloop/jobs.py`](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py) with four methods:
`submit` a job, report its `state`, `cancel` it, and `shutdown`, plus a line to register its name. The
Slurm class beside it is the model. Until that is written, evoloop can run designs as local processes inside one allocation you
hold (`compute.scheduler: local`).

The rest of this page is what the agent writes, in case you want to read or change it yourself.

## The site file

```
evoloop site --detect                  # print a draft
evoloop site --detect --write ~/.config/evoloop/site.yaml
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
| `rules` | text, for you and the agent to follow. Printed at the top of every plan. Not enforced by code |
| `forbid` | QoS and partition names that are never used. A brief that asks for one does not start, and a change during a run that asks for one is refused and recorded |

Where it is looked for, in order:

1. `site.yaml` in the search's own folder;
2. the file named by the environment variable `EVOLOOP_SITE` (`none` switches site files off);
3. `~/.config/evoloop/site.yaml`.

`evoloop site` shows the one in use and what it sets. `evoloop plan` says where designs will run
("Runs on: Slurm, one job per design, submitted as GPUs come free, partition gpu, qos normal, low, 8 at
once, 4:00:00 per job (site file: our-cluster)") and lists the site's rules.

## Getting GPUs

Two choices decide how much GPU time a search gets out of a shared cluster. Setup asks both.

**One job per design, or one block.** With `compute.allocation: per_design`, the default, each design
is a job of its own, submitted when a GPU comes free. A one-GPU job starts sooner than a job that needs
eight at once, and the search uses whatever is free, up to `compute.gpus` jobs.

Designs are written just in time. No new design is written while one job is still waiting for its first
start. A waiting job takes its design at the moment it starts, so if results arrive in the meantime that
overtake the design, another is written and takes the same job, which keeps its place in the queue. A
design is overtaken when it edits a parent that another design of the same lineage has since beaten.

With `compute.allocation: block`, one job holds every GPU for the whole search and the designs train
inside it, each on a GPU of its own. Nothing waits in the queue between designs. The job is harder to
schedule, and its GPUs are held while a design is being written. It suits a reservation or a machine
you have to yourself. A block is started as a job:

```
evoloop controller mysearch --name r1
sbatch mysearch/run_controller_r1.sbatch
```

**A short time limit.** A job that asks for four hours starts sooner than one that asks for two days.
A training run does not have to fit in one job: when a job reaches `compute.time_limit`, or is
preempted, the run is submitted again and continues from its checkpoint, for as long as each start
gets further than the last. This needs an evaluator that saves its state and resumes, which the
template from `evoloop init` does: [Interruptions](evaluator.md#interruptions). With an evaluator that
starts over, set a limit longer than one training run.

On a workstation (`compute.scheduler: local`) each job is given its own GPU through
`CUDA_VISIBLE_DEVICES`, from the GPUs the machine has or the ones already named in that variable.

## Machine-specific settings

| What differs | Where it goes |
|---|---|
| the scheduler | `compute.scheduler`: `slurm` or `local` |
| how GPUs are obtained | `compute.allocation`: `per_design` or `block` |
| the queue | `compute.partition`, `compute.qos` (one name, or a list in order of preference with a cap on each) |
| the hardware | `compute.gpu_type`, `compute.gpus_per_job`, `compute.cpus_per_job`, `compute.mem_gb` |
| time limits | `compute.time_limit`, per start of a job; a run that reaches it continues in another job |
| the environment | `compute.setup`: module loads, activating an environment, exporting paths |
| accounts, reservations, constraints, anything else | `compute.extra_sbatch`: any option `sbatch` accepts, one per line |
| how many jobs you may hold | `compute.gpus` (how many train at once), `compute.max_waiting` (how many may queue unstarted) |
| what must not be done | `rules` (for people and agents) and `forbid` (for code) |
| login-node rules | run the controller itself as a job: `evoloop controller` writes the script, and it requeues itself at its time limit |
| preemption | a preempted job is started again and continues from its checkpoint, like one that reached its time limit |

