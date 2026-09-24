function CodeIcon() {
    return (
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 fill-none stroke-current stroke-2 text-amber-300">
            <path strokeLinecap="round" strokeLinejoin="round" d="m8 9-3 3 3 3m8-6 3 3-3 3m-2.5-9-3 12" />
        </svg>
    );
}

// Adapted from AI-Codebase's plain-text viewer. React escapes repository content.
export default function FileViewer({ selectedFile, isLoading, error, onScrollStateChange }) {
    return (
        <section aria-label="File contents" className="flex h-full min-h-0 min-w-0 flex-col bg-slate-900/90 text-slate-100">
            {selectedFile && (
                <div className="flex h-11 shrink-0 items-center border-b border-sky-300/15 bg-slate-800/90 px-4 sm:px-5">
                    <div className="flex min-w-0 items-center gap-2">
                        <CodeIcon />
                        <h2 className="truncate text-xs font-semibold text-slate-100 sm:text-sm">{selectedFile.path}</h2>
                    </div>
                </div>
            )}

            {isLoading && <p role="status" className="p-6 text-sm text-slate-400">Loading file…</p>}
            {error && <p role="alert" className="p-6 text-sm text-red-300">{error}</p>}
            {!isLoading && !error && !selectedFile && (
                <div className="flex flex-1 items-center justify-center px-8 pb-40 pt-10 text-center">
                    <p className="text-lg font-semibold text-slate-200">Select a file to inspect</p>
                </div>
            )}
            {!isLoading && !error && selectedFile && (
                <div className="min-h-0 flex-1 overflow-auto pb-52" onScroll={event => onScrollStateChange(event.currentTarget.scrollTop > 32)}>
                    {selectedFile.index_note && (
                        <p className="border-b border-white/10 bg-amber-950/20 px-5 py-2 text-xs leading-5 text-amber-100/80">{selectedFile.index_note}</p>
                    )}
                    <pre className="min-w-max p-5 font-mono text-[13px] leading-6 sm:p-6 sm:text-sm"><code>{selectedFile.content}</code></pre>
                </div>
            )}
        </section>
    );
}
