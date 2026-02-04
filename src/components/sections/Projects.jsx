import Icon from '../layout/Icon.jsx';
import projectsData from '../../data/projects.json';
import CreateButton from '../layout/createButton.jsx';
import projectsButton from '../../data/projectsButton.js';

const projectsButtonData = projectsButton
const hasLogo = ["Python", "Node.js", "Next.js", "React", "TailwindCSS"]
const defaultColor = "bg-gray-700/60"

function DisplayTech({ project }) {
    return (
        <>
            {project.tech.map((tech, index) => {
                const colorClass = project.colours[tech] || defaultColor;

                return (
                    <span key={index} 
                    className={`border-none rounded-full px-2 py-1 flex flex-row items-center gap-2 ${colorClass}`}>
                            {(hasLogo.includes(tech)) && (
                                <Icon 
                                iconRef={`/sprites.svg#${tech.toLowerCase()}`} 
                                className="w-4 h-4" />
                            )}
                        {tech}
                    </span>
                )
            })}
        </>
    )
}

function Projects() {
    return (
        <section id="projects" className='mt-40 max-w-5xl'>
            <div className="flex flex-row items-center gap-4">
                <Icon className="w-9 h-9" iconRef="/sprites.svg#projects" />
                <h1 className='text-3xl font-bold'>Projects</h1>
            </div>

            {projectsData.map(project => {
                return (
                <div key={project.id} className="flex flex-col md:flex-row justify-center items-center gap-4 mt-6 mb-16 group">
                    <div className='border border-gray-500
                    inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(0,0,0,0.8))] 
                    rounded-xl min-w-1/2 w-fit md:w-1/2 h-56 sm:h-64 overflow-hidden pl-10 pt-4'>
                        <img 
                        src={project.image} 
                        alt={project.title} 
                        className='
                        w-fit sm:w-full h-full object-cover scale-105 rounded-tl-lg shadow-2xl shadow-black/40
                        group-hover:scale-110 transition-transform ease-in-out duration-700'/>
                    </div>

                    <div className='w-fit md:w-1/2 flex flex-col gap-4 px-8 md:px-4'>
                        <h2 className='font-semibold text-2xl'>{project.title}</h2>

                        <div className='text-xs flex flex-row flex-wrap gap-2'>
                            <DisplayTech project={project} />
                        </div>

                        <p className='text-gray-200 text-balance text-mdA md:text-lg'>
                            {project.description}
                        </p>

                        <div className='flex flex-row mt-4'>
                            {projectsButtonData.map(button => {
                                return <CreateButton key={button.name} name={button.name} link={project.links[button.link]} icon={button.icon} className="
                                w-28 rounded-xl bg-sky-900 px-4 py-2 mr-4 cursor-pointer
                                border border-gray-300
                                flex flex-row items-center justify-center gap-2" />
                            })}                            
                        </div>
                    </div>
                </div>
                )
            })}
        </section>
    );
}

export default Projects;