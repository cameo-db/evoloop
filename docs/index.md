---
hide:
  - navigation
---

# evoloop

**evoloop improves code you can score.** You mark the parts of your code that may change and write a
script that measures how good one version is. evoloop then runs an evolutionary search: LLM agents
propose changes, your script scores each one, and the results decide what is tried next.

Use it to raise a model's validation score, train a smaller student from a teacher, tune
hyperparameters, or make an algorithm or pipeline faster while its output stays the same.

[Set up a search](setting-up.md){ .md-button .md-button--primary }
[Explore the search options](options.md){ .md-button }
[Source on GitHub](https://github.com/cameo-db/evoloop){ .md-button }

<style>
.evo-flow { display: flex; flex-wrap: wrap; align-items: stretch; gap: 10px; margin: 28px 0 8px; }
.evo-flow > div { flex: 1 1 150px; border: 1px solid #9aa5a3; border-radius: 12px; padding: 16px 14px; }
.evo-flow > div.evo-flow-step { border: 2px solid #01796e; }
.evo-flow .evo-flow-arrow { flex: 0 0 auto; border: 0; padding: 0; align-self: center; font-size: 26px; color: #01796e; }
.evo-flow b { display: block; font-size: 20px; margin-bottom: 6px; }
.evo-flow span { display: block; font-size: 14px; line-height: 1.4; }
.evo-flow em { display: block; font-style: normal; font-size: 13px; line-height: 1.4; margin-top: 10px; padding-top: 10px; border-top: 1px dashed #9aa5a3; }
.evo-flow-note { text-align: center; font-size: 14px; margin: 0 0 24px; }
</style>
<div class="evo-flow">
  <div><b>You provide</b><span>Code with the parts that may change marked, and a script that scores one version.</span></div>
  <div class="evo-flow-arrow">&rarr;</div>
  <div class="evo-flow-step"><b>1. Choose</b><span>evoloop's code picks which earlier version to build on.</span><em>You choose the search strategy.</em></div>
  <div class="evo-flow-arrow">&rarr;</div>
  <div class="evo-flow-step"><b>2. Propose</b><span>An LLM agent writes a changed version.</span><em>You choose what may change and how much the agents decide.</em></div>
  <div class="evo-flow-arrow">&rarr;</div>
  <div class="evo-flow-step"><b>3. Score</b><span>Your script runs on it, as a job.</span><em>You choose the metric and the budget.</em></div>
  <div class="evo-flow-arrow">&rarr;</div>
  <div><b>You get</b><span>A leaderboard, every version with its score, and the search as one JSON file.</span></div>
</div>
<p class="evo-flow-note">Steps 1 to 3 repeat, many versions at a time. Each result changes what is chosen next.</p>

Agents write the changes. Code does everything that must be trusted: it picks what to build on, checks
that only the marked parts changed, runs the jobs, enforces the budget and your limits, and keeps the
record. The search runs on a laptop or on a Slurm cluster.

!!! tip "Recommended: run it through Claude Code"
    Open the evoloop repository in [Claude Code](https://claude.com/claude-code) and say what you want to improve.
    It sets up the search with you by asking the questions one at a time, starts the run when you confirm the
    plan, and watches it: it reports progress, reads the results with you, and turns your feedback into changes
    to the running search. You do not need to learn the commands first.

## Three ways to run it

evoloop is a Python package with a command line. You can drive it at whichever level you like.

| | What you do |
|---|---|
| **Let an agent run it** | Open the repository in Claude Code or another coding agent and say what you want to improve. The agent asks you the setup questions one at a time, marks the code and writes the scoring script with you, shows you the plan, and starts the search when you confirm. It follows [AGENTS.md](https://github.com/cameo-db/evoloop/blob/main/AGENTS.md). |
| **Answer the questions yourself** | `evoloop setup` asks the same questions in the terminal. `evoloop form` gives them as a web page. [Set up a search](setting-up.md). |
| **Edit the files** | Everything is a plain file you can open and change: the brief (`brief.yaml`), the task description the agents read, and the skill files. [Brief fields](fields.md) · [Commands](commands.md). |

Every search starts the same way, whichever you choose: a short list of questions, a plan that states
what will run and what it is likely to cost, and your confirmation. Nothing is spent before you confirm.
While it runs you can change settings, send the agents a note, or stop it.
[Monitor and steer a search](steering.md).

## Search strategies

The strategy decides which versions are built on. Each follows a known method.

| Strategy | Builds on | Known as |
|---|---|---|
| `lineage` (default) | the best version of each of several families, so a slow starter is not crowded out | speciation, as in NEAT |
| `archive` | the best version in each cell of a grid, such as each size band | MAP-Elites; with islands, AlphaEvolve's program database |
| `tournament` | the best of a few drawn from the most recent versions | regularized evolution |
| `pareto` | versions not beaten on both the score and a second measure, such as size | non-dominated sorting, as in NSGA-II |
| `greedy` | the single best version | hill climbing |

Any strategy can run as separate populations that are restarted from the best one, as in FunSearch.
[How evoloop compares with FunSearch and AlphaEvolve](compared.md).

## Skills

A skill is optional. It is a file that adapts the general search to one goal, such as distillation or a
faster algorithm: it sets the choices above and gives the agents guidance for that goal. Without one you
supply that guidance yourself in the task description.

The library has thirteen. During setup you can read the one you chose, edit it, or merge several into
one file. [Choose a skill](which-search.md) · [Edit, merge or write a skill](skills.md)

## CAMEO: start from other searches, and add yours

[CAMEO](https://cameo-db.github.io) is a public database of models, with their code, how they were trained
and how they scored. evoloop reads and writes its format.

- **In:** `evoloop import --from-study` takes designs from a CAMEO study file. Designs from the same project are
  trained in your search. Designs from other data are shown to the agents as ideas to adapt.
- **Out:** every search writes `study.json`, the whole search in one file in the CAMEO format, ready to deposit.

[Start from earlier designs](warm-start.md) · [Save and deposit the study](study.md)

## Read next

| To | Read |
|---|---|
| start on your own project | [Set up a search](setting-up.md) · [Write the evaluator](evaluator.md) · [Run on a cluster](servers.md) |
| understand the loop | [How it works](how-it-works.md) · [Search options on one page](options.md) |
| see it run on a toy problem | [Worked example](quickstart.md) |
| look something up | [Reference](reference.md) |

Version 0.2. evoloop passes its tests with a script standing in for the LLM. It has not yet been run
with a real LLM on a real training task. [Status and limits](status.md).
