"""Scripted proposals for the classifier example: deterministic and offline.

`respond(role, context)` answers every role, so the whole loop can be exercised with no model call. The
writer draws new designs from a fixed list and makes simple, real edits of a parent: widen or deepen it, drop a
layer, move the learning rate, or combine one parent's features with the other's layers. This shows the
machinery of a search on real training runs. It says nothing about what a language model would find."""
import ast
import re

RAW = 'def features(x):\n    """The two coordinates as they are."""\n    return x\n'
RADIUS = ('def features(x):\n    """The coordinates and the distance from the centre."""\n'
          '    r = np.sqrt((x ** 2).sum(1))\n    return np.stack([x[:, 0], x[:, 1], r], axis=1)\n')
SQUARES = ('def features(x):\n    """The coordinates, their squares and their product."""\n'
           '    return np.stack([x[:, 0], x[:, 1], x[:, 0] ** 2, x[:, 1] ** 2, x[:, 0] * x[:, 1]], axis=1)\n')
POLAR = ('def features(x):\n    """Distance from the centre, and the angle as a sine and a cosine."""\n'
         '    r = np.sqrt((x ** 2).sum(1))\n    theta = np.arctan2(x[:, 1], x[:, 0])\n'
         '    return np.stack([r, np.sin(theta), np.cos(theta)], axis=1)\n')
WAVES = ('def features(x):\n    """The coordinates, and waves along the distance from the centre."""\n'
         '    r = np.sqrt((x ** 2).sum(1))\n'
         '    return np.stack([x[:, 0], x[:, 1], np.sin(6.0 * r), np.cos(6.0 * r)], axis=1)\n')
BROKEN = 'def features(x):\n    return np.stack([x[:, 0], x[:, 1]\n'

# name, family, hidden layers, activation, features
FORMS = [
    ("one small hidden layer", "small network", [3], "tanh", RAW),
    ("distance as a feature", "added features", [], "tanh", RADIUS),
    ("two hidden layers", "deeper network", [8, 8], "tanh", RAW),
    ("squares and products", "added features", [], "tanh", SQUARES),
    ("a relu layer", "relu network", [16], "relu", RAW),
    ("a broken design", "broken", [8], "tanh", BROKEN),
    ("polar coordinates", "polar features", [], "tanh", POLAR),
    ("three narrow layers", "deeper network", [6, 6, 6], "tanh", RAW),
    ("waves along the radius", "periodic features", [4], "tanh", WAVES),
    ("wide and shallow", "small network", [24], "tanh", RAW),
]
STATE = {"calls": 0, "forms": 0}


def render(hidden, activation, feats):
    return ('HIDDEN = %r            # the widths of the hidden layers; none is a linear classifier\n'
            'ACTIVATION = "%s"    # tanh or relu\n\n\n%s' % (list(hidden), activation, feats))


def parse(block):
    hidden = ast.literal_eval(re.search(r"HIDDEN = (\[[^\]]*\])", block).group(1))
    activation = re.search(r'ACTIVATION = "(\w+)"', block).group(1)
    return list(hidden), activation, block[block.index("def features"):]


