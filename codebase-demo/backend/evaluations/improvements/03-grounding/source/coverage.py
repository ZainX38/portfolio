from fnmatch import fnmatchcase


def select_chunks(files, chunks, scope="all", patterns=()):
    if scope not in {"all", "selected"} or (scope == "selected" and not patterns):
        raise ValueError("Selected scope requires at least one --include path glob")
    def included(path):
        return scope == "all" or any(fnmatchcase(path, pattern) for pattern in patterns)

    selected = [chunk for chunk in chunks if included(chunk["path"])]
    indexed_paths = sorted({chunk["path"] for chunk in selected})
    indexed = set(indexed_paths)
    excluded = {}
    for path, file in files.items():
        if path in indexed:
            continue
        if "reason" in file:
            excluded[path] = file["reason"]
        elif not included(path):
            excluded[path] = "Outside the configured index paths"
        else:
            excluded[path] = "No non-empty chunks within the line-size limit"
    return selected, {"scope": scope, "patterns": list(patterns), "indexed_paths": indexed_paths, "excluded": excluded}
