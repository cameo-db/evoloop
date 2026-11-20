"""The search space: the marked blocks of the project's code, and which of them a run may change.

The code is marked once, with comment lines:

    # EVOLVE-BLOCK-START name=trunk kind=structure role=trunk
    ...
    # EVOLVE-BLOCK-END

    # EVOLVE-BLOCK-START name=fit_params kind=params role=optimizer
    PARAMS = {"lr": 3e-4, "batch_size": 128}
    # EVOLVE-BLOCK-END

`kind=structure` is code an agent rewrites; `kind=params` is one assignment of a dict literal. `role` says
what part of the system the block is (stem, trunk, heads, loss, optimizer, augmentation, ...); it defaults
to `model` for structure and `settings` for params. The brief then says, per run, which roles are open, so
one marked-up project serves many searches. Roles listed in `space.recipe_roles` make up the training
recipe; the other structure blocks make up the model. Everything outside the markers is frozen and checked
by hash."""
from __future__ import annotations

import ast
import difflib
import fnmatch
import hashlib
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

START = re.compile(r"^\s*(?:#|//)\s*EVOLVE-BLOCK-START\s+(.*?)\s*$")
END = re.compile(r"^\s*(?:#|//)\s*EVOLVE-BLOCK-END\s*$")
SKIP = ("__pycache__", ".git", "*.pyc", ".pytest_cache", "evo_out")
TEXT = (".py", ".yaml", ".yml", ".json", ".toml", ".cfg", ".txt", ".md", ".sh")


class SpaceError(Exception):
    pass


def parse(text: str, filename: str = "<text>") -> List[Dict[str, Any]]:
    """A file as segments: frozen text, and blocks with their attributes."""
    segments: List[Dict[str, Any]] = []
    frozen: List[str] = []
    block: Optional[Dict[str, Any]] = None
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        start = START.match(line)
        if start:
            if block is not None:
                raise SpaceError("%s:%d: blocks do not nest" % (filename, number))
            attrs = dict(item.split("=", 1) for item in start.group(1).split() if "=" in item)
            if "name" not in attrs:
                raise SpaceError("%s:%d: a block needs name=" % (filename, number))
            kind = attrs.get("kind", "structure")
            if kind not in ("structure", "params"):
                raise SpaceError("%s:%d: kind must be structure or params" % (filename, number))
            frozen.append(line)
            segments.append({"frozen": "".join(frozen)})
            frozen = []
            block = {"name": attrs["name"], "kind": kind, "lines": [],
                     "role": attrs.get("role") or ("settings" if kind == "params" else "model")}
        elif END.match(line):
            if block is None:
                raise SpaceError("%s:%d: END without START" % (filename, number))
            block["content"] = "".join(block.pop("lines"))
            segments.append(block)
            block = None
            frozen.append(line)
        elif block is not None:
            block["lines"].append(line)
        else:
            frozen.append(line)
    if block is not None:
        raise SpaceError("%s: block %s is never closed" % (filename, block["name"]))
    segments.append({"frozen": "".join(frozen)})
    return segments


def render(segments: List[Dict[str, Any]], blocks: Dict[str, str]) -> str:
    out = []
    for seg in segments:
        if "frozen" in seg:
            out.append(seg["frozen"])
        else:
            content = blocks.get(seg["name"], seg["content"])
            out.append(content if content.endswith("\n") or not content else content + "\n")
    return "".join(out)


def files(base: str) -> List[str]:
    out = []
    for root, dirs, names in os.walk(base):
        dirs[:] = sorted(d for d in dirs if not any(fnmatch.fnmatch(d, p) for p in SKIP))
        for name in sorted(names):
            if not any(fnmatch.fnmatch(name, p) for p in SKIP):
                out.append(os.path.relpath(os.path.join(root, name), base))
    return out


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def table(base: str) -> Dict[str, Dict[str, Any]]:
    """Every block of the base: name -> {file, kind, role, content}."""
    out: Dict[str, Dict[str, Any]] = {}
    for rel in files(base):
        if not rel.endswith(TEXT):
            continue
        try:
            text = read(os.path.join(base, rel))
        except (OSError, UnicodeDecodeError):
            continue
        if "EVOLVE-BLOCK-START" not in text:
            continue
        for seg in parse(text, rel):
            if "name" in seg:
                if seg["name"] in out:
                    raise SpaceError("block name %s is used twice (%s and %s)" % (seg["name"], out[seg["name"]]["file"], rel))
                out[seg["name"]] = {"file": rel, "kind": seg["kind"], "role": seg["role"], "content": seg["content"]}
    if not out:
        raise SpaceError("no EVOLVE-BLOCK markers found under %s" % base)
    return out


