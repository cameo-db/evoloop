"""The brief as a form in a browser: one self-contained HTML file, no server.

`evoloop form DIR` writes it. Open it in any browser (copy it to your own machine if the search folder is
on a server), answer by section, and the last step gives a small answers file; `evoloop brief DIR --import
FILE` reads it. Nothing is sent anywhere: the page has no network access to anything, and a draft is kept
only in that browser."""
from __future__ import annotations

import json
from typing import Any, Dict

from . import interview

PAGE = r"""<title>evoloop setup</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Layout: a rail of sections with their progress beside one section of questions at a time; a bar at the
   foot says where you are and moves you on. On a phone the rail becomes a strip above the questions. */
:root {
  --bg: #f4f7f7; --surface: #ffffff; --ink: #14201f; --muted: #556664; --line: #d5dedc;
  --accent: #0b6b66; --accent-ink: #ffffff; --soft: #e2efed; --warn: #a5471a;
  --seg-new: #0b6b66; --seg-cross: #c28a1c; --seg-local: #7d8f8c;
  --sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0e1615; --surface: #162120; --ink: #e4edeb; --muted: #94a7a4; --line: #2a3b38;
  --accent: #55c9bf; --accent-ink: #06201e; --soft: #1d302e; --warn: #f0a070;
  --seg-new: #55c9bf; --seg-cross: #e0b352; --seg-local: #6f8581; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0e1615; --surface: #162120; --ink: #e4edeb; --muted: #94a7a4; --line: #2a3b38;
  --accent: #55c9bf; --accent-ink: #06201e; --soft: #1d302e; --warn: #f0a070;
  --seg-new: #55c9bf; --seg-cross: #e0b352; --seg-local: #6f8581; color-scheme: dark }
* { box-sizing: border-box }
html, body { height: 100% }
body { background: var(--bg); color: var(--ink); font: 15px/1.5 var(--sans); margin: 0 }
.wrap { max-width: 980px; margin: 0 auto; padding-block: 20px 96px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)) }
header h1 { font-size: 20px; margin: 0; letter-spacing: -0.01em }
header p { margin: 4px 0 0; color: var(--muted); max-width: 65ch }
.grid { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 28px; margin-top: 22px }
nav ol { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px }
nav button { width: 100%; display: flex; justify-content: space-between; gap: 8px; align-items: baseline; text-align: left;
  background: none; border: 0; border-left: 3px solid transparent; padding: 7px 10px; color: var(--muted); font: inherit; cursor: pointer }
nav button[aria-current="step"] { color: var(--ink); border-left-color: var(--accent); background: var(--soft); font-weight: 600 }
nav button .count { font: 12px var(--mono); font-variant-numeric: tabular-nums }
nav button.full .count { color: var(--accent) }
main { min-width: 0; display: flex; flex-direction: column; gap: 18px }
h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin: 0; font-weight: 600 }
.q { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 16px 18px; display: flex; flex-direction: column; gap: 10px }
.q.missing { border-color: var(--warn) }
.q .num { font: 12px var(--mono); color: var(--muted); font-variant-numeric: tabular-nums }
.q h3 { margin: 0; font-size: 16px; text-wrap: balance }
.q .why { margin: 0; color: var(--muted); font-size: 13px; max-width: 65ch }
.opts { display: flex; flex-direction: column; gap: 6px }
.opt { display: grid; grid-template-columns: 18px minmax(0, 1fr); gap: 10px; align-items: start; padding: 8px 10px; border: 1px solid var(--line);
  border-radius: 5px; cursor: pointer }
.opt:has(input:checked) { border-color: var(--accent); background: var(--soft) }
.opt input { margin: 3px 0 0; accent-color: var(--accent) }
.opt b { font-weight: 600; font-family: var(--mono); font-size: 13.5px }
.opt span.d { display: block; color: var(--muted); font-size: 13px }
.chip { font: 11px var(--mono); border: 1px solid var(--line); border-radius: 3px; padding: 0 5px; margin-left: 6px; color: var(--muted) }
input[type=text], input[type=number], textarea { width: 100%; font: inherit; color: var(--ink); background: var(--bg); border: 1px solid var(--line);
  border-radius: 5px; padding: 8px 10px }
textarea { min-height: 76px; resize: vertical }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
.hint { font-size: 12.5px; color: var(--muted) }
.need { font-size: 12.5px; color: var(--warn) }
.phases { display: flex; flex-direction: column; gap: 6px; margin-top: 2px }
.phase { display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: 10px; align-items: center; font-size: 12.5px; color: var(--muted) }
.bar { display: flex; height: 18px; border-radius: 3px; overflow: hidden; background: var(--line) }
.bar i { display: block; height: 100% }
.legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 12.5px; color: var(--muted) }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px }
table { border-collapse: collapse; width: 100%; font-size: 13.5px }
td { border-top: 1px solid var(--line); padding: 6px 8px 6px 0; vertical-align: top }
td:first-child { font-family: var(--mono); font-size: 12.5px; color: var(--muted); white-space: nowrap }
td .dflt { color: var(--muted) }
.scroll { overflow-x: auto }
pre, .out { font: 12.5px/1.45 var(--mono) }
.out { min-height: 200px }
.row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center }
button.act { font: inherit; font-weight: 600; padding: 8px 16px; border-radius: 5px; border: 1px solid var(--accent); background: var(--accent);
  color: var(--accent-ink); cursor: pointer }
button.ghost { background: none; color: var(--ink); border-color: var(--line) }
button:disabled { opacity: 0.45; cursor: default }
footer { position: fixed; left: 0; right: 0; bottom: 0; background: var(--surface); border-top: 1px solid var(--line);
  padding: 10px max(16px, env(safe-area-inset-right, 0px)) calc(10px + env(safe-area-inset-bottom, 0px)) max(16px, env(safe-area-inset-left, 0px)) }
footer .in { max-width: 980px; margin: 0 auto; display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between }
.where { font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; min-width: 0 }
.where b { color: var(--ink) }
.track { height: 4px; background: var(--line); border-radius: 2px; margin-top: 5px; width: min(320px, 60vw) }
.track i { display: block; height: 100%; background: var(--accent); border-radius: 2px; transition: width .2s }
@media (prefers-reduced-motion: reduce) { .track i { transition: none } }
@media (max-width: 720px) {
  .grid { grid-template-columns: minmax(0, 1fr); gap: 16px }
  nav ol { flex-direction: row; overflow-x: auto; gap: 4px; padding-bottom: 4px }
  nav button { border-left: 0; border-bottom: 3px solid transparent; white-space: nowrap; width: auto }
  nav button[aria-current="step"] { border-bottom-color: var(--accent) }
}
</style>
<div class="wrap">
  <header>
    <h1>Set up a search</h1>
    <p>Answer by section. A choice marked <span class="chip">suggested</span> is a best guess, with its reason; one marked <span class="chip">default</span> is what the search uses if you leave it. Change anything you like. Nothing leaves this page: the last step gives you a small file to hand to <code>evoloop brief</code>.</p>
  </header>
  <div class="grid">
    <nav aria-label="Sections"><ol id="rail"></ol></nav>
    <main id="main"></main>
  </div>
</div>
<footer><div class="in">
  <div class="where"><span id="where"></span><div class="track"><i id="track"></i></div></div>
  <div class="row"><button class="act ghost" id="back" type="button">Back</button><button class="act" id="next" type="button">Next</button></div>
</div></footer>
<script>
const DATA = __DATA__;
const DOWNLOAD = __DOWNLOAD__;
const KEY = "evoloop-setup-draft";
const STEPS = DATA.sections.concat(["Review and save"]);
let answers = Object.assign({}, DATA.answers), seen = {}, step = 0, flagged = false;
try { const d = JSON.parse(localStorage.getItem(KEY) || "null"); if (d && d.goal === DATA.goal) { answers = d.answers; seen = d.seen; step = Math.min(d.step || 0, STEPS.length - 1); } } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify({goal: DATA.goal, answers, seen, step})); } catch (e) {} };
const byField = Object.fromEntries(DATA.questions.map(q => [q.field, q]));
const hint = q => (!(q.field in answers) && q.suggested) ? q.suggested : null;
const current = f => (f in answers ? answers[f] : (hint(byField[f]) ? byField[f].suggested.value : byField[f].default));
function applies(q) {
  for (const [f, vs] of Object.entries(q.when || {})) if (!vs.includes(current(f))) return false;
  for (const [f, vs] of Object.entries(q.when_not || {})) if (vs.includes(current(f))) return false;
  return true;
}
const live = () => DATA.questions.filter(applies);
const done = q => q.field in answers || (!q.required && seen[q.field]);
const el = (tag, attrs, kids) => { const n = document.createElement(tag); for (const [k, v] of Object.entries(attrs || {})) { if (k === "text") n.textContent = v; else if (k === "html") n.innerHTML = v; else n.setAttribute(k, v); } (kids || []).forEach(c => n.append(c)); return n; };
const id = f => "f-" + f.replace(/\./g, "-");
function setAnswer(f, v) { if (v === null || v === "" || v === undefined) delete answers[f]; else answers[f] = v; seen[f] = true; save(); frame(); }
function phases(type) {
  const ps = DATA.phases[type]; if (!ps) return null;
  const box = el("div", {class: "phases", "aria-label": "Schedule of this kind of search"});
  let last = 0;
  ps.forEach(p => {
    const bar = el("div", {class: "bar"});
    [["new", "--seg-new"], ["cross", "--seg-cross"], ["local", "--seg-local"]].forEach(([k, c]) => { const i = el("i"); i.style.width = (100 * (p[k] || 0)) + "%"; i.style.background = "var(" + c + ")"; bar.append(i); });
    const label = ps.length === 1 ? "whole budget" : Math.round(100 * last) + "–" + Math.round(100 * p.until) + "% of budget";
    box.append(el("div", {class: "phase"}, [el("span", {text: label}), bar]));
    box.append(el("div", {class: "hint", text: "new designs " + Math.round(100 * (p.new || 0)) + "%, crossover " + Math.round(100 * (p.cross || 0)) + "%, local moves " + Math.round(100 * (p.local || 0)) + "%"}));
    last = p.until;
  });
  const lg = el("div", {class: "legend"});
  [["new designs", "--seg-new"], ["crossover", "--seg-cross"], ["local moves", "--seg-local"]].forEach(([t, c]) => { const s = el("span"); const i = el("i"); i.style.background = "var(" + c + ")"; s.append(i, t); lg.append(s); });
  box.append(lg);
  return box;
}
function question(q, n, of) {
  const card = el("section", {class: "q" + (flagged && q.required && !(q.field in answers) ? " missing" : ""), "aria-labelledby": id(q.field) + "-h"});
  card.append(el("div", {class: "num", text: "Question " + n + " of " + of}), el("h3", {id: id(q.field) + "-h", text: q.question}), el("p", {class: "why", text: q.why}));
  const value = current(q.field);
  if (q.kind === "choice") {
    const opts = el("div", {class: "opts", role: "radiogroup", "aria-labelledby": id(q.field) + "-h"});
    const known = q.choices.map(c => c.value);
    q.choices.forEach((c, i) => {
      const input = el("input", {type: "radio", name: id(q.field), id: id(q.field) + "-" + i});
      input.checked = value === c.value;
      input.addEventListener("change", () => setAnswer(q.field, c.value));
      const name = el("b", {text: c.label});
      const head = el("span", {}, [name]);
      if (hint(q) && c.value === q.suggested.value) head.append(el("span", {class: "chip", text: "suggested"}));
      else if (!q.suggested && c.value === q.default) head.append(el("span", {class: "chip", text: "default"}));
      opts.append(el("label", {class: "opt", for: input.id}, [input, el("span", {}, [head, el("span", {class: "d", text: c.description})])]));
    });
    if (q.other) {
      const mine = value !== null && value !== undefined && !known.includes(value);
      const input = el("input", {type: "radio", name: id(q.field), id: id(q.field) + "-other"});
      input.checked = mine;
      const text = el("input", {type: "text", id: id(q.field) + "-other-text", placeholder: "another model id", "aria-label": "Another value"});
      text.value = mine ? value : "";
      text.addEventListener("change", () => { if (text.value.trim()) setAnswer(q.field, text.value.trim()); });
      input.addEventListener("change", () => text.focus());
      opts.append(el("label", {class: "opt", for: input.id}, [input, el("span", {}, [el("b", {text: "another"}), text])]));
    }
    card.append(opts);
    if (q.field === "run.type" && value) { const p = phases(value); if (p) card.append(p); }
  } else {
    const input = q.kind === "number" ? el("input", {type: "number", id: id(q.field), step: "any", min: "0", inputmode: "decimal"}) : (q.field === "objective.goal" || q.field === "run.description" ? el("textarea", {id: id(q.field), rows: "3"}) : el("input", {type: "text", id: id(q.field)}));
    input.setAttribute("aria-labelledby", id(q.field) + "-h");
    if (q.field in answers) input.value = answers[q.field];
    if (hint(q)) input.value = q.suggested.value;
    else if (q.default !== null && q.default !== undefined) input.placeholder = "default: " + q.default;
    input.addEventListener("change", () => { const raw = input.value.trim(); setAnswer(q.field, raw === "" ? null : (q.kind === "number" ? Number(raw) : raw)); });
    card.append(input);
  }
  if (hint(q)) card.append(el("div", {class: "hint", text: "Suggested because " + q.suggested.why + ". Leave it to accept, or change it."}));
  else if (q.required && !(q.field in answers)) card.append(el("div", {class: flagged ? "need" : "hint", text: "This one has no default: an answer is needed."}));
  else if (!(q.field in answers) && (q.default === null || q.default === undefined)) card.append(el("div", {class: "hint", text: "Left alone, the kind of search you chose decides this."}));
  return card;
}
function nested() {
  const out = {};
  for (const q of live()) if (q.field in answers) { const parts = q.field.split("."); let node = out; parts.slice(0, -1).forEach(p => node = node[p] = node[p] || {}); node[parts[parts.length - 1]] = answers[q.field]; }
  const kept = live().filter(q => !(q.field in answers) && seen[q.field]).map(q => q.field);
  if (kept.length) out.status = {asked: kept};
  return out;
}
function review() {
  const box = el("div", {style: "display:flex;flex-direction:column;gap:18px"});
  const qs = live(), open = qs.filter(q => q.required && !(q.field in answers));
  const card = el("section", {class: "q"});
  card.append(el("h3", {text: open.length ? open.length + " question" + (open.length > 1 ? "s" : "") + " still need an answer" : "Everything is answered"}));
  const table = el("table");
  qs.forEach(q => { const set = q.field in answers; const v = set ? answers[q.field] : q.default; const cell = el("td"); cell.append(v === null || v === undefined ? el("span", {class: "need", text: "needed"}) : String(v)); if (!set && v !== null && v !== undefined) cell.append(el("span", {class: "dflt", text: "  (default)"})); table.append(el("tr", {}, [el("td", {text: q.field}), cell])); });
  card.append(el("div", {class: "scroll"}, [table]));
  box.append(card);
  const file = el("section", {class: "q"});
  const text = JSON.stringify(nested(), null, 1);
  file.append(el("h3", {text: "Your answers file"}), el("p", {class: "why", text: "Save this as answers.json, then run:  evoloop brief DIR --import PATH/TO/answers.json   and   evoloop plan DIR. In a chat with an agent, paste it and ask for it to be imported."}));
  const area = el("textarea", {class: "out", id: "answers-out", readonly: "", "aria-label": "Answers file"}); area.value = text;
  const said = el("span", {class: "hint", role: "status"});
  const copy = el("button", {class: "act", type: "button", text: "Copy"});
  copy.addEventListener("click", () => { const fallback = () => { area.focus(); area.select(); said.textContent = "Selected: press Ctrl or Cmd + C."; }; if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(() => { said.textContent = "Copied."; }, fallback); else fallback(); });
  const row = el("div", {class: "row"}, [copy]);
  if (DOWNLOAD) { const a = el("a", {class: "act ghost", download: "answers.json", href: "data:application/json;charset=utf-8," + encodeURIComponent(text), text: "Download answers.json", style: "text-decoration:none"}); row.append(a); }
  row.append(said);
  file.append(area, row);
  box.append(file);
  return box;
}
function frame() {
  const qs = live(), total = qs.length, answered = qs.filter(done).length;
  const rail = document.getElementById("rail"); rail.textContent = "";
  STEPS.forEach((name, i) => {
    const mine = qs.filter(q => q.section === name), n = mine.filter(done).length;
    const last = i === STEPS.length - 1;
    const b = el("button", {type: "button", class: !last && mine.length && n === mine.length ? "full" : ""}, [el("span", {text: name}), el("span", {class: "count", text: last ? "" : n + "/" + mine.length})]);
    if (i === step) b.setAttribute("aria-current", "step");
    b.addEventListener("click", () => go(i));
    rail.append(el("li", {}, [b]));
  });
  const main = document.getElementById("main"), keep = document.activeElement && document.activeElement.id, top = window.scrollY;
  main.textContent = "";
  main.append(el("h2", {text: STEPS[step]}));
  if (step === STEPS.length - 1) main.append(review());
  else qs.forEach((q, i) => { if (q.section === STEPS[step]) main.append(question(q, i + 1, total)); });
  if (keep) { const again = document.getElementById(keep); if (again) again.focus({preventScroll: true}); }
  window.scrollTo(0, top);
  document.getElementById("where").innerHTML = "Section <b>" + (step + 1) + " of " + STEPS.length + "</b> · " + STEPS[step] + " · <b>" + answered + " of " + total + "</b> questions done";
  document.getElementById("track").style.width = (total ? 100 * answered / total : 0) + "%";
  document.getElementById("back").disabled = step === 0;
  document.getElementById("next").textContent = step === STEPS.length - 2 ? "Review" : "Next";
  document.getElementById("next").hidden = step === STEPS.length - 1;
}
function go(to) {
  live().forEach(q => { if (q.section === STEPS[step]) { if (hint(q)) answers[q.field] = q.suggested.value; seen[q.field] = true; } });   // what you passed counts as seen; a suggestion you left is accepted
  if (to === STEPS.length - 1) flagged = true;
  step = Math.max(0, Math.min(STEPS.length - 1, to)); save(); frame(); window.scrollTo(0, 0);
}
document.getElementById("back").addEventListener("click", () => go(step - 1));
document.getElementById("next").addEventListener("click", () => go(step + 1));
frame();
</script>
"""


def fragment(brief: Dict[str, Any], download: bool) -> str:
    """The page without its outer document tags (a host that wraps pages supplies those)."""
    data = json.dumps(interview.payload(brief), default=str).replace("</", "<\\/")
    return PAGE.replace("__DATA__", data).replace("__DOWNLOAD__", "true" if download else "false")


def document(brief: Dict[str, Any]) -> str:
    """The form as a complete file to open in a browser."""
    page = fragment(brief, download=True)
    head, body = page.split("</style>\n", 1)
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + head + "</style>\n</head>\n<body>\n"
            + body + "</body>\n</html>\n")
