const moduleRoleMatrix = {
  FOUNDER: ['founder'],
  INVESTOR: ['investor', 'founder'],
  HEMS: ['hems_supervisor', 'flight_nurse', 'flight_medic', 'pilot', 'aviation_qa', 'admin', 'founder'],
  BILLING: ['billing', 'admin', 'founder', 'medical_director'],
  QA: ['medical_director', 'admin', 'founder'],
  COMPLIANCE: ['medical_director', 'admin', 'founder'],
  LEGAL_PORTAL: ['admin', 'founder', 'medical_director'],
  TRAINING: ['admin', 'founder'],
  NARCOTICS: ['admin', 'provider', 'medical_director', 'founder'],
  MEDICATION: ['admin', 'provider', 'medical_director', 'founder'],
  INVENTORY: ['admin', 'provider', 'founder'],
  FLEET: ['admin', 'dispatcher', 'founder'],
  COMMS: ['dispatcher', 'admin', 'founder'],
  EMAIL: ['dispatcher', 'admin', 'founder', 'billing', 'medical_director'],
}

export function canAccessModule(moduleKey, role) {
  if (!moduleKey) {
    return true
  }
  const allowed = moduleRoleMatrix[moduleKey]
  if (!allowed) {
    return true
  }
  return allowed.includes(role)
}

export function defaultRoleHome(role) {
  if (role === 'founder') {
    return '/founder-ops'
  }
  if (role === 'investor') {
    return '/investor_demo'
  }
  if (['hems_supervisor', 'flight_nurse', 'flight_medic', 'pilot', 'aviation_qa'].includes(role)) {
    return '/hems'
  }
  if (role === 'billing') {
    return '/billing'
  }
  if (role === 'medical_director') {
    return '/qa'
  }
  return '/dashboard'
}
