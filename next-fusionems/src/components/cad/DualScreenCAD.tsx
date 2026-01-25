import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../../services/api.js'
import { useAppData } from '../../context/useAppData.js'
import CallDetailsPanel from './CallDetailsPanel'
import CallQueue from './CallQueue'
import MapView from './MapView'
import Timeline from './Timeline'
import UnitStatusBoard from './UnitStatusBoard'

export type CadCall = {
  id: number
  caller_name: string
  caller_phone: string
  location_address: string
  latitude: number
  longitude: number
  priority: string
  status: string
  eta_minutes?: number | null
}

export type CadUnit = {
  unit_identifier: string
  status: string
  latitude: number
  longitude: number
}

const statusShortcuts: Record<string, string> = {
  Digit1: 'Enroute',
  Digit2: 'OnScene',
  Digit3: 'Transport',
  Digit4: 'Available',
}

export default function DualScreenCAD() {
  const { calls, units, refreshAll } = useAppData()
  const [selectedCallId, setSelectedCallId] = useState<number | null>(null)
  const [activeUnitId, setActiveUnitId] = useState<string | null>(null)

  const selectedCall = useMemo(
    () => calls.find((call: CadCall) => call.id === selectedCallId) ?? null,
    [calls, selectedCallId]
  )

  const activeUnit = useMemo(
    () => units.find((unit: CadUnit) => unit.unit_identifier === activeUnitId) ?? null,
    [units, activeUnitId]
  )

  const handleAssign = useCallback(
    async (callId: number, unitIdentifier: string) => {
      await apiFetch(`/api/cad/calls/${callId}/assign`, {
        method: 'POST',
        body: JSON.stringify({ unit_identifier: unitIdentifier }),
      })
      setActiveUnitId(unitIdentifier)
      await refreshAll()
    },
    [refreshAll]
  )

  const handleStatusChange = useCallback(
    async (status: string) => {
      if (!selectedCallId) return
      await apiFetch(`/api/cad/calls/${selectedCallId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({
          status,
          unit_identifier: activeUnitId ?? undefined,
        }),
      })
      await refreshAll()
    },
    [activeUnitId, refreshAll, selectedCallId]
  )

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (!selectedCallId) return
      const status = statusShortcuts[event.code]
      if (status) {
        event.preventDefault()
        handleStatusChange(status)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleStatusChange, selectedCallId])

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const wsUrl = apiBase.replace(/^http/, 'ws') + '/api/cad/live'
    let socket: WebSocket | null = new WebSocket(wsUrl)
    socket.onmessage = () => {
      refreshAll()
    }
    socket.onerror = () => {
      if (socket) {
        socket.close()
        socket = null
      }
    }
    return () => {
      if (socket) {
        socket.close()
      }
    }
  }, [refreshAll])

  return (
    <section className="cad-shell">
      <div className="cad-column">
        <CallQueue calls={calls as CadCall[]} selectedCallId={selectedCallId} onSelect={setSelectedCallId} />
        <UnitStatusBoard
          units={units as CadUnit[]}
          activeUnitId={activeUnitId}
          onSelectUnit={setActiveUnitId}
          onAssign={handleAssign}
        />
      </div>
      <div className="cad-column cad-main">
        <MapView calls={calls as CadCall[]} units={units as CadUnit[]} selectedCallId={selectedCallId} />
        <div className="cad-details">
          <CallDetailsPanel
            call={selectedCall}
            units={units as CadUnit[]}
            activeUnit={activeUnit}
            onAssign={handleAssign}
            onStatusChange={handleStatusChange}
          />
          <Timeline callId={selectedCallId} />
        </div>
      </div>
    </section>
  )
}
