---
hide:
  - navigation
---

# evoloop

**evoloop is agent-led optimization of code you can score.** You mark the parts of your code that may change and write a
script that measures how good one version is. evoloop then runs an evolutionary search: LLM agents
propose changes, your script scores each one, and the results decide what is tried next.

<svg viewBox="0 0 1200 720" role="img" aria-label="The evoloop loop. Code selects which version to build on, a writer agent writes a changed version, your script evaluates it, and code records the result. Every few versions, analyst and strategist agents read the record: their lessons go to the writer and their schedule changes go to selection." style="width:100%;max-width:940px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7d8790"/></marker>
    <marker id="evo-t" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#01796e"/></marker>
  </defs>
  <g fill="none" stroke="#7d8790" stroke-width="3.5">
    <path d="M190 284 Q225 105 460 92" marker-end="url(#evo-a)"/>
    <path d="M740 92 Q975 105 1010 282" marker-end="url(#evo-a)"/>
    <path d="M1010 404 Q975 570 750 580" marker-end="url(#evo-a)"/>
    <path d="M460 592 Q225 580 190 404" marker-end="url(#evo-a)"/>
    <path d="M110 560 V404" marker-end="url(#evo-a)"/>
    <path d="M740 622 H940" marker-end="url(#evo-a)"/>
  </g>
  <g fill="none" stroke="#01796e" stroke-width="3" stroke-dasharray="9 7">
    <path d="M600 538 V402" marker-end="url(#evo-t)"/>
    <path d="M600 288 V154" marker-end="url(#evo-t)"/>
    <path d="M483 342 H336" marker-end="url(#evo-t)"/>
  </g>
  <g stroke-width="3">
    <rect x="60" y="290" width="260" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="470" y="40" width="260" height="106" rx="16" fill="#01796e" stroke="#01796e"/>
    <rect x="880" y="290" width="260" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="470" y="546" width="260" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="485" y="294" width="230" height="100" rx="16" fill="#dff1ee" stroke="#01796e" stroke-dasharray="9 7"/>
  </g>
  <g text-anchor="middle" font-weight="700" font-size="24">
    <text x="190" y="334" fill="#1c2326">Select</text>
    <text x="600" y="84" fill="#ffffff">Write</text>
    <text x="1010" y="334" fill="#1c2326">Evaluate</text>
    <text x="600" y="590" fill="#1c2326">Record</text>
    <text x="600" y="336" fill="#0f3f39" font-size="22">Reflect</text>
  </g>
  <g text-anchor="middle" font-size="17">
    <text x="190" y="372" fill="#1c2326">code picks what to build on</text>
    <text x="600" y="122" fill="#ffffff">an agent edits your marked code</text>
    <text x="1010" y="372" fill="#1c2326">your script scores it, as a job</text>
    <text x="600" y="628" fill="#1c2326">every version, parent and score</text>
    <text x="600" y="370" fill="#0f3f39">agents read the record</text>
  </g>
  <g font-size="16.5" font-style="italic" fill="currentColor" opacity="0.75">
    <text x="372" y="222" text-anchor="middle">a parent and a kind of change</text>
    <text x="872" y="196" text-anchor="middle">a new version</text>
    <text x="880" y="500" text-anchor="middle">its score</text>
    <text x="318" y="500" text-anchor="middle">the population</text>
    <text x="614" y="228">lessons</text>
    <text x="614" y="476">every few versions</text>
    <text x="406" y="328" text-anchor="middle">schedule</text>
  </g>
  <g font-size="17" fill="currentColor">
    <text x="110" y="592" text-anchor="middle" font-weight="700">You provide</text>
    <text x="110" y="616" text-anchor="middle">code, a scoring script,</text>
    <text x="110" y="638" text-anchor="middle">a budget</text>
    <text x="952" y="616" font-weight="700">You get</text>
    <text x="952" y="640">a leaderboard and the</text>
    <text x="952" y="662">whole search as JSON</text>
  </g>
  <g font-size="16" fill="currentColor">
    <rect x="60" y="690" width="30" height="20" rx="5" fill="#01796e"/>
    <text x="100" y="706">LLM agent</text>
    <rect x="215" y="690" width="30" height="20" rx="5" fill="#f1f3f4" stroke="#5f6b73" stroke-width="2.5"/>
    <text x="255" y="706">code</text>
    <path d="M330 700 H372" stroke="#01796e" stroke-width="3" stroke-dasharray="9 7"/>
    <text x="384" y="706">optional agents, every few versions</text>
  </g>
</svg>

The outer loop is evolutionary search: code selects, an agent writes, your script evaluates, code records.
Inside it, analyst and strategist agents read the record every few versions. Their lessons go to the
writer, and their changes to the schedule go to selection. You can steer at any point with a note or a
changed setting.

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
