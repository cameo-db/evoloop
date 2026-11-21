/* The interactive figures of the documentation. Plain JavaScript, no dependencies.
   - The plan explorer reads plans.json, which is written by the tool's own settings code (evoloop menu --plans).
   - The search playground is a toy simulation of how parents are chosen. It is not a model of real searches. */
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
  function chips(label, options, value, onPick) {
    var row = el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: label})]);
    var group = el("div", {"class": "evo-chips", role: "group", "aria-label": label});
    options.forEach(function (opt) {
      var b = el("button", {type: "button", "class": "evo-chip" + (opt[0] === value ? " on" : ""), text: opt[1], "aria-pressed": opt[0] === value ? "true" : "false"});
      if (opt[2]) { b.title = opt[2]; }
      b.addEventListener("click", function () { onPick(opt[0]); });
      group.appendChild(b);
    });
    row.appendChild(group);
    return row;
  }
  function pct(v) { return Math.round(v * 100) + "%"; }

  /* ---------------------------------------------------------------- the plan explorer */
  function planExplorer(root, data) {
    var state = {run: "explore_then_exploit", skill: "", level: "", budget: 100};
    var words = {
      strategy: {lineage: "families of designs kept side by side (lineage)", archive: "the best of each kind on a grid (archive)",
                 tournament: "a tournament among recent designs", pareto: "a trade-off front on two figures (pareto)", greedy: "always the current best (greedy)"},
      space: {settings_only: "settings only", module: "one module", template: "the model, keeping its overall shape",
              open_architecture: "the whole model", architecture_and_recipe: "the model and how it is trained", custom: "the roles the skill lists"},
      settings_by: {agent: "an agent", sampler: "a sampler in code", tpe: "a Bayesian estimator in code"},
      level: {minimal: "writers only", standard: "writers and an analyst", full: "writers, an analyst and re-checks of the leader"}
    };
    function plan(s) { return data.plans[[s.run, s.skill, s.level, s.budget].join("|")]; }
    function facts(p) {
      var total = Object.keys(p.calls).reduce(function (a, k) { return a + p.calls[k]; }, 0);
      var writes = (p.calls.writer || 0) > 0;
      var stop = p.stop === "none" ? "none" : (p.stop === "ladder" ? "a ladder: " : "new designs screened: ") +
        p.rungs.map(function (r) { return "at " + pct(r[0]) + " keep " + pct(r[1]); }).join(", ");
      return [
        ["Parents are chosen by", words.strategy[p.strategy] + (p.islands > 1 ? ", on " + p.islands + " islands" : "") + (p.second ? "; second figure: " + p.second : "")],
        ["What may change", words.space[p.space] || p.space],
        ["Designs are written by", writes ? "an agent" : "code alone"],
        ["Settings moves are made by", words.settings_by[p.settings_by]],
        ["Early stopping", stop],
        ["Designs the budget covers", String(p.designs)],
        ["Agent roles", words.level[p.level] + (p.strategist !== "off" ? "; a strategist (" + p.strategist + ")" : "") + (p.coordinator === "agent" ? "; an agent picks each slot" : "")],
        ["Agent calls, about", total ? Object.keys(p.calls).map(function (k) { return k + " " + p.calls[k]; }).join(" · ") + "  (" + total + " in all)" : "none: this search calls no agent"]
      ];
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
    function render() {
      var p = plan(state), base = plan({run: "explore_then_exploit", skill: "", level: "", budget: state.budget});
      root.innerHTML = "";
      var skillPick = el("select", {"class": "evo-select", "aria-label": "Goal"});
      data.skills.forEach(function (name) {
        var o = el("option", {value: name, text: name ? name + ": " + data.about.skills[name] : "no skill (the plain search)"});
        if (name === state.skill) { o.selected = true; }
        skillPick.appendChild(o);
      });
      skillPick.addEventListener("change", function () { state.skill = skillPick.value; render(); });
      root.appendChild(el("div", {"class": "evo-controls"}, [
        el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: "Goal (skill)"}), skillPick]),
        chips("How to search (run type)", data.run_types.map(function (r) { return [r, r, data.about.run_types[r]]; }), state.run, function (v) { state.run = v; render(); }),
        chips("How much the agents decide", data.levels.map(function (l) { return [l, l || "unset", data.about.levels[l]]; }), state.level, function (v) { state.level = v; render(); }),
        chips("Budget", data.budgets.map(function (b) { return [b, b + " evaluations"]; }), state.budget, function (v) { state.budget = v; render(); })
      ]));
      var legend = el("div", {"class": "evo-legend"}, MODES.map(function (m) {
        return el("span", {}, [el("i", {"class": "evo-swatch evo-bg-" + m[0]}), document.createTextNode(m[1])]);
      }));
      var list = el("dl", {"class": "evo-facts"});
      var now = facts(p), was = facts(base), changed = [];
      now.forEach(function (row, i) {
        var differs = row[1] !== was[i][1];
        if (differs) { changed.push(row[0].toLowerCase() + ": " + was[i][1] + "  →  " + row[1]); }
        list.appendChild(el("dt", {text: row[0]}));
        list.appendChild(el("dd", {"class": differs ? "evo-changed" : "", text: row[1]}));
      });
      var sharesDiffer = JSON.stringify(p.phases) !== JSON.stringify(base.phases);
      var diff = el("div", {"class": "evo-diff"}, [el("strong", {text: "Compared with the plain default at this budget: "})]);
      if (!changed.length && !sharesDiffer) { diff.appendChild(document.createTextNode("nothing differs. This is the default.")); }
      else {
        var ul = el("ul");
        if (sharesDiffer) { ul.appendChild(el("li", {text: "the shares of new designs, crossover and local moves (the bar above)"})); }
        changed.forEach(function (c) { ul.appendChild(el("li", {text: c})); });
        diff.appendChild(ul);
      }
      var brief = "run:\n  type: " + state.run + (state.skill ? "\n  skill: " + state.skill : "") +
        (state.level ? "\nharness:\n  autonomy: " + state.level : "") + "\nbudget:\n  evaluations: " + state.budget;
      var out = el("div", {"class": "evo-out"}, [
        el("h4", {text: "How the budget is shared"}), legend, bar(p, state.budget),
        el("h4", {text: "What this search does"}), list, diff,
        p.warn.length ? el("div", {"class": "evo-warn"}, [el("strong", {text: "The plan would warn: "}), el("ul", {}, p.warn.map(function (i) { return el("li", {text: data.warnings[i]}); }))]) : null,
        el("h4", {text: "In your brief"}), el("pre", {"class": "evo-brief"}, [el("code", {text: brief})])
      ]);
      root.appendChild(out);
    }
    render();
  }

  /* ---------------------------------------------------------------- the search playground */
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
    function landscape(seed) {
      var r = rng(seed * 101 + 3);
      var peaks = [[0.22 + 0.04 * (r() - 0.5), 0.55, 0.11], [0.52 + 0.06 * (r() - 0.5), 0.72, 0.05], [0.80 + 0.08 * (r() - 0.5), 1.0, 0.03]];
      return function (x) { return peaks.reduce(function (m, p) { return Math.max(m, p[1] * Math.exp(-Math.pow((x - p[0]) / p[2], 2) / 2)); }, 0.05); };
    }
    function reset() {
      stop();
      var f = landscape(state.seed);
      sim = {f: f, r: rng(state.seed * 7919 + 11), designs: [], counts: {new: 0, cross: 0, local: 0}, lineages: 0, best: [], last: null};
      add(0.2, "new", null);        // the baseline: on the nearest, lowest hill
      draw();
    }
    function add(x, mode, parents, lineage) {
      x = Math.min(1, Math.max(0, x));
      var d = {x: x, truth: sim.f(x), mode: mode, parents: parents || [], lineage: lineage === undefined ? sim.lineages++ : lineage, n: sim.designs.length};
      d.score = d.truth + state.noise * sim.r.normal();
      sim.designs.push(d);
      if (sim.designs.length > 1) { sim.counts[mode] += 1; }
      var lead = sim.designs.reduce(function (a, b) { return b.score > a.score ? b : a; });
      sim.best.push(lead.truth);
      sim.last = d;
    }
    function pickParent() {
      var all = sim.designs, r = sim.r;
      if (state.strategy === "greedy") { return all.reduce(function (a, b) { return b.score > a.score ? b : a; }); }
      if (state.strategy === "tournament") {
        var recent = all.slice(-12), drawn = [];
        for (var i = 0; i < 3; i++) { drawn.push(recent[Math.floor(r() * recent.length)]); }
        return drawn.reduce(function (a, b) { return b.score > a.score ? b : a; });
      }
      var groups = {};
      all.forEach(function (d) { var key = state.strategy === "archive" ? Math.min(9, Math.floor(d.x * 10)) : d.lineage; (groups[key] = groups[key] || []).push(d); });
      var elites = Object.keys(groups).map(function (k) {
        var members = groups[k];
        return {elite: members.reduce(function (a, b) { return b.score > a.score ? b : a; }), size: members.length};
      }).sort(function (a, b) { return b.elite.score - a.elite.score; });
      if (state.strategy === "lineage") { elites = elites.slice(0, 4); }      // the active families
      var weights = elites.map(function (e, i) { return (elites.length - i) / (1 + e.size); }), sum = weights.reduce(function (a, b) { return a + b; }, 0), t = r() * sum;
      for (var j = 0; j < elites.length; j++) { t -= weights[j]; if (t <= 0) { return elites[j].elite; } }
      return elites[0].elite;
    }
    function step() {
      if (sim.designs.length > BUDGET) { stop(); return; }
      var done = sim.designs.length - 1, cross = state.fresh < 0.9 && sim.lineages >= 2 ? 0.1 : 0;
      var shares = {new: state.fresh, cross: cross, local: Math.max(0, 1 - state.fresh - cross)};
      var mode = ["new", "cross", "local"].reduce(function (a, m) { return shares[m] * (done + 1) - sim.counts[m] > shares[a] * (done + 1) - sim.counts[a] ? m : a; }, "local");
      if (shares[mode] <= 0) { mode = "local"; }
      if (mode === "new") { add(sim.r(), "new", null); }
      else if (mode === "cross") {
        var a = pickParent(), others = sim.designs.filter(function (d) { return d.lineage !== a.lineage; });
        var b = others.reduce(function (p, q) { return q.score > p.score ? q : p; }, others[0]), mix = 0.3 + 0.4 * sim.r();
        add(a.x * mix + b.x * (1 - mix), "cross", [a, b]);
      } else { var p = pickParent(); add(p.x + 0.035 * sim.r.normal(), "local", [p], p.lineage); }
      draw();
    }
    function stop() { if (state.timer) { clearInterval(state.timer); state.timer = null; } }
    function play() { if (sim.designs.length > BUDGET) { reset(); } stop(); state.timer = setInterval(step, 140); draw(); }
    function draw() {
      root.innerHTML = "";
      var X = function (x) { return L + (W - L - R) * x; }, Y = function (v) { return T + (H - T - B) * (1 - Math.min(1.08, Math.max(-0.05, v)) / 1.08); };
      var fresh = el("input", {type: "range", min: 0, max: 80, step: 5, value: Math.round(state.fresh * 100), "aria-label": "Share of new designs"});
      fresh.addEventListener("input", function () { state.fresh = fresh.value / 100; reset(); });
      var noise = el("input", {type: "range", min: 0, max: 15, step: 1, value: Math.round(state.noise * 100), "aria-label": "Noise in the score"});
      noise.addEventListener("input", function () { state.noise = noise.value / 100; reset(); });
      var buttons = el("div", {"class": "evo-chips"}, [["Run", play], ["Step", function () { stop(); step(); }], ["Start over", reset], ["Another landscape", function () { state.seed += 1; reset(); }]].map(function (b) {
        var node = el("button", {type: "button", "class": "evo-chip" + (b[0] === "Run" ? " go" : ""), text: b[0] === "Run" && state.timer ? "Running…" : b[0]});
        node.addEventListener("click", b[1]);
        return node;
      }));
      root.appendChild(el("div", {"class": "evo-controls"}, [
        chips("Parents are chosen by", [["greedy", "greedy", "always the current best"], ["tournament", "tournament", "the best of three recent designs"],
                                        ["lineage", "lineage", "the best of the leading families, the less used favoured"], ["archive", "archive", "the best of each region, the less used favoured"]],
              state.strategy, function (v) { state.strategy = v; reset(); }),
        el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: "New designs: " + pct(state.fresh) + " of the budget"}), fresh]),
        el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: "Noise in a score: ±" + state.noise.toFixed(2)}), noise]),
        el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: ""}), buttons])
      ]));
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
      var lead = sim.designs.reduce(function (a, b) { return b.score > a.score ? b : a; });
      if (sim.last && sim.last.parents.length) {
        sim.last.parents.forEach(function (p) { svg.appendChild(el("line", {x1: X(p.x), y1: Y(p.score), x2: X(sim.last.x), y2: Y(sim.last.score), "class": "evo-link"})); });
      }
      sim.designs.forEach(function (d) {
        var dot = el("circle", {cx: X(d.x), cy: Y(d.score), r: d === sim.last ? 6 : 4.5, "class": "evo-dot evo-fill-" + (d.n === 0 ? "base" : d.mode) + (d === sim.last ? " now" : "")});
        dot.appendChild(el("title", {text: "Design " + (d.n + 1) + (d.n === 0 ? ", the baseline" : ", " + {new: "a new design", cross: "a crossover", local: "a local move"}[d.mode]) + ": scored " + d.score.toFixed(2) + " (true quality " + d.truth.toFixed(2) + ")"}));
        svg.appendChild(dot);
      });
      svg.appendChild(el("circle", {cx: X(lead.x), cy: Y(lead.score), r: 9, "class": "evo-ring"}));
      var found = lead.truth > 0.9, n = sim.designs.length - 1;
      var legend = el("div", {"class": "evo-legend"}, [["base", "the baseline"]].concat(MODES).map(function (m) {
        return el("span", {}, [el("i", {"class": "evo-swatch evo-bg-" + m[0]}), document.createTextNode(m[1])]);
      }).concat([el("span", {}, [el("i", {"class": "evo-swatch evo-ringed"}), document.createTextNode("the leader")])]));
      var read = el("p", {"class": "evo-read"});
      read.innerHTML = "<strong>" + n + " of " + BUDGET + "</strong> evaluations used. The leader's true quality is <strong>" + lead.truth.toFixed(2) +
        "</strong> of a possible 1.00" + (n >= BUDGET ? (found ? ": it found the highest peak." : ": it settled on a lower peak.") : ".") +
        (state.noise >= 0.08 && Math.abs(lead.score - lead.truth) > 0.08 ? " Its score (" + lead.score.toFixed(2) + ") flatters it: that is noise." : "");
      root.appendChild(legend);
      root.appendChild(svg);
      root.appendChild(read);
    }
    reset();
  }

  /* ---------------------------------------------------------------- the ladder */
  function ladder(root) {
    var W = 720, H = 250, L = 44, R = 12, T = 12, B = 30, N = 24;
    var state = {at: 0.1, keep: 0.5, second: true};
    var r = rng(42), runs = [];
    for (var i = 0; i < N; i++) {      // each design: where it ends up, and how fast it gets there
      var slow = i === 5 || i === 17;  // two designs start slowly and end among the best
      runs.push({final: slow ? 0.9 + 0.04 * r() : 0.45 + 0.42 * r(), rate: slow ? 0.55 : 0.08 + 0.14 * r(), n: i});
    }
    function at(run, t) { return run.final * (1 - Math.exp(-t / run.rate)); }
    function draw() {
      root.innerHTML = "";
      var rungs = [[state.at, state.keep]].concat(state.second ? [[Math.min(0.9, state.at * 3), state.keep]] : []);
      var alive = runs.slice(), stopped = {}, cost = 0;
      rungs.forEach(function (rung) {
        var ranked = alive.slice().sort(function (a, b) { return at(b, rung[0]) - at(a, rung[0]); });
        var kept = ranked.slice(0, Math.max(1, Math.round(ranked.length * rung[1])));
        ranked.slice(kept.length).forEach(function (run) { stopped[run.n] = rung[0]; cost += rung[0]; });
        alive = kept;
      });
      cost += alive.length;
      var best = runs.reduce(function (a, b) { return b.final > a.final ? b : a; });
      var bestKept = alive.reduce(function (a, b) { return b.final > a.final ? b : a; });
      var X = function (t) { return L + (W - L - R) * t; }, Y = function (v) { return T + (H - T - B) * (1 - v); };
      var a = el("input", {type: "range", min: 5, max: 30, step: 5, value: Math.round(state.at * 100), "aria-label": "Where the first rung is"});
      a.addEventListener("input", function () { state.at = a.value / 100; draw(); });
      var k = el("input", {type: "range", min: 25, max: 75, step: 5, value: Math.round(state.keep * 100), "aria-label": "Share kept at each rung"});
      k.addEventListener("input", function () { state.keep = k.value / 100; draw(); });
      root.appendChild(el("div", {"class": "evo-controls"}, [
        el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: "First rung at " + pct(state.at) + " of a run"}), a]),
        el("div", {"class": "evo-row"}, [el("span", {"class": "evo-label", text: "Kept at each rung: the best " + pct(state.keep)}), k]),
        chips("Rungs", [[false, "one"], [true, "two (the second at " + pct(Math.min(0.9, state.at * 3)) + ")"]], state.second, function (v) { state.second = v; draw(); })
      ]));
      var svg = el("svg", {viewBox: "0 0 " + W + " " + H, role: "img", "class": "evo-plot", "aria-label": "The learning curves of 24 designs, and where the weaker ones are stopped"});
      [0, 0.25, 0.5, 0.75, 1].forEach(function (v) {
        svg.appendChild(el("line", {x1: L, y1: Y(v), x2: W - R, y2: Y(v), "class": "evo-grid"}));
        svg.appendChild(el("text", {x: L - 6, y: Y(v) + 4, "text-anchor": "end", "class": "evo-small", text: v.toFixed(2)}));
      });
      rungs.forEach(function (rung) {
        svg.appendChild(el("line", {x1: X(rung[0]), y1: T, x2: X(rung[0]), y2: H - B, "class": "evo-link"}));
        svg.appendChild(el("text", {x: X(rung[0]) + 4, y: T + 10, "class": "evo-small", text: "rung at " + pct(rung[0])}));
      });
      runs.forEach(function (run) {
        var end = stopped[run.n] === undefined ? 1 : stopped[run.n], path = "";
        for (var j = 0; j <= 60; j++) { var t = end * j / 60; path += (j ? "L" : "M") + X(t).toFixed(1) + " " + Y(at(run, t)).toFixed(1); }
        var line = el("path", {d: path, "class": "evo-run" + (end < 1 ? " cut" : "") + (run === best ? " best" : "")});
        line.appendChild(el("title", {text: "Design " + (run.n + 1) + (end < 1 ? ": stopped at " + pct(end) + " of its run" : ": trained to the end") + "; would finish at " + run.final.toFixed(2)}));
        svg.appendChild(line);
        if (end < 1) { svg.appendChild(el("circle", {cx: X(end), cy: Y(at(run, end)), r: 3.5, "class": "evo-stop"})); }
      });
      svg.appendChild(el("text", {x: (L + W - R) / 2, y: H - 6, "text-anchor": "middle", "class": "evo-small", text: "share of a full training run"}));
      svg.appendChild(el("text", {transform: "translate(12 " + ((T + H - B) / 2) + ") rotate(-90)", "text-anchor": "middle", "class": "evo-small", text: "score so far"}));
      var read = el("p", {"class": "evo-read"});
      var lost = bestKept !== best;
      read.innerHTML = "These " + N + " designs cost <strong>" + cost.toFixed(1) + "</strong> full runs instead of " + N + ": a budget of 100 evaluations would cover about <strong>" +
        Math.round(100 * N / cost) + "</strong> designs. " + alive.length + " are trained to the end. " +
        (lost ? "<strong>The design that would have ended best was stopped</strong> (the thick line): it started slowly. The best one kept ends at " + bestKept.final.toFixed(2) + ", not " + best.final.toFixed(2) + "."
              : "The design that ends best (the thick line) was kept.");
      root.appendChild(svg);
      root.appendChild(read);
    }
    draw();
  }

  function start() {
    var rungs = document.getElementById("evo-ladder");
    if (rungs) { ladder(rungs); }
    var play = document.getElementById("evo-playground");
    if (play) { playground(play); }
    var plan = document.getElementById("evo-plan-explorer");
    if (plan) {
      fetch(new URL(plan.getAttribute("data-src"), document.baseURI)).then(function (r) { return r.json(); })
        .then(function (data) { planExplorer(plan, data); })
        .catch(function () { plan.textContent = "The plan explorer could not load its data. `evoloop plan` prints the same for your own brief."; });
    }
  }
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", start); } else { start(); }
})();
