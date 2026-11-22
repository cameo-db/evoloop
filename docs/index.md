---
hide:
  - navigation
---

# evoloop

**evoloop is agent-led optimization of code you can score.** You mark the parts of your code that may change and write a
script that measures how good one version is. evoloop then runs an evolutionary search: LLM agents
propose changes, your script scores each one, and the results decide what is tried next.

<svg viewBox="0 0 1220 690" role="img" aria-label="The evoloop loop: LLM agents propose a change, code runs and scores it, agents analyze the results, and the lessons go into the next proposal. Every version and score is recorded." style="width:100%;max-width:920px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#8c95a1"/></marker>
    <marker id="evo-b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker>
  </defs>
  <g fill="none" stroke="#8c95a1" stroke-width="3.5">
    <path d="M756 148 Q920 160 978 282" marker-end="url(#evo-a)"/>
    <path d="M980 406 Q930 530 772 544" marker-end="url(#evo-a)"/>
    <path d="M468 544 Q300 532 248 410" marker-end="url(#evo-a)"/>
    <path d="M245 286 Q300 160 464 148" marker-end="url(#evo-a)"/>
  </g>
  <g fill="none" stroke="currentColor" stroke-width="3.5">
    <path d="M240 102 H464" marker-end="url(#evo-b)"/>
    <path d="M756 590 H976" marker-end="url(#evo-b)"/>
  </g>
  <g stroke-width="3">
    <rect x="60" y="50" width="174" height="105" rx="16" fill="#f1f3f5" stroke="#9aa3ad"/>
    <rect x="988" y="538" width="174" height="105" rx="16" fill="#f1f3f5" stroke="#9aa3ad"/>
    <rect x="475" y="72" width="275" height="106" rx="16" fill="#e6eefb" stroke="#2a5db0"/>
    <rect x="122" y="293" width="247" height="106" rx="16" fill="#e6eefb" stroke="#2a5db0"/>
    <rect x="856" y="293" width="248" height="106" rx="16" fill="#e7f2ea" stroke="#3a7d4b"/>
    <rect x="475" y="514" width="275" height="106" rx="16" fill="#e7f2ea" stroke="#3a7d4b"/>
  </g>
  <g text-anchor="middle" font-weight="700" font-size="23">
    <text x="147" y="90" fill="#1c1f23" font-size="20">Your code</text>
    <text x="1075" y="578" fill="#1c1f23" font-size="20">Best</text>
    <text x="612" y="114" fill="#2a5db0">Propose</text>
    <text x="245" y="335" fill="#2a5db0">Analyze</text>
    <text x="980" y="335" fill="#3a7d4b">Run</text>
    <text x="612" y="556" fill="#3a7d4b">Score</text>
    <text x="612" y="332" fill="currentColor" font-size="20">Record</text>
  </g>
  <g text-anchor="middle" font-size="17" fill="#1c1f23">
    <text x="147" y="131">+ a scoring script</text>
    <text x="1075" y="619">versions</text>
    <text x="612" y="157">a writer agent</text>
    <text x="245" y="378">analyst · strategist</text>
    <text x="980" y="378">jobs, in parallel</text>
    <text x="612" y="598">your script</text>
  </g>
  <g text-anchor="middle" font-size="17" fill="currentColor" opacity="0.7">
    <text x="612" y="374">every version and score</text>
    <g font-style="italic">
      <text x="838" y="241">new version</text>
      <text x="838" y="462">finished runs</text>
      <text x="388" y="462">results</text>
      <text x="388" y="241">lessons</text>
    </g>
  </g>
  <g font-size="17" fill="currentColor">
    <rect x="42" y="651" width="32" height="23" rx="6" fill="#e6eefb" stroke="#2a5db0" stroke-width="2.5"/>
    <text x="87" y="668">LLM agents</text>
    <rect x="235" y="651" width="32" height="23" rx="6" fill="#e7f2ea" stroke="#3a7d4b" stroke-width="2.5"/>
    <text x="280" y="668">code</text>
  </g>
</svg>

Agents propose changes and learn from the results. Code runs every version, scores it with your script,
keeps the record, and decides which versions are built on.

Use it to raise a model's validation score, train a smaller student from a teacher, tune
hyperparameters, or make an algorithm or pipeline faster while its output stays the same.

[Set up a search](setting-up.md){ .md-button .md-button--primary }
[Explore the search options](options.md){ .md-button }
[Source on GitHub](https://github.com/cameo-db/evoloop){ .md-button }

How much the agents decide is a setting, from writing each version only to also choosing the moves.
Code always enforces the budget and your limits. [Agents](agents.md) · [How it works](how-it-works.md).
The search runs on a laptop or on a Slurm cluster.

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
