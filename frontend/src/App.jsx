import { Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './Dashboard.jsx'
import CadManagement from './pages/CadManagement.jsx'
import UnitTracking from './pages/UnitTracking.jsx'
import PatientCare from './pages/PatientCare.jsx'
import Scheduling from './pages/Scheduling.jsx'
import Billing from './pages/Billing.jsx'
import AiConsole from './pages/AiConsole.jsx'
import Reporting from './pages/Reporting.jsx'
import FounderDashboard from './pages/FounderDashboard.jsx'
import InvestorDashboard from './pages/InvestorDashboard.jsx'
import Layout from './components/Layout.jsx'
import { AppProvider } from './context/AppContext.jsx'

export default function App() {
  return (
    <AppProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cad" element={<CadManagement />} />
          <Route path="/tracking" element={<UnitTracking />} />
          <Route path="/epcr" element={<PatientCare />} />
          <Route path="/scheduling" element={<Scheduling />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/ai-console" element={<AiConsole />} />
          <Route path="/reporting" element={<Reporting />} />
          <Route path="/founder" element={<FounderDashboard />} />
          <Route path="/investor" element={<InvestorDashboard />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Layout>
    </AppProvider>
  )
}
