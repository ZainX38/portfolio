import { useState } from 'react';
import { askQuestion } from '../api.js';

export default function QuestionPanel({ repository, onFileSelect }) {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

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
        <section className="mt-8 overflow-hidden rounded-xl border border-sky-700/70 bg-slate-950/80 shadow-2xl shadow-sky-950/50" aria-labelledby="question-heading">
            <div className="border-b border-slate-700 bg-linear-to-r from-sky-950 to-slate-950 px-5 py-5 sm:px-7">
                <p className="text-xs font-semibold tracking-[0.2em] text-amber-300 uppercase">Ask the codebase</p>
                <h2 id="question-heading" className="mt-1 text-xl font-bold sm:text-2xl">What would you like to understand?</h2>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
                    Ask about a function, file, or implementation detail. Answers include links to the source used.
                </p>
            </div>
            <form onSubmit={submitQuestion} className="p-5 sm:p-7">
                <label htmlFor="question" className="mb-2 block text-sm font-semibold text-slate-100">Question</label>
                {!repository.ai_available && <p id="question-availability" className="mb-3 text-sm text-amber-200">{repository.ai_message}</p>}
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                    <textarea id="question" value={question} onChange={event => setQuestion(event.target.value)} maxLength={repository.max_question_chars || 1000} rows={3}
                        disabled={!repository.ai_available || isLoading} required placeholder="For example: How does Requests handle redirect authentication?"
                        aria-describedby={!repository.ai_available ? 'question-availability' : undefined}
                        className="block min-h-28 w-full resize-y rounded-lg border border-slate-600 bg-slate-900 px-4 py-3 text-base leading-6 text-white shadow-inner placeholder:text-slate-500 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-400/40 disabled:cursor-not-allowed disabled:bg-slate-900/50 disabled:text-slate-500 sm:min-h-24" />
                    <button type="submit" disabled={!repository.ai_available || isLoading || !question.trim()}
                        className="inline-flex min-h-12 shrink-0 items-center justify-center rounded-lg border border-sky-400 bg-sky-800 px-7 py-3 font-semibold text-white transition hover:bg-sky-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300 disabled:cursor-not-allowed disabled:border-slate-700 disabled:bg-slate-800 disabled:text-slate-500 sm:min-w-32">
                        {isLoading ? 'Thinking…' : 'Ask question'}
                    </button>
                </div>
            </form>
            {error && <p role="alert" className="mx-5 mb-5 rounded-lg border border-red-400/40 bg-red-950/70 p-4 text-sm text-red-100 sm:mx-7 sm:mb-7">{error}</p>}
            {answer && <div aria-live="polite" className="mx-5 mb-5 rounded-lg border border-slate-700 bg-black/30 p-5 sm:mx-7 sm:mb-7 sm:p-6">
                <h3 className="text-sm font-semibold tracking-wide text-sky-300 uppercase">Answer</h3>
                <p className="mt-3 whitespace-pre-wrap leading-7 text-slate-100">{answer.answer}</p>
                <h4 className="mt-5 text-sm font-semibold text-slate-300">Sources</h4>
                <ul className="mt-2 flex flex-wrap gap-2">
                    {answer.references.map(reference => <li key={`${reference.path}:${reference.start_line}`}>
                        <button type="button" className="break-all rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-left font-mono text-xs text-sky-300 transition-colors hover:border-sky-400 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300" onClick={() => onFileSelect(reference)}>
                            {reference.path}:{reference.start_line}–{reference.end_line}
                        </button>
                    </li>)}
                </ul>
            </div>}
        </section>
    );
}
