from models.ai_console import AiInsight
from models.ai_registry import AiOutputRegistry
from models.auth_session import AuthSession
from models.automation import WorkflowRule, WorkflowTask
from models.billing import BillingRecord, PriorAuthRequest
from models.billing_accounts import (
    BillingCustomer,
    BillingInvoice,
    BillingInvoiceLine,
    BillingLedgerEntry,
    BillingPayment,
    BillingWebhookReceipt,
)
from models.billing_ai import BillingAiInsight
from models.billing_claims import (
    BillingAssistResult,
    BillingClaim,
    BillingClaimExportSnapshot,
)
from models.billing_exports import (
    AppealPacket,
    ClaimStatusInquiry,
    ClaimSubmission,
    ClearinghouseAck,
    EligibilityCheck,
    BillingPatientStatement,
    PaymentPosting,
    RemittanceAdvice,
)
from models.billing_batch5 import (
    BillingAppeal,
    BillingClaimEvent,
    BillingContact,
    BillingContactAttempt,
    BillingDenial,
    BillingDocument,
    BillingFacility,
    BillingInvoiceEvent,
    BillingInvoiceItem,
    BillingPatientAccount,
    BillingPaymentEvent,
    BillingPortalToken,
)
from models.builders import BuilderRegistry, BuilderChangeLog
from models.business_ops import BusinessOpsTask
from models.consent import ConsentProvenance
from models.cad import (
    Call,
    Dispatch,
    Unit,
    CADIncident,
    CADIncidentTimeline,
    CrewLinkPage,
)
from models.mdt import MdtCadSyncEvent, MdtEvent, MdtObdIngest
from models.compliance import AccessAudit, ComplianceAlert
# New HR/Personnel Models
from models.hr_personnel import (
    Personnel,
    Certification,
    EmployeeDocument,
    PerformanceReview,
    DisciplinaryAction,
    TimeEntry,
    PayrollPeriod,
    Paycheck,
    LeaveRequest,
    LeaveBalance,
    ShiftDifferential,
)
# New Training Models
from models.training_management import (
    TrainingCourse,
    CredentialRecord,
    SkillCheckoff,
    CERecord,
)
# New Fire RMS Models
from models.fire_rms import (
    FirePersonnel,
    Hydrant,
    HydrantInspection,
    FireInspection,
    PreFirePlan,
    CommunityRiskReduction,
    ApparatusMaintenanceRecord,
    FireIncidentSupplement,
)
# ensure EPCR tables are loaded before patient portal models
from models.epcr import Patient, MasterPatient, MasterPatientLink, MasterPatientMerge, NEMSISValidationResult, PatientStateTimeline, NarrativeVersion
from models.epcr_core import (
    EpcrAssessment,
    EpcrIntervention,
    EpcrMedication,
    EpcrNarrative,
    EpcrOcrSnapshot,
    EpcrRecord,
    EpcrTimeline,
    EpcrVitals,
    OfflineSyncQueue,
    PreArrivalNotification,
    ProtocolPathway,
    ProviderCertification,
    CertificationType,
    EpcrValidationRule,
    EpcrVisibilityRule,
    EpcrSchematronRule,
)
from models.epcr_ems import EpcrEmsRecord
from models.epcr_fire import EpcrFireRecord
from models.epcr_hems import EpcrHemsRecord
# New Patient Portal Models
from models.patient_portal import (
    PatientBill,
    PatientPayment,
    PatientPaymentPlan,
    StripeCustomer,
)
from models.patient_portal_extended import (
    MedicalRecordRequest,
    PatientBillPayment,
    AppointmentRequest,
    PatientPortalAccessLog,
    PatientDocumentShare,
    PatientPreference,
    PatientSurveyResponse,
)
# New AI Intelligence Models
from models.ai_intelligence import (
    CallVolumePrediction,
    CrewFatigueAnalysis,
    OptimalUnitPlacement,
    AIDocumentationAssistant,
    PredictiveMaintenanceAlert,
    LiveEpcrCollaboration,
    TeamChatMessage,
    VideoConferenceSession,
    PerformanceBadge,
    PersonnelBadgeAward,
    Leaderboard,
    PerformancePoints,
    PointsTransaction,
    VoiceCommand,
    VoiceToTextVitals,
    AIProtocolRecommendation,
    DrugInteractionCheck,
    DifferentialDiagnosisAssistant,
)
from models.communications import (
    CommsBroadcast,
    CommsCallLog,
    CommsCallEvent,
    CommsMessage,
    CommsPhoneNumber,
    CommsRecording,
    CommsRingGroup,
    CommsRoutingPolicy,
    CommsTask,
    CommsTemplate,
    CommsThread,
    CommsTranscript,
    CommsVoicemail,
)
from models.communications_batch5 import (
    CommsDeliveryAttempt,
    CommsEvent,
    CommsProvider,
)
from models.documents import DocumentTemplate, DocumentRecord
from models.founder_documents import FounderDocumentFile, FounderDocumentFolder
from models.email import EmailAttachmentLink, EmailLabel, EmailMessage, EmailMessageLabel, EmailThread
from models.fax import FaxRecord, FaxAttachment
from models.quantum_documents import (
    DiscoveryExport,
    DocumentFile,
    DocumentFolder,
    DocumentPermission,
    DocumentVersion,
    RetentionPolicy,
)
from models.feature_flags import FeatureFlag
from models.jobs import JobQueue, JobRun
from models.organization import Organization
from models.event import EventLog
from models.module_registry import ModuleRegistry
from models.transportlink import TransportLeg, TransportTrip
from models.time import DeviceClockDrift
from models.device_trust import DeviceTrust
from models.legal import Addendum, LegalHold, OverrideRequest
from models.qa import QACase, QAReview, QARemediation, QARubric
from models.hems import (
    HemsAircraft,
    HemsAssignment,
    HemsBillingPacket,
    HemsChart,
    HemsCrew,
    HemsHandoff,
    HemsIncidentLink,
    HemsMission,
    HemsMissionTimeline,
    HemsFlightRequest,
    HemsFlightRequestTimeline,
    HemsQualityReview,
    HemsRiskAssessment,
)
from models.hems_aviation import (
    HemsFlightLog,
    HemsAircraftMaintenance,
    HemsAirworthinessDirective,
    HemsWeatherMinimums,
    HemsWeatherDecisionLog,
    HemsPilotCurrency,
    HemsFlightDutyRecord,
    HemsChecklist,
    HemsChecklistCompletion,
    HemsFRATAssessment,
)
from models.narcotics import NarcoticCustodyEvent, NarcoticDiscrepancy, NarcoticItem
from models.medication import MedicationAdministration, MedicationFormularyVersion, MedicationMaster
from models.inventory import InventoryItem, InventoryMovement, InventoryRigCheck
from models.fleet import FleetInspection, FleetMaintenance, FleetTelemetry, FleetVehicle
from models.founder_ops import DataGovernanceRule, IncidentCommand, PricingPlan, PwaDistribution
from models.exports import CarefusionExportSnapshot, DataExportManifest, OrphanRepairAction
from models.fire import (
    FireApparatus,
    FireApparatusInventory,
    FireAuditLog,
    FireExportRecord,
    FireIncident,
    FireIncidentApparatus,
    FireIncidentPersonnel,
    FirePreventionRecord,
    FireTrainingRecord,
    FireIncidentTimeline,
    FireInventoryHook,
)
from models.legal_portal import LegalCase, LegalEvidence
from models.founder import FounderMetric
from models.investor_demo import InvestorMetric
from models.analytics import AnalyticsMetric, UsageEvent
from models.workflow import WorkflowState
from models.mail import Message
from models.scheduling import Shift
from models.search import SearchIndexEntry, SavedSearch
from models.telehealth import (
    TelehealthMessage,
    TelehealthParticipant,
    TelehealthSession,
    TelehealthProvider,
    TelehealthPatient,
    TelehealthAppointment,
    TelehealthVisit,
    ProviderAvailability,
    TelehealthPrescription,
)
from models.user import User, UserRole
from models.validation import DataValidationIssue, ValidationRule
from models.terminology_builder import TerminologyEntry
from models.nemsis_watch import NemsisVersionWatch
from models.compliance import ForensicAuditLog
from models.support import SupportInteraction, SupportMirrorEvent, SupportSession
from models.notifications import InAppNotification, NotificationPreference
from models.telnyx import TelnyxCallSummary, TelnyxFaxRecord
from models.expenses import Expense, ExpenseReceipt, ExpenseApprovalWorkflow
from models.metriport import (
    PatientInsurance,
    MetriportPatientMapping,
    MetriportWebhookEvent,
    MetriportDocumentSync,
    InsuranceVerificationLog,
)
from models.routing import (
    TrafficEvent,
    RouteCalculation,
    TrafficFeedSource,
    RoutingConfig,
    TrafficEventType,
    TrafficSeverity,
    RoutingEngine
)

