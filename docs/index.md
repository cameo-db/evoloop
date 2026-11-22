---
hide:
  - navigation
---

# evoloop

**evoloop is agent-led optimization of code you can score.** You mark the parts of your code that may change and write a
script that measures how good one version is. evoloop then runs an evolutionary search: LLM agents
propose changes, your script scores each one, and the results decide what is tried next.

<style>
.evo-loop-list { display: none; }
@media screen and (max-width: 620px) { .evo-loop-svg { display: none !important; } .evo-loop-list { display: block; } }
</style>
<svg class="evo-loop-svg" viewBox="0 0 1200 720" role="img" aria-label="The evoloop loop. Code picks a version to improve, an LLM agent writes a change to it, your script runs and scores it, and code adds it to the leaderboard. Every few versions, optional LLM agents review the results and advise the writer and the picking rule." style="width:100%;max-width:940px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7d8790"/></marker>
    <marker id="evo-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#01796e"/></marker>
  </defs>
  <g fill="none" stroke="#7d8790" stroke-width="3.5">
    <path d="M190 284 Q220 105 436 92" marker-end="url(#evo-a)"/>
    <path d="M760 92 Q985 100 1020 262" marker-end="url(#evo-a)"/>
    <path d="M1010 404 Q980 575 772 592" marker-end="url(#evo-a)"/>
    <path d="M440 592 Q220 575 190 410" marker-end="url(#evo-a)"/>
    <path d="M100 568 V410" marker-end="url(#evo-a)"/>
    <path d="M100 134 V276" marker-end="url(#evo-a)" stroke-dasharray="3 6"/>
    <path d="M760 626 H936" marker-end="url(#evo-a)"/>
  </g>
  <g fill="none" stroke="#01796e" stroke-width="3" stroke-dasharray="9 7">
    <path d="M600 538 V408" marker-end="url(#evo-t)"/>
    <path d="M600 288 V160" marker-end="url(#evo-t)"/>
    <path d="M468 342 H354" marker-end="url(#evo-t)"/>
  </g>
  <g stroke-width="3">
    <rect x="40" y="290" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="450" y="40" width="300" height="106" rx="16" fill="#01796e" stroke="#01796e"/>
    <rect x="876" y="274" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#aab2b8"/>
    <rect x="868" y="282" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#8a949b"/>
    <rect x="860" y="290" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="450" y="546" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="470" y="294" width="260" height="100" rx="16" fill="#dff1ee" stroke="#01796e" stroke-dasharray="9 7"/>
  </g>
  <g text-anchor="middle" font-weight="700" font-size="21">
    <text x="190" y="334" fill="#1c2326">1. Pick a version to improve</text>
    <text x="600" y="84" fill="#ffffff">2. Write a change to it</text>
    <text x="1010" y="334" fill="#1c2326">3. Run it and score it</text>
    <text x="600" y="590" fill="#1c2326">4. Add it to the leaderboard</text>
    <text x="600" y="336" fill="#0f3f39">Review the results</text>
  </g>
  <g text-anchor="middle" font-size="17">
    <text x="190" y="372" fill="#1c2326">code, by a rule you choose</text>
    <text x="600" y="122" fill="#ffffff">an LLM agent</text>
    <text x="1010" y="372" fill="#1c2326">code checks it, your script runs it</text>
    <text x="600" y="628" fill="#1c2326">code</text>
    <text x="600" y="370" fill="#0f3f39">LLM agents, every few versions</text>
  </g>
  <g font-size="16.5" font-style="italic" fill="currentColor" opacity="0.8">
    <text x="614" y="218">what worked and</text>
    <text x="614" y="240">what did not</text>
    <text x="411" y="306" text-anchor="middle">what to try</text>
    <text x="411" y="328" text-anchor="middle">more of</text>
  </g>
  <g font-size="17" fill="currentColor">
    <text x="30" y="62" font-weight="700">You steer, at any time</text>
    <text x="30" y="86">change a setting, or send</text>
    <text x="30" y="108">the agents a note</text>
    <text x="100" y="598" text-anchor="middle" font-weight="700">You provide</text>
    <text x="100" y="622" text-anchor="middle">code, a scoring script,</text>
    <text x="100" y="644" text-anchor="middle">a budget</text>
    <text x="948" y="620" font-weight="700">You get</text>
    <text x="948" y="644">the best versions, and</text>
    <text x="948" y="666">every version tried</text>
  </g>
  <g font-size="16" fill="currentColor">
    <rect x="40" y="690" width="30" height="20" rx="5" fill="#01796e"/>
    <text x="80" y="706">LLM agent</text>
    <rect x="195" y="690" width="30" height="20" rx="5" fill="#f1f3f4" stroke="#5f6b73" stroke-width="2.5"/>
    <text x="235" y="706">code, no LLM</text>
    <path d="M370 700 H412" stroke="#01796e" stroke-width="3" stroke-dasharray="9 7"/>
    <text x="424" y="706">optional</text>
  </g>
</svg>

<ol class="evo-loop-list">
<li><b>Pick a version to improve.</b> Code, by a rule you choose.</li>
<li><b>Write a change to it.</b> An LLM agent.</li>
<li><b>Run it and score it.</b> Code checks the change, then your script runs it. Several run at once.</li>
<li><b>Add it to the leaderboard.</b> Code.</li>
<li><b>Review the results</b> (optional). LLM agents, every few versions, advise steps 1 and 2.</li>
</ol>

Steps 1 to 4 repeat until the budget is spent, several versions at a time. An LLM writes every change.
Which version it starts from is decided by code, by a rule you choose, such as "the best of each family
of designs". You can let an agent choose the kind of change as well. Before step 3, code refuses any
change that touches code you did not mark. Step 3 then runs your own script, which does whatever your
problem needs (train a model, time an algorithm) and reports a score. Several versions run at once.

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
