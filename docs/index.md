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

<div class="evo-map" markdown="0">
  <div class="evo-map-side">
    <h4>You provide</h4>
    <ul>
      <li><b>Your code</b>with the parts that may change marked</li>
      <li><b>A scoring script</b>that measures one version</li>
      <li><b>A budget</b>evaluations, and dollars for the agents</li>
    </ul>
  </div>
  <div class="evo-map-loop">
    <h4>The loop, repeated until the budget is spent</h4>
    <div class="evo-map-steps">
      <div class="evo-step">
        <div class="evo-step-top"><span class="evo-step-n">1</span><span class="evo-step-name">Choose</span>
          <p class="evo-step-what">Pick which earlier versions to build on, and what kind of change to try.</p>
          <span class="evo-who">evoloop's code</span></div>
        <div class="evo-step-choice"><span>Your choice</span><b>Search strategy</b>Keep several families alive, keep the best of each size, or follow the single best. <a href="parents/">Five strategies</a></div>
      </div>
      <div class="evo-step">
        <div class="evo-step-top"><span class="evo-step-n">2</span><span class="evo-step-name">Propose</span>
          <p class="evo-step-what">Write the new version: new contents for the marked parts.</p>
          <span class="evo-who agent">an LLM agent</span></div>
        <div class="evo-step-choice"><span>Your choice</span><b>What may change</b>Hyperparameters only, the training recipe, or the whole architecture. <a href="moves/">Moves</a></div>
      </div>
      <div class="evo-step">
        <div class="evo-step-top"><span class="evo-step-n">3</span><span class="evo-step-name">Score</span>
          <p class="evo-step-what">Run your script on the new version, as its own job.</p>
          <span class="evo-who">your script</span></div>
        <div class="evo-step-choice"><span>Your choice</span><b>What is measured</b>Your metric, on your data. Weak versions can be stopped part way. <a href="evaluator/">Evaluator</a></div>
      </div>
      <div class="evo-step">
        <div class="evo-step-top"><span class="evo-step-n">4</span><span class="evo-step-name">Record</span>
          <p class="evo-step-what">Keep the version, its parent and its score. Compare it with the rest.</p>
          <span class="evo-who">evoloop's code</span></div>
        <div class="evo-step-choice"><span>Your choice</span><b>Limits</b>Hard bounds, such as a largest model size, that no version may break. <a href="cost/">Budget and limits</a></div>
      </div>
    </div>
    <div class="evo-map-back">&#8634; each result changes what is chosen next</div>
  </div>
  <div class="evo-map-side">
    <h4>You get</h4>
    <ul>
      <li><b>A leaderboard</b>the best versions, beside your baseline</li>
      <li><b>Every version tried</b>with its code, parent and score</li>
      <li><b>One JSON file</b>the whole search, ready for CAMEO</li>
    </ul>
  </div>
  <div class="evo-map-across">
    <div class="evo-across"><b>How much the agents decide</b>From code planning every move to agents choosing the moves and adjusting the schedule. <a href="agents/">Agents</a></div>
    <div class="evo-across"><b>A skill, if you want one</b>Settings and agent guidance for one goal, such as distillation. Editable. <a href="which-search/">Skills</a></div>
    <div class="evo-across"><b>Where to start from</b>Your baseline, an earlier search, or designs from CAMEO. <a href="warm-start/">Start from earlier designs</a></div>
    <div class="evo-across"><b>Steering while it runs</b>Change settings, send the agents a note, or stop. <a href="steering/">Monitor and steer</a></div>
  </div>
</div>

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
