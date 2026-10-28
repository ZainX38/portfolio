import Icon from '../layout/Icon.jsx';
import techStackData from '../../data/techStack.json';

// Returns the logo as an SVG in the colour you ask for
const iconUrl = (slug) => `https://cdn.simpleicons.org/${slug}/d1d5db`;

function SkillPill({ item }) {
    return (
        <li className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm
            bg-white/5 border border-white/10 text-gray-200
            hover:border-amber-300/50 hover:text-white transition-colors">
            {item.icon && (
                <img
                    src={iconUrl(item.icon)}
                    alt=""
                    className="w-4 h-4"
                    loading="lazy"
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
            )}
            {item.name}
        </li>
    );
}

function TechStack() {
    return (
        <section id="tech-stack" data-section className="mt-20 max-w-5xl">
            <div className="flex flex-row items-center gap-4">
                <Icon className="w-9 h-9" iconRef="#projects-icon" />
                <h1 className="text-3xl font-bold">Tech Stack</h1>
            </div>

            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                {techStackData.map(group => (
                    <div key={group.category}
                        className="rounded-2xl p-5 bg-black/30 border border-white/10">
                        <h2 className="text-xs font-semibold uppercase tracking-widest text-amber-300/80 mb-4">
                            {group.category}
                        </h2>
                        <ul className="flex flex-wrap gap-2">
                            {group.items.map(item => (
                                <SkillPill key={item.name} item={item} />
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </section>
    );
}

export default TechStack;