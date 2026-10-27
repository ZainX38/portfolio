import CreateButton from './CreateButton.jsx'
import socialLinks from '../../data/socials.js'
import { contactEmail } from '../../data/navLinks.js'

function Footer() {
    const year = new Date().getFullYear()

    // Email + your existing socials, all in one list
    const links = [
        { name: 'Email', link: `mailto:${contactEmail}`, icon: '/sprites.svg#mail' },
        ...socialLinks,
    ]

    return (
        <footer className="mt-32 pt-8 border-t border-white/10
            flex flex-col sm:flex-row items-center justify-between gap-6
            text-sm text-gray-400">

            <p>© {year} Zain Mohammad. Built with React & Tailwind CSS.</p>

            <div className="flex flex-row items-center gap-3">
                {links.map(link => (
                    <CreateButton
                        key={link.name}
                        name={link.name}
                        link={link.link}
                        icon={link.icon}
                        className="flex flex-row items-center gap-2 px-3 py-1 rounded-full
                        border border-white/20 text-gray-300
                        hover:bg-white hover:text-black transition-colors" />
                ))}
            </div>

            <a href="#hero" className="hover:text-amber-300 transition-colors">
                Back to top ↑
            </a>
        </footer>
    )
}

export default Footer