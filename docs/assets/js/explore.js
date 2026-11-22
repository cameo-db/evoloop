/* The interactive figures of the documentation. Plain JavaScript, no dependencies.
   - The home page's loop: three fixed stages whose examples change with the goal chosen.
   - The plan preview reads plans.json, written by the tool's own settings code (evoloop menu --plans).
   - The parent-selection playground and the early-stopping figure are toy simulations, labelled as such. */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var MODES = [["new", "new designs"], ["cross", "crossover"], ["local", "local moves"]];

  function el(tag, attrs, kids) {
    var svg = ["svg", "rect", "line", "path", "circle", "text", "g", "title"].indexOf(tag) >= 0;
    var node = svg ? document.createElementNS(NS, tag) : document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") { node.textContent = attrs[k]; } else if (k === "html") { node.innerHTML = attrs[k]; } else { node.setAttribute(k, attrs[k]); }
    });
    (kids || []).forEach(function (kid) { if (kid) { node.appendChild(kid); } });
    return node;
  }
  function clear(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }
  function pct(v) { return Math.round(v * 100) + "%"; }
  function chipRow(label, options, value, onPick) {
    var group = el("div", {"class": "evo-chips", role: "group", "aria-label": label});
    var buttons = options.map(function (opt) {
      var b = el("button", {type: "button", "class": "evo-chip", "aria-pressed": "false"}, [document.createTextNode(opt[1])]);
      if (opt[3]) { b.appendChild(el("code", {text: opt[3]})); }
      if (opt[2]) { b.title = opt[2]; }
      b.addEventListener("click", function () { mark(opt[0]); onPick(opt[0]); });
      group.appendChild(b);
      return [opt[0], b];
    });
    function mark(v) { buttons.forEach(function (p) { p[1].setAttribute("class", "evo-chip" + (p[0] === v ? " on" : "")); p[1].setAttribute("aria-pressed", p[0] === v ? "true" : "false"); }); }
    mark(value);
    var row = el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: label}), group]);
    row.mark = mark;
    return row;
  }

  /* ---------------------------------------------------------------- the loop on the home page */
  var LOOP = {
    "model-performance": {name: "Improve a model",
      propose: "The agent is told to work out what limits the current best model (capacity, optimization or generalization) and to make one change that addresses it.",
      evaluate: "Your script trains the design and reports its validation score.",
      choose: "Several lineages are kept. The best ones get more edits, and new lineages keep being founded."},
    "settings-tuning": {name: "Tune hyperparameters",
      propose: "The agent reads the earlier trials and picks the next hyperparameters, changing the ones that interact (learning rate with batch size, width with depth) together.",
      evaluate: "Your script trains the same model with those values and reports the score and the parameter count.",
      choose: "Each trial starts from the best one so far."},
    "model-efficiency": {name: "Shrink a model",
      propose: "The agent designs a cheaper student network and the way to train it against your current model, which acts as the teacher.",
      evaluate: "Your script trains the student on the teacher's outputs and reports its score with its parameter count or speed.",
      choose: "Students on the trade-off between score and size are kept, so a small student survives even when a larger one scores higher."},
    "algorithm-runtime": {name: "Speed up an algorithm",
      propose: "The agent rewrites the marked function. It is told to look for a better algorithm first and to remove repeated work second.",
      evaluate: "Your benchmark times the code and compares its output with a reference. A version with a wrong output is rejected.",
      choose: "The fastest correct version is built on, and different approaches keep being tried."}
  };
  function loop(root) {
    var holder = root.querySelector(".evo-loop-goals"), link = root.querySelector(".evo-loop-link"), label = root.querySelector(".evo-loop-skill");
    function show(goal) {
      ["propose", "evaluate", "choose"].forEach(function (stage) {
        var node = root.querySelector('[data-stage="' + stage + '"]');
        if (node) { node.textContent = LOOP[goal][stage]; }
      });
      if (label) { label.textContent = goal; label.setAttribute("href", label.getAttribute("data-base") + goal + "/"); }
      if (link) { link.setAttribute("href", link.getAttribute("data-base") + "?goal=" + goal + "#preview-a-search"); }
    }
    if (holder) {
      holder.appendChild(chipRow("Skill", Object.keys(LOOP).map(function (g) { return [g, LOOP[g].name]; }), "model-performance", show));
    }
    show("model-performance");
  }

  /* ---------------------------------------------------------------- the plan preview */
  var RUN_LABEL = {explore_then_exploit: "Explore, then refine", refine: "Refine what works", survey: "Explore broadly",
                   discovery: "Look for something unusual", settings_only: "Settings only", custom: "Your own"};
  var WORDS = {
    strategy: {lineage: "Several lineages are kept going side by side", archive: "The best design of each kind is kept",
               tournament: "The best of a few recent designs", pareto: "Designs on the trade-off between two metrics", greedy: "Always the current best design"},
    space: {settings_only: "Numbers only", module: "One part of the model", template: "The model, keeping its overall shape",
            open_architecture: "The whole model", architecture_and_recipe: "The model and how it is trained", custom: "The parts the goal names"},
    settings_by: {agent: "an agent", sampler: "a random sampler in code", tpe: "a built-in Bayesian optimizer"},
    level: {minimal: "writers", standard: "writers and an analyst", full: "writers and an analyst, with re-checks of the leader"}
  };
  function source(text) {
    if (!text || text === "default") { return "default"; }
    if (text.indexOf("skill") === 0) { return "from the skill"; }
    if (text.indexOf("run type") === 0) { return "from the run type"; }
    if (text.indexOf("guidance") === 0) { return "from the budget size"; }
    if (text.indexOf("autonomy") === 0) { return "from the autonomy level"; }
    return text;
  }
  function planPreview(root, data) {
    var query = new URLSearchParams(window.location.search);
    var state = {run: data.run_types.indexOf(query.get("run")) >= 0 ? query.get("run") : "explore_then_exploit",
                 skill: data.skills.indexOf(query.get("goal")) >= 0 ? query.get("goal") : "", level: "", budget: 100};
    function plan(s) { return data.plans[[s.run, s.skill, s.level, s.budget].join("|")]; }
    function facts(p) {
      var total = Object.keys(p.calls).reduce(function (a, k) { return a + p.calls[k]; }, 0);
      var anyNew = p.phases.some(function (ph) { return ph[1] > 0; });
      var who = p.space === "settings_only" ? WORDS.settings_by[p.settings_by] : ((p.calls.writer || 0) > 0 ? "an agent" : "code alone");
      var stop = p.stop === "ladder" ? "every design, " + p.rungs.map(function (r) { return "at " + pct(r[0]) + " keep the best " + pct(r[1]); }).join(", ")
        : (p.stop === "screen" && anyNew ? "new designs are compared half way and the weaker half stop" : "none");
      var roles = total ? WORDS.level[p.level] + (p.strategist !== "off" ? ", and a strategist" : "") + (p.coordinator === "agent" ? ", and an agent choosing each move" : "") : "None";
      return {
        top: [
          ["Which earlier designs get built on", WORDS.strategy[p.strategy] + (p.islands > 1 ? ", in " + p.islands + " separate populations" : "") + (p.second ? " (score and " + p.second + ")" : ""), source(p.from.strategy), p.strategy],
          ["What may change", WORDS.space[p.space] || p.space, source(p.from.space), p.space],
          ["Who proposes the next design", who, source(p.space === "settings_only" ? p.from.settings_by : p.from.level), ""],
          ["Designs stopped early", stop, "", ""],
          ["Agents at work", roles, total ? source(p.from.level) : "", ""],
          ["Designs the budget covers", String(p.designs), "", ""]
        ],
        calls: total ? Object.keys(p.calls).map(function (k) { return k + " " + p.calls[k]; }).join(" · ") + "  (about " + total + " in all)" : "none"
      };
    }
    function bar(p, budget) {
      var W = 720, H = 108, L = 4, R = 4, top = 22, h = 34, width = W - L - R;
      var svg = el("svg", {viewBox: "0 0 " + W + " " + H, role: "img", "class": "evo-bar",
                           "aria-label": "How the " + budget + " evaluations are shared between new designs, crossover and local moves"});
      var from = 0;
      p.phases.forEach(function (ph, i) {
        var x0 = L + width * from, span = width * (ph[0] - from), x = x0;
        MODES.forEach(function (m, j) {
          var share = ph[1 + j], w = span * share;
          if (w <= 0) { return; }
          var seg = el("rect", {x: x + 1, y: top, width: Math.max(0, w - 2), height: h, rx: 3, "class": "evo-fill-" + m[0]});
          seg.appendChild(el("title", {text: m[1] + ": " + pct(share) + " of evaluations " + Math.round(from * budget) + " to " + Math.round(ph[0] * budget)}));
          svg.appendChild(seg);
          if (w > 30) { svg.appendChild(el("text", {x: x + w / 2, y: top + h + 15, "text-anchor": "middle", "class": "evo-share", text: pct(share)})); }
          x += w;
        });
        if (i > 0) { svg.appendChild(el("line", {x1: x0, y1: top - 6, x2: x0, y2: top + h + 6, "class": "evo-tick"})); }
        svg.appendChild(el("text", {x: x0 + 2, y: 14, "class": "evo-small", text: p.phases.length > 1 ? (i === 0 ? "first " : "then, to ") + pct(ph[0]) + " of the budget" : "the whole budget"}));
        from = ph[0];
      });
      svg.appendChild(el("text", {x: L, y: H - 6, "class": "evo-small", text: "evaluation 1"}));
      svg.appendChild(el("text", {x: W - R, y: H - 6, "text-anchor": "end", "class": "evo-small", text: "evaluation " + budget}));
      return svg;
    }
    var out = el("div", {"class": "evo-out"});
    var goalPick = el("select", {"class": "evo-select", "aria-label": "Goal"});
    data.skills.forEach(function (name) {
      var o = el("option", {value: name, text: name ? data.about.goals[name] + "  (" + name + ")" : "No skill"});
      if (name === state.skill) { o.selected = true; }
      goalPick.appendChild(o);
    });
    goalPick.addEventListener("change", function () { state.skill = goalPick.value; render(); });
    clear(root);
    root.appendChild(el("div", {"class": "evo-controls"}, [
      chipRow("Run type", data.run_types.map(function (r) { return [r, RUN_LABEL[r] || r, data.about.run_types[r], r]; }), state.run, function (v) { state.run = v; render(); }),
      el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: "Skill (optional)"}), goalPick]),
      chipRow("Budget", data.budgets.map(function (b) { return [b, b + " evaluations"]; }), state.budget, function (v) { state.budget = v; render(); }),
      chipRow("How much the agents decide", data.levels.map(function (l) { return [l, l || "run type default", data.about.levels[l]]; }), state.level, function (v) { state.level = v; render(); })
    ]));
    root.appendChild(out);
    function render() {
      var p = plan(state), base = plan({run: "explore_then_exploit", skill: "", level: "", budget: state.budget});
      var now = facts(p), was = facts(base), list = el("dl", {"class": "evo-facts"}), changed = [];
      now.top.forEach(function (row, i) {
        var differs = row[1] !== was.top[i][1];
        if (differs) { changed.push(row[0].toLowerCase() + ": " + row[1].toLowerCase()); }
        list.appendChild(el("dt", {text: row[0]}));
        var dd = el("dd", {"class": differs ? "evo-changed" : ""}, [document.createTextNode(row[1])]);
        if (row[3]) { dd.appendChild(el("code", {text: row[3]})); }
        if (row[2]) { dd.appendChild(el("span", {"class": "evo-from", text: row[2]})); }
        list.appendChild(dd);
      });
      var sharesDiffer = JSON.stringify(p.phases) !== JSON.stringify(base.phases);
      var note = el("p", {"class": "evo-read"});
      note.textContent = (!changed.length && !sharesDiffer) ? "This is the plain default at this budget."
        : "Marked lines differ from the plain default at this budget" + (sharesDiffer ? ", and so does the split of the budget." : ".");
      var brief = "run:\n  type: " + state.run + (state.skill ? "\n  skill: " + state.skill : "") +
        (state.level ? "\nharness:\n  autonomy: " + state.level : "") + "\nbudget:\n  evaluations: " + state.budget;
      var deeper = el("details", {"class": "evo-more"}, [
        el("summary", {text: "Agent calls by role, and the lines for your brief"}),
        el("p", {"class": "evo-read", text: "Agent calls, about: " + now.calls}),
        el("pre", {"class": "evo-brief"}, [el("code", {text: brief})])
      ]);
      clear(out);
      [el("h4", {text: "How the budget is split"}),
       el("div", {"class": "evo-legend"}, MODES.map(function (m) { return el("span", {}, [el("i", {"class": "evo-swatch evo-bg-" + m[0]}), document.createTextNode(m[1])]); })),
       bar(p, state.budget), el("h4", {text: "What this search does"}), list, note,
       p.warn.length ? el("div", {"class": "evo-warn"}, [el("strong", {text: "evoloop plan would warn: "}), el("ul", {}, p.warn.map(function (i) { return el("li", {text: data.warnings[i]}); }))]) : null,
       deeper].forEach(function (node) { if (node) { out.appendChild(node); } });
    }
    render();
  }

  /* ---------------------------------------------------------------- the parent-selection playground */
  function rng(seed) {
    var a = seed >>> 0;
    function next() { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }
    next.normal = function () { var u = 0, v = 0; while (u === 0) { u = next(); } v = next(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
    return next;
  }
  function playground(root) {
    var BUDGET = 60, W = 720, H = 250, L = 44, R = 12, T = 12, B = 30;
    var state = {strategy: "greedy", fresh: 0.1, noise: 0.03, seed: 7, timer: null};
    var sim;
    function best(list) { return list.reduce(function (a, b) { return b.score > a.score ? b : a; }); }
    function landscape(seed) {
      var r = rng(seed * 101 + 3);
      // The baseline's own hill is always low and near the left. The other hills differ from one landscape to the
      // next in number, place, height and width, and so does which of them is the highest.
      var peaks = [[0.14 + 0.10 * r(), 0.42 + 0.16 * r(), 0.07 + 0.05 * r()]];
      var slots = r() < 0.5 ? [[0.40, 0.58], [0.70, 0.93]] : [[0.36, 0.48], [0.56, 0.70], [0.80, 0.95]];
      var top = Math.floor(r() * slots.length);
      slots.forEach(function (s, i) { peaks.push([s[0] + (s[1] - s[0]) * r(), i === top ? 1.0 : 0.60 + 0.26 * r(), i === top ? 0.02 + 0.015 * r() : 0.04 + 0.03 * r()]); });
      return function (x) { return peaks.reduce(function (m, p) { return Math.max(m, p[1] * Math.exp(-Math.pow((x - p[0]) / p[2], 2) / 2)); }, 0.05); };
    }
    function add(x, mode, parents, lineage) {
      x = Math.min(1, Math.max(0, x));
      var d = {x: x, truth: sim.f(x), mode: mode, parents: parents || [], lineage: lineage === undefined ? sim.lineages++ : lineage, n: sim.designs.length};
      d.score = d.truth + state.noise * sim.r.normal();
      sim.designs.push(d);
      if (sim.designs.length > 1) { sim.counts[mode] += 1; }
      sim.last = d;
    }
    function eligible() {        // the designs the parent rule could build on next
      var all = sim.designs;
      if (state.strategy === "greedy") { return [{elite: best(all), size: 1}]; }
      if (state.strategy === "tournament") { return all.slice(-12).map(function (d) { return {elite: d, size: 1}; }); }
      var groups = {};
      all.forEach(function (d) { var key = state.strategy === "archive" ? Math.min(9, Math.floor(d.x * 10)) : d.lineage; (groups[key] = groups[key] || []).push(d); });
      var elites = Object.keys(groups).map(function (k) { return {elite: best(groups[k]), size: groups[k].length}; })
        .sort(function (a, b) { return b.elite.score - a.elite.score; });
      return state.strategy === "lineage" ? elites.slice(0, 4) : elites;
    }
    function pickParent() {
      var pool = eligible(), r = sim.r;
      if (state.strategy === "greedy") { return pool[0].elite; }
      if (state.strategy === "tournament") {
        var drawn = [];
        for (var i = 0; i < 3; i++) { drawn.push(pool[Math.floor(r() * pool.length)].elite); }
        return best(drawn);
      }
      var weights = pool.map(function (e, i) { return (pool.length - i) / (1 + e.size); }), sum = weights.reduce(function (a, b) { return a + b; }, 0), t = r() * sum;
      for (var j = 0; j < pool.length; j++) { t -= weights[j]; if (t <= 0) { return pool[j].elite; } }
      return pool[0].elite;
    }
    function step(quiet) {
      if (sim.designs.length > BUDGET) { stop(); return; }
      var done = sim.designs.length - 1, cross = state.fresh < 0.9 && sim.lineages >= 2 ? 0.1 : 0;
      var shares = {new: state.fresh, cross: cross, local: Math.max(0, 1 - state.fresh - cross)};
      var mode = ["new", "cross", "local"].reduce(function (a, m) { return shares[m] * (done + 1) - sim.counts[m] > shares[a] * (done + 1) - sim.counts[a] ? m : a; }, "local");
      if (shares[mode] <= 0) { mode = "local"; }
      if (mode === "new") { add(sim.r(), "new", null); }
      else if (mode === "cross") {
        var a = pickParent(), others = sim.designs.filter(function (d) { return d.lineage !== a.lineage; });
        var b = best(others), mix = 0.3 + 0.4 * sim.r();
        add(a.x * mix + b.x * (1 - mix), "cross", [a, b]);
      } else { var p = pickParent(); add(p.x + 0.035 * sim.r.normal(), "local", [p], p.lineage); }
      if (quiet !== true) { draw(); }
    }
    function stop() { if (state.timer) { clearInterval(state.timer); state.timer = null; } runButton.textContent = "Replay step by step"; }
    function reset() {
      stop();
      sim = {f: landscape(state.seed), r: rng(state.seed * 7919 + 11), designs: [], counts: {new: 0, cross: 0, local: 0}, lineages: 0, last: null};
      add(0.2, "new", null);        // the baseline: on the nearest, lowest hill
      draw();
    }
    // A change of setting reruns the whole search at once, so its effect shows without pressing anything.
    function finish() { reset(); while (sim.designs.length <= BUDGET) { step(true); } draw(); }
    function play() { reset(); state.timer = setInterval(function () { step(); }, 120); runButton.textContent = "Replaying…"; }

    // The controls are built once and stay in place, so a slider keeps the keyboard focus while the plot changes.
    var freshLabel = el("span", {"class": "evo-label"}), noiseLabel = el("span", {"class": "evo-label"});
    var fresh = el("input", {type: "range", min: 0, max: 80, step: 5, value: Math.round(state.fresh * 100), "aria-label": "Share of new designs"});
    fresh.addEventListener("input", function () { state.fresh = fresh.value / 100; labels(); finish(); });
    var noise = el("input", {type: "range", min: 0, max: 15, step: 1, value: Math.round(state.noise * 100), "aria-label": "Noise in the score"});
    noise.addEventListener("input", function () { state.noise = noise.value / 100; labels(); finish(); });
    function labels() { freshLabel.textContent = "New designs: " + pct(state.fresh) + " of the budget"; noiseLabel.textContent = "Noise in a score: ±" + state.noise.toFixed(2); }
    var runButton = el("button", {type: "button", "class": "evo-chip go", text: "Replay step by step"});
    runButton.addEventListener("click", play);
    var buttons = el("div", {"class": "evo-chips"}, [runButton].concat([["Another landscape", function () { state.seed += 1; finish(); }]].map(function (b) {
      var node = el("button", {type: "button", "class": "evo-chip", text: b[0]});
      node.addEventListener("click", b[1]);
      return node;
    })));
    var plot = el("div"), read = el("p", {"class": "evo-read", "aria-live": "polite"});
    clear(root);
    root.appendChild(el("div", {"class": "evo-controls"}, [
      chipRow("Parent rule", [["greedy", "greedy", "always the current best"], ["tournament", "tournament", "the best of three recent designs"],
                              ["lineage", "lineage", "the best of the leading lineages, the less used favoured"], ["archive", "archive", "the best of each region, the less used favoured"]],
              state.strategy, function (v) { state.strategy = v; finish(); }),
      el("div", {"class": "evo-row"}, [freshLabel, fresh]),
      el("div", {"class": "evo-row"}, [noiseLabel, noise]),
      el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: "Each change reruns the whole search."}), buttons])
    ]));
    root.appendChild(el("div", {"class": "evo-legend"}, [["base", "the baseline"]].concat(MODES).map(function (m) {
      return el("span", {}, [el("i", {"class": "evo-swatch evo-bg-" + m[0]}), document.createTextNode(m[1])]);
    }).concat([el("span", {}, [el("i", {"class": "evo-swatch evo-ringed"}), document.createTextNode("the leader")]),
               el("span", {}, [el("i", {"class": "evo-swatch evo-dashed"}), document.createTextNode("could be a parent next")])])));
    root.appendChild(plot);
    root.appendChild(read);
    labels();

    function draw() {
      var X = function (x) { return L + (W - L - R) * x; }, Y = function (v) { return T + (H - T - B) * (1 - Math.min(1.08, Math.max(-0.05, v)) / 1.08); };
      var svg = el("svg", {viewBox: "0 0 " + W + " " + H, role: "img", "class": "evo-plot", "aria-label": "A toy design space: the true quality of every possible design, and the designs tried so far"});
      [0, 0.25, 0.5, 0.75, 1].forEach(function (v) {
        svg.appendChild(el("line", {x1: L, y1: Y(v), x2: W - R, y2: Y(v), "class": "evo-grid"}));
        svg.appendChild(el("text", {x: L - 6, y: Y(v) + 4, "text-anchor": "end", "class": "evo-small", text: v.toFixed(2)}));
      });
      var path = "";
      for (var i = 0; i <= 240; i++) { path += (i ? "L" : "M") + X(i / 240).toFixed(1) + " " + Y(sim.f(i / 240)).toFixed(1); }
      svg.appendChild(el("path", {d: path, "class": "evo-curve"}));
      svg.appendChild(el("text", {x: (L + W - R) / 2, y: H - 6, "text-anchor": "middle", "class": "evo-small", text: "every possible design, laid out on a line (similar designs are close)"}));
      svg.appendChild(el("text", {transform: "translate(12 " + ((T + H - B) / 2) + ") rotate(-90)", "text-anchor": "middle", "class": "evo-small", text: "score"}));
      var lead = best(sim.designs), pool = eligible().map(function (e) { return e.elite; });
      if (sim.last && sim.last.parents.length) {
        sim.last.parents.forEach(function (p) { svg.appendChild(el("line", {x1: X(p.x), y1: Y(p.score), x2: X(sim.last.x), y2: Y(sim.last.score), "class": "evo-link"})); });
      }
      pool.forEach(function (d) { svg.appendChild(el("circle", {cx: X(d.x), cy: Y(d.score), r: 8, "class": "evo-elig"})); });
      sim.designs.forEach(function (d) {
        var dot = el("circle", {cx: X(d.x), cy: Y(d.score), r: d === sim.last ? 6 : 4.5, "class": "evo-dot evo-fill-" + (d.n === 0 ? "base" : d.mode) + (d === sim.last ? " now" : "")});
        dot.appendChild(el("title", {text: "Design " + (d.n + 1) + (d.n === 0 ? ", the baseline" : ", " + {new: "a new design", cross: "a crossover", local: "a local move"}[d.mode]) + ": scored " + d.score.toFixed(2) + " (true quality " + d.truth.toFixed(2) + ")"}));
        svg.appendChild(dot);
      });
      svg.appendChild(el("circle", {cx: X(lead.x), cy: Y(lead.score), r: 10.5, "class": "evo-ring"}));
      clear(plot);
      plot.appendChild(svg);
      var found = lead.truth > 0.9, n = sim.designs.length - 1, last = sim.last;
      var what = !last || last.n === 0 ? "" : " Design " + (last.n + 1) + " was " + (last.mode === "local" ? "a local move on design " + (last.parents[0].n + 1)
        : last.mode === "cross" ? "a crossover of designs " + (last.parents[0].n + 1) + " and " + (last.parents[1].n + 1) : "a new design") + ".";
      read.textContent = n + " of " + BUDGET + " evaluations used." + what + " The leader's true quality is " + lead.truth.toFixed(2) + " of a possible 1.00" +
        (n >= BUDGET ? (found ? ": the search found the highest peak." : ": the search settled on a lower peak.") : ".") +
        (Math.abs(lead.score - lead.truth) > 0.08 ? " Its score, " + lead.score.toFixed(2) + ", flatters it: that is noise." : "") +
        " " + pool.length + (pool.length === 1 ? " design" : " designs") + " could be a parent next.";
    }
    finish();
  }

  /* ---------------------------------------------------------------- the early-stopping figure */
  function ladder(root) {
    var W = 720, H = 250, L = 44, R = 12, T = 12, B = 30, N = 24;
    var state = {at: 0.1, keep: 0.5, second: true};
    var r = rng(42), runs = [];
    for (var i = 0; i < N; i++) {      // each design: its score at the end of a full run, and how it gets there
      var slow = i === 5 || i === 17;  // two designs start slowly and end best
      runs.push({final: slow ? (i === 5 ? 0.93 : 0.90) : 0.45 + 0.42 * r(), rate: 0.08 + 0.14 * r(), slow: slow, n: i});
    }
    // The score after a share t of the run. Every curve ends at its `final`, the score at the full training length.
    function at(run, t) {
      var quick = (1 - Math.exp(-t / run.rate)) / (1 - Math.exp(-1 / run.rate));
      return run.final * (run.slow ? 0.45 * quick + 0.55 * Math.pow(t, 1.6) : quick);
    }
    var winner = runs.reduce(function (a, b) { return b.final > a.final ? b : a; });
    var firstLabel = el("span", {"class": "evo-label"}), keepLabel = el("span", {"class": "evo-label"});
    var a = el("input", {type: "range", min: 5, max: 60, step: 5, value: Math.round(state.at * 100), "aria-label": "Where the first check is"});
    a.addEventListener("input", function () { state.at = a.value / 100; draw(); });
    var k = el("input", {type: "range", min: 25, max: 75, step: 5, value: Math.round(state.keep * 100), "aria-label": "Share kept at each check"});
    k.addEventListener("input", function () { state.keep = k.value / 100; draw(); });
    var rungRow = chipRow("Checks", [[false, "one"], [true, "two"]], state.second, function (v) { state.second = v; draw(); });
    var plot = el("div"), read = el("p", {"class": "evo-read", "aria-live": "polite"});
    clear(root);
    root.appendChild(el("div", {"class": "evo-controls"}, [el("div", {"class": "evo-row"}, [firstLabel, a]), el("div", {"class": "evo-row"}, [keepLabel, k]), rungRow]));
    root.appendChild(plot);
    root.appendChild(read);
    function outcome() {
      var rungs = [[state.at, state.keep]].concat(state.second ? [[Math.min(0.9, state.at * 3), state.keep]] : []);
      var alive = runs.slice(), stopped = {}, cost = 0;
      rungs.forEach(function (rung) {
        var ranked = alive.slice().sort(function (p, q) { return at(q, rung[0]) - at(p, rung[0]); });
        var kept = ranked.slice(0, Math.max(1, Math.round(ranked.length * rung[1])));
        ranked.slice(kept.length).forEach(function (run) { stopped[run.n] = rung[0]; cost += rung[0]; });
        alive = kept;
      });
      return {rungs: rungs, alive: alive, stopped: stopped, cost: cost + alive.length};
    }
    function draw() {
      var o = outcome(), X = function (t) { return L + (W - L - R) * t; }, Y = function (v) { return T + (H - T - B) * (1 - v); };
      firstLabel.textContent = "First check at " + pct(state.at) + " of a run";
      keepLabel.textContent = "Kept at each check: the best " + pct(state.keep);
      var svg = el("svg", {viewBox: "0 0 " + W + " " + H, role: "img", "class": "evo-plot", "aria-label": "The learning curves of 24 designs, and where the weaker ones are stopped"});
      [0, 0.25, 0.5, 0.75, 1].forEach(function (v) {
        svg.appendChild(el("line", {x1: L, y1: Y(v), x2: W - R, y2: Y(v), "class": "evo-grid"}));
        svg.appendChild(el("text", {x: L - 6, y: Y(v) + 4, "text-anchor": "end", "class": "evo-small", text: v.toFixed(2)}));
      });
      o.rungs.forEach(function (rung) {
        svg.appendChild(el("line", {x1: X(rung[0]), y1: T, x2: X(rung[0]), y2: H - B, "class": "evo-link"}));
        svg.appendChild(el("text", {x: X(rung[0]) + 4, y: T + 10, "class": "evo-small", text: "check at " + pct(rung[0])}));
      });
      function curve(run, from, to) {
        var d = "";
        for (var j = 0; j <= 60; j++) { var t = from + (to - from) * j / 60; d += (j ? "L" : "M") + X(t).toFixed(1) + " " + Y(at(run, t)).toFixed(1); }
        return d;
      }
      runs.forEach(function (run) {
        var end = o.stopped[run.n] === undefined ? 1 : o.stopped[run.n];
        if (end < 1) { svg.appendChild(el("path", {d: curve(run, end, 1), "class": "evo-run ghost" + (run === winner ? " best" : "")})); }   // what it would have done
        var line = el("path", {d: curve(run, 0, end), "class": "evo-run" + (end < 1 ? " cut" : "") + (run === winner ? " best" : "")});
        line.appendChild(el("title", {text: "Design " + (run.n + 1) + (end < 1 ? ": stopped at " + pct(end) + " of its run; a full run would have scored " : ": trained to the end, scoring ") + run.final.toFixed(2)}));
        svg.appendChild(line);
        if (end < 1) { svg.appendChild(el("circle", {cx: X(end), cy: Y(at(run, end)), r: 3.5, "class": "evo-stop"})); }
      });
      svg.appendChild(el("text", {x: (L + W - R) / 2, y: H - 6, "text-anchor": "middle", "class": "evo-small", text: "share of a full training run"}));
      svg.appendChild(el("text", {transform: "translate(12 " + ((T + H - B) / 2) + ") rotate(-90)", "text-anchor": "middle", "class": "evo-small", text: "score so far"}));
      clear(plot);
      plot.appendChild(svg);
      var kept = o.alive.reduce(function (p, q) { return q.final > p.final ? q : p; }), lost = o.stopped[winner.n] !== undefined;
      read.textContent = "These " + N + " designs cost " + o.cost.toFixed(1) + " full runs in place of " + N + ", so 100 evaluations would cover about " +
        Math.round(100 * N / o.cost) + " designs. " + o.alive.length + " are trained to the end. " +
        (lost ? "The design that a full run would have scored highest (" + winner.final.toFixed(2) + ", the thick line) was stopped at " + pct(o.stopped[winner.n]) +
                ": it starts slowly. The best design kept scores " + kept.final.toFixed(2) + "."
              : "The design a full run scores highest (" + winner.final.toFixed(2) + ", the thick line) was kept.");
    }
    draw();
    root.evoOutcome = function (at_, keep, second) { state.at = at_; state.keep = keep; state.second = second; var o = outcome(); return o.stopped[winner.n] === undefined; };
  }

  function start() {
    var home = document.getElementById("evo-loop");
    if (home) { loop(home); }
    var rungs = document.getElementById("evo-ladder");
    if (rungs) { ladder(rungs); }
    var play = document.getElementById("evo-playground");
    if (play) { playground(play); }
    var plan = document.getElementById("evo-plan-explorer");
    if (plan) {
      fetch(new URL(plan.getAttribute("data-src"), document.baseURI)).then(function (r) { return r.json(); })
        .then(function (data) { planPreview(plan, data); })
        .catch(function () { plan.textContent = "The preview could not load its data. `evoloop plan` prints the same for your own brief."; });
    }
  }
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", start); } else { start(); }
})();
