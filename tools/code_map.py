"""Write docs/code.md: every module of the package, with its public classes and functions, linked to the source.

    python tools/code_map.py > docs/code.md
"""
import ast
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evoloop")
REPO = "https://github.com/cameo-db/evoloop/blob/main/evoloop"
ORDER = ["cli", "controller", "schedule", "strategies", "design", "agents", "space", "jobs", "store", "form", "skill",
         "interview", "formpage", "estimate", "strategist", "approaches", "tpe", "audit", "report", "study", "site", "menu", "model"]


def first(doc):
    text = " ".join((doc or "").strip().split("\n\n")[0].split())
    cut = text.find(". ")
    return (text if cut < 0 else text[:cut + 1]).replace("|", "\\|")


def rows(path, rel):
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            kind = "class " if isinstance(node, ast.ClassDef) else ""
            args = "" if kind else "(%s)" % ", ".join(a.arg for a in node.args.args)
            out.append("| [`%s%s%s`](%s/%s#L%d) | %s |" % (kind, node.name, args, REPO, rel, node.lineno, first(ast.get_docstring(node))))
            if kind:
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) and not sub.name.startswith("_") and ast.get_docstring(sub):
                        out.append("| &nbsp;&nbsp;[`.%s()`](%s/%s#L%d) | %s |" % (sub.name, REPO, rel, sub.lineno, first(ast.get_docstring(sub))))
    return ast.get_docstring(tree), out


def modules():
    found = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "skills", "examples"))
        for name in sorted(files):
            if name.endswith(".py"):
                found.append(os.path.relpath(os.path.join(base, name), ROOT))
    key = lambda rel: (ORDER.index(rel.split(os.sep)[0].replace(".py", "")) if rel.split(os.sep)[0].replace(".py", "") in ORDER else 99, rel)
    return sorted(found, key=key)


def main():
    out = ["# Code map", "",
           "evoloop is used through its [commands](commands.md); it has no separate programming interface to learn. "
           "This page is for reading or changing the code: every module, what it is for, and its public classes and "
           "functions, each linked to its line in the repository. It is written from the source by `tools/code_map.py`.", "",
           "| Module | What it is for |", "|---|---|"]
    body = []
    for rel in modules():
        doc, table = rows(os.path.join(ROOT, rel), rel.replace(os.sep, "/"))
        if rel.endswith("__init__.py") and not table and not doc:
            continue
        name = rel.replace(os.sep, "/")
        anchor = "m-" + "".join(c if c.isalnum() else "-" for c in name).strip("-")
        out.append("| [`%s`](#%s) | %s |" % (name, anchor, first(doc)))
        body += ["", "## `%s` { #%s }" % (name, anchor), "", "[Source](%s/%s)" % (REPO, name), ""]
        if doc:
            body += [first(doc), ""]
        if table:
            body += ["| Name | What it does |", "|---|---|"] + table
    sys.stdout.write("\n".join(out + body) + "\n")


if __name__ == "__main__":
    main()
