"""Draw the figure of the built-in example used on the documentation's front page and in the README.

    python tools/demo_figure.py demo/runs/first docs/assets

Reads the run's own records (run.json for the direction of the score, runs.jsonl for the designs) and writes
demo-light.svg and demo-dark.svg (for the README), demo-inline.html (the same chart, taking its colours from
the page and with a note on every point, for the docs) and demo-table.md (the same numbers as a table).
Nothing here is drawn by hand: run the example and this script again and the figure follows."""
import json
import math
import os
import sys

LIGHT = {"surface": "#fcfcfb", "ink": "#0b0b0b", "soft": "#52514e", "grid": "#e6e5e1", "series": "#2a78d6", "dot": "#8f8e88"}
DARK = {"surface": "#1a1a19", "ink": "#f0efec", "soft": "#c3c2b7", "grid": "#33332f", "series": "#3987e5", "dot": "#8f8e88"}
VARS = {k: "var(--evo-%s)" % k for k in LIGHT}
W, H, LEFT, RIGHT, TOP, BOTTOM = 640, 330, 62, 128, 20, 46
FONT = 'font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"'
MOVES = {"new_approach": "a new design", "structural_change": "an edit", "settings_move": "a settings move",
         "ablation": "an ablation", "hybrid": "a crossover", "graft": "a crossover", "block_swap": "a crossover"}


