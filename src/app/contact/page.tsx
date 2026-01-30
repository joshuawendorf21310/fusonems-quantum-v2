"use client"

import { useState } from "react"

export default function ContactPage() {
  const [status, setStatus] = useState<"idle"|"sending"|"sent"|"error">("idle")
  const [form, setForm] = useState({
    name: "",
    email: "",
    organization: "",
    subject: "",
    message: "",
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement|HTMLTextAreaElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus("sending")
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      })
      if (res.ok) setStatus("sent")
      else setStatus("error")
    } catch {
      setStatus("error")
    }
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center px-4">
      <div className="w-full max-w-lg bg-[#181818] rounded-xl shadow-lg p-8 border border-[#C41E3A]/30">
        <h1 className="text-2xl font-bold mb-6 text-[#FF6B35]">Contact Platform Team</h1>
        {status === "sent" ? (
          <div className="text-green-400 font-semibold text-center py-8">Thank you! Your message has been sent.</div>
        ) : (
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <input name="name" type="text" required placeholder="Your Name" className="rounded px-3 py-2 bg-black/80 border border-[#FF6B35] text-white" value={form.name} onChange={handleChange} />
          <input name="email" type="email" required placeholder="Your Email" className="rounded px-3 py-2 bg-black/80 border border-[#FF6B35] text-white" value={form.email} onChange={handleChange} />
          <input name="organization" type="text" placeholder="Organization (optional)" className="rounded px-3 py-2 bg-black/80 border border-[#FF6B35] text-white" value={form.organization} onChange={handleChange} />
          <input name="subject" type="text" required placeholder="Subject" className="rounded px-3 py-2 bg-black/80 border border-[#FF6B35] text-white" value={form.subject} onChange={handleChange} />
          <textarea name="message" required placeholder="How can we help you?" className="rounded px-3 py-2 bg-black/80 border border-[#FF6B35] text-white min-h-[100px]" value={form.message} onChange={handleChange} />
          <button type="submit" disabled={status==='sending'} className="rounded bg-[#FF6B35] hover:bg-[#C41E3A] text-white font-semibold px-4 py-2 mt-2 transition">
            {status==='sending' ? 'Sending...' : 'Send Message'}
          </button>
          {status === "error" && <div className="text-red-400 text-sm mt-2">There was an error sending your message. Please try again.</div>}
        </form>
        )}
      </div>
    </div>
  )
}
