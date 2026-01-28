"use client"

import { useState, useEffect } from "react"

interface TimeSlot {
  id: string
  dayOfWeek: string
  startTime: string
  endTime: string
  isAvailable: boolean
}

interface ScheduleBlock {
  id?: string
  dayOfWeek: string
  startTime: string
  endTime: string
  slotDuration: number
}

const DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

export default function SchedulePage() {
  const [schedule, setSchedule] = useState<TimeSlot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [newBlock, setNewBlock] = useState<ScheduleBlock>({
    dayOfWeek: "Monday",
    startTime: "09:00",
    endTime: "17:00",
    slotDuration: 30
  })

  useEffect(() => {
    fetchSchedule()
  }, [])

  const fetchSchedule = async () => {
    try {
      setLoading(true)
      const response = await fetch("/api/carefusion/provider/schedule", {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to fetch schedule")
      
      const data = await response.json()
      setSchedule(data.schedule || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading schedule")
    } finally {
      setLoading(false)
    }
  }

  const handleAddBlock = async () => {
    try {
      const response = await fetch("/api/carefusion/provider/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(newBlock)
      })

      if (!response.ok) throw new Error("Failed to add schedule block")

      await fetchSchedule()
      setNewBlock({
        dayOfWeek: "Monday",
        startTime: "09:00",
        endTime: "17:00",
        slotDuration: 30
      })
      setIsEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error adding schedule block")
    }
  }

  const handleToggleAvailability = async (slotId: string, isAvailable: boolean) => {
    try {
      const response = await fetch(`/api/carefusion/provider/schedule/${slotId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ isAvailable })
      })

      if (!response.ok) throw new Error("Failed to update availability")

      await fetchSchedule()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error updating availability")
    }
  }

  const handleDeleteSlot = async (slotId: string) => {
    try {
      const response = await fetch(`/api/carefusion/provider/schedule/${slotId}`, {
        method: "DELETE",
        credentials: "include"
      })

      if (!response.ok) throw new Error("Failed to delete slot")

      await fetchSchedule()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error deleting slot")
    }
  }

  const getScheduleByDay = (day: string) => {
    return schedule.filter(slot => slot.dayOfWeek === day)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading schedule...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
              Schedule Management
            </h1>
            <p className="text-zinc-400">Manage your availability and appointment slots</p>
          </div>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition"
          >
            {isEditing ? "Cancel" : "Add Availability Block"}
          </button>
        </div>

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {isEditing && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Add Availability Block</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Day of Week</label>
                <select
                  value={newBlock.dayOfWeek}
                  onChange={(e) => setNewBlock({ ...newBlock, dayOfWeek: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {DAYS_OF_WEEK.map(day => (
                    <option key={day} value={day}>{day}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Start Time</label>
                <input
                  type="time"
                  value={newBlock.startTime}
                  onChange={(e) => setNewBlock({ ...newBlock, startTime: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">End Time</label>
                <input
                  type="time"
                  value={newBlock.endTime}
                  onChange={(e) => setNewBlock({ ...newBlock, endTime: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Slot Duration (min)</label>
                <select
                  value={newBlock.slotDuration}
                  onChange={(e) => setNewBlock({ ...newBlock, slotDuration: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>60 minutes</option>
                </select>
              </div>
            </div>
            <button
              onClick={handleAddBlock}
              className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition"
            >
              Add Block
            </button>
          </div>
        )}

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-zinc-800">
            <h2 className="text-xl font-semibold">Weekly Schedule</h2>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-7 divide-y lg:divide-y-0 lg:divide-x divide-zinc-800">
            {DAYS_OF_WEEK.map(day => {
              const daySlots = getScheduleByDay(day)
              return (
                <div key={day} className="p-4">
                  <h3 className="font-semibold text-center mb-4 text-purple-400">{day}</h3>
                  <div className="space-y-2">
                    {daySlots.length === 0 ? (
                      <p className="text-xs text-center text-zinc-500">No availability</p>
                    ) : (
                      daySlots.map(slot => (
                        <div
                          key={slot.id}
                          className={`p-2 rounded-lg border text-xs ${
                            slot.isAvailable
                              ? "bg-green-950/30 border-green-800 text-green-400"
                              : "bg-zinc-800 border-zinc-700 text-zinc-400"
                          }`}
                        >
                          <div className="font-medium mb-1">
                            {slot.startTime} - {slot.endTime}
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleToggleAvailability(slot.id, !slot.isAvailable)}
                              className="flex-1 px-2 py-1 bg-zinc-950 hover:bg-zinc-900 rounded text-xs transition"
                            >
                              {slot.isAvailable ? "Block" : "Unblock"}
                            </button>
                            <button
                              onClick={() => handleDeleteSlot(slot.id)}
                              className="px-2 py-1 bg-red-950/50 hover:bg-red-900/50 text-red-400 rounded text-xs transition"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="mt-6 bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h3 className="font-semibold mb-2">Schedule Management Tips</h3>
          <ul className="text-sm text-zinc-400 space-y-1">
            <li>• Add availability blocks for each day you want to see patients</li>
            <li>• Use different slot durations for different appointment types</li>
            <li>• Block individual time slots for breaks or meetings</li>
            <li>• Delete blocks to remove entire time ranges</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
