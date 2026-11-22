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
<svg class="evo-loop-svg" viewBox="0 0 1200 720" role="img" aria-label="The evoloop loop. The writer agent proposes new code. Your script trains or runs it as parallel jobs. Code scores and ranks it. The analyst and strategist agents analyze the results, and their lessons go into the next proposal. In the middle, code keeps the lineages: it selects each parent and retires lineages that stall." style="width:100%;max-width:940px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7d8790"/></marker>
  </defs>
  <g fill="none" stroke="#7d8790" stroke-width="3.5">
    <path d="M760 92 Q985 100 1020 262" marker-end="url(#evo-a)"/>
    <path d="M1010 404 Q980 575 772 592" marker-end="url(#evo-a)"/>
    <path d="M440 592 Q220 575 190 410" marker-end="url(#evo-a)"/>
    <path d="M190 284 Q220 105 436 100" marker-end="url(#evo-a)"/>
    <path d="M244 60 H436" marker-end="url(#evo-a)"/>
    <path d="M760 626 H936" marker-end="url(#evo-a)"/>
    <path d="M100 574 V410" marker-end="url(#evo-a)" stroke-dasharray="3 6"/>
  </g>
  <g stroke-width="3">
    <rect x="450" y="40" width="300" height="106" rx="16" fill="#01796e" stroke="#01796e"/>
    <rect x="40" y="290" width="300" height="106" rx="16" fill="#01796e" stroke="#01796e"/>
    <rect x="876" y="274" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#aab2b8"/>
    <rect x="868" y="282" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#8a949b"/>
    <rect x="860" y="290" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="450" y="546" width="300" height="106" rx="16" fill="#f1f3f4" stroke="#5f6b73"/>
  </g>
  <g text-anchor="middle" font-weight="700" font-size="24">
    <text x="600" y="84" fill="#ffffff">Propose</text>
    <text x="1010" y="334" fill="#1c2326">Train</text>
    <text x="600" y="590" fill="#1c2326">Score</text>
    <text x="190" y="334" fill="#ffffff">Analyze</text>
    <text x="600" y="322" fill="currentColor" font-size="22">Lineages</text>
  </g>
  <g text-anchor="middle" font-size="17">
    <text x="600" y="122" fill="#ffffff">the writer agent</text>
    <text x="1010" y="372" fill="#1c2326">your script, as parallel jobs</text>
    <text x="600" y="628" fill="#1c2326">your metric, ranked by code</text>
    <text x="190" y="372" fill="#ffffff">the analyst and strategist agents</text>
    <text x="600" y="354" fill="currentColor">code selects each parent and</text>
    <text x="600" y="378" fill="currentColor">retires lineages that stall</text>
  </g>
  <g font-size="16.5" font-style="italic" fill="currentColor" opacity="0.8" text-anchor="middle">
    <text x="872" y="212">new code</text>
    <text x="872" y="486">results</text>
    <text x="330" y="486">scores</text>
    <text x="330" y="212">lessons</text>
  </g>
  <g font-size="17" fill="currentColor">
    <text x="30" y="52" font-weight="700">You provide</text>
    <text x="30" y="76">code, a scoring script,</text>
    <text x="30" y="98">a budget</text>
    <text x="30" y="606" font-weight="700">You steer, at any time</text>
    <text x="30" y="630">a note to the agents,</text>
    <text x="30" y="652">or a changed setting</text>
    <text x="948" y="620" font-weight="700">You get</text>
    <text x="948" y="644">the best versions, and</text>
    <text x="948" y="666">every version tried</text>
  </g>
  <g font-size="16" fill="currentColor">
    <rect x="40" y="690" width="30" height="20" rx="5" fill="#01796e"/>
    <text x="80" y="706">LLM agents</text>
    <rect x="205" y="690" width="30" height="20" rx="5" fill="#f1f3f4" stroke="#5f6b73" stroke-width="2.5"/>
    <text x="245" y="706">code, no LLM</text>
  </g>