from models.intelligence import (
    CallVolumeForecast,
    CoverageRiskSnapshot,
    UnitTurnaroundPrediction,
    CrewFatigueScore,
    IntelligentAlert,
    DocumentationRiskAssessment,
    NEMSISValidationPrediction,
    AIRecommendationOutcome,
    UserAIFeedback,
    AIAuditLog,
    ForecastHorizon,
    CallVolumeType,
    ConfidenceLevel,
    CoverageRiskLevel,
    AlertSeverity,
    AlertType,
    AlertAudience,
    FeedbackType
)

from models.guided_automation import (
    RecommendedAction,
    GuidedWorkflow,
    AssistedDocumentation,
    IntelligentScheduleSuggestion,
    SupplyReplenishmentPrompt,
    ActionType,
    ActionStatus,
    WorkflowStage
)

from models.autonomous_ops import (
    NotificationRoutingRule,
    BackgroundOptimization,
    SystemInitiatedSuggestion,
    SelfHealingAction,
    AutomatedReporting,
    LearnedPattern,
    AutonomousActionLog,
    AutomationTrigger,
    AutomationStatus
)

from models.ecosystem_intelligence import (
    CrossAgencyLoadBalance,
    RegionalCoverageOptimization,
    HospitalDemandAwareness,
    SystemWideSurgeCoordination,
    AgencyPartnership,
    NetworkOptimizationResult,
    RegionalCoordinationType,
    AgencyRelationshipType
)

