import { useState } from 'react';
import { getContents } from '../api.js';
import { sortEntries } from '../utils/sortEntries.js';

function ChevronIcon({ expanded }) {
    return (
        <svg aria-hidden="true" viewBox="0 0 20 20" className={`h-3.5 w-3.5 shrink-0 fill-current transition-transform ${expanded ? 'rotate-90' : ''}`}>
            <path d="m7.2 4.5 5.5 5.5-5.5 5.5 1.4 1.4 6.9-6.9-6.9-6.9-1.4 1.4Z" />
        </svg>
    );
}

function FolderIcon({ open = false }) {
    return (
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 shrink-0 fill-none stroke-current stroke-[1.7] text-sky-300">
            <path strokeLinecap="round" strokeLinejoin="round" d={open ? 'M3 7.5h6l2 2h10l-2 9H5l-2-11Z' : 'M3 6h6l2 2h10v10H3V6Z'} />
        </svg>
    );
}

function FileIcon() {
    return (
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4 shrink-0 fill-none stroke-current stroke-[1.7] text-slate-400">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 3h8l4 4v14H6V3Zm8 0v5h4M9 12h6M9 16h6" />
        </svg>
    );
}

function FileTree({ entries, snapshotId, level, onFileSelect, selectedPath }) {
    return (
        <ul>
            {sortEntries(entries).map(entry => entry.type === 'dir' ? (
                <Folder key={entry.path} entry={entry} snapshotId={snapshotId} level={level} onFileSelect={onFileSelect} selectedPath={selectedPath} />
            ) : (
                <li key={entry.path}>
                    <button
                        type="button"
                        onClick={() => onFileSelect(entry)}
                        title={entry.unavailable || entry.path}
                        aria-current={selectedPath === entry.path ? 'true' : undefined}
                        className={`flex w-full items-center gap-2 truncate rounded-md py-1.5 pr-3 text-left text-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-amber-300 ${selectedPath === entry.path ? 'bg-sky-700/80 text-white' : entry.unavailable ? 'text-slate-500 hover:bg-slate-700/60 hover:text-slate-300' : 'text-slate-200 hover:bg-slate-700/70 hover:text-white'}`}
                        style={{ paddingLeft: `${level * 14 + 26}px` }}
                    >
                        <FileIcon />
                        <span className="truncate">{entry.name}{entry.unavailable ? ' (unavailable)' : ''}</span>
                    </button>
                </li>
            ))}
        </ul>
    );
}

function Folder({ entry, snapshotId, level, onFileSelect, selectedPath }) {
    const [isExpanded, setIsExpanded] = useState(false);
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
            <button
                type="button"
                onClick={toggleFolder}
                aria-expanded={isExpanded}
                title={entry.path}
                className="flex w-full items-center gap-1.5 truncate rounded-md py-1.5 pr-3 text-left text-sm font-medium text-slate-100 transition-colors hover:bg-slate-700/70 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-amber-300"
                style={{ paddingLeft: `${level * 14 + 8}px` }}
            >
                <ChevronIcon expanded={isExpanded} />
                <FolderIcon open={isExpanded} />
                <span className="truncate">{entry.name}</span>
            </button>
            {isExpanded && isLoading && <p className="px-8 py-1 text-xs text-slate-500">Loading…</p>}
            {isExpanded && error && <p role="alert" className="px-8 py-1 text-xs text-red-300">{error}</p>}
            {isExpanded && entries && (
                <FileTree entries={entries} snapshotId={snapshotId} level={level + 1} onFileSelect={onFileSelect} selectedPath={selectedPath} />
            )}
        </li>
    );
}

export default function RepositoryTree({ entries, snapshotId, isLoading, error, onFileSelect, selectedPath }) {
    return (
        <aside aria-label="Repository files" className="max-h-72 overflow-auto border-b border-sky-300/15 bg-slate-800/85 lg:max-h-none lg:min-h-0 lg:border-r lg:border-b-0">
            <div className="sticky top-0 z-10 flex items-center gap-2 border-b border-sky-300/15 bg-slate-800/95 px-4 py-3 backdrop-blur">
                <FolderIcon open />
                <h2 className="text-sm font-bold text-slate-200">Explorer</h2>
            </div>
            <div className="p-2">
                {isLoading && <p role="status" className="p-3 text-sm text-slate-400">Loading files…</p>}
                {error && <p role="alert" className="p-3 text-sm text-red-300">{error}</p>}
                {!isLoading && !error && <FileTree entries={entries} snapshotId={snapshotId} level={0} onFileSelect={onFileSelect} selectedPath={selectedPath} />}
            </div>
        </aside>
    );
}
