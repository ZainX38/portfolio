import './input.css'
import Hero from './components/sections/Hero.jsx'
import Projects from './components/sections/Projects.jsx'
import AboutMe from './components/sections/AboutMe.jsx'
import OpenSource from './components/sections/OpenSource.jsx'
import TechStack from './components/sections/TechStack.jsx'
import Navbar from "./components/layout/Navbar.jsx"
import Footer from './components/layout/Footer.jsx'
import SpriteSheet from './components/layout/SpriteSheet.jsx'
import Experience from './components/sections/Experience.jsx'

function App() {
  return (
    <>
      <SpriteSheet />
      <Navbar />    
      <main className="
      bg-linear-to-b from-black via-sky-700 to-gray-800 
      text-white font-sans 
      px-14 sm:px-20 lg:px-60 py-20
      max-w-screen min-h-dvh
      ">
        <Hero/>
        <Experience />
        <Projects />
        <TechStack />
        <AboutMe />
        <Footer />
      </main>
    </> 
  )
}

export default App
