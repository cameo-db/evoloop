---
hide:
  - navigation
---

# evoloop

**AI agents that run your model search for you, while you stay in charge.**

Improving a model is a loop. You have an idea, change the code, train it, look at the result, and
decide what to try next. evoloop runs that loop on its own, hundreds of times. An AI agent writes each
new idea as code. Your own training script tests it. Ideas that score well are developed further, and
ideas that do not are dropped.

You set it up once: which part of your code may change, how a result is scored, and how much you are
willing to spend. You approve the plan before anything runs. While the search is running you can
watch it, redirect it, or stop it.

When it finishes you have a leaderboard of every model it tried, each with its code and its score.

It also works for code that is not a model. If a script can score it, evoloop can search over it: an
algorithm you want faster, a data pipeline you want cheaper.

[Set up a search](setting-up.md){ .md-button .md-button--primary }
[Source on GitHub](https://github.com/cameo-db/evoloop){ .md-button }

## How it works

<style>
.evo-loop-list { display: none; }
@media screen and (max-width: 620px) { .evo-loop-svg { display: none !important; } .evo-loop-list { display: block; } }
</style>
<svg class="evo-loop-svg" viewBox="0 0 1200 670" role="img" aria-label="The evoloop loop. Propose: an AI agent writes a new version. Train: your script trains it. Score: it is ranked against all the others. Analyze: AI agents study what worked. The best versions become the next parents, and the loop repeats." style="width:100%;max-width:900px;height:auto;display:block;margin:28px auto 12px;font-family:inherit">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7d8790"/></marker>
  </defs>
  <g fill="none" stroke="#7d8790" stroke-width="4">
    <path d="M777 95 Q1005 100 1012 228" marker-end="url(#evo-a)"/>
    <path d="M1005 399 Q1000 545 779 545" marker-end="url(#evo-a)"/>
    <path d="M423 545 Q200 545 195 399" marker-end="url(#evo-a)"/>
    <path d="M195 243 Q200 100 421 95" marker-end="url(#evo-a)"/>
  </g>
  <g stroke-width="3">
    <rect x="435" y="30" width="330" height="130" rx="18" fill="#01796e" stroke="#01796e"/>
    <rect x="30" y="255" width="330" height="130" rx="18" fill="#01796e" stroke="#01796e"/>
    <rect x="856" y="239" width="330" height="130" rx="18" fill="#f1f3f4" stroke="#aab2b8"/>
    <rect x="848" y="247" width="330" height="130" rx="18" fill="#f1f3f4" stroke="#8a949b"/>
    <rect x="840" y="255" width="330" height="130" rx="18" fill="#f1f3f4" stroke="#5f6b73"/>
    <rect x="435" y="480" width="330" height="130" rx="18" fill="#f1f3f4" stroke="#5f6b73"/>
  </g>
  <g text-anchor="middle" font-weight="700" font-size="31">
    <text x="600" y="88" fill="#ffffff">Propose</text>
    <text x="1005" y="313" fill="#1c2326">Train</text>
    <text x="600" y="538" fill="#1c2326">Score</text>
    <text x="195" y="313" fill="#ffffff">Analyze</text>
  </g>
  <g text-anchor="middle" font-size="19">
    <text x="600" y="128" fill="#ffffff">An AI agent writes a new version</text>
    <text x="1005" y="353" fill="#1c2326">Your script trains it</text>
    <text x="600" y="578" fill="#1c2326">It is ranked against the others</text>
    <text x="195" y="353" fill="#ffffff">AI agents study what worked</text>
  </g>
  <g text-anchor="middle" fill="currentColor" font-size="22" font-weight="700">
    <text x="600" y="310">The best versions</text>
    <text x="600" y="340">become the next parents</text>
  </g>
  <g font-size="17" fill="currentColor">
    <rect x="440" y="640" width="30" height="20" rx="5" fill="#01796e"/>
    <text x="480" y="656">AI agent</text>
    <rect x="610" y="640" width="30" height="20" rx="5" fill="#f1f3f4" stroke="#5f6b73" stroke-width="2.5"/>
    <text x="650" y="656">ordinary code</text>
  </g>
</svg>

<p class="evo-loop-list"><b>Propose</b> &rarr; <b>Train</b> &rarr; <b>Score</b> &rarr; <b>Analyze</b> &rarr; back to Propose.</p>

Four steps repeat until the budget is spent.

1. **Propose.** An AI agent, the *writer*, takes a version that has done well and changes it. Sometimes
   it combines two good versions into one.
2. **Train.** Your script trains the new version. Many versions train at the same time.
3. **Score.** The new version gets its score and is ranked against all the others.
4. **Analyze.** Two more agents read the results. The *analyst* writes down what has worked and what
   has not, and the writer reads those notes before its next proposal. The *strategist* decides where
   the search should put its effort next.

The agents supply the ideas. Everything that has to be dependable is ordinary code, with no AI
involved: choosing which versions to build on, checking that a new version changed only what you
allowed, and stopping when the budget runs out.

[How it works, in detail](how-it-works.md) · [The agents](agents.md)

## Lineages

A search that only ever improves its current best model gets stuck on the first decent idea. evoloop
avoids this by keeping several *lineages* alive at once. A lineage is one design idea together with
every version that grew out of it.

<svg class="evo-loop-svg" viewBox="0 0 1200 500" role="img" aria-label="An illustration of lineages in one search, as validation score against evaluations spent. The baseline CNN stops improving and is retired. A dilated CNN climbs steadily. A transformer starts below the others, is protected for its first two runs, and then climbs. A crossover of the dilated CNN and the transformer founds a new lineage that ends as the best version." style="width:100%;max-width:940px;height:auto;display:block;margin:24px auto 8px;font-family:inherit">
  <rect x="80" y="64" width="620" height="356" fill="#01796e" opacity="0.06"/>
  <path d="M700 64 V420" stroke="#7d8790" stroke-width="2" stroke-dasharray="5 6"/>
  <path d="M80 64 V420 H1120" stroke="#7d8790" stroke-width="2" fill="none"/>
  <g font-size="18" font-weight="700" fill="currentColor"><text x="92" y="48">First, explore: start many designs</text><text x="712" y="48">Then, exploit: improve the best</text></g>
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
    <text x="200" y="406">dropped after 6 tries with no gain</text>
    <text x="1024" y="184" font-weight="700">Dilated CNN</text>
    <text x="778" y="236" font-weight="700" fill="#01796e">crossover</text>
    <text x="866" y="263" font-weight="700">Transformer</text>
    <text x="866" y="285">slow start, given 2 protected runs</text>
    <text x="714" y="88" font-weight="700">Dilated CNN &#215; Transformer</text>
    <text x="714" y="110">a crossover of the two. It wins.</text>
  </g>
  <g font-size="15.5" fill="currentColor" opacity="0.85">
    <text x="80" y="448">training runs &#8594;</text>
    <text x="1120" y="448" text-anchor="end">each dot is one trained version</text>
    <text x="80" y="476">An illustration, not real results. Hollow dots are protected runs.</text>
    <text transform="translate(24 300) rotate(-90)">score</text>
  </g>
</svg>

Reading the picture from left to right:

- **A new idea starts a lineage.** The search begins with the baseline CNN, then tries a dilated CNN,
  then a transformer.
- **A new lineage gets a fair chance.** The transformer's first score is the worst on the board. Its
  first two runs are protected, so it is not thrown out before it has been tuned.
- **A lineage that stops improving is dropped.** After six tries with no gain, the baseline CNN gets no
  more training runs. They go to the others.
- **Crossover combines two lineages.** The agent merges the dilated CNN with the transformer. The result
  starts a new lineage, and here it wins.

Early on, most training runs go to new ideas. Later, most go to improving the best lineages and
crossing them. You choose where that switch happens.

This is evolutionary search. The versions are a population, the agent's edits are the mutations, and
the score decides what survives. [Parent selection](parents.md) covers the other strategies evoloop
offers and how they relate to FunSearch, AlphaEvolve and MAP-Elites.

## Getting started

!!! tip "The easy way: Claude Code"
    Open the evoloop repository in [Claude Code](https://claude.com/claude-code) and tell it what you want to improve.
    It asks you a short list of questions, one at a time, and sets everything up. It starts the search
    once you approve the plan, keeps an eye on it, and changes course when you tell it what you think of
    the results.

Prefer to do it yourself? `evoloop setup` asks the same questions in a terminal, and every setting is
a plain text file you can edit. [Set up a search](setting-up.md)

What you need:

- **Your code**, with the part that may change marked.
- **A script that scores one version.** For a model, that is your training script.
- **A budget**: how many versions to try, and a spending cap for the agents.

Two things are optional and save time:

- **A skill.** A skill is a ready-made set of settings and advice for one kind of goal, such as
  distilling a large model into a small one. There are thirteen, and you can edit them.
  [Skills](which-search.md)
- **A head start from CAMEO.** [CAMEO](https://cameo-db.github.io) is a public database of models and
  how they scored. You can start your search from designs that worked for someone else. When your search
  ends, evoloop saves it in the same format, so you can add yours.
  [Start from earlier designs](warm-start.md) · [Save and deposit the study](study.md)

## More

- [Every search option on one page](options.md)
- [A toy search you can run in half a minute](quickstart.md)
- [Run on a cluster](servers.md)
- [Reference](reference.md)

evoloop is at version 0.2. Its tests pass with a script standing in for the AI agent. It has not yet
been run with a real agent on a real training task. [Status and limits](status.md)
