import React, { useState } from 'react'

const CreditDispute: React.FC = () => {
  const [fileText, setFileText] = useState('')
  const [analysis, setAnalysis] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAnalyze = async () => {
    setLoading(true)
    setAnalysis('')
    try {
      const payload = {
        template_name: 'credit_analysis',
        context: { document_text: fileText, previous_analysis: '' }
      }

      const res = await fetch('/api/v1/documents/prompts/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const txt = await res.text()
        setAnalysis('Error: ' + txt)
      } else {
        const json = await res.json()
        setAnalysis(json.data.rendered)
      }
    } catch (err: any) {
      setAnalysis('Fetch error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <textarea value={fileText} onChange={e => setFileText(e.target.value)} placeholder="Paste document text here" rows={10} style={{ width: '100%' }} />
      <div style={{ marginTop: 8 }}>
        <button onClick={handleAnalyze} disabled={loading || !fileText}>Analyze (render prompt)</button>
      </div>
      {loading && <p>Rendering...</p>}
      {analysis && (
        <pre style={{ whiteSpace: 'pre-wrap', marginTop: 12, background: '#f5f5f5', padding: 12 }}>{analysis}</pre>
      )}
    </div>
  )
}

export default CreditDispute