from models.strategic_intelligence import (
    StrategicTrendAnalysis,
    LongTermForecast,
    PolicyImpactSimulation,
    BudgetStrategyModel,
    StaffingStrategyRecommendation,
    OutcomeOptimizationInsight,
    RegulatoryReadinessScore,
    ExecutiveDashboardMetric,
    TrendDirection,
    PolicyImpactConfidence
)

from models.founder_billing import (
    PatientStatement as FounderPatientStatement,
    StatementDelivery,
    BillingAuditLog,
    StatementEscalation,
    LobMailJob,
    SoleBillerConfig,
    AIBillingDecision,
    StatementLifecycleState,
    DeliveryChannel,
    AIActionType
)

from models.wisconsin_billing import (
    PatientStatementTemplate,
    WisconsinBillingConfig,
    BillingHealthSnapshot,
    StatementDeliveryLog,
    TaxExemptionRecord,
    CollectionsEscalationRecord,
    AIBillingActionLog,
    TemplateType,
    BillingHealthStatus
)

from models.collections_governance import (
    CollectionsGovernancePolicy,
    CollectionsAccount,
    CollectionsActionLog,
    CollectionsDecisionRequest,
    WriteOffRecord,
    CollectionsProhibitedAction,
    CollectionsPhase,
    CollectionsAction,
    WriteOffReason
)

