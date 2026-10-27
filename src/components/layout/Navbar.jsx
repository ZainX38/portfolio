import { useEffect, useEffectEvent, useState } from "react";
import navLinks from "../../data/navLinks";

function Navbar() {
    const [scrolled, setScrolled] = useState(false)
    const [active, setActive] = useState('')
    const [atTop, setAtTop] = useState(true) 
    
    useEffect(() => {
        const onScroll = () => {
            // If user has scrolled over 40px, set scrolled to True
            setScrolled(window.scrollY > 40)
            setAtTop(window.scrollY < 150)  // Keeps Hero highlighted until scrolled > 150px
        }

        onScroll() // Run at the start in case the page loads already scrolled

        // {passive: true} tells the browser this listener never blocks the scroll, which keeps it smooth
        window.addEventListener("scroll", onScroll, {passive: true})

        return () => window.removeEventListener("scroll", onScroll)
    }, [])

    useEffect(() => {
        // Find the actual <section> elements from the ids
        const sections = navLinks
            .map(link => document.getElementById(link.id))
            .filter(Boolean)    // drops any id that doesn't exist on the page
        console.log('Watching sections:', sections.map(s => s.id))

        // Create the observer
        const observer = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        console.log('Active section:', entry.target.id)
                        setActive(entry.target.id)
                    }
                })
            },
            { rootMargin: '-45% 0px -50% 0px' }
        )

        // Start watching each section
        sections.forEach(section => observer.observe(section))

        return () => observer.disconnect()   // cleanup: stop watching
    }, [])

    return (
        // fixed top-0 - removes the header from the page flow and pins it to the top so it's fixed
        // inset-x-0 + flex justify-center - makes header full width and centres pill shape inside it
        // 
        <header className="fixed top-0 inset-x-0 z-50 flex justify-center mt-4 px-4">
            <nav className={`flex items-center gap-1 rounded-full px-2 py-1.5
                text-xs sm:text-sm font-medium border transition-all duration-300
                ${scrolled
                    ? 'bg-slate-950/70 backdrop-blur-md border-white/10 shadow-lg shadow-black/30'
                    : 'bg-transparent border-transparent'}`}>
                {navLinks.map(link => {
                    const current = atTop ? 'hero' : active
                    const isActive = current === link.id
                    return (
                        <a key={link.id}
                            href={`#${link.id}`}
                            aria-current={isActive ? 'true' : undefined}
                            className={`rounded-full px-2 sm:px-3 py-1.5 transition-colors duration-200
                            ${isActive
                                ? 'text-amber-300 bg-amber-300/10 font-semibold'
                                : 'text-gray-300 hover:text-amber-300'}`}>
                            {link.title}
                        </a>
                    )
                })}
            </nav>
        </header>
    )
}

export default Navbar