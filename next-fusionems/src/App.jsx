import { Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './Dashboard.jsx'
import Landing from './pages/Landing.jsx'
import ProviderPortal from './pages/ProviderPortal.jsx'
import CadManagement from './pages/CadManagement.jsx'
import UnitTracking from './pages/UnitTracking.jsx'
import PatientCare from './pages/PatientCare.jsx'
import Scheduling from './pages/Scheduling.jsx'
import Billing from './pages/Billing.jsx'
import AiConsole from './pages/AiConsole.jsx'
import Reporting from './pages/Reporting.jsx'
import FounderDashboard from './pages/FounderDashboard.jsx'
import InvestorDashboard from './pages/InvestorDashboard.jsx'
import Communications from './pages/Communications.jsx'
import VoiceConsole from './pages/VoiceConsole.jsx'
import Telehealth from './pages/Telehealth.jsx'
import AutomationCompliance from './pages/AutomationCompliance.jsx'
import QAReview from './pages/QAReview.jsx'
import TrainingCenter from './pages/TrainingCenter.jsx'
import Narcotics from './pages/Narcotics.jsx'
import Medication from './pages/Medication.jsx'
import Inventory from './pages/Inventory.jsx'
import Fleet from './pages/Fleet.jsx'
import FounderOps from './pages/FounderOps.jsx'
import FounderWorkspace from './pages/FounderWorkspace.jsx'
import FounderWorkspaceDocuments from './pages/FounderWorkspaceDocuments.jsx'
import FounderWorkspaceVoice from './pages/FounderWorkspaceVoice.jsx'
import FounderWorkspaceHolds from './pages/FounderWorkspaceHolds.jsx'
import FounderWorkspaceExports from './pages/FounderWorkspaceExports.jsx'
import RetentionGovernance from './pages/RetentionGovernance.jsx'
import LegalPortal from './pages/LegalPortal.jsx'
import PatientPortal from './pages/PatientPortal.jsx'
import FireDashboard from './pages/FireDashboard.jsx'
import FireIncidents from './pages/FireIncidents.jsx'
import FireApparatus from './pages/FireApparatus.jsx'
import FirePersonnel from './pages/FirePersonnel.jsx'
import FireTraining from './pages/FireTraining.jsx'
import FirePrevention from './pages/FirePrevention.jsx'
import HemsDashboard from './pages/HemsDashboard.jsx'
import HemsMissionBoard from './pages/HemsMissionBoard.jsx'
import HemsMissionView from './pages/HemsMissionView.jsx'
import HemsClinical from './pages/HemsClinical.jsx'
import HemsAircraft from './pages/HemsAircraft.jsx'
import HemsCrew from './pages/HemsCrew.jsx'
import HemsQA from './pages/HemsQA.jsx'
import HemsBilling from './pages/HemsBilling.jsx'
import RepairConsole from './pages/RepairConsole.jsx'
import DataExports from './pages/DataExports.jsx'
import DocumentStudio from './pages/DocumentStudio.jsx'
import Documents from './pages/Documents.jsx'
import DocumentsHolds from './pages/DocumentsHolds.jsx'
import DocumentsExports from './pages/DocumentsExports.jsx'
import BuilderRegistry from './pages/BuilderRegistry.jsx'
import ValidationBuilder from './pages/ValidationBuilder.jsx'
import SearchDiscovery from './pages/SearchDiscovery.jsx'
import JobsConsole from './pages/JobsConsole.jsx'
import AnalyticsCore from './pages/AnalyticsCore.jsx'
import FeatureFlags from './pages/FeatureFlags.jsx'
import EmailInbox from './pages/EmailInbox.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Layout from './components/Layout.jsx'
import { AppProvider } from './context/AppProvider.jsx'
import { AuthProvider } from './context/AuthProvider.jsx'
import { useAuth } from './context/useAuth.js'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { canAccessModule } from './utils/access.js'

function Guarded({ moduleKey, children }) {
  const { userRole } = useAuth()
  if (moduleKey && !canAccessModule(moduleKey, userRole)) {
    return (
      <ProtectedRoute allowedRoles={['__blocked__']}>
        {children}
      </ProtectedRoute>
    )
  }
  return <ProtectedRoute>{children}</ProtectedRoute>
}

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/landing" element={<Landing />} />
            <Route path="/provider-portal" element={<ProviderPortal />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/cad"
              element={
                <Guarded moduleKey="CAD">
                  <CadManagement />
                </Guarded>
              }
            />
            <Route
              path="/tracking"
              element={
                <Guarded moduleKey="CAD">
                  <UnitTracking />
                </Guarded>
              }
            />
            <Route
              path="/epcr"
              element={
                <Guarded moduleKey="EPCR">
                  <PatientCare />
                </Guarded>
              }
            />
            <Route
              path="/scheduling"
              element={
                <Guarded moduleKey="SCHEDULING">
                  <Scheduling />
                </Guarded>
              }
            />
            <Route
              path="/billing"
              element={
                <Guarded moduleKey="BILLING">
                  <Billing />
                </Guarded>
              }
            />
            <Route
              path="/ai-console"
              element={
                <Guarded moduleKey="AI_CONSOLE">
                  <AiConsole />
                </Guarded>
              }
            />
            <Route
              path="/communications"
              element={
                <Guarded moduleKey="COMMS">
                  <Communications />
                </Guarded>
              }
            />
            <Route
              path="/email"
              element={
                <Guarded moduleKey="EMAIL">
                  <EmailInbox />
                </Guarded>
              }
            />
            <Route
              path="/communications/voice"
              element={
                <Guarded moduleKey="COMMS">
                  <VoiceConsole />
                </Guarded>
              }
            />
            <Route
              path="/qa"
              element={
                <Guarded moduleKey="QA">
                  <QAReview />
                </Guarded>
              }
            />
            <Route
              path="/training-center"
              element={
                <Guarded moduleKey="TRAINING">
                  <TrainingCenter />
                </Guarded>
              }
            />
            <Route
              path="/narcotics"
              element={
                <Guarded moduleKey="NARCOTICS">
                  <Narcotics />
                </Guarded>
              }
            />
            <Route
              path="/medication"
              element={
                <Guarded moduleKey="MEDICATION">
                  <Medication />
                </Guarded>
              }
            />
            <Route
              path="/inventory"
              element={
                <Guarded moduleKey="INVENTORY">
                  <Inventory />
                </Guarded>
              }
            />
            <Route
              path="/fleet"
              element={
                <Guarded moduleKey="FLEET">
                  <Fleet />
                </Guarded>
              }
            />
            <Route
              path="/founder-ops"
              element={
                <Guarded moduleKey="FOUNDER">
                  <FounderOps />
                </Guarded>
              }
            />
            <Route
              path="/founder/workspace"
              element={
                <Guarded moduleKey="FOUNDER">
                  <FounderWorkspace />
                </Guarded>
              }
            />
            <Route
              path="/founder/workspace/documents"
              element={
                <Guarded moduleKey="FOUNDER">
                  <FounderWorkspaceDocuments />
                </Guarded>
              }
            />
            <Route
              path="/founder/workspace/voice"
              element={
                <Guarded moduleKey="FOUNDER">
                  <FounderWorkspaceVoice />
                </Guarded>
              }
            />
            <Route
              path="/founder/workspace/holds"
              element={
                <Guarded moduleKey="FOUNDER">
                  <FounderWorkspaceHolds />
                </Guarded>
              }
            />
            <Route
              path="/founder/workspace/exports"
              element={
                <Guarded moduleKey="FOUNDER">
                  <FounderWorkspaceExports />
                </Guarded>
              }
            />
            <Route
              path="/founder/governance/retention"
              element={
                <Guarded moduleKey="FOUNDER">
                  <RetentionGovernance />
                </Guarded>
              }
            />
            <Route
              path="/legal-portal"
              element={
                <Guarded moduleKey="LEGAL_PORTAL">
                  <LegalPortal />
                </Guarded>
              }
            />
            <Route
              path="/patient-portal"
              element={
                <Guarded moduleKey="BILLING">
                  <PatientPortal />
                </Guarded>
              }
            />
            <Route
              path="/telehealth"
              element={
                <Guarded moduleKey="TELEHEALTH">
                  <Telehealth />
                </Guarded>
              }
            />
            <Route
              path="/automation"
              element={
                <Guarded moduleKey="AUTOMATION">
                  <AutomationCompliance />
                </Guarded>
              }
            />
            <Route
              path="/fire"
              element={
                <Guarded moduleKey="FIRE">
                  <FireDashboard />
                </Guarded>
              }
            />
            <Route
              path="/fire/incidents"
              element={
                <Guarded moduleKey="FIRE">
                  <FireIncidents />
                </Guarded>
              }
            />
            <Route
              path="/fire/apparatus"
              element={
                <Guarded moduleKey="FIRE">
                  <FireApparatus />
                </Guarded>
              }
            />
            <Route
              path="/fire/personnel"
              element={
                <Guarded moduleKey="FIRE">
                  <FirePersonnel />
                </Guarded>
              }
            />
            <Route
              path="/fire/training"
              element={
                <Guarded moduleKey="FIRE">
                  <FireTraining />
                </Guarded>
              }
            />
            <Route
              path="/fire/prevention"
              element={
                <Guarded moduleKey="FIRE">
                  <FirePrevention />
                </Guarded>
              }
            />
            <Route
              path="/hems"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsDashboard />
                </Guarded>
              }
            />
            <Route
              path="/hems/missions"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsMissionBoard />
                </Guarded>
              }
            />
            <Route
              path="/hems/missions/:missionId"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsMissionView />
                </Guarded>
              }
            />
            <Route
              path="/hems/chart/:missionId"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsClinical />
                </Guarded>
              }
            />
            <Route
              path="/hems/aircraft"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsAircraft />
                </Guarded>
              }
            />
            <Route
              path="/hems/crew"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsCrew />
                </Guarded>
              }
            />
            <Route
              path="/hems/qa"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsQA />
                </Guarded>
              }
            />
            <Route
              path="/hems/billing"
              element={
                <Guarded moduleKey="HEMS">
                  <HemsBilling />
                </Guarded>
              }
            />
            <Route
              path="/repair"
              element={
                <Guarded moduleKey="REPAIR">
                  <RepairConsole />
                </Guarded>
              }
            />
            <Route
              path="/exports"
              element={
                <Guarded moduleKey="EXPORTS">
                  <DataExports />
                </Guarded>
              }
            />
            <Route
              path="/documents"
              element={
                <Guarded moduleKey="DOCUMENT_STUDIO">
                  <Documents />
                </Guarded>
              }
            />
            <Route
              path="/document-studio"
              element={
                <Guarded moduleKey="DOCUMENT_STUDIO">
                  <DocumentStudio />
                </Guarded>
              }
            />
            <Route
              path="/documents/holds"
              element={
                <Guarded moduleKey="DOCUMENT_STUDIO">
                  <DocumentsHolds />
                </Guarded>
              }
            />
            <Route
              path="/documents/exports"
              element={
                <Guarded moduleKey="DOCUMENT_STUDIO">
                  <DocumentsExports />
                </Guarded>
              }
            />
            <Route
              path="/builders"
              element={
                <Guarded moduleKey="BUILDERS">
                  <BuilderRegistry />
                </Guarded>
              }
            />
            <Route
              path="/builders/validation"
              element={
                <Guarded moduleKey="BUILDERS">
                  <ValidationBuilder />
                </Guarded>
              }
            />
            <Route
              path="/search"
              element={
                <Guarded moduleKey="SEARCH">
                  <SearchDiscovery />
                </Guarded>
              }
            />
            <Route
              path="/jobs"
              element={
                <Guarded moduleKey="JOBS">
                  <JobsConsole />
                </Guarded>
              }
            />
            <Route
              path="/analytics"
              element={
                <Guarded moduleKey="ANALYTICS">
                  <AnalyticsCore />
                </Guarded>
              }
            />
            <Route
              path="/feature-flags"
              element={
                <Guarded moduleKey="FEATURE_FLAGS">
                  <FeatureFlags />
                </Guarded>
              }
            />
            <Route
              path="/reporting"
              element={
                <Guarded moduleKey="COMPLIANCE">
                  <Reporting />
                </Guarded>
              }
            />
            <Route
              path="/founder"
              element={
                <Guarded moduleKey="FOUNDER">
                  <FounderDashboard />
                </Guarded>
              }
            />
            <Route
              path="/investor"
              element={
                <Guarded moduleKey="INVESTOR">
                  <InvestorDashboard />
                </Guarded>
              }
            />
            <Route
              path="/investor_demo"
              element={
                <Guarded moduleKey="INVESTOR">
                  <InvestorDashboard />
                </Guarded>
              }
            />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Layout>
      </AppProvider>
    </AuthProvider>
  )
}
