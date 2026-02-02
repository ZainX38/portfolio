import Icon from '../layout/Icon.jsx';
import projectsData from '../../data/projects.json';
import CreateButton from '../layout/createButton.jsx';

function Projects() {
    return (
        <section id="projects" className='mt-30 min-w-4xl'>
            <div className="flex flex-row items-center gap-4">
                <Icon className="w-9 h-9" iconRef="/sprites.svg#projects" />
                <h1 className='text-3xl font-bold'>Projects</h1>
            </div>

            {projectsData.map(project => {
                return (
                <div className="grid grid-cols-2 gap-10 mt-6 mb-16 group">
                    <div className='border border-gray-500
                    inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(0,0,0,0.8))] 
                    rounded-xl w-fit h-56 sm:h-64 overflow-hidden pl-10 pt-4'>
                        <img 
                        src={project.image} 
                        alt={project.title} 
                        className='
                        w-full h-full object-cover scale-105 rounded-tl-lg shadow-2xl shadow-black/40
                        group-hover:scale-110 transition-transform ease-in-out duration-700'/>
                    </div>

                    <div className='flex flex-col gap-4'>
                        <h2 className='font-semibold text-2xl'>{project.title}</h2>

                        <div>
                            <span>{project.tech}</span>
                        </div>

                        <p className='text-gray-200'>
                            {project.description}
                        </p>

                        <div className='flex flex-row mt-4'>
                            <CreateButton name="Code" link={project.links.github} icon="/sprites.svg#github" className='
                            w-28 rounded-xl bg-sky-900 px-4 py-2 mr-4 cursor-pointer
                            border border-gray-300
                            flex flex-row items-center justify-center gap-2'/>
                            <CreateButton name="Preview" link={project.links.preview} icon="/sprites.svg#preview" className='
                            w-28 rounded-xl bg-sky-900 px-4 py-2 mr-4 cursor-pointer
                            border border-gray-300
                            flex flex-row items-center justify-center gap-2' />
                        </div>
                    </div>
                </div>
                )
            })}
        </section>
    );
}

export default Projects;