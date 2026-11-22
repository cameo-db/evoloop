---
hide:
  - navigation
  - toc
---

<div class="evo-home" markdown>

# evoloop

**evoloop is an open-source, general-purpose AutoResearch loop driven by AI agents.** You give it code
and a way to score that code. AI agents propose changes, every change is evaluated automatically, and the results decide what
is tried next. A search runs for hundreds of experiments and keeps a record of every one. It is MIT
licensed, and the source is on [GitHub](https://github.com/cameo-db/evoloop).

It was built for machine-learning research, where it searches for better architectures, tunes training
recipes, distils large models into smaller ones, and maps the trade-off between accuracy and size. The
same loop works on any code that a script can score, such as an algorithm or a data pipeline.

You stay in charge of a search. You decide what may change and how much may be spent, you approve the
plan before anything runs, and you can redirect the search while it is running.

[Get started](get-started.md){ .md-button .md-button--primary }
[How it works](how-it-works.md){ .md-button }
[GitHub](https://github.com/cameo-db/evoloop){ .md-button }

## How it works

You mark the parts of your code that may change and provide an *evaluator*: a script that runs one
version of the code and reports its score. For a model, the marked parts might be the architecture, the
loss or the training recipe, and the evaluator trains the model and reports its validation score.
evoloop then runs an evolutionary search over the marked parts.

<figure class="evo-figure">
<svg class="evo-fig" viewBox="0 0 1000 600" role="img" aria-label="Overview of evoloop. The researcher supplies a brief and baseline code. The writer agent proposes new code. Your training script trains each proposal as a parallel job. The validation metric scores it. The analyst and strategist agents analyze the results and return lessons to the writer. In the centre are the lineages, from which code chooses the parents. Skills and CAMEO are optional inputs. The outputs are a leaderboard and a study file for CAMEO. The researcher can steer during the run.">
  <defs>
    <marker id="evo-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#8c95a1"/></marker>
    <marker id="evo-k" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#4a5059"/></marker>
  </defs>
  <g fill="none" stroke="#8c95a1" stroke-width="3">
    <path d="M638 100 Q800 108 842 222" marker-end="url(#evo-a)"/>
    <path d="M842 338 Q800 470 640 486" marker-end="url(#evo-a)"/>
    <path d="M362 486 Q200 470 160 338" marker-end="url(#evo-a)"/>
    <path d="M160 222 Q200 108 360 100" marker-end="url(#evo-a)"/>
  </g>
  <g fill="none" stroke="#4a5059" stroke-width="3">
    <path d="M238 56 H360" marker-end="url(#evo-k)"/>
    <path d="M762 56 H640" marker-end="url(#evo-k)"/>
    <path d="M638 522 H760" marker-end="url(#evo-k)"/>
    <path d="M82 112 V222" marker-end="url(#evo-k)" stroke-dasharray="7 6"/>
  </g>
  <g stroke-width="2.5">
    <rect x="30" y="20" width="200" height="84" rx="14" fill="#f1f3f5" stroke="#9aa3ad"/>
    <rect x="770" y="20" width="200" height="84" rx="14" fill="#f1f3f5" stroke="#9aa3ad" stroke-dasharray="7 6"/>
    <rect x="770" y="496" width="200" height="84" rx="14" fill="#f1f3f5" stroke="#9aa3ad"/>
    <rect x="370" y="30" width="260" height="96" rx="14" fill="#e6eefb" stroke="#2a5db0"/>
    <rect x="30" y="232" width="260" height="96" rx="14" fill="#e6eefb" stroke="#2a5db0" stroke-dasharray="7 6"/>
    <rect x="710" y="232" width="260" height="96" rx="14" fill="#e7f2ea" stroke="#3a7d4b"/>
    <rect x="370" y="434" width="260" height="96" rx="14" fill="#e7f2ea" stroke="#3a7d4b"/>
  </g>
  <g text-anchor="middle" font-weight="700" font-size="24">
    <text x="500" y="72" fill="#2a5db0">Propose</text>
    <text x="160" y="274" fill="#2a5db0">Analyze</text>
    <text x="840" y="274" fill="#3a7d4b">Train</text>
    <text x="500" y="476" fill="#3a7d4b">Score</text>
    <text x="500" y="276" fill="currentColor" font-size="22">Lineages</text>
    <text x="130" y="56" fill="#1c1f23" font-size="19">Researcher</text>
    <text x="870" y="56" fill="#1c1f23" font-size="19">Skills · CAMEO</text>
    <text x="870" y="532" fill="#1c1f23" font-size="19">Leaderboard</text>
  </g>
  <g text-anchor="middle" font-size="16" fill="#1c1f23">
    <text x="500" y="103">writer</text>
    <text x="160" y="305">analyst · strategist</text>
    <text x="840" y="305">your training script, in parallel</text>
    <text x="500" y="507">validation metric</text>
    <text x="130" y="84">brief · baseline code</text>
    <text x="870" y="84">guidance · prior designs</text>
    <text x="870" y="560">study file for CAMEO</text>
  </g>
  <text x="500" y="304" text-anchor="middle" font-size="16" fill="currentColor" opacity="0.75">parents chosen by code</text>
  <g font-size="15" font-style="italic" fill="currentColor" opacity="0.75" text-anchor="middle">
    <text x="756" y="180">new code</text>
    <text x="722" y="414">trained models</text>
    <text x="262" y="414">results</text>
    <text x="238" y="172">lessons</text>
    <text x="122" y="172">steering</text>
  </g>
  <g font-size="14" fill="currentColor">
    <rect x="30" y="566" width="28" height="18" rx="5" fill="#e6eefb" stroke="#2a5db0" stroke-width="2"/>
    <text x="66" y="580">LLM agents</text>
    <rect x="166" y="566" width="28" height="18" rx="5" fill="#e7f2ea" stroke="#3a7d4b" stroke-width="2"/>
    <text x="202" y="580">code</text>
    <rect x="262" y="566" width="28" height="18" rx="5" fill="none" stroke="#9aa3ad" stroke-width="2" stroke-dasharray="5 4"/>
    <text x="298" y="580">optional</text>
  </g>
</svg>
</figure>

A search repeats four steps until its budget of training runs is spent. The *writer* agent proposes a
design: an edit to a parent, a crossover of two parents, or something new. The evaluator trains it as
a job on your GPUs, alongside others. The design is scored on your validation metric and ranked. Every
few designs the *analyst* agent summarizes what has and has not worked, and the writer reads those
lessons before its next proposal. A *strategist* agent can shift effort between new designs and
refinement.

The agents propose and advise. Everything else is deterministic code: choosing which designs become
parents, rejecting any proposal that edits code you did not mark, stopping weak training runs early,
keeping test-set results away from the agents, and enforcing the budget. The method follows
[FunSearch and AlphaEvolve](compared.md), adapted to searches in which every evaluation is a full
training run and the researcher wants to steer.

[How it works →](how-it-works.md)

## Lineages

Editing only the current best design tends to converge on the first idea that works. By default
evoloop keeps several *lineages* going. A lineage is one founding design and its descendants.

<figure class="evo-figure">
<svg class="evo-fig" viewBox="0 0 1000 410" role="img" aria-label="Schematic of lineages in one search, as validation score against evaluations. In the explore phase three lineages are founded: a CNN baseline, a dilated CNN and a transformer. The first runs of each are protected. The baseline stops improving and is retired. In the exploit phase a crossover of the dilated CNN and the transformer founds a hybrid lineage, which ends with the best score.">
  <rect x="70" y="50" width="534" height="290" fill="#3a7d4b" opacity="0.07"/>
  <path d="M604 50 V340" stroke="#8c95a1" stroke-width="1.5" stroke-dasharray="5 6"/>
  <path d="M70 44 V340 H966" stroke="#8c95a1" stroke-width="2" fill="none"/>
  <path d="M64 54 L70 42 L76 54 M954 334 L966 340 L954 346" stroke="#8c95a1" stroke-width="2" fill="none"/>
  <g font-size="17" font-weight="700" fill="currentColor"><text x="82" y="34">Explore</text><text x="616" y="34">Exploit</text></g>
  <path d="M90 313 L135 294 L180 286 L225 286 L270 286 L315 286 L360 286 L405 286 L450 286" stroke="#a3abb3" stroke-width="3" fill="none" stroke-linejoin="round"/>
  <circle cx="90" cy="313" r="6" fill="#ffffff" stroke="#a3abb3" stroke-width="2.5"/>
  <circle cx="135" cy="294" r="6" fill="#ffffff" stroke="#a3abb3" stroke-width="2.5"/>
  <circle cx="180" cy="286" r="6" fill="#a3abb3"/>
  <circle cx="225" cy="286" r="6" fill="#a3abb3"/>
  <circle cx="270" cy="286" r="6" fill="#a3abb3"/>
  <circle cx="315" cy="286" r="6" fill="#a3abb3"/>
  <circle cx="360" cy="286" r="6" fill="#a3abb3"/>
  <circle cx="405" cy="286" r="6" fill="#a3abb3"/>
  <circle cx="450" cy="286" r="6" fill="#a3abb3"/>
  <path d="M481 277 L499 295 M481 295 L499 277" stroke="#a3abb3" stroke-width="3" fill="none"/>
  <path d="M150 281 L200 251 L255 227 L315 205 L380 189 L445 178 L510 170 L570 165 L640 159 L710 159 L780 156 L850 156" stroke="#5f6b73" stroke-width="3" fill="none" stroke-linejoin="round"/>
  <circle cx="150" cy="281" r="6" fill="#ffffff" stroke="#5f6b73" stroke-width="2.5"/>
  <circle cx="200" cy="251" r="6" fill="#ffffff" stroke="#5f6b73" stroke-width="2.5"/>
  <circle cx="255" cy="227" r="6" fill="#5f6b73"/>
  <circle cx="315" cy="205" r="6" fill="#5f6b73"/>
  <circle cx="380" cy="189" r="6" fill="#5f6b73"/>
  <circle cx="445" cy="178" r="6" fill="#5f6b73"/>
  <circle cx="510" cy="170" r="6" fill="#5f6b73"/>
  <circle cx="570" cy="165" r="6" fill="#5f6b73"/>
  <circle cx="640" cy="159" r="6" fill="#5f6b73"/>
  <circle cx="710" cy="159" r="6" fill="#5f6b73"/>
  <circle cx="780" cy="156" r="6" fill="#5f6b73"/>
  <circle cx="850" cy="156" r="6" fill="#5f6b73"/>
  <path d="M430 332 L480 308 L535 259 L590 232 L645 213 L705 202 L765 200" stroke="#5f6b73" stroke-width="3" fill="none" stroke-linejoin="round"/>
  <circle cx="430" cy="332" r="6" fill="#ffffff" stroke="#5f6b73" stroke-width="2.5"/>
  <circle cx="480" cy="308" r="6" fill="#ffffff" stroke="#5f6b73" stroke-width="2.5"/>
  <circle cx="535" cy="259" r="6" fill="#5f6b73"/>
  <circle cx="590" cy="232" r="6" fill="#5f6b73"/>
  <circle cx="645" cy="213" r="6" fill="#5f6b73"/>
  <circle cx="705" cy="202" r="6" fill="#5f6b73"/>
  <circle cx="765" cy="200" r="6" fill="#5f6b73"/>
  <path d="M640 159 Q668 158 686 153 M645 213 Q682 200 688 156" stroke="#2a5db0" stroke-width="2.5" fill="none" stroke-dasharray="6 5"/>
  <path d="M690 151 L740 135 L795 119 L850 105 L905 94 L950 86" stroke="#2a5db0" stroke-width="3" fill="none" stroke-linejoin="round"/>
  <circle cx="690" cy="151" r="6" fill="#ffffff" stroke="#2a5db0" stroke-width="2.5"/>
  <circle cx="740" cy="135" r="6" fill="#ffffff" stroke="#2a5db0" stroke-width="2.5"/>
  <circle cx="795" cy="119" r="6" fill="#2a5db0"/>
  <circle cx="850" cy="105" r="6" fill="#2a5db0"/>
  <circle cx="905" cy="94" r="6" fill="#2a5db0"/>
  <circle cx="950" cy="86" r="6" fill="#2a5db0"/>
  <circle cx="950" cy="86" r="13" fill="none" stroke="#2a5db0" stroke-width="2.5"/>
  <g font-size="16" font-weight="700" fill="currentColor">
    <text x="196" y="310">CNN baseline</text>
    <text x="862" y="161">Dilated CNN</text>
    <text x="777" y="205">Transformer</text>
    <text x="748" y="100" fill="#2a5db0">Hybrid</text>
  </g>
  <text x="706" y="183" font-size="14" font-style="italic" fill="#2a5db0">crossover</text>
  <g font-size="14" fill="currentColor" opacity="0.85">
    <text x="70" y="366">evaluations</text>
    <text transform="translate(52 250) rotate(-90)">validation score</text>
    <circle cx="610" cy="361" r="6" fill="#ffffff" stroke="#5f6b73" stroke-width="2.5"/><text x="624" y="366">protected run</text>
    <path d="M740 355 l12 12 m-12 0 l12 -12" stroke="#a3abb3" stroke-width="3" fill="none"/><text x="762" y="366">retired</text>
    <path d="M836 361 h30" stroke="#2a5db0" stroke-width="2.5" stroke-dasharray="6 5"/><text x="874" y="366">crossover</text>
  </g>
</svg>
</figure>

In this schematic three lineages are founded while the search explores. A new lineage's first runs are
protected from comparison with the others, so the transformer survives a poor start. The baseline stops
improving and is retired. Later the search exploits what it has found: it refines the leading lineages
and crosses two of them, and the hybrid ends up best.

Lineages are one of five selection strategies. The others are a MAP-Elites archive, tournament
selection as in regularized evolution, a Pareto front over the score and a second measure such as model
size, and greedy hill climbing. Any of them can run as islands, as in FunSearch.

[Parent selection →](parents.md) · [Schedule →](schedule.md)

## Agents and autonomy

Only the writer is required. The analyst and the strategist run in the default configuration and can
be turned off. An assessor reviews, for you, how well the other agents are doing. A coordinator, which
chooses the kind of change for each proposal, is off unless you ask for more autonomy.

One setting controls how much the agents decide. At one end the controller plans every step and the
agents only write code. At the other, agents also choose what kind of change to make and adjust the
schedule. At every level the controller holds the budget, your limits, and the rule that only marked
code can change.

[Agents →](agents.md)

## Skills

A skill is a file of search settings and agent guidance for one goal: raising a score, distilling a
teacher into a student, mapping an accuracy-size frontier, fine-tuning, speeding up an algorithm.
evoloop runs without one. With one, you supply less yourself. The library has thirteen, and the one you
choose is copied into your search folder, where you can edit it. You can also write your own, for any
goal, without following the library.

[Choose a skill →](which-search.md) · [Edit or merge a skill →](skills.md) · [Write a skill →](custom-skills.md)

## Running a search

The simplest way is from Claude Code. Open the repository there and say what you want to optimize. It
marks the code with you, writes the evaluator, asks the setup questions, and shows you a plan with a
cost estimate. Nothing is spent until you approve the plan. Claude Code then launches the search,
reports on it, and turns your feedback into changes to the running search. Every step is also a
command you can run yourself.

Training runs on a workstation or a Slurm cluster, one job per design. The agents need an Anthropic API
key or a Claude Code login.

[Get started →](get-started.md) · [Monitor and steer a search →](steering.md) · [Budget and cost →](cost.md)

## CAMEO

[CAMEO](https://cameo-db.github.io) is a public database of trained models with their code and
scores, and it already holds searches run with evoloop. A search can start from designs in CAMEO, and
every search is saved in CAMEO's format so that it can be deposited there.

[Start from earlier designs →](warm-start.md) · [Save and deposit the study →](study.md)

## Extending

The library skills, run types and strategies are starting points. Without touching the code you can
write your own skill, schedule, metrics and limits, and replace the LLM with a proposer of your own. A
new strategy, scheduler or LLM backend is a short module.

[Extending evoloop →](extending.md)

## Disclaimer

Every AutoResearch method is a search, and how a search is run changes what it finds. No strategy,
preset or custom configuration is guaranteed to find the best design. evoloop is infrastructure for
running different kinds of search and recording what each one did. The agents add variability of
their own: an LLM does not return the same proposal twice, so two runs of the same search can end in
different places. Treat the result of a search as a candidate, and check it on held-out data.

[Limitations →](limitations.md)

</div>
