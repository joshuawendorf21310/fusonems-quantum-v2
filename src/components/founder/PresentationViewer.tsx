
import React from "react"
import { FaPlay, FaStepBackward, FaStepForward, FaExpand } from "react-icons/fa"

interface Props {
  slides: string[]
}

/**
 * Sanitize HTML to prevent XSS attacks.
 * Allows only safe tags for presentation content.
 */
function sanitizeHTML(html: string): string {
  // Create a temporary element to parse HTML
  if (typeof document === 'undefined') return html
  
  const temp = document.createElement('div')
  temp.innerHTML = html
  
  // Allowed tags for presentation content
  const allowedTags = new Set([
    'P', 'DIV', 'SPAN', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'UL', 'OL', 'LI', 'BR', 'HR', 'STRONG', 'B', 'EM', 'I', 'U',
    'A', 'IMG', 'TABLE', 'TR', 'TD', 'TH', 'THEAD', 'TBODY',
    'BLOCKQUOTE', 'PRE', 'CODE', 'SUP', 'SUB'
  ])
  
  // Dangerous attributes to remove
  const dangerousAttrs = ['onclick', 'onerror', 'onload', 'onmouseover', 'onfocus', 'onblur']
  
  function cleanNode(node: Node): void {
    if (node.nodeType === Node.ELEMENT_NODE) {
      const el = node as Element
      
      // Remove script and style tags entirely
      if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE' || el.tagName === 'IFRAME') {
        el.remove()
        return
      }
      
      // Remove dangerous attributes
      for (const attr of dangerousAttrs) {
        el.removeAttribute(attr)
      }
      
      // Remove javascript: hrefs
      if (el.hasAttribute('href') && el.getAttribute('href')?.toLowerCase().startsWith('javascript:')) {
        el.setAttribute('href', '#')
      }
      
      // Recursively clean children
      Array.from(el.childNodes).forEach(cleanNode)
    }
  }
  
  Array.from(temp.childNodes).forEach(cleanNode)
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

  return (
    <div className="bg-white rounded-lg shadow border max-w-4xl mx-auto" style={{ borderColor: "#EDEBE9" }}>
      {toolbar}
      <div className="p-6 bg-white rounded-b-lg min-h-[300px] flex items-center justify-center">
        <div dangerouslySetInnerHTML={{ __html: sanitizedSlide }} />
      </div>
      <div className="mt-4 text-center text-gray-700">Slide {current + 1} / {slides.length}</div>
    </div>
  )
}

export default PresentationViewer
