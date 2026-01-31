import { io, Socket } from 'socket.io-client'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:3000'

let socket: Socket | null = null

export const initSocket = (unitId?: string) => {
  if (!socket) {
    socket = io(SOCKET_URL, {
      auth: {
        token: localStorage.getItem('auth_token'),
      },
    })

    socket.on('connect', () => {
      console.log('Socket connected:', socket?.id)
      if (unitId) {
        socket?.emit('join:unit', unitId)
      }
    })

    socket.on('disconnect', () => {
      console.log('Socket disconnected')
    })

    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error)
    })

    socket.on('reconnect', () => {
      // Refresh token from localStorage on reconnection
      const freshToken = localStorage.getItem('auth_token')
      if (freshToken && socket) {
        socket.auth = { token: freshToken }
        console.log('Socket reconnected with refreshed token')
        if (unitId) {
          socket.emit('join:unit', unitId)
        }
      }
    })
  }

  return socket
}

export const getSocket = () => socket

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

export default { initSocket, getSocket, disconnectSocket }
