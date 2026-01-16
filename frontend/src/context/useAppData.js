import { useContext } from 'react'
import AppContext from './appContext.js'

export function useAppData() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppData must be used within an AppProvider')
  }
  return context
}
