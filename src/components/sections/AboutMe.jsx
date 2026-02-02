import Icon from "../layout/Icon"
import zainImage from '/images/zain3.jpg';

function AboutMe() {
    return (
        <section id="aboutme" className="text-white pb-50">
            <div className="flex flex-row items-center gap-4 mb-4">
                <Icon iconRef="/sprites.svg#about" className="w-8 h-8" />
                <h1 className="text-3xl font-bold">About Me</h1>
            </div>

            <div className="grid grid-cols-5 text-balanced leading-7">
                <div className="col-span-4 mr-24 flex flex-col gap-4">
                <p>
                    I'm Zain Mohammad and I started programming with Arduinos, when I was 12 years old. Now, I am first year Computer Science student who is
                    experimenting with different technologies and building projects.
                </p>
                <p>
                Some of my achievements include building
                <span className='text-amber-200'> full-stack web applications and AI-powered projects, </span>
                such as an end-to-end RAG retrieval system and an AI-enhanced recipe platform, combining practical engineering with innovative problem-solving. 
                </p>
                <p>
                Through my work, I aim to build real-world solutions, deepen my understanding of software development, and contribute to meaningful projects. 
                My goal is to secure software engineering internships where I can continue growing, apply my skills, and make a tangible impact.
                </p>
                </div>
                <div className="col-span-1 flex justify-center items-center">
                <img src={zainImage} className="
                w-44 bg-black/40 border border-gray-500 p-2 rounded-2xl rotate-6
                "></img>
                </div>
            </div>

        </section>
    )
}

export default AboutMe