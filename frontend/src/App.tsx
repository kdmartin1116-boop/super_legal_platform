import { Routes, Route } from 'react-router-dom'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { DocumentProcessing } from '@/pages/DocumentProcessing'
import { DocumentGeneration } from '@/pages/DocumentGeneration'
import { Education } from '@/pages/Education'
import { LegalResearch } from '@/pages/LegalResearch'
import { UserProfile } from '@/pages/UserProfile'

function App() {
  return (
    <ErrorBoundary>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/documents/*" element={<DocumentProcessing />} />
          <Route path="/generation/*" element={<DocumentGeneration />} />
          <Route path="/education/*" element={<Education />} />
          <Route path="/research/*" element={<LegalResearch />} />
          <Route path="/profile" element={<UserProfile />} />
        </Routes>
      </Layout>
    </ErrorBoundary>
  )
}

export default App