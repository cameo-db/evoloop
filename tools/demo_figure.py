"""Draw the figure of the CPU demo used on the documentation's front page and in the README.

    python tools/demo_figure.py demo/runs/first docs/assets

Reads the run's own records (runs.jsonl) and writes: demo-light.svg and demo-dark.svg (for the README),
demo-inline.html (the same chart with theme colours taken from the page and a note on every point, for the
docs), and demo-table.md (the same numbers as a table). Nothing here is drawn by hand: run the demo and this
script again and the figure follows."""
import json
import math
import os
import sys

LIGHT = {"surface": "#fcfcfb", "ink": "#0b0b0b", "soft": "#52514e", "grid": "#e6e5e1", "series": "#2a78d6", "dot": "#8f8e88"}
DARK = {"surface": "#1a1a19", "ink": "#f0efec", "soft": "#c3c2b7", "grid": "#33332f", "series": "#3987e5", "dot": "#8f8e88"}
VARS = {k: "var(--evo-%s)" % k for k in LIGHT}
W, H, LEFT, RIGHT, TOP, BOTTOM = 640, 320, 64, 132, 18, 46


def load(run_dir):
    runs = {}
    with open(os.path.join(run_dir, "runs.jsonl"), encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record["id"] in runs:
                for key, value in record.items():
                    if isinstance(value, dict) and isinstance(runs[record["id"]].get(key), dict):
                        runs[record["id"]][key].update(value)
                    else:
                        runs[record["id"]][key] = value
            else:
                runs[record["id"]] = record
    rows = []
    for run in sorted(runs.values(), key=lambda r: int(r["id"][1:])):
        perf = run.get("performance") or {}
        if perf.get("status") != "done" or not isinstance(perf.get("score"), (int, float)):
            continue
        rows.append({"run": run["id"], "design": run.get("candidate"), "score": float(perf["score"]),
                     "baseline": run.get("purpose") == "baseline", "move": (run.get("history") or {}).get("move"),
                     "recheck": run.get("purpose") == "recheck"})
    return rows, len(runs)


def nice(value):
    return "%.4g" % value


def draw(rows, colours, notes):
    scores = [r["score"] for r in rows]
    low, high = math.floor(math.log10(min(scores))), math.ceil(math.log10(max(scores)))
    n = len(rows)
    x = lambda i: LEFT + (W - LEFT - RIGHT) * (i / max(1, n - 1))                                 # noqa: E731
    y = lambda v: TOP + (H - TOP - BOTTOM) * (1 - (math.log10(v) - low) / (high - low))           # noqa: E731
    c = colours
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" '
           'aria-label="Validation score of each design in the CPU demo, and the best so far, over %d scored runs">' % (W, H, n),
           '<rect width="%d" height="%d" rx="8" fill="%s"/>' % (W, H, c["surface"])]
    font = 'font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif"'
    for power in range(low, high + 1):
        yy = y(10 ** power)
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>' % (LEFT, yy, W - RIGHT, yy, c["grid"]))
        out.append('<text x="%d" y="%.1f" text-anchor="end" font-size="12" %s fill="%s">%s</text>' % (
            LEFT - 8, yy + 4, font, c["soft"], ("%g" % (10 ** power))))
    for i in range(0, n, max(1, n // 6)):
        out.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="12" %s fill="%s">%d</text>' % (
            x(i), H - BOTTOM + 18, font, c["soft"], i + 1))
    out.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="12" %s fill="%s">Scored run</text>' % (
        (LEFT + W - RIGHT) / 2, H - 8, font, c["soft"]))
    out.append('<text transform="translate(16 %.1f) rotate(-90)" text-anchor="middle" font-size="12" %s fill="%s">'
               'Validation score (log scale; lower is better)</text>' % ((TOP + H - BOTTOM) / 2, font, c["soft"]))
    base = next((r["score"] for r in rows if r["baseline"]), rows[0]["score"])
    out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.5" stroke-dasharray="5 4"/>' % (
        LEFT, y(base), W - RIGHT, y(base), c["soft"]))
    out.append('<text x="%d" y="%.1f" font-size="12" %s fill="%s">Baseline</text>' % (W - RIGHT + 10, y(base) - 2, font, c["soft"]))
    out.append('<text x="%d" y="%.1f" font-size="15" font-weight="600" %s fill="%s">%s</text>' % (
        W - RIGHT + 10, y(base) + 15, font, c["ink"], nice(base)))
    best, path = None, []
    for i, row in enumerate(rows):                 # the best score so far: a step that only ever goes down
        if best is None or row["score"] < best:
            if path:
                path.append("H%.1f" % x(i))
            best = row["score"]
            path.append("%s%.1f %.1f" % ("V" if path else "M", x(i), y(best)) if not path else "V%.1f" % y(best))
    path.append("H%.1f" % x(n - 1))
    out.append('<path d="%s" fill="none" stroke="%s" stroke-width="2" stroke-linejoin="round"/>' % (" ".join(path), c["series"]))
    for i, row in enumerate(rows):
        note = "%s (%s): %s%s" % (row["design"], row["run"], nice(row["score"]), ", a re-check of the leader on a new seed" if row["recheck"] else
                                  ", the baseline" if row["baseline"] else (", %s" % row["move"] if row["move"] else ""))
        out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s" stroke="%s" stroke-width="2">%s</circle>' % (
            x(i), y(row["score"]), c["dot"], c["surface"], "<title>%s</title>" % note if notes else ""))
        if notes:      # a larger target than the mark, for the pointer
            out.append('<circle cx="%.1f" cy="%.1f" r="10" fill="transparent"><title>%s</title></circle>' % (x(i), y(row["score"]), note))
    out.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" stroke="%s" stroke-width="2"/>' % (x(n - 1), y(best), c["series"], c["surface"]))
    means = {}
    for row in rows:      # a design fitted more than once is judged by the mean of its fits, as the leaderboard does
        means.setdefault(row["design"], []).append(row["score"])
    chosen = min(sum(v) / len(v) for v in means.values())
    out.append('<text x="%d" y="%.1f" font-size="12" %s fill="%s">Selected</text>' % (W - RIGHT + 10, y(best) - 8, font, c["soft"]))
    out.append('<text x="%d" y="%.1f" font-size="15" font-weight="600" %s fill="%s">%s</text>' % (
        W - RIGHT + 10, y(best) + 9, font, c["ink"], nice(chosen)))
    lx = LEFT + 10
    out.append('<circle cx="%d" cy="%d" r="4" fill="%s" stroke="%s" stroke-width="2"/>' % (lx, TOP + 10, c["dot"], c["surface"]))
    out.append('<text x="%d" y="%d" font-size="12" %s fill="%s">each design</text>' % (lx + 10, TOP + 14, font, c["soft"]))
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (lx + 92, TOP + 10, lx + 112, TOP + 10, c["series"]))
    out.append('<text x="%d" y="%d" font-size="12" %s fill="%s">best so far</text>' % (lx + 118, TOP + 14, font, c["soft"]))
    out.append("</svg>")
    return "\n".join(out), base, chosen


def main(run_dir, out_dir):
    rows, total = load(run_dir)
    os.makedirs(out_dir, exist_ok=True)
    for name, colours in (("light", LIGHT), ("dark", DARK)):
        svg, base, best = draw(rows, colours, notes=False)
        with open(os.path.join(out_dir, "demo-%s.svg" % name), "w", encoding="utf-8") as handle:
            handle.write(svg + "\n")
    inline, base, best = draw(rows, VARS, notes=True)
    with open(os.path.join(out_dir, "demo-inline.html"), "w", encoding="utf-8") as handle:
        handle.write('<div class="evo-chart">\n%s\n</div>\n' % inline)
    with open(os.path.join(out_dir, "demo-table.md"), "w", encoding="utf-8") as handle:
        handle.write("| Scored run | Design | Move | Validation score |\n|---|---|---|---|\n")
        for i, row in enumerate(rows):
            handle.write("| %d | %s | %s | %s |\n" % (i + 1, row["design"], "baseline" if row["baseline"] else ("re-check on a new seed" if row["recheck"] else row["move"]), nice(row["score"])))
    print(json.dumps({"scored": len(rows), "runs": total, "baseline": base, "best": best,
                      "ratio": base / best}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
