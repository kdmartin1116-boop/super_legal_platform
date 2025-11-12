import React, { useState } from 'react'

const FlowDiagram: React.FC = () => {
  const [endorsementType, setEndorsementType] = useState('Qualified')
  const [explanation, setExplanation] = useState('')
  const [loading, setLoading] = useState(false)

  const handleExplain = async () => {
    setLoading(true)
    setExplanation('')
    try {
      const payload = { template_name: 'endorsement_explanation', context: { endorsement_type: endorsementType } }
      const res = await fetch('/api/v1/documents/prompts/render', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      })
      const json = await res.json()
      setExplanation(json.data.rendered)
    } catch (err: any) {
      setExplanation('Error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <label>
        Endorsement type: 
        <select value={endorsementType} onChange={e => setEndorsementType(e.target.value)}>
          <option>Blank</option>
          <option>Special</option>
          <option>Restrictive</option>
          <option>Qualified</option>
        </select>
      </label>
      <div style={{ marginTop: 8 }}>
        <button onClick={handleExplain} disabled={loading}>Explain</button>
      </div>
      {loading && <p>Loading...</p>}
      {explanation && <pre style={{ whiteSpace: 'pre-wrap', background: '#f7f7f7', padding: 10 }}>{explanation}</pre>}
    </div>
  )
}

export default FlowDiagram
