import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../services/api.js'
import {
  fallbackCalls,
  fallbackUnits,
  fallbackPatients,
  fallbackShifts,
  fallbackInvoices,
  fallbackInsights,
} from '../data/fallback.js'

const AppContext = createContext(null)

const formatTime = (date) =>
  new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)

export function AppProvider({ children }) {
  const [calls, setCalls] = useState(fallbackCalls)
  const [units, setUnits] = useState(fallbackUnits)
  const [patients, setPatients] = useState(fallbackPatients)
  const [shifts, setShifts] = useState(fallbackShifts)
  const [invoices, setInvoices] = useState(fallbackInvoices)
  const [insights, setInsights] = useState(fallbackInsights)
  const [lastSync, setLastSync] = useState('')

  const refreshAll = useCallback(async () => {
    try {
      const [callsData, unitsData, patientsData, shiftsData, invoicesData, insightsData] =
        await Promise.all([
          apiFetch('/api/cad/calls'),
          apiFetch('/api/cad/units'),
          apiFetch('/api/epcr/patients'),
          apiFetch('/api/schedule/shifts'),
          apiFetch('/api/billing/invoices'),
          apiFetch('/api/ai_console/insights'),
        ])

      if (Array.isArray(callsData)) {
        setCalls(callsData)
      }
      if (unitsData?.active_units) {
        setUnits(unitsData.active_units)
      }
      if (Array.isArray(patientsData)) {
        setPatients(patientsData)
      }
      if (Array.isArray(shiftsData)) {
        setShifts(shiftsData)
      }
      if (Array.isArray(invoicesData)) {
        setInvoices(invoicesData)
      }
      if (Array.isArray(insightsData)) {
        setInsights(insightsData)
      }
      setLastSync(formatTime(new Date()))
    } catch (error) {
      console.warn('Live refresh failed, using cached data.', error)
    }
  }, [])

  const value = useMemo(
    () => ({
      calls,
      units,
      patients,
      shifts,
      invoices,
      insights,
      lastSync,
      refreshAll,
    }),
    [calls, units, patients, shifts, invoices, insights, lastSync, refreshAll]
  )

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppData() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppData must be used within an AppProvider')
  }
  return context
}
