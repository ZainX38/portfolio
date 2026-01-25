import React from 'react';

function Hero() {
    return (
        <section>
            <div className="flex flex-row items-center gap-10 mb-4">
                <img src="/src/assets/images/zain.webp" alt="Hero Image" className="
                w-20 h-20 object-cover rounded-full
                "></img>
                <a href="#" className="rounded-4xl border border-white px-2 py-1 text-xs">
                    Available for internships
                </a>
            </div>

            <h1 className="text-4xl font-bold mb-4">Hey, I'm Zain</h1>

            <p className="text-lg max-w-3xl">
                I’m a first-year Computer Science student building <span className='font-bold text-amber-300'> full-stack web applications and exploring AI-powered solutions </span>to solve real problems.
                I’m actively seeking software engineering internships where I can contribute, learn, and grow.
            </p>
            
            <div className='flex flex-row gap-4'>
                <a>GitHub</a>
                <a>LinkedIn</a>
            </div>
        </section>
    )
}

export default Hero