import { useEffect, useState } from 'react';
import { askQuestion } from '../api.js';

function SendIcon() {
    return (
        <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 fill-none stroke-current stroke-2">
            <path strokeLinecap="round" strokeLinejoin="round" d="m5 12 14-7-4 14-3-6-7-1Zm7 1 7-8" />
        </svg>
    );
}

export default function QuestionPanel({ repository, onFileSelect, isDimmed }) {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0);

    useEffect(() => {
        if (!isLoading) {
            setLoadingStep(0);
            return undefined;
        }
        const timer = window.setInterval(() => {
            setLoadingStep(step => (step + 1) % 4);
        }, 450);
        return () => window.clearInterval(timer);
    }, [isLoading]);

    function handleQuestionKeyDown(event) {
        if (
            event.key === 'Enter'
            && !event.shiftKey
            && !event.nativeEvent.isComposing
            && !isLoading
        ) {
            event.preventDefault();
            event.currentTarget.form?.requestSubmit();
        }
    }

    async function submitQuestion(event) {
        event.preventDefault();
        if (!question.trim() || isLoading || !repository.ai_available) return;
        setIsLoading(true);
        setError('');
        setAnswer(null);
        try {
            setAnswer(await askQuestion(repository.snapshot_id, question.trim()));
        } catch (error) {
            setError(error.message);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <section className="pointer-events-none absolute inset-x-0 bottom-0 z-20 px-3 pb-3 sm:px-5 sm:pb-5" aria-labelledby="question-heading">
            <div className={`pointer-events-auto mx-auto max-w-4xl transition-opacity duration-300 ${isDimmed ? 'opacity-55 hover:opacity-100 focus-within:opacity-100' : 'opacity-100'}`}>
                {(error || answer || isLoading) && (
                    <div aria-live="polite" className="mb-2 max-h-52 overflow-auto rounded-2xl border border-sky-300/20 bg-slate-800/95 p-4 shadow-2xl shadow-slate-950/40 backdrop-blur-xl sm:p-5">
                        {error && <p role="alert" className="text-sm text-red-200">{error}</p>}
                        {isLoading && <p role="status" className="text-sm font-medium text-sky-200">{'loading' + '.'.repeat(loadingStep)}</p>}
                        {answer && (
                            <>
                                <p className="whitespace-pre-wrap text-sm leading-6 text-slate-100">{answer.answer}</p>
                                {answer.references.length > 0 && (
                                    <div className="mt-4 border-t border-white/10 pt-3">
                                        <h3 className="text-xs font-semibold text-sky-300">Sources</h3>
                                        <ul className="mt-2 flex flex-wrap gap-2">
                                            {answer.references.map(reference => (
                                                <li key={`${reference.path}:${reference.start_line}`}>
                                                    <button
                                                        type="button"
                                                        className="break-all rounded-md border border-slate-600 bg-slate-900 px-2.5 py-1.5 text-left text-xs text-sky-200 transition-colors hover:border-sky-400 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300"
                                                        onClick={() => onFileSelect(reference)}
                                                    >
                                                        {reference.path}:{reference.start_line}–{reference.end_line}
                                                    </button>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

                <form onSubmit={submitQuestion} className="rounded-3xl border border-sky-300/35 bg-slate-800/90 p-3 shadow-2xl shadow-slate-950/40 ring-1 ring-white/10 backdrop-blur-xl transition-colors duration-300 focus-within:border-sky-300 focus-within:bg-slate-800/95 focus-within:ring-2 focus-within:ring-sky-300/20 sm:p-4">
                    <label id="question-heading" htmlFor="question" className="sr-only">Ask a question about this repository</label>
                    {!repository.ai_available && <p id="question-availability" className="px-2 pb-2 text-sm text-amber-200">{repository.ai_message}</p>}
                    <div className="flex items-end gap-3">
                        <textarea
                            id="question"
                            value={question}
                            onChange={event => setQuestion(event.target.value)}
                            maxLength={repository.max_question_chars || 1000}
                            rows={2}
                            disabled={!repository.ai_available || isLoading}
                            required
                            onKeyDown={handleQuestionKeyDown}
                            placeholder="Ask a question about the repository…"
                            aria-describedby={!repository.ai_available ? 'question-availability' : undefined}
                            className="max-h-36 min-h-16 w-full resize-none bg-transparent px-2 py-2 text-sm leading-6 text-white outline-none placeholder:text-slate-500 disabled:cursor-not-allowed disabled:text-slate-500 sm:text-base"
                        />
                        <button
                            type="submit"
                            disabled={!repository.ai_available || isLoading || !question.trim()}
                            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-sky-300/70 bg-sky-700 text-white shadow-md transition duration-200 hover:bg-white hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-300 disabled:cursor-not-allowed disabled:border-slate-600 disabled:bg-slate-700 disabled:text-slate-400"
                            aria-label={isLoading ? 'Sending question' : 'Send question'}
                        >
                            <SendIcon />
                        </button>
                    </div>
                </form>
                <p className="mt-2 text-center text-[11px] text-slate-500">Answers are grounded in the indexed repository.</p>
            </div>
        </section>
    );
}
