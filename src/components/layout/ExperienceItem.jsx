function ExperienceItem({ item }) {
    return (
        <li data-section className="relative ml-8 pb-12 last:pb-0">

            {/* The dot on the timeline line */}
            <span className="absolute -left-[39px] top-1.5 flex size-3.5 items-center justify-center"
                aria-hidden="true">
                {item.current && (
                    <span className="absolute inline-flex size-full rounded-full bg-amber-300/50
                        animate-ping motion-reduce:animate-none" />
                )}
                <span className={`relative inline-flex size-2.5 rounded-full bg-amber-300
                    ${item.current ? 'shadow-[0_0_8px_2px_rgba(252,211,77,0.5)]' : ''}`} />
            </span>

            <div className="grid gap-4 md:grid-cols-5 md:gap-10">

                {/* Left: title, company, date */}
                <div className="md:col-span-2">
                    <h3 className="text-xl font-bold text-amber-300">{item.title}</h3>
                    <h4 className="text-lg font-semibold text-white">{item.company}</h4>
                    <time className="text-sm text-gray-400">{item.date}</time>
                </div>

                {/* Right: description, highlights, tech */}
                <div className="md:col-span-3 flex flex-col gap-3 text-gray-200">
                    <p>{item.description}</p>

                    <ul className="list-disc pl-5 space-y-1.5 marker:text-amber-300">
                        {item.highlights.map(point => (
                            <li key={point}>{point}</li>
                        ))}
                    </ul>

                    <div className="flex flex-wrap gap-2 text-xs mt-1">
                        {item.tech.map(t => (
                            <span key={t} className="rounded-full px-2 py-1 bg-white/10">{t}</span>
                        ))}
                    </div>
                </div>
            </div>
        </li>
    )
}

export default ExperienceItem