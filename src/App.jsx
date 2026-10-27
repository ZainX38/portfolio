import './input.css'
import Hero from './components/sections/Hero.jsx'
import Projects from './components/sections/Projects.jsx'
import AboutMe from './components/sections/AboutMe.jsx'
import OpenSource from './components/sections/OpenSource.jsx'
import TechStack from './components/sections/TechStack.jsx'
import Navbar from "./components/layout/Navbar.jsx"

function App() {
  return (
    <>
      <Navbar />    
      <main className="
      bg-linear-to-b from-black via-sky-700 to-gray-800 
      text-white font-sans 
      px-14 sm:px-20 lg:px-60 py-20
      max-w-screen min-w-xl min-h-dvh
      ">
        <Hero/>
        <Projects />
        <TechStack />
        <AboutMe />
      </main>
    </> 
  )
}

export default App