__all__ = [
    "AiInsight",
    "AiOutputRegistry",
    "AuthSession",
    "WorkflowRule",
    "WorkflowTask",
    "BillingRecord",
    "PriorAuthRequest",
    "BillingCustomer",
    "BillingInvoice",
    "BillingInvoiceLine",
    "BillingPayment",
    "BillingLedgerEntry",
    "BillingWebhookReceipt",
    "ClaimSubmission",
    "RemittanceAdvice",
    "ClearinghouseAck",
    "EligibilityCheck",
    "ClaimStatusInquiry",
    "BillingPatientStatement",
    "PaymentPosting",
    "AppealPacket",
    "BillingClaim",
    "BillingAssistResult",
    "BillingAiInsight",
    "BillingClaimExportSnapshot",
    "BuilderRegistry",
    "BuilderChangeLog",
    "BusinessOpsTask",
    "ConsentProvenance",
    "Call",
    "Dispatch",
    "Unit",
    "CADIncident",
    "CADIncidentTimeline",
    "CrewLinkPage",
    "MdtEvent",
    "MdtObdIngest",
    "MdtCadSyncEvent",
    "AccessAudit",
    "ForensicAuditLog",
    "ComplianceAlert",
    "CommsThread",
    "CommsMessage",
    "CommsCallLog",
    "CommsCallEvent",
    "CommsPhoneNumber",
    "CommsRoutingPolicy",
    "CommsRingGroup",
    "CommsRecording",
    "CommsVoicemail",
    "CommsTranscript",
    "CommsBroadcast",
    "CommsTask",
    "CommsEvent",
    "CommsDeliveryAttempt",
    "CommsProvider",
    "CommsTemplate",
    "EmailThread",
    "EmailMessage",
    "EmailLabel",
    "EmailMessageLabel",
    "EmailAttachmentLink",
    "FaxRecord",
    "FaxAttachment",
    "DocumentTemplate",
    "DocumentRecord",
    "DocumentFolder",
    "DocumentFile",
    "DocumentVersion",
    "DocumentPermission",
    "RetentionPolicy",
    "DiscoveryExport",
    "FeatureFlag",
    "JobQueue",
    "JobRun",
    "EventLog",
    "ModuleRegistry",
    "TransportLeg",
    "TransportTrip",
    "DeviceClockDrift",
    "DeviceTrust",
    "LegalHold",
    "Addendum",
    "OverrideRequest",
    "QARubric",
    "QACase",
    "QAReview",
    "QARemediation",
    "HemsMission",
    "HemsMissionTimeline",
    "HemsFlightRequest",
    "HemsFlightRequestTimeline",
    "HemsAircraft",
    "HemsCrew",
    "HemsAssignment",
    "HemsRiskAssessment",
    "HemsChart",
    "HemsHandoff",
    "HemsBillingPacket",
    "HemsIncidentLink",
    "HemsQualityReview",
    "NarcoticItem",
    "NarcoticCustodyEvent",
    "NarcoticDiscrepancy",
    "MedicationMaster",
    "MedicationAdministration",
    "MedicationFormularyVersion",
    "InventoryItem",
    "InventoryMovement",
    "InventoryRigCheck",
    "FleetVehicle",
    "FleetMaintenance",
    "FleetInspection",
    "FleetTelemetry",
    "PwaDistribution",
    "PricingPlan",
    "IncidentCommand",
    "DataGovernanceRule",
    "DataExportManifest",
    "OrphanRepairAction",
    "CarefusionExportSnapshot",
    "Patient",
    "MasterPatient",
    "MasterPatientLink",
    "MasterPatientMerge",
    "EpcrAssessment",
    "EpcrIntervention",
    "EpcrMedication",
    "EpcrNarrative",
    "EpcrOcrSnapshot",
    "EpcrRecord",
    "EpcrTimeline",
    "EpcrVitals",
    "OfflineSyncQueue",
    "PreArrivalNotification",
    "ProtocolPathway",
    "ProviderCertification",
    "CertificationType",
    "EpcrSchematronRule",
    "EpcrVisibilityRule",
    "EpcrValidationRule",
    "EpcrEmsRecord",
    "EpcrFireRecord",
    "EpcrHemsRecord",
    "FounderMetric",
    "InvestorMetric",
    "AnalyticsMetric",
    "UsageEvent",
    "WorkflowState",
    "Message",
    "Shift",
    "SearchIndexEntry",
    "SavedSearch",
    "TrainingCourse",
    "CredentialRecord",
    "SkillCheckoff",
    "CERecord",
    "TelehealthMessage",
    "TelehealthParticipant",
    "TelehealthSession",
    "TelehealthProvider",
    "TelehealthPatient",
    "TelehealthAppointment",
    "TelehealthVisit",
    "ProviderAvailability",
    "TelehealthPrescription",
    "CarefusionLedgerEntry",
    "CarefusionClaim",
    "CarefusionPayerRouting",
    "CarefusionAuditEvent",
    "User",
    "UserRole",
    "Organization",
    "DataValidationIssue",
    "TerminologyEntry",
    "NemsisVersionWatch",
    "FireIncident",
    "FireApparatus",
    "FireApparatusInventory",
    "FirePersonnel",
    "FireIncidentApparatus",
    "FireIncidentPersonnel",
    "FireTrainingRecord",
    "FirePreventionRecord",
    "FireAuditLog",
    "FireExportRecord",
    "FireIncidentTimeline",
    "FireInventoryHook",
    "LegalCase",
    "LegalEvidence",
    "PatientPortalAccount",
    "PatientPortalMessage",
    "PatientBill",
    "PatientPayment",
    "PatientPaymentPlan",
    "StripeCustomer",
    "MedicalRecordRequest",
    "PatientBillPayment",
    "AppointmentRequest",
    "PatientPortalAccessLog",
    "PatientDocumentShare",
    "PatientPreference",
    "PatientSurveyResponse",
    "SupportInteraction",
    "SupportMirrorEvent",
    "SupportSession",
    "InAppNotification",
    "NotificationPreference",
    "TelnyxCallSummary",
    "TelnyxFaxRecord",
    "Expense",
    "ExpenseReceipt",
    "ExpenseApprovalWorkflow",
    "PatientInsurance",
    "MetriportPatientMapping",
    "MetriportWebhookEvent",
    "MetriportDocumentSync",
    "InsuranceVerificationLog",
]
