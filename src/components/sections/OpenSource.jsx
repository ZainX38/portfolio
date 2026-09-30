import Icon from '../layout/Icon.jsx';
import openSourceData from '../../data/openSource.json';

function OpenSource() {
    return (
        <section id="open-source" className='mt-20 max-w-5xl'>
            <div className="flex flex-row items-center gap-4">
                <Icon className="w-9 h-9" iconRef="/sprites.svg#github" />
                <h1 className='text-3xl font-bold'>Open Source</h1>
            </div>

            <div className='flex flex-row flex-wrap gap-5 mt-8'>
                {openSourceData.map(item => (
                    <a key={item.id}
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ '--accent': item.accent }}
                    className='group relative w-64 h-72 flex flex-col justify-between
                    rounded-2xl p-6 overflow-hidden
                    bg-black/40 border border-white/10
                    hover:border-[var(--accent)] transition-colors duration-500'>

                        <div className='absolute -top-16 -right-16 w-40 h-40 rounded-full blur-3xl opacity-30
                        group-hover:opacity-60 transition-opacity duration-700'
                            style={{ backgroundColor: 'var(--accent)' }} />

                        <div className='relative'>
                            <span className='text-5xl font-bold leading-none'
                                style={{ color: 'var(--accent)' }}>
                                {item.name.charAt(0)}
                            </span>
                            <h2 className='font-semibold text-xl mt-4'>{item.name}</h2>
                            <p className='text-gray-400 text-sm'>{item.tagline}</p>
                        </div>

                        <p className='relative text-gray-200 text-sm leading-relaxed'>
                            {item.description}
                        </p>

                        <div className='relative flex flex-row items-center justify-between text-xs'>
                            <span className='flex items-center gap-2 text-gray-300'>
                                <span className='w-2 h-2 rounded-full'
                                    style={{ backgroundColor: 'var(--accent)' }} />
                                {item.contributionType  }
                            </span>
                            <span className='text-gray-400'>
                                {item.contributions} merged
                            </span>
                        </div>
                    </a>
                ))}
            </div>
        </section>
    );
}

export default OpenSource;