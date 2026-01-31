
import React from "react"
import { FaPlay, FaStepBackward, FaStepForward, FaExpand } from "react-icons/fa"

interface Props {
  slides: string[]
}

/**
 * Sanitize HTML to prevent XSS attacks
 * Removes script tags, event handlers, and dangerous attributes
 */
function sanitizeHTML(html: string): string {
  // Create a temporary div to parse HTML
  const temp = document.createElement('div')
  temp.textContent = html // This escapes all HTML
  
  // If you need to support some safe HTML tags, use a proper sanitization library
  // For now, we'll escape everything to be safe
  return temp.innerHTML
}

const PresentationViewer: React.FC<Props> = ({ slides }) => {
  const [current, setCurrent] = React.useState(0)
  
  // Sanitize the slide content before rendering
  const sanitizedSlide = React.useMemo(
    () => sanitizeHTML(slides[current] || ''),
    [slides, current]
  )

  const toolbar = (
    <div className="flex items-center gap-2 p-2 rounded-t-lg border-b" style={{ background: "#D83B01", borderColor: "#b33301" }}>
      <FaPlay className="text-white/90 mr-2" />
      <span className="text-white font-bold">Presentation</span>
      <span className="flex-1" />
      <button className="p-2 hover:bg-white/20 rounded text-white" title="First Slide" onClick={() => setCurrent(0)}><FaStepBackward /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Previous" onClick={() => setCurrent(c => Math.max(0, c - 1))}>Prev</button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Next" onClick={() => setCurrent(c => Math.min(slides.length - 1, c + 1))}>Next</button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Last Slide" onClick={() => setCurrent(slides.length - 1)}><FaStepForward /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Fullscreen" onClick={() => document.documentElement.requestFullscreen()}><FaExpand /></button>
    </div>
  )

  // Add bounds checking
  const slideIndex = Math.min(Math.max(0, current), slides.length - 1)
  const currentSlide = slides[slideIndex] || ""

  return (
    <div className="bg-white rounded-lg shadow border max-w-4xl mx-auto" style={{ borderColor: "#EDEBE9" }}>
      {toolbar}
      <div className="p-6 bg-white rounded-b-lg min-h-[300px] flex items-center justify-center">
        <div dangerouslySetInnerHTML={{ __html: sanitizeHTML(currentSlide) }} />
      </div>
      <div className="mt-4 text-center text-gray-700">Slide {slideIndex + 1} / {slides.length}</div>
    </div>
  )
}

export default PresentationViewer
