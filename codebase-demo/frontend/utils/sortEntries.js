// Adapted from AI-Codebase's explorer: sort a copy, directories first, then A–Z.
export function sortEntries(entries) {
    return [...entries].sort((firstEntry, secondEntry) => {
        if (firstEntry.type === secondEntry.type) {
            return firstEntry.name.localeCompare(secondEntry.name);
        }
        return firstEntry.type === 'dir' ? -1 : 1;
    });
}
