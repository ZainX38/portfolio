import { useEffect, useRef, useState } from 'react';
import { getContents } from '../api.js';
import FileViewer from './FileViewer.jsx';
import RepositoryTree from './RepositoryTree.jsx';
import QuestionPanel from './QuestionPanel.jsx';

// Adapted from AI-Codebase: root loading, file caching and stale-response protection.
export default function RepositoryExplorer({ repository }) {
    const [entries, setEntries] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isTreeLoading, setIsTreeLoading] = useState(true);
    const [isFileLoading, setIsFileLoading] = useState(false);
    const [treeError, setTreeError] = useState('');
    const [fileError, setFileError] = useState('');
    const fileCache = useRef(new Map());
    const selectedPath = useRef('');
    const snapshotId = repository.snapshot_id;

    useEffect(() => {
        let isCurrentRequest = true;
        async function loadRepository() {
            try {
                const rootEntries = await getContents(snapshotId);
                if (isCurrentRequest) setEntries(rootEntries);
            } catch (error) {
                if (isCurrentRequest) setTreeError(error.message);
            } finally {
                if (isCurrentRequest) setIsTreeLoading(false);
            }
        }
        loadRepository();
        return () => { isCurrentRequest = false; };
    }, [snapshotId]);

    async function selectFile(entry) {
        selectedPath.current = entry.path;
        setFileError('');
        if (fileCache.current.has(entry.path)) {
            setSelectedFile(fileCache.current.get(entry.path));
            setIsFileLoading(false);
            return;
        }
        setSelectedFile(null);
        setIsFileLoading(true);
        try {
            const file = await getContents(snapshotId, entry.path);
            fileCache.current.set(entry.path, file);
            if (selectedPath.current === entry.path) setSelectedFile(file);
        } catch (error) {
            if (selectedPath.current === entry.path) setFileError(error.message);
        } finally {
            if (selectedPath.current === entry.path) setIsFileLoading(false);
        }
    }

    return (
        <>
            <QuestionPanel repository={repository} onFileSelect={selectFile} />
            <section className="mt-8" aria-labelledby="explorer-heading">
                <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <p className="text-xs font-semibold tracking-[0.2em] text-sky-300 uppercase">Source browser</p>
                        <h2 id="explorer-heading" className="mt-1 text-2xl font-bold">Repository explorer</h2>
                    </div>
                    {repository.coverage && (
                        <p className="text-sm text-slate-400">
                            {repository.coverage.indexed_files} of {repository.coverage.total_files} files indexed
                            {repository.coverage.scope === 'selected' && ' · Configured paths only'}
                        </p>
                    )}
                </div>
                <div className="grid overflow-hidden rounded-xl border border-slate-700 bg-slate-950/80 shadow-2xl shadow-black/30 lg:grid-cols-[300px_minmax(0,1fr)]">
                <RepositoryTree entries={entries} snapshotId={snapshotId} isLoading={isTreeLoading} error={treeError} onFileSelect={selectFile} />
                <FileViewer selectedFile={selectedFile} isLoading={isFileLoading} error={fileError} />
                </div>
            </section>
        </>
    );
}
