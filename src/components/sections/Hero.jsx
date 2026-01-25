import heroImage from '../../assets/images/zain.webp';

function Hero() {
    const buttonData = [{
            name: 'GitHub', 
            link: 'github.com',
            icon: '/sprites.svg#github'
        }, {
            name: 'LinkedIn',
            link: 'linkedin.com',
            icon: '/sprites.svg#linkedin'
        }];

    return (
        <section>
            <div className="flex flex-row items-center gap-10 mb-4">
                <img src={heroImage} alt="Hero Image" className="
                w-20 h-20 object-cover rounded-full
                "></img>
                <a href="#" className="rounded-4xl border border-white px-2 py-1 text-xs">
                    Available for internships
                </a>
            </div>

            <h1 className="text-4xl font-bold mb-4">Hey, I'm Zain</h1>

            <p className="text-lg max-w-3xl mb-4">
                I’m a first-year Computer Science student building <span className='font-bold text-amber-300'> full-stack web applications and exploring AI-powered solutions </span>to solve real problems.
                I’m actively seeking software engineering internships where I can contribute, learn, and grow.
            </p>
            
            <div className='flex flex-row gap-4'>
                {buttonData.map(button => {
                    return (
                        <a key={button.name} href={button.link} 
                        className="
                        text-md px-2 py-1 border rounded-full cursor-pointer bg-sky-900
                        hover:bg-white hover:text-black hover:scale-110
                        transition-transform flex flex-row items-center gap-2">
                            <svg className="w-4 h-4">
                                <use href={button.icon} />
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