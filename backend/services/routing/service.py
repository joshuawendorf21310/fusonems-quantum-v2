import httpx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from shapely.geometry import Point, LineString, shape
from shapely.ops import nearest_points
from geoalchemy2.shape import from_shape, to_shape
from sqlalchemy.orm import Session
from models.routing import (
    TrafficEvent, 
    RouteCalculation, 
    TrafficFeedSource,
    RoutingConfig,
    TrafficSeverity,
    RoutingEngine,
    TrafficEventType
)
import logging

logger = logging.getLogger(__name__)


class RoutingService:
    """
    Routing and traffic-awareness service using OSM + Valhalla as primary,
    with optional paid API enhancement.
    """
    
    def __init__(self, db: Session, config: Optional[RoutingConfig] = None):
        self.db = db
        self.config = config or self._get_default_config()
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    def _get_default_config(self) -> RoutingConfig:
        config = self.db.query(RoutingConfig).first()
        if not config:
            config = RoutingConfig(
                id="default",
                valhalla_endpoint="http://valhalla:8002"
            )
            self.db.add(config)
            self.db.commit()
        return config
    
    async def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        incident_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        priority_level: Optional[str] = None,
        dispatcher_requested: bool = False,
        user_id: Optional[str] = None
    ) -> RouteCalculation:
        """
        Calculate route with traffic awareness.
        Always uses Valhalla as primary, optionally enhances with paid API.
        """
        start_time = datetime.utcnow()
        
        baseline_route = await self._calculate_valhalla_route(
            origin_lat, origin_lon, dest_lat, dest_lon
        )
        
        traffic_events = await self._get_active_traffic_on_route(
            baseline_route['geometry']
        )
        
        penalties = self._calculate_penalties(traffic_events)
        
        traffic_adjusted_route = None
        paid_api_used = False
        paid_api_cost = 0
        
        should_use_paid_api = (
            self.config.enable_paid_apis and
            dispatcher_requested and
            priority_level in self.config.high_priority_threshold.split(',') and
            len(traffic_events) > 0 and
            self._check_paid_api_budget()
        )
        
        if should_use_paid_api:
            try:
                traffic_adjusted_route = await self._calculate_paid_api_route(
                    origin_lat, origin_lon, dest_lat, dest_lon
                )
                paid_api_used = True
                paid_api_cost = 5
                await self._increment_api_spend(paid_api_cost)
            except Exception as e:
                logger.warning(f"Paid API failed, falling back to Valhalla: {e}")
                traffic_adjusted_route = await self._apply_penalties_to_valhalla(
                    origin_lat, origin_lon, dest_lat, dest_lon, penalties
                )
        elif penalties:
            traffic_adjusted_route = await self._apply_penalties_to_valhalla(
                origin_lat, origin_lon, dest_lat, dest_lon, penalties
            )
        
        calculation_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        route_calc = RouteCalculation(
            id=f"route_{datetime.utcnow().timestamp()}",
            incident_id=incident_id,
            unit_id=unit_id,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            destination_lat=dest_lat,
            destination_lon=dest_lon,
            routing_engine=RoutingEngine.MAPBOX if paid_api_used else RoutingEngine.VALHALLA,
            route_geometry=from_shape(LineString(baseline_route['geometry']), srid=4326),
            route_geojson=baseline_route['geojson'],
            baseline_eta_seconds=baseline_route['duration'],
            baseline_distance_meters=baseline_route['distance'],
            traffic_adjusted=traffic_adjusted_route is not None,
            traffic_adjusted_eta_seconds=traffic_adjusted_route['duration'] if traffic_adjusted_route else None,
            traffic_events_applied=[e.id for e in traffic_events],
            penalties_applied=penalties,
            calculation_time_ms=calculation_time,
            dispatcher_requested=dispatcher_requested,
            paid_api_used=paid_api_used,
            paid_api_cost_cents=paid_api_cost,
            created_by=user_id
        )
        
        self.db.add(route_calc)
        self.db.commit()
        
        return route_calc
    
    async def _calculate_valhalla_route(
        self, 
        origin_lat: float, 
        origin_lon: float, 
        dest_lat: float, 
        dest_lon: float
    ) -> Dict:
        """Calculate baseline route using Valhalla + OSM"""
        payload = {
            "locations": [
                {"lat": origin_lat, "lon": origin_lon},
                {"lat": dest_lat, "lon": dest_lon}
            ],
            "costing": "auto",
            "directions_options": {
                "units": "miles"
            }
        }
        
        response = await self.http_client.post(
            f"{self.config.valhalla_endpoint}/route",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        trip = data['trip']
        leg = trip['legs'][0]
        
        coords = []
        for point in leg['shape']:
            coords.append((point['lon'], point['lat']))
        
        return {
            'geometry': coords,
            'geojson': data,
            'duration': int(trip['summary']['time']),
            'distance': int(trip['summary']['length'] * 1609.34)
        }
    
    async def _apply_penalties_to_valhalla(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        penalties: List[Dict]
    ) -> Dict:
        """Apply traffic penalties to Valhalla routing using cost matrix"""
        payload = {
            "locations": [
                {"lat": origin_lat, "lon": origin_lon},
                {"lat": dest_lat, "lon": dest_lon}
            ],
            "costing": "auto",
            "costing_options": {
                "auto": {
                    "use_ferry": 0.0
                }
            }
        }
        
        if penalties:
            avoid_polygons = []
            for penalty in penalties:
                if penalty['severity'] == 'road_closure':
                    avoid_polygons.append({
                        "type": "Polygon",
                        "coordinates": penalty['geometry']
                    })
            
            if avoid_polygons:
                payload['exclude_polygons'] = avoid_polygons
        
        response = await self.http_client.post(
            f"{self.config.valhalla_endpoint}/route",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        trip = data['trip']
        leg = trip['legs'][0]
        
        return {
            'geometry': [(p['lon'], p['lat']) for p in leg['shape']],
            'duration': int(trip['summary']['time']),
            'distance': int(trip['summary']['length'] * 1609.34)
        }
    
    async def _calculate_paid_api_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict:
        """Calculate route using paid API (Mapbox) for traffic refinement"""
        if self.config.paid_api_provider == "mapbox":
            return await self._calculate_mapbox_route(
                origin_lat, origin_lon, dest_lat, dest_lon
            )
        raise ValueError(f"Unsupported paid API: {self.config.paid_api_provider}")
    
    async def _calculate_mapbox_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict:
        """Mapbox Directions API with live traffic"""
        from core.config import settings
        mapbox_token = settings.MAPBOX_ACCESS_TOKEN
        
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        params = {
            "access_token": mapbox_token,
            "geometries": "geojson",
            "overview": "full",
            "annotations": "duration,distance"
        }
        
        response = await self.http_client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        route = data['routes'][0]
        
        coords = route['geometry']['coordinates']
        
        return {
            'geometry': coords,
            'duration': int(route['duration']),
            'distance': int(route['distance'])
        }
    
    async def _get_active_traffic_on_route(
        self, 
        route_coords: List[Tuple[float, float]]
    ) -> List[TrafficEvent]:
        """Get active traffic events intersecting the route"""
        route_line = LineString(route_coords)
        buffer_meters = 500
        route_buffered = route_line.buffer(buffer_meters / 111000)
        
        active_events = self.db.query(TrafficEvent).filter(
            TrafficEvent.active == True,
            TrafficEvent.end_time > datetime.utcnow()
        ).all()
        
        intersecting = []
        for event in active_events:
            event_geom = to_shape(event.geometry)
            if route_buffered.intersects(event_geom):
                intersecting.append(event)
        
        return intersecting
    
    def _calculate_penalties(self, traffic_events: List[TrafficEvent]) -> List[Dict]:
        """Convert traffic events to routing penalties"""
        penalties = []
        
        for event in traffic_events:
            penalty_seconds = self.config.severity_penalties.get(
                event.severity.value, 60
            )
            
            event_geom = to_shape(event.geometry)
            
            penalties.append({
                'event_id': event.id,
                'severity': event.severity.value,
                'penalty_seconds': penalty_seconds,
                'geometry': event_geom.__geo_interface__['coordinates']
            })
        
        return penalties
    
    def _check_paid_api_budget(self) -> bool:
        """Check if paid API budget allows another call"""
        if self.config.paid_api_monthly_budget_cents == 0:
            return False
        
        return (
            self.config.paid_api_current_month_spend_cents < 
            self.config.paid_api_monthly_budget_cents
        )
    
    async def _increment_api_spend(self, cost_cents: int):
        """Increment paid API spend counter"""
        self.config.paid_api_current_month_spend_cents += cost_cents
        self.db.commit()


class TrafficFeedIngestionService:
    """
    Ingest open government traffic feeds (DOT/511)
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def poll_feed(self, feed_source: TrafficFeedSource):
        """Poll a single traffic feed and update events"""
        try:
            response = await self.http_client.get(feed_source.url)
            response.raise_for_status()
            
            data = response.json()
            
            events = self._parse_feed_data(data, feed_source)
            
            for event_data in events:
                await self._upsert_traffic_event(event_data, feed_source)
            
            feed_source.last_poll_at = datetime.utcnow()
            feed_source.last_success_at = datetime.utcnow()
            feed_source.events_ingested_count += len(events)
            self.db.commit()
            
            logger.info(f"Ingested {len(events)} events from {feed_source.name}")
            
        except Exception as e:
            feed_source.last_error = str(e)
            self.db.commit()
            logger.error(f"Failed to poll {feed_source.name}: {e}")
    
    def _parse_feed_data(
        self, 
        data: Dict, 
        feed_source: TrafficFeedSource
    ) -> List[Dict]:
        """Parse feed-specific format into normalized events"""
        events = []
        
        if feed_source.source_type == "511_json":
            for feature in data.get('features', []):
                events.append(self._parse_511_feature(feature))
        
        return events
    
    def _parse_511_feature(self, feature: Dict) -> Dict:
        """Parse 511 GeoJSON feature"""
        props = feature['properties']
        geom = feature['geometry']
        
        event_type = self._map_event_type(props.get('event_type', 'other'))
        severity = self._map_severity(props.get('severity', 'minor'))
        
        return {
            'source_event_id': props.get('id'),
            'event_type': event_type,
            'severity': severity,
            'title': props.get('description', 'Traffic incident'),
            'description': props.get('long_description'),
            'geometry': geom,
            'start_time': props.get('start_time'),
            'end_time': props.get('end_time'),
            'metadata': props
        }
    
    def _map_event_type(self, raw_type: str) -> TrafficEventType:
        """Map feed event type to internal enum"""
        mapping = {
            'accident': TrafficEventType.ACCIDENT,
            'crash': TrafficEventType.ACCIDENT,
            'closure': TrafficEventType.CLOSURE,
            'road_closure': TrafficEventType.CLOSURE,
            'construction': TrafficEventType.CONSTRUCTION,
            'work_zone': TrafficEventType.CONSTRUCTION,
            'congestion': TrafficEventType.CONGESTION,
            'hazard': TrafficEventType.HAZARD
        }
        return mapping.get(raw_type.lower(), TrafficEventType.OTHER)
    
    def _map_severity(self, raw_severity: str) -> TrafficSeverity:
        """Map feed severity to internal enum"""
        mapping = {
            'closure': TrafficSeverity.ROAD_CLOSURE,
            'closed': TrafficSeverity.ROAD_CLOSURE,
            'major': TrafficSeverity.MAJOR,
            'moderate': TrafficSeverity.MODERATE,
            'minor': TrafficSeverity.MINOR,
            'low': TrafficSeverity.MINOR
        }
        return mapping.get(raw_severity.lower(), TrafficSeverity.MINOR)
    
    async def _upsert_traffic_event(
        self, 
        event_data: Dict, 
        feed_source: TrafficFeedSource
    ):
        """Create or update traffic event"""
        source_id = event_data['source_event_id']
        
        existing = self.db.query(TrafficEvent).filter(
            TrafficEvent.source == feed_source.name,
            TrafficEvent.source_event_id == source_id
        ).first()
        
        geom_shape = shape(event_data['geometry'])
        
        if existing:
            existing.title = event_data['title']
            existing.description = event_data['description']
            existing.severity = event_data['severity']
            existing.event_type = event_data['event_type']
            existing.geometry = from_shape(geom_shape, srid=4326)
            existing.last_updated = datetime.utcnow()
            existing.active = True
        else:
            event = TrafficEvent(
                id=f"{feed_source.name}_{source_id}",
                source=feed_source.name,
                source_event_id=source_id,
                event_type=event_data['event_type'],
                severity=event_data['severity'],
                title=event_data['title'],
                description=event_data['description'],
                geometry=from_shape(geom_shape, srid=4326),
                geometry_type=event_data['geometry']['type'],
                start_time=event_data.get('start_time', datetime.utcnow()),
                end_time=event_data.get('end_time', datetime.utcnow() + timedelta(hours=2)),
                metadata=event_data.get('metadata', {})
            )
            self.db.add(event)
        
        self.db.commit()