def frozen_hash(base: str, extra: Optional[str] = None) -> str:
    """A hash of everything a run may not change: the base with its blocks blanked, and the adapter."""
    digest = hashlib.sha256()
    for folder in (base, extra):
        if not folder or not os.path.isdir(folder):
            continue
        for rel in files(folder):
            path = os.path.join(folder, rel)
            digest.update(rel.encode())
            try:
                text = read(path)
                if "EVOLVE-BLOCK-START" in text:
                    text = "".join(seg.get("frozen", "") for seg in parse(text, rel))
                digest.update(text.encode())
            except (UnicodeDecodeError, OSError):
                with open(path, "rb") as handle:
                    digest.update(handle.read())
    return digest.hexdigest()[:20]


def part_of(block: Dict[str, Any], settings: Dict[str, Any]) -> str:
    """`settings`, `recipe` or `model`: which part of a design a block belongs to."""
    if block["kind"] == "params":
        return "settings"
    return "recipe" if block["role"] in settings["space"]["recipe_roles"] else "model"


def open_blocks(blocks: Dict[str, Dict[str, Any]], settings: Dict[str, Any]) -> Dict[str, str]:
    """The blocks this run may change: name -> kind. Decided by the brief's `space`."""
    space = settings["space"]
    preset, roles = space["preset"], space.get("roles") or {}
    out: Dict[str, str] = {}
    for name, block in blocks.items():
        state = roles.get(block["role"]) or roles.get(name)
        if block["kind"] == "params":
            allowed = space["settings"]
            is_open = state != "fixed" and (allowed == "open" or (isinstance(allowed, list) and (
                name in allowed or any(str(a).startswith(name + ".") for a in allowed))))
        elif state is not None:
            is_open = state == "open"
        elif preset == "settings_only" or preset == "custom":
            is_open = False
        elif preset == "module":
            is_open = block["role"] in space["modules"] or name in space["modules"]
        elif preset in ("template", "open_architecture"):
            is_open = part_of(block, settings) == "model"
        else:   # architecture_and_recipe, everything
            is_open = True
        if is_open:
            out[name] = block["kind"]
    return out


def parse_params(content: str) -> Tuple[str, Dict[str, Any]]:
    try:
        tree = ast.parse(content.strip() + "\n")
    except SyntaxError as exc:
        raise SpaceError("a params block must be one assignment of a dict literal (%s)" % exc)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign) or len(tree.body[0].targets) != 1 \
            or not isinstance(tree.body[0].targets[0], ast.Name):
        raise SpaceError("a params block must be exactly one assignment, NAME = {...}")
    try:
        values = ast.literal_eval(tree.body[0].value)
    except (ValueError, SyntaxError):
        raise SpaceError("a params block must assign a dict literal of numbers, booleans or strings")
    if not isinstance(values, dict) or not all(
            isinstance(k, str) and isinstance(v, (int, float, bool, str)) for k, v in values.items()):
        raise SpaceError("a params block must assign a dict of numbers, booleans or strings")
    return tree.body[0].targets[0].id, values


def render_params(name: str, values: Dict[str, Any]) -> str:
    return "%s = %r\n" % (name, values)


def all_params(table_: Dict[str, Dict[str, Any]], blocks: Dict[str, str]) -> Dict[str, Any]:
    """The resolved settings of a design: block.key -> value over every params block."""
    out: Dict[str, Any] = {}
    for name, block in table_.items():
        if block["kind"] == "params":
            try:
                for key, value in parse_params(blocks.get(name, block["content"]))[1].items():
                    out["%s.%s" % (name, key)] = value
            except SpaceError:
                continue
    return out


def full(table_: Dict[str, Dict[str, Any]], blocks: Dict[str, str]) -> Dict[str, str]:
    """Every block's content: the given ones, and the base's for the rest."""
    return {name: blocks.get(name, block["content"]) for name, block in table_.items()}


