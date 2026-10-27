import navLinks from "../../data/navLinks";

function Navbar() {
    return (
        // fixed top-0 - removes the header from the page flow and pins it to the top so it's fixed
        // inset-x-0 + flex justify-center - makes header full width and centres pill shape inside it
        // 
        <header className="fixed top-0 inset-x-0 z-50 flex justify-center mt-4 px-4">
            <nav className="flex items-center gap-1 rounded-full px-2 py-1.5
                text-xs sm:text-sm font-medium
                bg-slate-950/70 backdrop-blur-md border border-white/10">
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