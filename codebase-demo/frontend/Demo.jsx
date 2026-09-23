import { useEffect, useState } from 'react';
import { getRepository } from './api.js';
import RepositoryExplorer from './components/RepositoryExplorer.jsx';

export default function Demo() {
    const [repository, setRepository] = useState(null);
    const [error, setError] = useState('');

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
        <main className="min-h-screen bg-linear-to-b from-black via-sky-950 to-slate-900 px-4 py-8 font-sans text-white sm:px-8 lg:px-12 lg:py-12">
            <div className="mx-auto max-w-7xl">
                <a
                    className="inline-flex items-center gap-2 rounded-full border border-slate-600 bg-slate-950/70 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:border-sky-400 hover:bg-sky-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
                    href="/"
                >
                    <span aria-hidden="true">←</span> Back to portfolio
                </a>
                <header className="mt-8 border-b border-slate-700 pb-6 sm:flex sm:items-end sm:justify-between sm:gap-8">
                    <div>
                        <p className="mb-3 text-xs font-semibold tracking-[0.22em] text-sky-300 uppercase">Interactive project</p>
                        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Codebase AI</h1>
                        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">
                            Explore a real repository, inspect its source, and ask questions grounded in the indexed code.
                        </p>
                    </div>
                    {repository && (
                        <div className="mt-5 flex shrink-0 flex-wrap gap-2 text-xs sm:mt-0 sm:max-w-sm sm:justify-end">
                            <span className="rounded-full border border-slate-600 bg-slate-900/80 px-3 py-1.5 font-medium text-slate-200">{repository.repository}</span>
                            <span className="rounded-full border border-slate-600 bg-slate-900/80 px-3 py-1.5 text-slate-300">{repository.branch}</span>
                            <a
                                className="rounded-full border border-sky-700 bg-sky-950 px-3 py-1.5 font-mono text-sky-200 transition-colors hover:border-sky-400 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
                                href={`https://github.com/${repository.repository}/tree/${repository.commit}`}
                                target="_blank"
                                rel="noreferrer"
                            >
                                {repository.commit.slice(0, 7)}
                            </a>
                        </div>
                    )}
                </header>
                {error && <p role="alert" className="mt-8 rounded-xl border border-red-400/40 bg-red-950/60 p-5 text-red-100">{error}</p>}
                {!repository && !error && <p role="status" className="mt-8 rounded-xl border border-slate-700 bg-slate-950/70 p-5 text-slate-300">Loading repository…</p>}
                {repository && <RepositoryExplorer repository={repository} />}
            </div>
        </main>
    );
}
