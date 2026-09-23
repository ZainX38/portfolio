"""Small Python symbol lookup layered on the existing vector index.

Only indexed source is considered. No imports or repository code are executed.
Other languages and unparseable Python continue to use vector retrieval.
"""
import ast
import re
from pathlib import PurePosixPath


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def symbols(repository):
    if hasattr(repository, "_python_symbols"):
        return repository._python_symbols
    found = []
    paths = {chunk["path"] for chunk in repository.chunks}
    for path in sorted(paths):
        if not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(repository.files[path]["content"])
        except (SyntaxError, ValueError, RecursionError):
            continue
        module = PurePosixPath(path).stem

        def visit(nodes, owner=""):
            for node in nodes:
                if isinstance(node, ast.ClassDef):
                    visit(node.body, node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body = node.body
                    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                        body = body[1:]
                    if not body:
                        continue
                    calls = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                calls.append(("", child.func.id))
                            elif isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name) and child.func.value.id in ("self", "cls"):
                                calls.append((owner, child.func.attr))
                    found.append({"path": path, "module": module, "owner": owner,
                        "name": node.name, "start": node.lineno, "end": node.end_lineno,
                        "body_start": body[0].lineno, "statements": body, "calls": calls})
        visit(tree.body)
    repository._python_symbols = found
    return found


def ranked_symbols(repository, question):
    identifiers = set(re.findall(r"[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*", question))
    query_words = words(question)
    direct = []
    for symbol in symbols(repository):
        name, owner, module = symbol["name"], symbol["owner"], symbol["module"]
        score = 0
        for identifier in identifiers:
            parts = identifier.split(".")
            if len(parts) > 1 and parts[-1] == name and parts[-2] in (owner, module):
                score = max(score, 30)
            elif identifier == name and ("_" in name or not owner and name not in {"get", "post", "request", "send"}):
                score = max(score, 25)
        if owner and owner in identifiers and not name.startswith("__"):
            overlap = words(name) & query_words - {"get", "request", "send"}
            if overlap:
                score = max(score, 20 + len(overlap))
        if score:
            direct.append((score, symbol))
    direct.sort(key=lambda item: (-item[0], item[1]["path"], item[1]["start"]))
    related = []
    direct_keys = {(s["path"], s["start"]) for _, s in direct}
    for _, parent in direct:
        for symbol in symbols(repository):
            if symbol["path"] != parent["path"] or (symbol["path"], symbol["start"]) in direct_keys:
                continue
            if (symbol["owner"], symbol["name"]) in parent["calls"]:
                related.append((10 + len(words(symbol["name"]) & query_words), symbol))
    # A callee can be reached from more than one directly named function.
    unique = {}
    for score, symbol in direct + related:
        key = symbol["path"], symbol["start"]
        if key not in unique or score > unique[key][0]:
            unique[key] = score, symbol
    return sorted(unique.values(), key=lambda item: (-item[0], item[1]["path"], item[1]["start"]))


def rank_chunks(repository, question, cosine_scores):
    matches = ranked_symbols(repository, question)
    priorities = []
    for index, chunk in enumerate(repository.chunks):
        priority = 0
        for score, symbol in matches:
            if chunk["path"] != symbol["path"]:
                continue
            overlap = max(0, min(chunk["end_line"], symbol["end"]) - max(chunk["start_line"], symbol["body_start"]) + 1)
            if overlap:
                priority = max(priority, score + overlap / (symbol["end"] - symbol["body_start"] + 1))
        priorities.append((priority, cosine_scores[index]))
    return sorted(range(len(priorities)), key=priorities.__getitem__, reverse=True)
