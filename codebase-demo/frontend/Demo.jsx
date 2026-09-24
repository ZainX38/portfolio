import { useEffect, useState } from 'react';
import { getRepository } from './api.js';
import RepositoryExplorer from './components/RepositoryExplorer.jsx';

function HomeIcon() {
    return (
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 fill-none stroke-current stroke-2">
            <path strokeLinecap="round" strokeLinejoin="round" d="m3 11 9-8 9 8M5.5 9.5V21h13V9.5M9.5 21v-6h5v6" />
        </svg>
    );
}

export default function Demo() {
    const [repository, setRepository] = useState(null);
    const [error, setError] = useState('');
    const topControlClass = 'inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-sky-400/40 bg-slate-800/90 px-4 text-sm font-semibold text-slate-100 shadow-md shadow-black/15 transition-colors hover:border-sky-300 hover:bg-sky-800 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300';

    useEffect(() => {
        let isCurrentRequest = true;
        getRepository().then(data => {
            if (isCurrentRequest) setRepository(data);
        }).catch(error => {
            if (isCurrentRequest) setError(error.message);
        });
        return () => { isCurrentRequest = false; };
    }, []);

    return (
        <main className="flex min-h-dvh flex-col bg-linear-to-br from-slate-900 via-sky-900 to-slate-800 font-sans text-white lg:h-dvh lg:overflow-hidden">
            <header className="flex shrink-0 items-center justify-between gap-4 border-b border-sky-300/20 bg-slate-900/85 px-4 py-3 shadow-sm backdrop-blur-xl sm:px-6 lg:px-8">
                <div className="min-w-0 flex-1">
                    <h1 className="truncate text-lg font-bold tracking-tight sm:text-xl">Codebase AI</h1>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                    {repository && (
                        <div className="hidden items-center gap-2 md:flex" aria-label="Repository details">
                            <span className={topControlClass}>
                                {repository.branch}
                            </span>
                            <a
                                className={`${topControlClass} hidden max-w-52 truncate lg:inline-flex`}
                                href={`https://github.com/${repository.repository}`}
                                target="_blank"
                                rel="noreferrer"
                                aria-label={`View ${repository.repository} on GitHub`}
                            >
                                {repository.repository}
                            </a>
                        </div>
                    )}
                    <a
                        className={topControlClass}
                        href="/"
                        aria-label="Return to portfolio home page"
                    >
                        <span className="hidden sm:inline">Portfolio</span>
                        <HomeIcon />
                    </a>
                </div>
            </header>

            <div className="flex min-h-0 flex-1 flex-col px-3 py-3 sm:px-5 sm:py-5 lg:px-6">
                {error && <p role="alert" className="mx-auto mt-8 w-full max-w-3xl rounded-xl border border-red-400/40 bg-red-950/70 p-5 text-red-100">{error}</p>}
                {!repository && !error && (
                    <div role="status" className="m-auto flex items-center gap-3 rounded-full border border-white/10 bg-slate-950/70 px-5 py-3 text-sm text-slate-300 shadow-xl">
                        <span className="h-2 w-2 animate-pulse rounded-full bg-amber-300" />
                        Loading repository…
                    </div>
                )}
                {repository && <RepositoryExplorer repository={repository} />}
            </div>
        </main>
    );
}
