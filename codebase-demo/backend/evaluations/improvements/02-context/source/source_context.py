"""Pack exact, line-addressable implementation spans within a byte budget."""
import ast
import re

from symbol_retrieval import ranked_symbols, symbols, words


def header(excerpt):
    label = f" ({excerpt['symbol']}; {excerpt['scope']})" if "symbol" in excerpt else ""
    return f"[{excerpt['id']}] {excerpt['path']}:{excerpt['start_line']}-{excerpt['end_line']}{label}\n"


def terms(text):
    # Light inflection handling, not a language model or a second index.
    result = set()
    for word in words(text):
        if word.endswith("ies"):
            word = word[:-3] + "y"
        elif word.endswith("ing"):
            word = word[:-3]
        elif word.endswith("ed"):
            word = word[:-2]
        elif word.endswith("s"):
            word = word[:-1]
        if word.startswith("except"):
            word = "except"
        result.add(word)
    return result - {"how", "do", "doe", "the", "a", "an", "in", "and", "or", "of", "to", "for", "it", "self", "src", "py", "request", "response", "handle", "choose", "convert", "determine", "work", "include", "between", "before", "value", "translate"}


def implementation_context(repository, chunks, question, budget):
    matches = ranked_symbols(repository, question)
    if not matches:
        return None  # Retain existing vector-context behavior for other queries.
    highest = matches[0][0]
    primary = [s for score, s in matches if score == highest]
    related = [s for score, s in matches if score < 20]
    # A package-qualified convenience function can already be present in a
    # retrieved module chunk (e.g. a re-export). Preserve that body as well.
    qualified_names = {name.split(".")[-1] for name in re.findall(r"\b\w+(?:\.\w+)+", question)}
    for symbol in symbols(repository):
        if not symbol["owner"] and symbol["name"] in qualified_names and any(
            c["path"] == symbol["path"] and c["start_line"] <= symbol["body_start"] <= c["end_line"] for c in chunks
        ):
            primary.append(symbol)
    available_lines = {}
    for chunk in repository.chunks:
        available_lines.setdefault(chunk["path"], set()).update(range(chunk["start_line"], chunk["end_line"] + 1))
    excerpts, seen = [], set()
    focus = question
    for symbol in primary:
        focus = focus.replace(symbol["name"], "")
    query_terms = terms(focus)

    def excerpt(symbol, start, end, scope):
        lines = repository.files[symbol["path"]]["content"].splitlines(keepends=True)
        return {"id": f"source-{len(excerpts) + 1}", "path": symbol["path"],
            "start_line": start, "end_line": end, "text": "".join(lines[start-1:end]),
            "symbol": ".".join(part for part in (symbol["owner"], symbol["name"]) if part), "scope": scope}

    def cost(item):
        return len((header(item) + item["text"] + "\n\n").encode())

    for symbol in primary + related:
        if all(isinstance(node, ast.Pass) or isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value is Ellipsis for node in symbol["statements"]):
            continue
        key = symbol["path"], symbol["start"]
        if key in seen:
            continue
        seen.add(key)
        start, end = symbol["body_start"], symbol["end"]
        # Expansion must never reintroduce lines that the index excluded.
        if not set(range(start, end + 1)) <= available_lines[symbol["path"]]:
            continue
        item = excerpt(symbol, start, end, "complete body")
        if cost(item) > budget:
            if symbol not in primary:
                continue  # Do not replace useful primary evidence with helper fragments.
            # Oversized methods: a relevant contiguous window, bounded at AST
            # statements and explicitly labelled as partial. Prefer earlier
            # context on equal relevance so guards precede their consequences.
            nodes = [node for statement in symbol["statements"] for node in ast.walk(statement)
                if isinstance(node, (ast.stmt, ast.ExceptHandler))]
            starts = sorted({node.lineno for node in nodes})
            ends = sorted({node.end_lineno for node in nodes})
            best = None
            for first in starts:
                for last in ends:
                    if last < first:
                        continue
                    candidate = excerpt(symbol, first, last, "partial body; other code omitted")
                    if cost(candidate) > budget:
                        break
                    overlap = query_terms & terms(candidate["text"])
                    score = (len(overlap), -first, last - first)
                    if best is None or score > best[0]:
                        best = score, candidate
            if best is None:
                continue
            item = best[1]
        excerpts.append(item)
        budget -= cost(item)
    return excerpts
