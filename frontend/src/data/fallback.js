export const fallbackCalls = [
  {
    id: 1042,
    caller_name: 'M. Hernandez',
    location_address: '1447 Eastline Ave',
    priority: 'High',
    status: 'Dispatched',
    eta_minutes: 6,
  },
  {
    id: 1043,
    caller_name: 'A. Chen',
    location_address: 'Pier 17 Dock',
    priority: 'Routine',
    status: 'Queued',
    eta_minutes: null,
  },
  {
    id: 1044,
    caller_name: 'J. Patel',
    location_address: 'North River Mall',
    priority: 'Critical',
    status: 'En Route',
    eta_minutes: 4,
  },
]

export const fallbackUnits = [
  { unit_identifier: 'A-14', status: 'En Route', latitude: 40.74, longitude: -73.99 },
  { unit_identifier: 'B-03', status: 'On Scene', latitude: 40.71, longitude: -74.02 },
  { unit_identifier: 'C-11', status: 'Available', latitude: 40.73, longitude: -74.01 },
]

export const fallbackPatients = [
  {
    id: 521,
    first_name: 'Riley',
    last_name: 'Morgan',
    incident_number: 'INC-3812',
    vitals: { bp: '128/82', hr: 94, spo2: '96%' },
    interventions: ['IV access', 'Oxygen 2L'],
  },
  {
    id: 522,
    first_name: 'Jordan',
    last_name: 'Lee',
    incident_number: 'INC-3813',
    vitals: { bp: '98/66', hr: 112, spo2: '92%' },
    interventions: ['12-lead ECG', 'Aspirin 325mg'],
  },
]

export const fallbackShifts = [
  {
    id: 87,
    crew_name: 'Night ALS 1',
    shift_start: '2024-01-15T18:00:00Z',
    shift_end: '2024-01-16T06:00:00Z',
    status: 'Scheduled',
    certifications: ['ACLS', 'PALS'],
  },
  {
    id: 88,
    crew_name: 'Day BLS 4',
    shift_start: '2024-01-16T06:00:00Z',
    shift_end: '2024-01-16T18:00:00Z',
    status: 'Swapped',
    certifications: ['BLS'],
  },
]

export const fallbackInvoices = [
  {
    id: 304,
    patient_name: 'Riley Morgan',
    invoice_number: 'INV-2218',
    payer: 'BlueCross',
    amount_due: 1280,
    status: 'Open',
  },
  {
    id: 305,
    patient_name: 'Jordan Lee',
    invoice_number: 'INV-2219',
    payer: 'Medicare',
    amount_due: 860,
    status: 'Pending',
  },
]

export const fallbackInsights = [
  {
    category: 'Coverage',
    prompt: 'Predictive staging for Zone 4',
    response: 'Reassign ALS unit C-11 to Zone 4 between 17:00-20:00.',
  },
  {
    category: 'Documentation',
    prompt: 'ePCR completeness trend',
    response: 'Vitals missing on 8% of trauma reports. Add auto prompt at triage.',
  },
]

export const fallbackFounderKpis = [
  { label: 'Net Revenue', value: '$4.2M', delta: '+7.4%' },
  { label: 'Fleet Utilization', value: '78%', delta: '+3.1%' },
  { label: 'Compliance Score', value: '98.6%', delta: '+0.9%' },
]

export const fallbackInvestorKpis = [
  { label: 'ARR', value: '$12.6M', delta: '+18%' },
  { label: 'Gross Margin', value: '62%', delta: '+4%' },
  { label: 'Agencies Live', value: '47', delta: '+5' },
]