def proposal(context, index):
    request = context["request"]
    STATE["calls"] += 1
    n = STATE["calls"]
    move, mode = request["move"], request["mode"]
    parents = context.get("parents") or []
    source = parents[0]["blocks"] if parents else (context.get("starting_blocks") or {})
    blocks, family, parts = {}, None, None
    if mode in ("new", "novel"):
        name, family, hidden, activation, feats = FORMS[STATE["forms"] % len(FORMS)]
        if STATE["forms"] >= len(FORMS):      # the list has been used once: later rounds widen each design
            hidden, name = [h + 4 * (STATE["forms"] // len(FORMS)) for h in hidden] or [8], "%s, wider" % name
        STATE["forms"] += 1
        blocks["model"] = render(hidden, activation, feats)
        change = "a new design: %s" % name
    elif move == "settings_move":
        rate = float(re.search(r'"lr": ([0-9.e-]+)', source["fit"]).group(1))
        decay = float(re.search(r'"weight_decay": ([0-9.e-]+)', source["fit"]).group(1))
        if n % 4 == 0:      # now and then the weight decay, otherwise the learning rate, by a different factor each time
            fresh = [0.0001, 0.001, 0.0, 0.0003][(n // 4) % 4]
            blocks["fit"] = re.sub(r'"weight_decay": [0-9.e-]+', '"weight_decay": %.4g' % fresh, source["fit"])
            change = "weight decay %.4g -> %.4g" % (decay, fresh)
        else:
            fresh = min(0.3, max(0.0005, rate * [2.0, 0.5, 1.5, 0.7, 3.0, 0.3][n % 6]))
            blocks["fit"] = re.sub(r'"lr": [0-9.e-]+', '"lr": %.4g' % fresh, source["fit"])
            change = "learning rate %.4g -> %.4g" % (rate, fresh)
    elif move == "ablation":
        hidden, activation, feats = parse(source["model"])
        if len(hidden) > 1:
            blocks["model"], change = render(hidden[:-1], activation, feats), "removed the last hidden layer"
        elif feats != RAW:
            blocks["model"], change = render(hidden or [8], activation, RAW), "removed the added features"
        else:
            blocks["model"], change = render([max(2, (hidden or [8])[0] // 2)], activation, feats), "halved the hidden layer"
    elif move == "hybrid" and len(parents) > 1:
        mine, other = parse(parents[0]["blocks"]["model"]), parse(parents[1]["blocks"]["model"])
        # A real crossover: the layers of whichever parent has more of them, with the other parent's features.
        deep, given = (mine, other) if sum(mine[0]) >= sum(other[0]) else (other, mine)
        blocks["model"] = render(deep[0] or [8], deep[1], given[2])
        parts = {"layers": parents[0]["candidate"] if deep is mine else parents[1]["candidate"],
                 "features": parents[1]["candidate"] if deep is mine else parents[0]["candidate"]}
        change = "the layers of one parent with the features of the other"
    else:   # structural_change, graft: one real edit, a different kind each time
        hidden, activation, feats = parse(source["model"])
        kind = n % 4
        if not hidden:
            hidden, change = [6 + 2 * (n % 3)], "added a hidden layer"
        elif kind == 0 and len(hidden) < 4:
            hidden, change = hidden + [max(4, hidden[-1] // 2 + n % 3)], "added a narrower layer on top"
        elif kind == 1 and max(hidden) < 48:
            hidden, change = [h + 4 + n % 5 for h in hidden], "widened every layer"
        elif kind == 2:
            activation, change = ("relu" if activation == "tanh" else "tanh"), "changed the activation"
        elif max(hidden) < 64:
            hidden, change = hidden[:-1] + [hidden[-1] * 2], "doubled the last layer"
        else:
            hidden, change = [h - 3 - n % 4 for h in hidden if h > 8] or [8], "narrowed the layers"
        blocks["model"] = render(hidden, activation, feats)
    return {"name": "scripted design %d" % n, "family": family, "hypothesis": "This design separates the spirals better.",
            "predicted_effect": "a higher accuracy", "expected_gain": {"gain": 0.5 + 0.1 * index, "probability_better": 0.4},
            "change_summary": change, "parts_from": parts, "blocks": blocks}


def respond(role, context):
    base = {"reasoning": "scripted", "note": "scripted", "followed_notes": [n["id"] for n in context.get("notes_from_the_person") or []]}
    if role == "writer":
        return dict(base, proposals=[proposal(context, i) for i in range(int(context["request"].get("number_of_proposals") or 1))])
    if role == "analyst":
        results = [r for r in context.get("results") or [] if r.get("score") is not None]
        lessons = [{"statement": "The change in %s was scored." % results[0]["run"], "status": "tentative",
                    "evidence": [results[0]["run"]]}] if results else []
        return dict(base, lessons=lessons, questions=[])
    if role == "coordinator":
        return dict(base, choice=int(context.get("code_would_choose") or 0))
    if role == "conductor":
        return dict(base, reply="Scripted conductor: nothing was changed.", decisions=[], approve=[], decline=[])
    if role == "strategist":
        facts = context.get("facts") or {}
        if (facts.get("designs_since_the_best_rose") or 0) >= 6:
            return dict(base, decisions=[{"action": "force", "args": {"mode": "cross", "kind": "hybrid", "count": 2},
                                          "reason": "no gain for a stretch: combine the best families",
                                          "expects": {"gain": 1.0, "within": 10}}])
        return dict(base, decisions=[{"action": "stay", "args": {}, "reason": "the search is still gaining",
                                      "expects": {"gain": 1.0, "within": 10}}])
    if role == "assessor":
        return dict(base, assessment="Scripted review of %s: no judgment was made." % context.get("role"), strengths=[],
                    weaknesses=[], suggestions=[{"change": "none (scripted)", "figure": "none"}])
    return dict(base, changes=[], notes=[{"text": str(context.get("words") or ""), "roles": ["writer"]}], not_covered=[])
