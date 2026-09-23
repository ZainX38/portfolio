import { useState } from 'react';
import { getContents } from '../api.js';
import { sortEntries } from '../utils/sortEntries.js';

// Adapted from AI-Codebase: each FileTree renders one level of the directory.
function FileTree({ entries, snapshotId, level, onFileSelect }) {
    return (
        <ul>
            {sortEntries(entries).map(entry => entry.type === 'dir' ? (
                <Folder key={entry.path} entry={entry} snapshotId={snapshotId} level={level} onFileSelect={onFileSelect} />
            ) : (
                <li key={entry.path}>
                    <button type="button" onClick={() => onFileSelect(entry)} title={entry.unavailable || entry.path}
                        className="w-full truncate rounded-md py-2 pr-3 text-left font-mono text-xs text-slate-300 transition-colors hover:bg-sky-900/60 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-sky-300 disabled:text-slate-600"
                        style={{ paddingLeft: `${level * 16 + 24}px` }}>
                        {entry.name}{entry.unavailable ? ' (unavailable)' : ''}
                    </button>
                </li>
            ))}
        </ul>
    );
}

function Folder({ entry, snapshotId, level, onFileSelect }) {
    const [isExpanded, setIsExpanded] = useState(false);
    // null means not loaded; [] means loaded and empty. Collapsing keeps the cache.
    const [entries, setEntries] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    async function toggleFolder() {
        if (isExpanded) {
            setIsExpanded(false);
            return;
        }
        setIsExpanded(true);
        if (entries || isLoading) return;
        setIsLoading(true);
        setError('');
        try {
            setEntries(await getContents(snapshotId, entry.path));
        } catch (error) {
            setError(error.message);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <li>
            <button type="button" onClick={toggleFolder} aria-expanded={isExpanded} title={entry.path}
                className="w-full truncate rounded-md py-2 pr-3 text-left text-sm font-medium text-slate-200 transition-colors hover:bg-sky-900/60 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-sky-300"
                style={{ paddingLeft: `${level * 16 + 8}px` }}>
                <span aria-hidden="true">{isExpanded ? '▾' : '▸'} </span>{entry.name}
            </button>
            {isExpanded && isLoading && <p className="px-4 py-1 text-xs text-slate-400">Loading…</p>}
            {isExpanded && error && <p role="alert" className="px-4 py-1 text-xs text-red-300">{error}</p>}
            {isExpanded && entries && <FileTree entries={entries} snapshotId={snapshotId} level={level + 1} onFileSelect={onFileSelect} />}
        </li>
    );
}

export default function RepositoryTree({ entries, snapshotId, isLoading, error, onFileSelect }) {
    return (
        <aside aria-label="Repository files" className="max-h-80 overflow-auto border-b border-slate-700 bg-slate-900/90 p-3 lg:max-h-[65vh] lg:min-h-[32rem] lg:border-r lg:border-b-0">
            <h3 className="sticky top-0 z-10 border-b border-slate-700 bg-slate-900 px-2 py-3 text-sm font-semibold tracking-wide text-white uppercase">Repository files</h3>
            {isLoading && <p role="status" className="p-3 text-sm text-slate-400">Loading files…</p>}
            {error && <p role="alert" className="p-3 text-sm text-red-300">{error}</p>}
            {!isLoading && !error && <FileTree entries={entries} snapshotId={snapshotId} level={0} onFileSelect={onFileSelect} />}
        </aside>
    );
}
