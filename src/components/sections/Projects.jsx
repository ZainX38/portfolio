import Icon from '../Icon.jsx';
import projectsData from '../../data/projects.json';

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
                        <img src={project.image} alt="Project Image" className='
                        w-full h-full object-cover scale-105 rounded-tl-lg shadow-2xl shadow-black/40
                        group-hover:scale-110 transition-transform ease-in-out duration-700'/>
                    </div>
                    <div>
                        <h2 className='text-2xl font-semibold mt-4'>{project.title}</h2>
                        <span>{project.tech}</span>
                        <p className='text-md mt-2'>
                            {project.description}
                        </p>
                        <button className="">
                            <a href={project.links.github} target="_blank" rel="noopener noreferrer">Code</a>
                        </button>
                        <button className="">
                            <a href={project.links.preview} target="_blank" rel="noopener noreferrer">Preview</a>
                        </button>
                    </div>
                </div>
                )
            })}
        </section>
    );
}

export default Projects;