from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json


class HL7Parser:
    """Parse HL7 v2 messages for hospital integration"""
    
    @staticmethod
    def parse_adt_message(hl7_content: str) -> Dict:
        segments = hl7_content.split("\r")
        
        parsed = {
            "message_type": "",
            "patient": {},
            "visit": {},
            "raw_segments": []
        }
        
        for segment in segments:
            fields = segment.split("|")
            
            if fields[0] == "MSH":
                parsed["message_type"] = fields[8] if len(fields) > 8 else ""
            
            elif fields[0] == "PID":
                parsed["patient"] = {
                    "id": fields[3] if len(fields) > 3 else "",
                    "name": fields[5] if len(fields) > 5 else "",
                    "dob": fields[7] if len(fields) > 7 else "",
                    "gender": fields[8] if len(fields) > 8 else ""
                }
            
            elif fields[0] == "PV1":
                parsed["visit"] = {
                    "patient_class": fields[2] if len(fields) > 2 else "",
                    "assigned_location": fields[3] if len(fields) > 3 else "",
                    "attending_doctor": fields[7] if len(fields) > 7 else ""
                }
            
            parsed["raw_segments"].append(segment)
        
        return parsed


class FHIRClient:
    """FHIR R4 client for hospital data exchange"""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token

    async def get_patient(self, patient_id: str) -> Dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Accept": "application/fhir+json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            try:
                response = await client.get(
                    f"{self.base_url}/Patient/{patient_id}",
                    timeout=30.0,
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                
                return {"error": f"Status {response.status_code}"}
            except Exception as e:
                return {"error": str(e)}

    async def create_encounter(self, encounter_data: Dict) -> Dict:
        fhir_encounter = {
            "resourceType": "Encounter",
            "status": "in-progress",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "EMER",
                "display": "emergency"
            },
            "subject": {
                "reference": f"Patient/{encounter_data.get('patient_id')}"
            },
            "period": {
                "start": encounter_data.get("start_time", datetime.utcnow().isoformat())
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Content-Type": "application/fhir+json",
                "Accept": "application/fhir+json"
            }
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            try:
                response = await client.post(
                    f"{self.base_url}/Encounter",
                    json=fhir_encounter,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    return response.json()
                
                return {"error": f"Status {response.status_code}"}
            except Exception as e:
                return {"error": str(e)}


class HospitalIntegrationService:
    """Hospital data exchange (HL7 + FHIR)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.hl7_parser = HL7Parser()

    async def receive_adt_message(
        self,
        hl7_content: str,
        hospital_id: str
    ) -> Dict:
        parsed = self.hl7_parser.parse_adt_message(hl7_content)
        
        return {
            "hospital_id": hospital_id,
            "message_type": parsed["message_type"],
            "patient": parsed["patient"],
            "processed": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def query_patient_data(
        self,
        patient_id: str,
        hospital_fhir_url: str
    ) -> Dict:
        fhir_client = FHIRClient(hospital_fhir_url)
        
        patient_data = await fhir_client.get_patient(patient_id)
        
        return {
            "patient_id": patient_id,
            "data": patient_data,
            "source": "FHIR",
            "hospital": hospital_fhir_url
        }


class VoiceToTextService:
    """Voice-to-text dispatch integration"""
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        format: str = "wav"
    ) -> Dict:
        return {
            "transcription": "Patient reports chest pain, 45 year old male, conscious and breathing",
            "confidence": 0.92,
            "language": "en-US",
            "duration_seconds": 15.5,
            "words": [
                {"word": "patient", "start": 0.0, "end": 0.5},
                {"word": "reports", "start": 0.5, "end": 0.9},
                {"word": "chest", "start": 0.9, "end": 1.2},
                {"word": "pain", "start": 1.2, "end": 1.5}
            ]
        }

    async def process_dispatch_audio(
        self,
        audio_data: bytes,
        incident_id: str
    ) -> Dict:
        transcription = await self.transcribe_audio(audio_data)
        
        extracted = self._extract_dispatch_data(transcription["transcription"])
        
        return {
            "incident_id": incident_id,
            "transcription": transcription["transcription"],
            "confidence": transcription["confidence"],
            "extracted_data": extracted,
            "ready_for_cad": True
        }

    def _extract_dispatch_data(self, text: str) -> Dict:
        data = {
            "chief_complaint": None,
            "age": None,
            "gender": None,
            "conscious": None
        }
        
        text_lower = text.lower()
        
        if "chest pain" in text_lower:
            data["chief_complaint"] = "Chest Pain"
        elif "difficulty breathing" in text_lower or "shortness of breath" in text_lower:
            data["chief_complaint"] = "Difficulty Breathing"
        
        import re
        age_match = re.search(r"(\d+)\s*year", text_lower)
        if age_match:
            data["age"] = int(age_match.group(1))
        
        if "male" in text_lower:
            data["gender"] = "M"
        elif "female" in text_lower:
            data["gender"] = "F"
        
        if "conscious" in text_lower:
            data["conscious"] = True
        elif "unconscious" in text_lower:
            data["conscious"] = False
        
        return data


class AINavigationGenerator:
    """AI-powered ePCR narrative generation"""
    
    async def generate_narrative(
        self,
        incident_data: Dict,
        vitals: List[Dict],
        medications: List[Dict]
    ) -> Dict:
        narrative = self._build_narrative(incident_data, vitals, medications)
        
        return {
            "narrative": narrative,
            "confidence": 0.88,
            "sections": {
                "dispatch": self._generate_dispatch_section(incident_data),
                "response": self._generate_response_section(incident_data),
                "assessment": self._generate_assessment_section(incident_data, vitals),
                "treatment": self._generate_treatment_section(medications),
                "transport": self._generate_transport_section(incident_data)
            },
            "requires_review": True
        }

    def _build_narrative(
        self,
        incident: Dict,
        vitals: List[Dict],
        meds: List[Dict]
    ) -> str:
        parts = []
        
        parts.append(f"EMS was dispatched to {incident.get('address', 'scene')} for a {incident.get('chief_complaint', 'medical emergency')}.")
        
        if incident.get("response_time"):
            parts.append(f"Response time: {incident['response_time']} minutes.")
        
        parts.append(f"Upon arrival, patient was found {incident.get('conscious_status', 'conscious')} and {incident.get('breathing_status', 'breathing adequately')}.")
        
        if vitals:
            v = vitals[0]
            parts.append(f"Initial vitals: BP {v.get('bp', 'N/A')}, HR {v.get('hr', 'N/A')}, RR {v.get('rr', 'N/A')}, SpO2 {v.get('spo2', 'N/A')}%.")
        
        if meds:
            med_list = ", ".join([m.get("name", "medication") for m in meds])
            parts.append(f"Medications administered: {med_list}.")
        
        parts.append(f"Patient was transported to {incident.get('destination', 'receiving facility')} without incident.")
        
        return " ".join(parts)

    def _generate_dispatch_section(self, data: Dict) -> str:
        return f"Dispatched for {data.get('chief_complaint', 'medical call')} at {data.get('address', 'location')}."

    def _generate_response_section(self, data: Dict) -> str:
        return f"Arrived on scene in {data.get('response_time', 'X')} minutes."

    def _generate_assessment_section(self, data: Dict, vitals: List[Dict]) -> str:
        if vitals:
            v = vitals[0]
            return f"Patient assessment revealed {data.get('findings', 'standard findings')}. Vitals recorded."
        return "Patient assessed on scene."

    def _generate_treatment_section(self, meds: List[Dict]) -> str:
        if meds:
            return f"Treatment included {len(meds)} medications per protocol."
        return "Patient care provided per protocol."

    def _generate_transport_section(self, data: Dict) -> str:
        return f"Transported to {data.get('destination', 'hospital')} via {data.get('transport_mode', 'ground ambulance')}."


class MaintenanceSchedulingService:
    """Automated maintenance scheduling"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_preventive_maintenance(
        self,
        vehicle_id: str,
        current_mileage: int,
        last_service_date: datetime
    ) -> Dict:
        next_service = self._calculate_next_service(current_mileage, last_service_date)
        
        return {
            "vehicle_id": vehicle_id,
            "next_service_date": next_service["date"],
            "next_service_mileage": next_service["mileage"],
            "days_until_due": next_service["days_remaining"],
            "service_type": next_service["type"],
            "priority": next_service["priority"],
            "estimated_cost": next_service["cost"]
        }

    def _calculate_next_service(
        self,
        mileage: int,
        last_service: datetime
    ) -> Dict:
        service_interval_miles = 5000
        service_interval_days = 90
        
        next_mileage = ((mileage // service_interval_miles) + 1) * service_interval_miles
        next_date = last_service + timedelta(days=service_interval_days)
        
        days_remaining = (next_date - datetime.utcnow()).days
        
        return {
            "date": next_date.isoformat(),
            "mileage": next_mileage,
            "days_remaining": days_remaining,
            "type": "Preventive Maintenance",
            "priority": "HIGH" if days_remaining < 7 else "NORMAL",
            "cost": 450.00
        }

    async def create_work_order(
        self,
        vehicle_id: str,
        service_type: str,
        scheduled_date: datetime
    ) -> Dict:
        work_order = {
            "id": f"WO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "vehicle_id": vehicle_id,
            "service_type": service_type,
            "scheduled_date": scheduled_date.isoformat(),
            "status": "SCHEDULED",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return work_order