def load(run_dir):
    runs = {}
    with open(os.path.join(run_dir, "runs.jsonl"), encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            known = runs.setdefault(record["id"], {})
            for key, value in record.items():
                if isinstance(value, dict) and isinstance(known.get(key), dict):
                    known[key].update(value)
                else:
                    known[key] = value
    with open(os.path.join(run_dir, "run.json"), encoding="utf-8") as handle:
        brief = json.load(handle)["brief"]
    rows = []
    for run in sorted(runs.values(), key=lambda r: int(r["id"][1:])):
        perf = run.get("performance") or {}
        if perf.get("status") != "done" or not isinstance(perf.get("score"), (int, float)):
            continue
        purpose = run.get("purpose")
        rows.append({"run": run["id"], "design": run.get("candidate"), "score": float(perf["score"]),
                     "baseline": purpose == "baseline", "recheck": purpose == "recheck",
                     "move": "the baseline" if purpose == "baseline" else ("a re-check on a new seed" if purpose == "recheck"
                                                                         else MOVES.get((run.get("history") or {}).get("move"), "a design"))})
    return rows, (brief.get("objective") or {}).get("direction") != "minimize", (brief.get("objective") or {}).get("metric") or "score"


def nice(value):
    return "%.4g" % value


def draw(rows, higher, metric, colours, notes):
    c, n = colours, len(rows)
    scores = [r["score"] for r in rows]
    logscale = (not higher) and min(scores) > 0 and max(scores) / min(scores) > 100
    if logscale:
        low, high = math.floor(math.log10(min(scores))), math.ceil(math.log10(max(scores)))
        place = lambda v: (math.log10(v) - low) / (high - low)                                    # noqa: E731
        ticks = [10 ** p for p in range(low, high + 1)]
    else:
        step = 0.1 if max(scores) - min(scores) > 0.25 else 0.05
        low, high = math.floor(min(scores) / step) * step, math.ceil(max(scores) / step) * step
        place = lambda v: (v - low) / (high - low)                                                # noqa: E731
        ticks = [low + i * step for i in range(int(round((high - low) / step)) + 1)]
    x = lambda i: LEFT + (W - LEFT - RIGHT) * (i / max(1, n - 1))                                 # noqa: E731
    y = lambda v: TOP + (H - TOP - BOTTOM) * (1 - place(v))                                       # noqa: E731
    better = (lambda a, b: a > b) if higher else (lambda a, b: a < b)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" aria-label="The %s of each model '
           'in the built-in example, and the best so far, over %d models">' % (W, H, metric, n),
           '<rect width="%d" height="%d" rx="8" fill="%s"/>' % (W, H, c["surface"])]
    for tick in ticks:
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>' % (LEFT, y(tick), W - RIGHT, y(tick), c["grid"]))
        out.append('<text x="%d" y="%.1f" text-anchor="end" font-size="12" %s fill="%s">%s</text>' % (
            LEFT - 8, y(tick) + 4, FONT, c["soft"], "%g" % round(tick, 6)))
    for i in list(range(0, n, max(1, n // 7))):
        out.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="12" %s fill="%s">%d</text>' % (
            x(i), H - BOTTOM + 18, FONT, c["soft"], i + 1))
    out.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="12" %s fill="%s">Model iteration</text>' % (
        (LEFT + W - RIGHT) / 2, H - 8, FONT, c["soft"]))
    out.append('<text transform="translate(16 %.1f) rotate(-90)" text-anchor="middle" font-size="12" %s fill="%s">%s%s (%s is better)</text>' % (
        (TOP + H - BOTTOM) / 2, FONT, c["soft"], metric[:1].upper() + metric[1:], ", log scale" if logscale else "",
        "higher" if higher else "lower"))
    base = next((r["score"] for r in rows if r["baseline"]), rows[0]["score"])
    out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.5" stroke-dasharray="5 4"/>' % (
        LEFT, y(base), W - RIGHT, y(base), c["soft"]))
    best, path = None, []
    for i, row in enumerate(rows):                 # the best score so far: a step that only ever moves one way
        if best is None:
            best = row["score"]
            path.append("M%.1f %.1f" % (x(i), y(best)))
        elif better(row["score"], best):
            best = row["score"]
            path.append("H%.1f V%.1f" % (x(i), y(best)))
    path.append("H%.1f" % x(n - 1))
    out.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % (" ".join(path), c["series"]))
    for i, row in enumerate(rows):
        note = "Model %d (%s): %s, %s" % (i + 1, row["design"], nice(row["score"]), row["move"])
        out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s" stroke="%s" stroke-width="2">%s</circle>' % (
            x(i), y(row["score"]), c["dot"], c["surface"], "<title>%s</title>" % note if notes else ""))
        if notes:      # a larger target than the mark, for the pointer
            out.append('<circle cx="%.1f" cy="%.1f" r="10" fill="transparent"><title>%s</title></circle>' % (x(i), y(row["score"]), note))
    means = {}
    for row in rows:      # a design fitted more than once is judged by the mean of its fits, as the leaderboard does
        means.setdefault(row["design"], []).append(row["score"])
    pick = max if higher else min
    chosen = pick(sum(v) / len(v) for v in means.values())
    out.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" stroke="%s" stroke-width="2"/>' % (x(n - 1), y(best), c["series"], c["surface"]))
    for label, value, at, bold in (("Baseline", base, y(base), False), ("Selected", chosen, y(best), True)):
        shift = 16 if (at < TOP + 30) else -8
        out.append('<text x="%d" y="%.1f" font-size="12" %s fill="%s">%s</text>' % (W - RIGHT + 12, at + shift, FONT, c["soft"], label))
        out.append('<text x="%d" y="%.1f" font-size="15" font-weight="600" %s fill="%s">%s</text>' % (
            W - RIGHT + 12, at + shift + 17, FONT, c["ink"], nice(value)))
    lx, ly = (W - RIGHT - 196, H - BOTTOM - 34) if higher else (LEFT + 12, TOP + 12)      # the key sits where the points are not
    out.append('<circle cx="%d" cy="%d" r="4" fill="%s" stroke="%s" stroke-width="2"/>' % (lx, ly, c["dot"], c["surface"]))
    out.append('<text x="%d" y="%d" font-size="12" %s fill="%s">each model</text>' % (lx + 10, ly + 4, FONT, c["soft"]))
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (lx + 86, ly, lx + 106, ly, c["series"]))
    out.append('<text x="%d" y="%d" font-size="12" %s fill="%s">best so far</text>' % (lx + 112, ly + 4, FONT, c["soft"]))
    out.append("</svg>")
    return "\n".join(out), base, chosen


def main(run_dir, out_dir):
    rows, higher, metric = load(run_dir)
    os.makedirs(out_dir, exist_ok=True)
    for name, colours in (("light", LIGHT), ("dark", DARK)):
        svg, base, chosen = draw(rows, higher, metric, colours, notes=False)
        with open(os.path.join(out_dir, "demo-%s.svg" % name), "w", encoding="utf-8") as handle:
            handle.write(svg + "\n")
    inline, base, chosen = draw(rows, higher, metric, VARS, notes=True)
    with open(os.path.join(out_dir, "demo-inline.html"), "w", encoding="utf-8") as handle:
        handle.write('<div class="evo-chart">\n%s\n</div>\n' % inline)
    with open(os.path.join(out_dir, "demo-table.md"), "w", encoding="utf-8") as handle:
        handle.write("| Model | Design | Made by | %s |\n|---|---|---|---|\n" % (metric[:1].upper() + metric[1:]))
        for i, row in enumerate(rows):
            handle.write("| %d | %s | %s | %s |\n" % (i + 1, row["design"], row["move"], nice(row["score"])))
    print(json.dumps({"models": len(rows), "baseline": base, "selected": chosen, "higher_is_better": higher}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
