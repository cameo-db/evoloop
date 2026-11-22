---
hide:
  - navigation
---

# evoloop

**evoloop is agent-led optimization of code you can score.** You mark the parts of your code that may change and write a
script that measures how good one version is. evoloop then runs an evolutionary search: LLM agents
propose changes, your script scores each one, and the results decide what is tried next.

<style>
.evo-ring { display: grid; grid-template-columns: minmax(0, 1fr) 56px minmax(0, 1fr); gap: 10px; margin: 28px auto 14px; max-width: 980px; }
.evo-ring .box { border: 2px solid #8a9694; border-radius: 14px; padding: 18px 18px 16px; }
.evo-ring .box.agent, .evo-others .box.agent { border-color: #01796e; background: #01796e; color: #fff; }
.evo-ring .box b { display: block; font-size: 22px; margin-bottom: 6px; }
.evo-ring .box span, .evo-others .box span { display: block; font-size: 15px; line-height: 1.45; }
.evo-ring .tag, .evo-others .tag { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; border: 1px solid currentColor; border-radius: 999px; padding: 2px 10px; margin-bottom: 10px; }
.evo-ring .arrow { display: flex; align-items: center; justify-content: center; font-size: 34px; color: #01796e; }
.evo-ring .mid { display: flex; align-items: center; justify-content: center; text-align: center; font-size: 14px; line-height: 1.4; padding: 6px 0; grid-column: 1 / -1; }
.evo-ring .mid div { border: 1px dashed #8a9694; border-radius: 12px; padding: 10px 18px; max-width: 520px; }
.evo-ring .updown { display: flex; justify-content: space-around; grid-column: 1 / -1; font-size: 34px; color: #01796e; line-height: 1; }
.evo-others { display: flex; flex-wrap: wrap; gap: 10px; margin: 0 auto 10px; max-width: 980px; }
.evo-others .box { flex: 1 1 200px; border: 2px solid #01796e; border-radius: 14px; padding: 14px 16px; }
.evo-others .box b { display: block; font-size: 17px; margin-bottom: 4px; }
.evo-key { max-width: 980px; margin: 0 auto 26px; font-size: 14px; }
.evo-key i { display: inline-block; width: 14px; height: 14px; border-radius: 4px; vertical-align: -2px; margin: 0 6px 0 14px; border: 2px solid #8a9694; }
.evo-key i.a { background: #01796e; border-color: #01796e; margin-left: 0; }
</style>
<div class="evo-ring">
  <div class="box"><span class="tag">Code</span><b>1. Choose</b><span>The search strategy picks which earlier version to build on, and the schedule picks the kind of change.</span></div>
  <div class="arrow">&rarr;</div>
  <div class="box agent"><span class="tag">Agent: writer</span><b>2. Propose</b><span>An LLM writes the changed version, with a reason and a forecast of its effect.</span></div>
  <div class="updown"><span>&uarr;</span><span>&darr;</span></div>
  <div class="box"><span class="tag">Code</span><b>4. Record</b><span>The version, its parent, its score and the forecast are written to the search's files. Budget and limits are enforced.</span></div>
  <div class="arrow">&larr;</div>
  <div class="box"><span class="tag">Code + your script</span><b>3. Check and score</b><span>Code checks that only the marked parts changed, then runs your scoring script on the version as a job.</span></div>
</div>
<div class="evo-others">
  <div class="box agent"><span class="tag">Agent &middot; on by default</span><b>Analyst</b><span>Every 8 versions, reads the results and writes lessons the writer is given.</span></div>
  <div class="box agent"><span class="tag">Agent &middot; on in most run types</span><b>Strategist</b><span>Every 15 versions or on a plateau, may shift the schedule within bounds you set.</span></div>
  <div class="box agent"><span class="tag">Agent &middot; optional</span><b>Coordinator</b><span>Picks the kind of change at step 1, in place of the schedule.</span></div>
  <div class="box agent"><span class="tag">Agent &middot; on by default</span><b>Assessor</b><span>Part way through, reviews how the other agents are doing, for you.</span></div>
</div>
<p class="evo-key"><i class="a"></i>an LLM agent<i></i>deterministic code, or your own script. Only the writer is required. You can steer at any point, yourself or through Claude Code.</p>

Use it to raise a model's validation score, train a smaller student from a teacher, tune
hyperparameters, or make an algorithm or pipeline faster while its output stays the same.

[Set up a search](setting-up.md){ .md-button .md-button--primary }
[Explore the search options](options.md){ .md-button }
[Source on GitHub](https://github.com/cameo-db/evoloop){ .md-button }

Agents propose and advise. Code does everything that must be trusted: it picks what to build on, checks
each version, runs the jobs, enforces the budget and your limits, and keeps the record. How much the
agents decide is a setting, from writing only to choosing the moves. [Agents](agents.md). The search runs
on a laptop or on a Slurm cluster.

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
