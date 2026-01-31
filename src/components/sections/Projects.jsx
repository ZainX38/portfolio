import Icon from '../Icon.jsx';

function Projects() {
    return (
        <section id="projects" className='mt-30 min-w-4xl'>
            <div className="flex flex-row items-center gap-4">
                <Icon className="w-9 h-9" iconRef="/sprites.svg#projects" />
                <h1 className='text-3xl font-bold'>Projects</h1>
            </div>
        </section>
    );
}

export default Projects;