import heroImage from '../../assets/images/zain.webp';

function GlowingBadge({ children }) {
    return (
        <div className="relative overflow-hidden rounded-full p-px text-xs">
            {/*Creates Animation with moving gradient*/}
            <span className="
            absolute inset-[-1000%] animate-[spin_2s_linear_infinite]
            bg-[conic-gradient(from_90deg_at_50%_50%,#E2CBFF_0%,#393BB2_50%,#E2CBFF_100%)]"/>
            {/*MASK - covers centre so only border is shown*/}
            <span className='
            inline-flex h-full w-full items-center justify-center rounded-full
            bg-slate-950 px-3 py-1 font-medium text-white backdrop-blur-3xl'>
                {children}
            </span>
        </div>
    )
}

function Hero() {
    const buttonData = [{
            name: 'GitHub', 
            link: 'https://github.com/ZainX38',
            icon: '/sprites.svg#github'
        }, {
            name: 'LinkedIn',
            link: 'https://www.linkedin.com/in/zain-mohammad-283774227/',
            icon: '/sprites.svg#linkedin'
        }];

    return (
        <section id="hero" className='max-w-5xl mx-auto px-4'>
            <div className="flex flex-row items-center gap-10 mb-4">
                <img src={heroImage} alt="Hero Image" className="
                w-14 h-14 sm:w-20 sm:h-20 object-cover rounded-full"/>
                
                <GlowingBadge>
                    Available for internships
                </GlowingBadge>
            </div>

            <h1 className="text-xl sm:text-3xl font-bold leading-tight mb-4">Hey, I'm Zain</h1>

            <p className="text-sm md:text-lg min-w-44 mb-4 text-balance">
                I’m a first-year Computer Science student building <span className='font-bold text-amber-300'> full-stack web applications and exploring AI-powered solutions </span>to solve real problems.
                I’m actively seeking software engineering internships where I can contribute, learn, and grow.
            </p>
            
            <div className='flex flex-row gap-4'>
                {buttonData.map(button => {
                    return (
                        <a 
                        key={button.name} 
                        href={button.link} 
                        target='_blank'
                        rel="noopener noreferrer"
                        className="
                        text-sm md:text-md px-2 py-1 border rounded-full cursor-pointer bg-sky-900
                        hover:bg-white hover:text-black hover:scale-110
                        transition-transform flex flex-row items-center gap-2">
                            <svg aria-hidden="true" 
                            className={button.name === 'GitHub' ? "w-4 h-4" : "w-6 h-6 pt-1"}>
                                <use href={button.icon}/>
                            </svg>
                            {button.name}
                        </a>
                    )
                })}
            </div>
        </section>
    )
}

export default Hero