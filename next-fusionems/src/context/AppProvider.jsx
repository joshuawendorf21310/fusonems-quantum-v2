import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../services/api.js'
import AppContext from './appContext.js'
import {
  fallbackCalls,
  fallbackUnits,
  fallbackPatients,
  fallbackShifts,
  fallbackInvoices,
  fallbackInsights,
  fallbackModules,
  fallbackSystemHealth,
} from '../data/fallback.js'

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
  const [trainingStatus, setTrainingStatus] = useState({
    org_mode: 'DISABLED',
    user_mode: false,
  })
  const [modules, setModules] = useState(fallbackModules)
  const [systemHealth, setSystemHealth] = useState(fallbackSystemHealth)

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
      try {
        const trainingData = await apiFetch('/api/training/status')
        if (trainingData?.org_mode) {
          setTrainingStatus(trainingData)
        }
      } catch (trainingError) {
        console.warn('Training status unavailable', trainingError)
      }
      try {
        const [moduleData, healthData] = await Promise.all([
          apiFetch('/api/system/modules'),
          apiFetch('/api/system/health'),
        ])
        if (Array.isArray(moduleData)) {
          setModules(moduleData)
        }
        if (healthData?.status) {
          setSystemHealth(healthData)
        }
      } catch (healthError) {
        console.warn('System health unavailable', healthError)
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
      trainingStatus,
      modules,
      systemHealth,
      lastSync,
      refreshAll,
    }),
    [
      calls,
      units,
      patients,
      shifts,
      invoices,
      insights,
      trainingStatus,
      modules,
      systemHealth,
      lastSync,
      refreshAll,
    ]
  )

  useEffect(() => {
    refreshAll()
  }, [refreshAll])

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}