def check(table_: Dict[str, Dict[str, Any]], changed: Dict[str, str], allowed: Dict[str, str],
          settings: Dict[str, Any]) -> Optional[str]:
    """Why a proposal's blocks cannot be run, or None. Code enforces the space; an agent cannot argue past it."""
    for name, content in changed.items():
        if name not in table_:
            return "block %s does not exist" % name
        if name not in allowed and content != table_[name]["content"]:
            return "block %s is not open in this search" % name
        if not isinstance(content, str) or not content.strip():
            return "block %s is empty" % name
        if "EVOLVE-BLOCK-" in content:
            return "block %s contains a marker line" % name
        if table_[name]["kind"] == "params":
            try:
                parse_params(content)
            except SpaceError as exc:
                return "block %s: %s" % (name, exc)
        elif table_[name]["file"].endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError as exc:
                try:   # a block inside a class or a function is indented
                    ast.parse("if True:\n" + content)
                except SyntaxError:
                    return "block %s does not parse: %s" % (name, exc)
        lowered = content.lower()
        for term in settings["space"].get("forbidden_terms") or []:
            if str(term).lower() in lowered:
                return "block %s uses %r, which this search forbids" % (name, term)
    return None


def materialize(base: str, adapter: Optional[str], blocks: Dict[str, str], workdir: str) -> None:
    """A working copy for one run: the base with the blocks spliced in, and the adapter beside it."""
    os.makedirs(workdir, exist_ok=True)
    for rel in files(base):
        src, dst = os.path.join(base, rel), os.path.join(workdir, rel)
        os.makedirs(os.path.dirname(dst) or workdir, exist_ok=True)
        done = False
        if rel.endswith(TEXT):
            try:
                text = read(src)
                if "EVOLVE-BLOCK-START" in text:
                    with open(dst, "w", encoding="utf-8") as handle:
                        handle.write(render(parse(text, rel), blocks))
                    done = True
            except UnicodeDecodeError:
                pass
        if not done:
            if os.path.islink(src):
                os.symlink(os.readlink(src), dst)
            else:
                shutil.copy2(src, dst)
    if adapter and os.path.isdir(adapter):
        shutil.copytree(adapter, os.path.join(workdir, "adapter"), dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))


def spliced_text(base: str, table_: Dict[str, Dict[str, Any]], blocks: Dict[str, str], part: str,
                 settings: Dict[str, Any]) -> str:
    """The files that hold a design's model (or recipe), as run: what a study file records as its code."""
    wanted = sorted({b["file"] for b in table_.values() if part_of(b, settings) == part
                     or (part == "recipe" and b["kind"] == "params")})
    texts = []
    for rel in wanted:
        text = render(parse(read(os.path.join(base, rel)), rel), blocks)
        texts.append(text if len(wanted) == 1 else "# ==== file: %s ====\n%s" % (rel, text))
    return "\n".join(texts)


def key_of(blocks: Dict[str, str], names: List[str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(names):
        # Trailing space and blank lines do not make a different design; indentation does.
        text = "\n".join(line.rstrip() for line in blocks.get(name, "").splitlines() if line.strip())
        digest.update(name.encode() + b"\0" + text.encode() + b"\0")
    return digest.hexdigest()[:16]


TOKEN = re.compile(r"[A-Za-z_]\w*|\d+(?:\.\d+)?|\S")


def shingles(text: str, width: int = 3) -> frozenset:
    tokens = TOKEN.findall(text)
    if len(tokens) < width:
        return frozenset([tuple(tokens)]) if tokens else frozenset()
    return frozenset(tuple(tokens[i:i + width]) for i in range(len(tokens) - width + 1))


def similarity(a: Any, b: Any) -> float:
    """How much two pieces of code share: the overlap of their runs of three tokens (1 the same, 0 nothing
    shared). It follows what the code says rather than how long it is or which characters it uses."""
    a = a if isinstance(a, frozenset) else shingles(a)
    b = b if isinstance(b, frozenset) else shingles(b)
    if not a and not b:
        return 1.0
    return len(a & b) / float(len(a | b))


def diff(old: Dict[str, str], new: Dict[str, str], limit: int = 6000) -> str:
    out = []
    for name in sorted(set(old) | set(new)):
        if old.get(name, "") != new.get(name, ""):
            out.extend(difflib.unified_diff(old.get(name, "").splitlines(), new.get(name, "").splitlines(),
                                            "before/" + name, "after/" + name, lineterm="", n=2))
    text = "\n".join(out)
    return text if len(text) <= limit else text[:limit] + "\n... (cut)"
