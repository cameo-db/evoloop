---
hide:
  - navigation
---

# evoloop

**evoloop improves code by evolving it.** An LLM writes new versions of the parts you mark. Your script
scores each one. The best become parents of the next.

[Set up a search](setting-up.md){ .md-button .md-button--primary }
[Search options](options.md){ .md-button }
[Source on GitHub](https://github.com/cameo-db/evoloop){ .md-button }

<style>
.evo-loop-list { display: none; }
@media screen and (max-width: 620px) { .evo-loop-svg { display: none !important; } .evo-loop-list { display: block; } }
</style>
<svg class="evo-loop-svg" viewBox="0 0 1200 720" role="img" aria-label="The evoloop loop: the writer agent proposes new code, your script trains it, code scores it, and the analyst and strategist agents analyze the results and pass lessons to the writer. In the middle, code keeps the lineages: it picks the parents and drops dead ends." style="width:100%;max-width:940px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7d8790"/></marker>
  </defs>
  <g fill="none" stroke="#7d8790" stroke-width="3.5">
    <path d="M760 92 Q985 100 1020 262" marker-end="url(#evo-a)"/>
    <path d="M1010 404 Q980 575 772 592" marker-end="url(#evo-a)"/>
    <path d="M440 592 Q220 575 190 410" marker-end="url(#evo-a)"/>
    <path d="M190 284 Q220 105 436 100" marker-end="url(#evo-a)"/>
    <path d="M262 60 H436" marker-end="url(#evo-a)"/>
    <path d="M760 626 H936" marker-end="url(#evo-a)"/>
    <path d="M70 448 V410" marker-end="url(#evo-a)"/>
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
    <text x="600" y="122" fill="#ffffff">writer agent</text>
    <text x="1010" y="372" fill="#1c2326">your script, many at once</text>
    <text x="600" y="628" fill="#1c2326">your metric</text>
    <text x="190" y="372" fill="#ffffff">analyst + strategist agents</text>
    <text x="600" y="354" fill="currentColor">code picks the parents</text>
    <text x="600" y="378" fill="currentColor">and drops dead ends</text>
  </g>
  <g font-size="16.5" font-style="italic" fill="currentColor" opacity="0.8" text-anchor="middle">
    <text x="872" y="212">new code</text>
    <text x="872" y="486">results</text>
    <text x="330" y="486">scores</text>
    <text x="330" y="212">lessons</text>
  </g>
  <g font-size="17" fill="currentColor">
    <text x="20" y="52" font-weight="700">You bring</text>
    <text x="20" y="76">code + a scoring script</text>
    <text x="20" y="98">a budget</text>
    <text x="20" y="128" opacity="0.8">optional: a skill,</text>
    <text x="20" y="150" opacity="0.8">designs from CAMEO</text>
    <text x="20" y="474" font-weight="700">You steer</text>
    <text x="20" y="497">notes, settings</text>
    <text x="948" y="620" font-weight="700">You get</text>
    <text x="948" y="644">ranked versions</text>
    <text x="948" y="666">the full record,</text>
    <text x="948" y="688">ready for CAMEO</text>
  </g>
  <g font-size="16" fill="currentColor">
    <rect x="40" y="690" width="30" height="20" rx="5" fill="#01796e"/>
    <text x="80" y="706">LLM agents</text>
    <rect x="205" y="690" width="30" height="20" rx="5" fill="#f1f3f4" stroke="#5f6b73" stroke-width="2.5"/>
    <text x="245" y="706">code, no LLM</text>
  </g>
</svg>

<ol class="evo-loop-list">
<li><b>Propose.</b> The writer agent rewrites a parent.</li>
<li><b>Train.</b> Your script trains or runs it.</li>
<li><b>Score.</b> Code reads your metric and ranks it.</li>
<li><b>Analyze.</b> The analyst and strategist agents pass lessons to the writer.</li>
</ol>

| Step | Who | What happens |
|---|---|---|
| **Propose** | writer agent | Rewrites a parent, or combines two. |
| **Train** | your script | Trains or runs the new version. Many run at once. |
| **Score** | code | Reads your metric and ranks the version. A version that breaks your limits is rejected. |
| **Analyze** | analyst and strategist agents | The analyst tells the writer what has worked. The strategist decides what to try more of. Both are optional. |
| **Lineages** | code | Picks the parents. Drops lineages that have stopped improving. |

Agents write and advise. Code picks the parents, checks that a new version changed only what you
marked, and holds the budget.

## What you bring

| | |
|---|---|
| **Your code** | Mark the parts that may change. [Set up a search](setting-up.md) |
| **A scoring script** | Runs one version and reports a number. [Write the evaluator](evaluator.md) |
| **A budget** | How many versions to try, and a dollar cap for the agents. [Budget and cost](cost.md) |
| **A skill** (optional) | Settings and advice for one goal, such as distillation. The library has thirteen, and you can edit any of them. [Skills](which-search.md) |
| **Earlier designs** (optional) | From a previous search, or from [CAMEO](https://cameo-db.github.io), so you start ahead of your baseline. [Start from earlier designs](warm-start.md) |

## What you get

A ranked list of versions, and the code and score of every version tried. The whole search is also
saved as one file, `study.json`, in the format [CAMEO](https://cameo-db.github.io) accepts. What you
find can seed someone else's search, the same way theirs can seed yours.
[Save and deposit the study](study.md)

## Lineages

A lineage is a family of versions that descend from one new design. evoloop keeps several going at
once.

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
  <path d="M440 411 L500 386 L570 335 L640 301 L710 276 L780 262 L850 257" stroke="#5f6b73" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="440" cy="411" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="500" cy="386" r="7" fill="#ffffff" stroke="#5f6b73" stroke-width="3"/>
  <circle cx="570" cy="335" r="7" fill="#5f6b73"/>
  <circle cx="640" cy="301" r="7" fill="#5f6b73"/>
  <circle cx="710" cy="276" r="7" fill="#5f6b73"/>
  <circle cx="780" cy="262" r="7" fill="#5f6b73"/>
  <circle cx="850" cy="257" r="7" fill="#5f6b73"/>
  <path d="M720 191 Q750 188 770 176 M710 276 Q760 250 768 180" stroke="#01796e" stroke-width="3" fill="none" stroke-dasharray="6 5"/>
  <path d="M770 174 L820 157 L880 140 L940 123 L1000 111 L1060 100" stroke="#01796e" stroke-width="3.5" fill="none" stroke-linejoin="round"/>
  <circle cx="770" cy="174" r="7" fill="#ffffff" stroke="#01796e" stroke-width="3"/>
  <circle cx="820" cy="157" r="7" fill="#ffffff" stroke="#01796e" stroke-width="3"/>
  <circle cx="880" cy="140" r="7" fill="#01796e"/>
  <circle cx="940" cy="123" r="7" fill="#01796e"/>
  <circle cx="1000" cy="111" r="7" fill="#01796e"/>
  <circle cx="1060" cy="100" r="7" fill="#01796e"/>
  <circle cx="1060" cy="100" r="15" fill="none" stroke="#01796e" stroke-width="3"/>
  <g font-size="16" fill="currentColor">
    <text x="200" y="384" font-weight="700">Baseline CNN</text>
    <text x="200" y="406">retired: 6 tries, no gain</text>
    <text x="1024" y="184" font-weight="700">Dilated CNN</text>
    <text x="866" y="263" font-weight="700">Transformer</text>
    <text x="866" y="285">slow start, protected for 2 runs</text>
    <text x="714" y="88" font-weight="700">Dilated CNN &#215; Transformer</text>
    <text x="714" y="110">a cross of the two, ends up best</text>
  </g>
  <g font-size="15.5" fill="currentColor" opacity="0.85">
    <text x="80" y="448">evaluations spent &#8594;</text>
    <text x="1120" y="448" text-anchor="end">one dot = one version</text>
    <text x="80" y="476">Illustration, not real data. Hollow dot = protected run.</text>
    <text transform="translate(24 300) rotate(-90)">validation score</text>
  </g>
</svg>

- **A new design starts a lineage.** Here: a dilated CNN, then a transformer.
- **Its first 2 runs are protected.** The transformer starts at the bottom and would have been dropped.
  It gets time to catch up.
- **Six tries with no gain and a lineage is retired.** The baseline CNN goes this way.
- **Two lineages can be crossed.** Here the cross ends up best.

Early in the budget most versions are new designs. Later most are refinements and crosses of the best
lineages. Where the switch happens, and every number above, is a setting.

Lineages are the default. There are four other ways to pick parents:

| Strategy | Builds on | Known as |
|---|---|---|
| `lineage` (default) | the best version in each family | speciation, as in NEAT |
| `archive` | the best version in each cell of a grid, such as each size band | MAP-Elites; AlphaEvolve's program database |
| `tournament` | the best of a few recent versions | regularized evolution |
| `pareto` | versions not beaten on both score and a second measure, such as size | NSGA-II |
| `greedy` | the single best version | hill climbing |

Any of them can run as separate populations that restart from the best one, as in FunSearch.
[Parent selection](parents.md) · [Compared with FunSearch and AlphaEvolve](compared.md)

This is not tree search. Versions have parents, so the history looks like a tree, but nothing walks
it. It is a population, as in a genetic algorithm, with an LLM making the mutations.

## How to run it

!!! tip "Easiest: use Claude Code"
    Open the evoloop repository in [Claude Code](https://claude.com/claude-code) and tell it what you want to improve.
    It asks you the setup questions one at a time, starts the search when you approve the plan, and
    keeps watch. Tell it what you think of the results and it adjusts the search.

You can also do it by hand. `evoloop setup` asks the same questions in the terminal. Or edit the files
directly: the settings (`brief.yaml`), the task description, and the skill files are all plain text.
[Commands](commands.md) · [Brief fields](fields.md)

Either way, every search begins with a plan that says what will run and what it should cost. Nothing
is spent until you approve it. Once it is running you can change settings, send the agents a note, or
stop it. [Monitor and steer a search](steering.md)

It runs on a laptop or a Slurm cluster. [Run on a cluster](servers.md)

## More

| | |
|---|---|
| How the loop works in detail | [How it works](how-it-works.md) · [Agents](agents.md) |
| Every setting | [Search options on one page](options.md) · [Reference](reference.md) |
| A toy search you can run in half a minute | [Worked example](quickstart.md) |

Version 0.2. Tested with a script standing in for the LLM. Not yet run with a real LLM on a real
training task. [Status and limits](status.md)
