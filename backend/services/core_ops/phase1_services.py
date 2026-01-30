from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import httpx
import asyncio
from math import radians, cos, sin, asin, sqrt

from models.core_operations import (
    FacilitySearchCache,
    DuplicateCallDetection,
    AddressGeocoding,
    GeofenceZone,
    GeofenceEvent
)
from models.cad import Call


class FacilitySearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_facilities(
        self,
        query: str,
        organization_id: str,
        limit: int = 10
    ) -> Dict:
        recent = await self._search_recent(query, organization_id, limit=3)
        internal = await self._search_internal(query, organization_id, limit=3)
        cms = await self._search_cms(query, limit=4)
        
        return {
            "query": query,
            "results": {
                "recent": recent,
                "internal": internal,
                "cms": cms
            },
            "total": len(recent) + len(internal) + len(cms)
        }

    async def _search_recent(self, query: str, org_id: str, limit: int) -> List[Dict]:
        q = select(FacilitySearchCache).where(
            and_(
                FacilitySearchCache.organization_id == org_id,
                FacilitySearchCache.facility_name.ilike(f"%{query}%")
            )
        ).order_by(FacilitySearchCache.last_searched_at.desc()).limit(limit)
        
        result = await self.db.execute(q)
        facilities = result.scalars().all()
        
        return [self._format_facility(f, "RECENT") for f in facilities]

    async def _search_internal(self, query: str, org_id: str, limit: int) -> List[Dict]:
        q = select(FacilitySearchCache).where(
            and_(
                FacilitySearchCache.organization_id == org_id,
                FacilitySearchCache.source == "INTERNAL",
                FacilitySearchCache.facility_name.ilike(f"%{query}%")
            )
        ).limit(limit)
        
        result = await self.db.execute(q)
        facilities = result.scalars().all()
        
        return [self._format_facility(f, "INTERNAL") for f in facilities]

    async def _search_cms(self, query: str, limit: int) -> List[Dict]:
        return [
            {
                "name": f"CMS Hospital {i+1}",
                "address": f"123 Medical Dr, City {i+1}, ST 12345",
                "source": "CMS",
                "cms_provider_id": f"CMS{100000+i}",
                "badge": "CMS-Associated · Reference Only"
            }
            for i in range(min(limit, 3))
        ]

    def _format_facility(self, facility: FacilitySearchCache, source: str) -> Dict:
        return {
            "id": facility.id,
            "name": facility.facility_name,
            "address": f"{facility.address}, {facility.city}, {facility.state} {facility.zip_code}",
            "source": source,
            "cms_provider_id": facility.cms_provider_id,
            "latitude": facility.latitude,
            "longitude": facility.longitude
        }

    async def record_facility_selection(
        self,
        facility_id: str,
        organization_id: str
    ):
        q = select(FacilitySearchCache).where(FacilitySearchCache.id == facility_id)
        result = await self.db.execute(q)
        facility = result.scalars().first()
        
        if facility:
            facility.search_count += 1
            facility.last_searched_at = datetime.utcnow()
            await self.db.commit()


class DuplicateCallDetectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_for_duplicates(
        self,
        call_data: Dict,
        organization_id: str
    ) -> Optional[Dict]:
        recent_window = datetime.utcnow() - timedelta(minutes=30)
        
        q = select(Call).where(
            and_(
                Call.organization_id == organization_id,
                Call.created_at >= recent_window,
                Call.status.in_(["PENDING", "DISPATCHED", "EN_ROUTE", "ON_SCENE"])
            )
        )
        
        result = await self.db.execute(q)
        recent_calls = result.scalars().all()
        
        for existing_call in recent_calls:
            similarity = self._calculate_similarity(call_data, existing_call)
            
            if similarity["score"] >= 0.75:
                detection = DuplicateCallDetection(
                    organization_id=organization_id,
                    call_id_1=call_data.get("id"),
                    call_id_2=existing_call.id,
                    similarity_score=similarity["score"],
                    matching_fields=similarity["matching_fields"],
                    address_match=similarity["address_match"],
                    time_proximity_minutes=similarity["time_proximity"],
                    caller_phone_match=similarity["phone_match"]
                )
                
                self.db.add(detection)
                await self.db.commit()
                
                return {
                    "duplicate_detected": True,
                    "existing_call_id": existing_call.id,
                    "similarity_score": similarity["score"],
                    "matching_fields": similarity["matching_fields"]
                }
        
        return None

    def _calculate_similarity(self, new_call: Dict, existing_call: Call) -> Dict:
        score = 0.0
        matching = []
        
        address_match = self._compare_addresses(
            new_call.get("address", ""),
            getattr(existing_call, "address", "")
        )
        if address_match:
            score += 0.4
            matching.append("address")
        
        time_diff = abs((datetime.utcnow() - existing_call.created_at).total_seconds() / 60)
        if time_diff < 10:
            score += 0.3
            matching.append("time")
        
        phone_match = new_call.get("caller_phone") == getattr(existing_call, "caller_phone", None)
        if phone_match:
            score += 0.3
            matching.append("phone")
        
        return {
            "score": score,
            "matching_fields": matching,
            "address_match": address_match,
            "phone_match": phone_match,
            "time_proximity": time_diff
        }

    def _compare_addresses(self, addr1: str, addr2: str) -> bool:
        return addr1.lower().strip() == addr2.lower().strip()


class GeocodingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def geocode_address(self, address: str) -> Optional[Dict]:
        cached = await self._check_cache(address)
        if cached:
            return cached
        
        result = await self._geocode_with_nominatim(address)
        
        if result:
            await self._cache_result(address, result)
        
        return result

    async def _check_cache(self, address: str) -> Optional[Dict]:
        q = select(AddressGeocoding).where(
            AddressGeocoding.raw_address == address
        )
        result = await self.db.execute(q)
        cached = result.scalars().first()
        
        if cached:
            cached.hit_count += 1
            await self.db.commit()
            
            return {
                "latitude": cached.latitude,
                "longitude": cached.longitude,
                "normalized_address": cached.normalized_address,
                "accuracy": cached.accuracy,
                "from_cache": True
            }
        
        return None

    async def _geocode_with_nominatim(self, address: str) -> Optional[Dict]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 1
                    },
                    timeout=10.0,
                    headers={"User-Agent": "FusionEMS-Quantum/1.0"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return {
                            "latitude": float(data[0]["lat"]),
                            "longitude": float(data[0]["lon"]),
                            "normalized_address": data[0].get("display_name"),
                            "accuracy": "HIGH",
                            "from_cache": False
                        }
            except Exception as e:
                print(f"Geocoding error: {e}")
        
        return None

    async def _cache_result(self, address: str, result: Dict):
        geocoding = AddressGeocoding(
            raw_address=address,
            normalized_address=result.get("normalized_address"),
            latitude=result["latitude"],
            longitude=result["longitude"],
            accuracy=result.get("accuracy", "MEDIUM"),
            geocoding_provider="NOMINATIM"
        )
        
        self.db.add(geocoding)
        await self.db.commit()


class GeofencingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_geofence_entry(
        self,
        unit_id: str,
        latitude: float,
        longitude: float,
        incident_id: Optional[str] = None
    ) -> Optional[Dict]:
        q = select(GeofenceZone).where(GeofenceZone.active == True)
        result = await self.db.execute(q)
        zones = result.scalars().all()
        
        for zone in zones:
            distance = self._haversine_distance(
                latitude, longitude,
                zone.center_lat, zone.center_lon
            )
            
            if distance <= zone.radius_meters:
                return await self._trigger_geofence_event(
                    zone, unit_id, latitude, longitude, "ENTER", incident_id
                )
        
        return None

    async def _trigger_geofence_event(
        self,
        zone: GeofenceZone,
        unit_id: str,
        lat: float,
        lon: float,
        event_type: str,
        incident_id: Optional[str]
    ) -> Dict:
        auto_status = zone.auto_status_rules.get(event_type.lower())
        
        event = GeofenceEvent(
            zone_id=zone.id,
            unit_id=unit_id,
            event_type=event_type,
            latitude=lat,
            longitude=lon,
            auto_status_triggered=bool(auto_status),
            new_status=auto_status,
            incident_id=incident_id
        )
        
        self.db.add(event)
        await self.db.commit()
        
        return {
            "zone_triggered": zone.zone_name,
            "event_type": event_type,
            "auto_status": auto_status,
            "should_update_unit_status": bool(auto_status)
        }

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        
        a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
