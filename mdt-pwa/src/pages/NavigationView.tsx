import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet'
import { Icon } from 'leaflet'
import { getIncident } from '../lib/api'
import { NavigationEngine, NavigationState, formatDistance, formatDuration } from '../lib/navigation'
import { startTracking, stopTracking } from '../lib/geolocation'
import type { Incident, LocationData } from '../types'

const ambulanceIcon = new Icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/2913/2913133.png',
  iconSize: [48, 48],
})

function MapUpdater({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom)
  }, [center, zoom, map])
  return null
}

export default function NavigationView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [currentLocation, setCurrentLocation] = useState<LocationData | null>(null)
  const [navEngine, setNavEngine] = useState<NavigationEngine | null>(null)
  const [navState, setNavState] = useState<NavigationState | null>(null)
  const [routeGeometry, setRouteGeometry] = useState<[number, number][] | null>(null)
  const [currentSpeed, setCurrentSpeed] = useState<number>(0)
  const [showUpcoming, setShowUpcoming] = useState(false)
  const navUpdateIntervalRef = useRef<number | null>(null)

  useEffect(() => {
    if (!id) return

    getIncident(id).then((data) => {
      setIncident(data)
      
      // Initialize navigation engine
      const engine = new NavigationEngine(
        [data.pickup_location.coordinates[1], data.pickup_location.coordinates[0]],
        [data.destination_location.coordinates[1], data.destination_location.coordinates[0]]
      )
      
      engine.fetchRoute(true).then((route) => {
        setRouteGeometry(route.geometry)
        setNavEngine(engine)
      })
    })

    // Start GPS tracking
    startTracking((location) => {
      setCurrentLocation(location)
      setCurrentSpeed(location.speed ? location.speed * 3.6 : 0) // m/s to km/h
    })

    return () => {
      stopTracking()
      if (navUpdateIntervalRef.current) {
        clearInterval(navUpdateIntervalRef.current)
      }
    }
  }, [id])

  useEffect(() => {
    if (navEngine && currentLocation) {
      const state = navEngine.updateLocation(currentLocation)
      setNavState(state)
    }
  }, [navEngine, currentLocation])

  if (!incident || !currentLocation || !navState) {
    return (
      <div className="h-screen bg-black flex items-center justify-center">
        <div className="text-white text-2xl">Initializing Navigation...</div>
      </div>
    )
  }

  const mapCenter: [number, number] = [currentLocation.latitude, currentLocation.longitude]
  const route = navEngine?.getRoute()
  const upcomingSteps = route?.steps.slice(navState.currentStep, navState.currentStep + 3) || []

  const getManeuverIcon = (instruction: string) => {
    const lower = instruction.toLowerCase()
    if (lower.includes('sharp left')) return '↰↰'
    if (lower.includes('left')) return '↰'
    if (lower.includes('sharp right')) return '↱↱'
    if (lower.includes('right')) return '↱'
    if (lower.includes('straight') || lower.includes('continue')) return '↑'
    if (lower.includes('arrive')) return '🏁'
    if (lower.includes('depart')) return '▶'
    return '↑'
  }

  const getManeuverColor = (instruction: string) => {
    const lower = instruction.toLowerCase()
    if (lower.includes('arrive')) return 'text-green-400'
    if (lower.includes('left')) return 'text-blue-400'
    if (lower.includes('right')) return 'text-yellow-400'
    return 'text-white'
  }

  return (
    <div className="h-screen bg-black relative overflow-hidden">
      {/* Full-Screen Map */}
      <MapContainer
        center={mapCenter}
        zoom={16}
        style={{ height: '100%', width: '100%', background: '#1a1a1a' }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater center={mapCenter} zoom={16} />

        {routeGeometry && (
          <Polyline
            positions={routeGeometry}
            pathOptions={{
              color: '#60a5fa',
              weight: 8,
              opacity: 0.9,
            }}
          />
        )}

        <Marker position={mapCenter} icon={ambulanceIcon} />
        
        {incident.destination_location && (
          <Marker position={[
            incident.destination_location.coordinates[1],
            incident.destination_location.coordinates[0]
          ]} />
        )}
      </MapContainer>

      {/* Top HUD - Next Maneuver */}
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black via-black/95 to-transparent p-6 z-[1000]">
        <div className="max-w-4xl mx-auto">
          {/* Main Instruction */}
          <div className="bg-gray-900/95 backdrop-blur-lg border-4 border-blue-500 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center gap-6">
              <div className={`text-8xl ${getManeuverColor(navState.nextInstruction)}`}>
                {getManeuverIcon(navState.nextInstruction)}
              </div>
              <div className="flex-1">
                <div className="text-6xl font-bold text-white mb-2">
                  {formatDistance(navState.distanceToNextStep)}
                </div>
                <div className="text-3xl font-semibold text-gray-300">
                  {navState.nextInstruction}
                </div>
              </div>
            </div>
          </div>

          {/* Upcoming Maneuvers Preview */}
          {upcomingSteps.length > 1 && (
            <div className="mt-4 bg-gray-900/90 backdrop-blur rounded-xl p-4 border border-gray-700">
              <div className="text-sm text-gray-400 uppercase tracking-wide mb-2">Then</div>
              <div className="space-y-2">
                {upcomingSteps.slice(1, 3).map((step, idx) => (
                  <div key={`upcoming-${idx}-${step.distance}`} className="flex items-center gap-3 text-white">
                    <span className="text-2xl">{getManeuverIcon(step.instruction)}</span>
                    <span className="text-lg">{step.instruction}</span>
                    <span className="text-sm text-gray-500 ml-auto">
                      {formatDistance(step.distance)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom HUD - Trip Info */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/95 to-transparent p-6 z-[1000]">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-900/95 backdrop-blur-lg rounded-2xl p-6 border border-gray-700 shadow-2xl">
            <div className="grid grid-cols-4 gap-6 text-center">
              {/* ETA */}
              <div>
                <div className="text-sm text-gray-400 uppercase tracking-wide mb-1">ETA</div>
                <div className="text-4xl font-bold text-green-400">
                  {navState.eta.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {formatDuration(navState.remainingTime)}
                </div>
              </div>

              {/* Distance */}
              <div>
                <div className="text-sm text-gray-400 uppercase tracking-wide mb-1">Distance</div>
                <div className="text-4xl font-bold text-blue-400">
                  {formatDistance(navState.remainingDistance)}
                </div>
              </div>

              {/* Speed */}
              <div>
                <div className="text-sm text-gray-400 uppercase tracking-wide mb-1">Speed</div>
                <div className="text-4xl font-bold text-white">
                  {Math.round(currentSpeed)}
                </div>
                <div className="text-sm text-gray-500 mt-1">km/h</div>
              </div>

              {/* Destination */}
              <div>
                <div className="text-sm text-gray-400 uppercase tracking-wide mb-1">To</div>
                <div className="text-xl font-bold text-white truncate">
                  {incident.destination_facility || 'Destination'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top Right - Controls */}
      <div className="absolute top-6 right-6 z-[1001] space-y-3">
        <button
          onClick={() => navigate(`/active-trip/${id}`)}
          className="bg-gray-900/95 backdrop-blur hover:bg-gray-800 text-white px-6 py-4 rounded-xl shadow-lg border border-gray-700 font-semibold text-lg transition-colors"
        >
          Exit Navigation
        </button>
        
        <button
          onClick={() => setShowUpcoming(!showUpcoming)}
          className="bg-blue-900/95 backdrop-blur hover:bg-blue-800 text-white px-6 py-4 rounded-xl shadow-lg border border-blue-700 font-semibold text-lg transition-colors w-full"
        >
          {showUpcoming ? 'Hide' : 'Show'} Steps
        </button>
      </div>

      {/* Full Step List Overlay */}
      {showUpcoming && route && (
        <div className="absolute left-6 top-32 bottom-32 w-96 z-[1001]">
          <div className="h-full bg-gray-900/98 backdrop-blur-xl rounded-2xl border border-gray-700 shadow-2xl overflow-hidden flex flex-col">
            <div className="bg-gray-800 px-6 py-4 border-b border-gray-700">
              <h3 className="text-xl font-bold text-white">All Turns</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {route.steps.map((step, idx) => (
                <div
                  key={`step-${idx}-${step.distance}`}
                  className={`p-4 rounded-lg border transition-colors ${
                    idx === navState.currentStep
                      ? 'bg-blue-600/30 border-blue-500'
                      : idx < navState.currentStep
                      ? 'bg-gray-800/50 border-gray-700 opacity-50'
                      : 'bg-gray-800 border-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={`text-3xl ${idx === navState.currentStep ? 'text-blue-400' : 'text-gray-500'}`}>
                      {getManeuverIcon(step.instruction)}
                    </span>
                    <div className="flex-1">
                      <div className={`font-semibold ${idx === navState.currentStep ? 'text-white' : 'text-gray-400'}`}>
                        {step.instruction}
                      </div>
                      <div className="text-sm text-gray-500">
                        {formatDistance(step.distance)}
                      </div>
                    </div>
                    {idx === navState.currentStep && (
                      <div className="text-green-400 font-bold">NOW</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
