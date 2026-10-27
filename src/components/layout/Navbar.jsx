import { useEffect, useEffectEvent, useState } from "react";
import navLinks from "../../data/navLinks";

function Navbar() {
    const [scrolled, setScrolled] = useState(false)
    
    useEffect(() => {
        const onScroll = () => {
            // If user has scrolled over 40px, set scrolled to True
            setScrolled(window.scrollY > 40)
        }

        onScroll() // Run at the start in case the page loads already scrolled

        // {passive: true} tells the browser this listener never blocks the scroll, which keeps it smooth
        window.addEventListener("scroll", onScroll, {passive: true})

        return () => window.removeEventListener("scroll", onScroll)
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
                {navLinks.map(link => (
                    <a key={link.id}
                        href={`#${link.id}`}
                        className="rounded-full px-2 sm:px-3 py-1.5 text-gray-300
                        hover:text-amber-300 transition-colors">
                        {link.title}
                    </a>
                ))}
            </nav>
        </header>
    )
}

export default Navbar