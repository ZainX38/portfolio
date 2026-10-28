import Icon from '../layout/Icon.jsx'
import ExperienceItem from '../layout/ExperienceItem.jsx'
import experienceData from '../../data/experience.json'

function Experience() {
    return (
        <section id="experience" className="mt-20 max-w-5xl">
            <div className="flex flex-row items-center gap-4">
                <Icon className="w-9 h-9" iconRef="#projects-icon" />
                <h1 className="text-3xl font-bold">Experience</h1>
            </div>

            {/* The vertical timeline line */}
            <ol className="relative mt-10 ml-3 border-l-2 border-white/15">
                {experienceData.map(item => (
                    <ExperienceItem key={item.id} item={item} />
                ))}
            </ol>
        </section>
    )
}

export default Experience