// Adapted from AI-Codebase's plain-text viewer. React escapes repository content.
export default function FileViewer({ selectedFile, isLoading, error }) {
    return (
        <section aria-label="File contents" className="min-h-96 min-w-0 bg-[#020617] text-slate-200 lg:min-h-[32rem]">
            {isLoading && <p role="status" className="p-6 text-slate-400">Loading file…</p>}
            {error && <p role="alert" className="p-6 text-red-300">{error}</p>}
            {!isLoading && !error && !selectedFile && (
                <div className="flex min-h-96 items-center justify-center p-8 text-center lg:min-h-[32rem]">
                    <div>
                        <p className="text-lg font-semibold text-slate-200">Select a file to inspect</p>
                        <p className="mt-2 text-sm text-slate-500">Choose any available file from the repository tree.</p>
                    </div>
                </div>
            )}
            {!isLoading && !error && selectedFile && (
                <>
                    <div className="sticky top-0 border-b border-slate-700 bg-slate-900 px-5 py-4 sm:px-6">
                        <h3 className="break-all font-mono text-sm font-semibold text-slate-100">{selectedFile.path}</h3>
                        {selectedFile.index_note && <p className="mt-2 text-xs leading-5 text-slate-400">{selectedFile.index_note}</p>}
                    </div>
                    <pre className="max-h-[65vh] overflow-auto p-5 font-mono text-[13px] leading-6 sm:p-6 sm:text-sm"><code>{selectedFile.content}</code></pre>
                </>
            )}
        </section>
    );
}
