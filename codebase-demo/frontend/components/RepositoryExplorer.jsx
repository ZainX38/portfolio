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
    const [isFileScrolling, setIsFileScrolling] = useState(false);
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
        setIsFileScrolling(false);
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
        <section className="mx-auto flex min-h-0 w-full max-w-[1600px] flex-1 flex-col" aria-label="Codebase workspace">
            <div className="mb-3 flex items-center justify-between gap-4 px-1 text-xs text-slate-300">
                <p className="font-semibold tracking-wide text-sky-200">Repository Explorer</p>
                {repository.coverage && (
                    <p className="text-right">
                        <span className="font-medium text-slate-200">{repository.coverage.indexed_files}</span> of {repository.coverage.total_files} files indexed
                        {repository.coverage.scope === 'selected' && ' · configured paths'}
                    </p>
                )}
            </div>

            <div className="grid min-h-0 flex-1 overflow-hidden rounded-2xl border border-sky-300/25 bg-slate-800/80 shadow-2xl shadow-slate-950/35 backdrop-blur-sm lg:grid-cols-[280px_minmax(0,1fr)]">
                <RepositoryTree
                    entries={entries}
                    snapshotId={snapshotId}
                    isLoading={isTreeLoading}
                    error={treeError}
                    onFileSelect={selectFile}
                    selectedPath={selectedFile?.path}
                />
                <div className="relative min-h-[36rem] min-w-0 lg:min-h-0">
                    <FileViewer selectedFile={selectedFile} isLoading={isFileLoading} error={fileError} onScrollStateChange={setIsFileScrolling} />
                    <QuestionPanel repository={repository} onFileSelect={selectFile} isDimmed={isFileScrolling} />
                </div>
            </div>
        </section>
    );
}
