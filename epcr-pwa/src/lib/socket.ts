import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

export const initSocket = (unitId: string): Socket => {
  if (socket?.connected) {
    return socket
  }

  const token = localStorage.getItem('epcr_token')
  socket = io(import.meta.env.VITE_WS_URL || 'http://localhost:8000', {
    auth: { token },
    query: { unitId },
    transports: ['websocket'],
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
  })

  socket.on('connect', () => {
    console.log('[Socket] Connected to server')
    socket?.emit('join:unit', unitId)
  })

  socket.on('disconnect', (reason) => {
    console.log('[Socket] Disconnected:', reason)
  })

  socket.on('connect_error', (error) => {
    console.error('[Socket] Connection error:', error)
  })

  socket.on('reconnect', () => {
    // Refresh token from localStorage on reconnection
    const freshToken = localStorage.getItem('epcr_token')
    if (freshToken && socket) {
      socket.auth = { token: freshToken }
      console.log('[Socket] Reconnected with refreshed token')
      socket.emit('join:unit', unitId)
    }
  })

  return socket
}

export const getSocket = (): Socket | null => socket

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

export type CrewLinkAckEvent = {
  tripId: string
  unitId: string
  acknowledgedAt: string
  tripType: string
  pickup: {
    name: string
    address: string
  }
  destination: {
    name: string
    address: string
  }
  patient?: {
    name: string
    dob?: string
  }
}

export type MDTStatusEvent = {
  unitId: string
  status: string
  timestamp: string
  location?: { lat: number; lng: number }
}

export type MDTTimestampEvent = {
  tripId: string
  unitId: string
  timestampType: keyof import('../types').NEMSISTimestamps
  timestamp: string
  source: 'mdt' | 'manual'
}

export const subscribeToCrewLinkAck = (callback: (event: CrewLinkAckEvent) => void) => {
  socket?.on('crewlink:trip_acknowledged', callback)
  return () => socket?.off('crewlink:trip_acknowledged', callback)
}

export const subscribeToMDTStatus = (callback: (event: MDTStatusEvent) => void) => {
  socket?.on('mdt:status_change', callback)
  return () => socket?.off('mdt:status_change', callback)
}

export const subscribeToMDTTimestamp = (callback: (event: MDTTimestampEvent) => void) => {
  socket?.on('mdt:timestamp', callback)
  return () => socket?.off('mdt:timestamp', callback)
}
