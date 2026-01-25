import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { CadCall, CadUnit } from './DualScreenCAD'

type MapViewProps = {
  calls: CadCall[]
  units: CadUnit[]
  selectedCallId: number | null
}

export default function MapView({ calls, units, selectedCallId }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null)
  const layerRef = useRef<L.LayerGroup | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const tileUrl = import.meta.env.VITE_MAP_TILE_URL
    if (!containerRef.current || mapRef.current || !tileUrl) return
    const centerCandidate = calls[0] ?? units[0]
    if (!centerCandidate) return
    const center: [number, number] = [centerCandidate.latitude, centerCandidate.longitude]
    const map = L.map(containerRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView(center, 12)
    L.tileLayer(tileUrl, {
      attribution: import.meta.env.VITE_MAP_ATTRIBUTION || '',
    }).addTo(map)
    mapRef.current = map
    layerRef.current = L.layerGroup().addTo(map)
  }, [calls, units])

  useEffect(() => {
    if (!mapRef.current || !layerRef.current) return
    layerRef.current.clearLayers()
    calls.forEach((call) => {
      const color = call.id === selectedCallId ? '#ff6a00' : '#ff1f1f'
      const marker = L.circleMarker([call.latitude, call.longitude], {
        radius: 8,
        color,
        fillColor: color,
        fillOpacity: 0.8,
      }).bindPopup(`Call #${call.id} · ${call.priority}`)
      marker.addTo(layerRef.current!)
    })
    units.forEach((unit) => {
      const marker = L.circleMarker([unit.latitude, unit.longitude], {
        radius: 6,
        color: '#53d1ff',
        fillColor: '#53d1ff',
        fillOpacity: 0.8,
      }).bindPopup(`Unit ${unit.unit_identifier} · ${unit.status}`)
      marker.addTo(layerRef.current!)
    })
  }, [calls, units, selectedCallId])

  if (!import.meta.env.VITE_MAP_TILE_URL) {
    return (
      <div className="panel cad-map cad-map-empty">
        <p className="empty-state">Map tiles are not configured for this environment.</p>
      </div>
    )
  }

  return <div ref={containerRef} className="panel cad-map" aria-label="CAD map" />
}
