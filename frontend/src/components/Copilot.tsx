import { useState, useRef, useEffect } from 'react'
import { api } from '../lib/api'

interface Msg { role: 'user' | 'assistant'; text: string }

export default function Copilot() {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: 'assistant', text: 'नमस्ते! I am Disha, your AI assistant. Ask me about any prospect — "Why did PR001 score 72?" or "Who should I call today?"' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  async function send() {
    const q = input.trim()
    if (!q) return
    setInput('')
    setMsgs(m => [...m, { role: 'user', text: q }])
    setLoading(true)
    try {
      const { answer } = await api.askCopilot(q)
      setMsgs(m => [...m, { role: 'assistant', text: answer }])
    } catch {
      setMsgs(m => [...m, { role: 'assistant', text: 'Sorry, I could not reach the backend. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen(o => !o)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-idbi-700 text-white shadow-lg flex items-center justify-center text-2xl hover:bg-idbi-500 transition-colors z-50"
        title="Disha Copilot"
      >
        💬
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden z-50" style={{ height: 420 }}>
          <div className="bg-idbi-700 text-white px-4 py-3 flex items-center justify-between">
            <span className="font-semibold text-sm">✨ Disha — RM Copilot</span>
            <button onClick={() => setOpen(false)} className="text-white/70 hover:text-white">✕</button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-slate-50">
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] text-xs rounded-2xl px-3 py-2 leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-idbi-700 text-white rounded-br-sm'
                    : 'bg-white border border-slate-200 text-slate-700 rounded-bl-sm'
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-3 py-2 text-xs text-slate-400">
                  Thinking…
                </div>
              </div>
            )}
            <div ref={bottom} />
          </div>

          <div className="p-2 border-t border-slate-200 flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              placeholder="Ask about a prospect…"
              className="flex-1 text-xs border border-slate-200 rounded-full px-3 py-2 focus:outline-none focus:ring-2 focus:ring-idbi-500"
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="bg-idbi-700 text-white text-xs rounded-full px-3 py-2 hover:bg-idbi-500 disabled:opacity-40 transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  )
}
