import React from 'react'
import CreditDispute from './components/CreditDispute'
import FlowDiagram from './components/FlowDiagram'

const App: React.FC = () => {
  return (
    <div style={{ fontFamily: 'sans-serif', padding: 24 }}>
      <h1>Sovereign Legal Demo</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <h2>Credit Dispute</h2>
          <CreditDispute />
        </div>
        <div>
          <h2>Endorsement Flow</h2>
          <FlowDiagram />
        </div>
      </div>
    </div>
  )
}

export default App
