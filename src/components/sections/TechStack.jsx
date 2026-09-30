import Icon from '../layout/Icon.jsx';
import techStackData from '../../data/techStack.json';

const hasLogo = ["Python", "Node.js", "Next.js", "React", "TailwindCSS"];
const defaultColor = "bg-gray-700/60";

function TechStack() {
    return (
        <section id="tech-stack" className='mt-20 max-w-5xl'>
            <div className="flex flex-row items-center gap-4">
                <Icon className="w-9 h-9" iconRef="/sprites.svg#about" />
                <h1 className='text-3xl font-bold'>Tech Stack</h1>
            </div>

            <div className='mt-8 border-none rounded-xl px-6 py-2'>
                {techStackData.map((group, index) => (
                    <div key={group.category}
                         className={`flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6 py-4
                         ${index !== techStackData.length - 1 ? 'border-b border-gray-500/40' : ''}`}>

                        <h2 className='text-gray-300 text-sm w-28 shrink-0'>
                            {group.category}
                        </h2>

                        <div className='text-xs flex flex-row flex-wrap gap-2'>
                            {group.items.map(item => (
                                <span key={item}
                                      className={`border-none rounded-full px-2 py-1
                                      flex flex-row items-center gap-2
                                      ${group.colours?.[item] || defaultColor}`}>
                                    {hasLogo.includes(item) && (
                                        <Icon iconRef={`/sprites.svg#${item.toLowerCase()}`}
                                              className="w-4 h-4" />
                                    )}
                                    {item}
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}

export default TechStack;