"""Stub agents for the symbolic regression example: deterministic and offline.

`respond(role, context)` answers every role, so the whole loop can be exercised with no model call. The
writer draws new forms from a fixed list and makes simple edits of a parent. This proves the machinery,
not the quality of a real agent's designs."""
import re

FORMS = [
    ("quadratic", "polynomial", "N_CONSTANTS = 6\n\n\ndef predict(x, c):\n    x0, x1 = x[:, 0], x[:, 1]\n"
     "    return c[0] + c[1] * x0 + c[2] * x1 + c[3] * x0 ** 2 + c[4] * x1 ** 2 + c[5] * x0 * x1\n"),
    ("sine plus quadratic", "trigonometric", "N_CONSTANTS = 4\n\n\ndef predict(x, c):\n"
     "    return c[0] * np.sin(c[1] * x[:, 0]) + c[2] * x[:, 1] ** 2 + c[3]\n"),
    ("broken syntax", "broken", "N_CONSTANTS = 2\n\n\ndef predict(x, c):\n    return c[0] * (x[:, 0] + c[1]\n"),
    ("tanh ridge", "ridge", "N_CONSTANTS = 5\n\n\ndef predict(x, c):\n"
     "    return c[0] * np.tanh(c[1] * x[:, 0] + c[2] * x[:, 1] + c[3]) + c[4] * x[:, 1] ** 2\n"),
    ("damped sine", "modulated trigonometric", "N_CONSTANTS = 4\n\n\ndef predict(x, c):\n"
     "    wave = np.sin(c[1] * x[:, 0]) * np.exp(c[2] * x[:, 1])\n    return c[0] * wave + c[3] * x[:, 1] ** 2\n"),
    ("gaussian bump", "radial", "N_CONSTANTS = 4\n\n\ndef predict(x, c):\n"
     "    bump = np.exp(-((c[1] * x[:, 0]) ** 2))\n    return c[0] * bump + c[2] * x[:, 1] ** 2 + c[3]\n"),
    ("absolute value", "piecewise linear", "N_CONSTANTS = 3\n\n\ndef predict(x, c):\n"
     "    return c[0] * np.abs(x[:, 0]) + c[1] * np.abs(x[:, 1]) + c[2]\n"),
    ("cubic", "polynomial", "N_CONSTANTS = 5\n\n\ndef predict(x, c):\n    x0, x1 = x[:, 0], x[:, 1]\n"
     "    return c[0] + c[1] * x0 + c[2] * x0 ** 3 + c[3] * x1 ** 2 + c[4] * x1\n"),
    ("cosine product", "trigonometric", "N_CONSTANTS = 4\n\n\ndef predict(x, c):\n"
     "    return c[0] * np.cos(c[1] * x[:, 0]) * x[:, 1] + c[2] * x[:, 1] ** 2 + c[3]\n"),
    ("log growth", "logarithmic", "N_CONSTANTS = 3\n\n\ndef predict(x, c):\n"
     "    return c[0] * np.log1p(x[:, 0] ** 2) + c[1] * x[:, 1] ** 2 + c[2]\n"),
]
STATE = {"calls": 0, "forms": 0}
NUMBER = re.compile(r"(?<![\w.\[])(\d+\.\d+)")


def add_term(code, n):
    """One more additive term with a new constant: a single attributable change."""
    count = int(re.search(r"N_CONSTANTS = (\d+)", code).group(1))
    terms = ["x[:, 1]", "x[:, 0] * x[:, 1]", "x[:, 0] ** 2", "np.sin(x[:, 1])", "x[:, 1] ** 3"]
    term = terms[n % len(terms)]
    code = code.replace("N_CONSTANTS = %d" % count, "N_CONSTANTS = %d" % (count + 1), 1)
    lines = code.rstrip("\n").split("\n")
    lines[-1] = lines[-1] + " + c[%d] * %s" % (count, term)
    return "\n".join(lines) + "\n"


def drop_term(code):
    lines = code.rstrip("\n").split("\n")
    parts = lines[-1].split(" + ")
    if len(parts) > 2:
        lines[-1] = " + ".join(parts[:-1])
    return "\n".join(lines) + "\n"


def nudge(text, n):
    found = list(NUMBER.finditer(text))
    if not found:
        return text
    m = found[n % len(found)]
    return text[:m.start(1)] + repr(round(float(m.group(1)) * (1.5 if n % 2 else 0.6), 6)) + text[m.end(1):]


def proposal(context, index):
    request = context["request"]
    STATE["calls"] += 1
    n = STATE["calls"]
    move, mode = request["move"], request["mode"]
    parents = context.get("parents") or []
    source = parents[0]["blocks"] if parents else (context.get("starting_blocks") or {})
    blocks = {}
    family = None
    if mode in ("new", "novel"):
        name, family, code = FORMS[STATE["forms"] % len(FORMS)]
        STATE["forms"] += 1
        blocks["model"] = code
        change = "a new form: %s" % name
    elif move == "settings_move":
        blocks["fit_params"] = nudge(source["fit_params"], n)
        change = "moved one setting"
    elif move == "ablation":
        blocks["model"] = drop_term(source["model"])
        change = "removed the last term"
    elif move == "hybrid" and len(parents) > 1:
        blocks["model"] = add_term(parents[1]["blocks"]["model"], n)
        blocks["fit_params"] = parents[0]["blocks"]["fit_params"]
        change = "the form of the second parent with a term added, the settings of the first"
    else:   # structural_change, graft
        blocks["model"] = add_term(source["model"], n)
        change = "added one term"
    return {"name": "stub design %d" % n, "family": family, "hypothesis": "This form fits the data better.",
            "predicted_effect": "a lower error", "expected_gain": {"gain": 0.5 + 0.1 * index, "probability_better": 0.4},
            "change_summary": change, "parts_from": None, "blocks": blocks}


def respond(role, context):
    base = {"reasoning": "stub", "note": "stub", "followed_notes": [n["id"] for n in context.get("notes_from_the_person") or []]}
    if role == "writer":
        return dict(base, proposals=[proposal(context, i) for i in range(int(context["request"].get("number_of_proposals") or 1))])
    if role == "analyst":
        results = [r for r in context.get("results") or [] if r.get("score") is not None]
        lessons = [{"statement": "Adding a term helped in %s." % results[0]["run"], "status": "tentative",
                    "evidence": [results[0]["run"]]}] if results else []
        return dict(base, lessons=lessons, questions=[{"question": "Should forms with more than 6 constants be allowed?",
                                                       "default": "yes"}] if len(results) > 3 else [])
    if role == "coordinator":
        return dict(base, choice=int(context.get("code_would_choose") or 0))
    if role == "assessor":
        return dict(base, assessment="Stub review of %s: no judgment was made." % context.get("role"), strengths=[],
                    weaknesses=[], suggestions=[{"change": "none (stub)", "figure": "none"}])
    words = str(context.get("words") or "")
    changes = [{"key": "schedule.novelty", "value": 0.8, "from": words}] if "novel" in words.lower() else []
    return dict(base, changes=changes, notes=[{"text": words, "roles": ["writer"]}], not_covered=[])
