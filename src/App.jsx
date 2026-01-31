import './input.css'
import Hero from './components/sections/Hero.jsx'
import Projects from './components/sections/Projects.jsx'

function App() {
  return (
    <main className="
    bg-linear-to-b from-black via-sky-700 to-gray-800 
    text-white font-sans 
    px-18 sm:px-20 md:px-28 lg:px-60 py-20
    max-w-screen min-w-xl min-h-dvh
    ">
      <Hero/>
      <Projects />
    </main>
    
  )
}

export default App
