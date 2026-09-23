def chunk_files(files, max_chars=3000, overlap_lines=5):
    chunks = []
    for path, file in sorted(files.items()):
        lines = file.get("content", "").splitlines(keepends=True)
        start = 0
        while start < len(lines):
            # Skip pathological generated lines without losing original line numbers.
            if len(lines[start]) > max_chars:
                start += 1
                continue
            end = start
            size = 0
            while end < len(lines) and size + len(lines[end]) <= max_chars:
                size += len(lines[end])
                end += 1
            text = "".join(lines[start:end])
            if text.strip():
                chunks.append({
                    "id": f"chunk-{len(chunks) + 1}",
                    "path": path,
                    "start_line": start + 1,
                    "end_line": end,
                    "text": text,
                })
            start = max(start + 1, end - overlap_lines)
            if end == len(lines):
                break
    return chunks
