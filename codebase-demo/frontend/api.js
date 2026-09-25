// Only a public API origin belongs in Vite configuration. Never put keys here.
const apiUrl = `${import.meta.env.VITE_DEMO_API_ORIGIN || ''}/api/demo`;

async function getResponseData(response) {
    if (!response.headers.get('content-type')?.includes('application/json')) {
        throw new Error('Repository service is unavailable. Please try again later.');
    }
    const data = await response.json();
    if (!response.ok) {
        const detail = data.detail;
        const error = new Error(
            typeof detail === 'string'
                ? detail
                : detail?.message || 'The request could not be completed.',
        );
        error.questionsRemaining = data.questions_remaining ?? detail?.questions_remaining;
        throw error;
    }
    return data;
}

export async function getRepository() {
    return getResponseData(await fetch(`${apiUrl}/repository`, { cache: 'no-store', credentials: 'include' }));
}

export async function getContents(snapshotId, path = '') {
    const params = new URLSearchParams({ snapshot_id: snapshotId, path });
    return getResponseData(await fetch(`${apiUrl}/contents?${params}`, { credentials: 'include' }));
}

export async function askQuestion(snapshotId, question) {
    return getResponseData(await fetch(`${apiUrl}/ask`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ snapshot_id: snapshotId, question }),
    }));
}