</svg>

<ol class="evo-loop-list">
<li><b>Propose.</b> The writer agent writes new code from a parent.</li>
<li><b>Train.</b> Your script trains or runs it, as parallel jobs.</li>
<li><b>Score.</b> Your metric, ranked by code.</li>
<li><b>Analyze.</b> The analyst and strategist agents read the results and pass lessons to the writer.</li>
</ol>

This is evolutionary search with an LLM as the mutation operator.

| Step | Who | What happens |
|---|---|---|
| **Propose** | the **writer** agent | Writes new code from a parent: a mutation of it, or a crossover with another. |
| **Train** | your script | Trains or runs the new code, as a job. Code first refuses any change outside the parts you marked. |
| **Score** | code | Reads your metric, enforces your limits, and ranks the version. |
| **Analyze** | the **analyst** and **strategist** agents | The analyst writes lessons for the writer. The strategist can shift the schedule and retire or revive a lineage. Both are optional. |
| **Lineages** | code | Selects each parent and retires lineages that stop improving. |

## Lineages: how the search explores and exploits

By default the population is a set of **lineages**. A lineage is a family of versions descended from
one new design.

<svg class="evo-loop-svg" viewBox="0 0 1200 500" role="img" aria-label="An illustration of lineages in one search, as validation score against evaluations spent. The baseline CNN stops improving and is retired. A dilated CNN climbs steadily. A transformer starts below the others, is protected for its first two runs, and then climbs. A crossover of the dilated CNN and the transformer founds a new lineage that ends as the best version." style="width:100%;max-width:940px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <rect x="80" y="64" width="620" height="356" fill="#01796e" opacity="0.06"/>
  <path d="M700 64 V420" stroke="#7d8790" stroke-width="2" stroke-dasharray="5 6"/>
  <path d="M80 64 V420 H1120" stroke="#7d8790" stroke-width="2" fill="none"/>
  <g font-size="18" font-weight="700" fill="currentColor"><text x="92" y="48">Explore: try new designs</text><text x="712" y="48">Exploit: refine and cross the best</text></g>
  <g font-size="15" fill="currentColor" opacity="0.8" text-anchor="end"><text x="70" y="425">0.60</text><text x="70" y="255">0.70</text><text x="70" y="85">0.80</text></g>
  <path d="M100 386 L150 369 L210 360 L280 352 L350 352 L420 352 L480 352" stroke="#9aa3ab" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="100" cy="386" r="7" fill="#ffffff" stroke="#9aa3ab" stroke-width="3"/>
  <circle cx="150" cy="369" r="7" fill="#ffffff" stroke="#9aa3ab" stroke-width="3"/>
  <circle cx="210" cy="360" r="7" fill="#9aa3ab"/>
  <circle cx="280" cy="352" r="7" fill="#9aa3ab"/>
  <circle cx="350" cy="352" r="7" fill="#9aa3ab"/>
  <circle cx="420" cy="352" r="7" fill="#9aa3ab"/>
  <circle cx="480" cy="352" r="7" fill="#9aa3ab"/>
  <path d="M511 343 L529 361 M511 361 L529 343" stroke="#9aa3ab" stroke-width="3.5" fill="none"/>
  <path d="M170 352 L230 318 L300 284 L380 250 L470 225 L560 208 L640 199 L720 191 L790 182 L860 182 L940 179 L1010 179" stroke="#5f6b73" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="170" cy="352" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="230" cy="318" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="300" cy="284" r="7" fill="#5f6b73"/>
  <circle cx="380" cy="250" r="7" fill="#5f6b73"/>
  <circle cx="470" cy="225" r="7" fill="#5f6b73"/>
  <circle cx="560" cy="208" r="7" fill="#5f6b73"/>
  <circle cx="640" cy="199" r="7" fill="#5f6b73"/>
  <circle cx="720" cy="191" r="7" fill="#5f6b73"/>
  <circle cx="790" cy="182" r="7" fill="#5f6b73"/>
  <circle cx="860" cy="182" r="7" fill="#5f6b73"/>
  <circle cx="940" cy="179" r="7" fill="#5f6b73"/>
  <circle cx="1010" cy="179" r="7" fill="#5f6b73"/>
  <path d="M360 411 L420 386 L500 318 L580 259 L660 216 L740 199 L810 194 L880 193" stroke="#5f6b73" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="360" cy="411" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="420" cy="386" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="500" cy="318" r="7" fill="#5f6b73"/>
  <circle cx="580" cy="259" r="7" fill="#5f6b73"/>
  <circle cx="660" cy="216" r="7" fill="#5f6b73"/>
  <circle cx="740" cy="199" r="7" fill="#5f6b73"/>
  <circle cx="810" cy="194" r="7" fill="#5f6b73"/>
  <circle cx="880" cy="193" r="7" fill="#5f6b73"/>
  <path d="M720 191 Q750 188 770 176 M660 216 Q730 205 768 178" stroke="#01796e" stroke-width="3" fill="none" stroke-dasharray="6 5"/>
  <path d="M770 174 L820 157 L880 140 L940 123 L1000 111 L1060 100" stroke="#01796e" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="770" cy="174" r="7" fill="#ffffff" stroke="#01796e" stroke-width="3"/>
  <circle cx="820" cy="157" r="7" fill="#ffffff" stroke="#01796e" stroke-width="3"/>
  <circle cx="880" cy="140" r="7" fill="#01796e"/>
  <circle cx="940" cy="123" r="7" fill="#01796e"/>
  <circle cx="1000" cy="111" r="7" fill="#01796e"/>
  <circle cx="1060" cy="100" r="7" fill="#01796e"/>
  <circle cx="1060" cy="100" r="15" fill="none" stroke="#01796e" stroke-width="3"/>
  <g font-size="16" fill="currentColor">
    <text x="540" y="334" font-weight="700">Baseline CNN</text>
    <text x="540" y="356">retired: 6 tries, no gain</text>
    <text x="1024" y="184" font-weight="700">Dilated CNN</text>
    <text x="474" y="392" font-weight="700">Transformer</text>
    <text x="474" y="413">a slow starter, protected at first</text>
    <text x="714" y="88" font-weight="700">Dilated CNN &#215; Transformer</text>
    <text x="714" y="110">a crossover: the best version</text>
  </g>
  <g font-size="15.5" fill="currentColor" opacity="0.85">
    <text x="80" y="448">evaluations spent &#8594;</text>
    <text x="1120" y="448" text-anchor="end">each dot is one version, trained and scored</text>
    <text x="80" y="476">An illustration, not data from a run. Hollow dots are a lineage's protected first runs.</text>
    <text transform="translate(24 300) rotate(-90)">validation score</text>
  </g>
</svg>

Read it left to right:

- **A lineage is founded** by a new design. Here the search tries a dilated CNN, then a transformer.
- **A new lineage is protected** for its first 2 runs. The transformer starts below everything else and
  would be dropped on its first score; protected, it catches up.
- **A lineage that stalls is retired**, after 6 changes in a row with no gain above the noise. The
  baseline CNN goes this way, and its evaluations go to the others.
- **Two lineages are crossed** to found a third. The cross of the dilated CNN and the transformer ends as
  the best version.
- Up to 8 lineages are active at once, and none takes more than 40% of the refinements.

The schedule moves from exploring to exploiting. In the first 60% of the budget, 65% of the versions
are new designs. After that, 60% are refinements of an existing lineage and 25% are crossovers. All of
these numbers are settings.

Every version has a parent, so the history is a family tree, but this is not tree search. Nothing is
expanded systematically and no values are backed up the tree, as in Monte Carlo tree search. It is a
population that changes over time. Lineages are the default rule for selecting parents; four other rules are
below.

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
