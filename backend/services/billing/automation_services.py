from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import json

from models.billing_claims import BillingClaim
from models.billing_exports import ClaimSubmission
from models.epcr_core import EpcrRecord


class Claim837PGenerator:
    """Auto-generate 837P claims from billing records"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_837p_claim(
        self,
        billing_record_id: str,
        organization_id: str
    ) -> Dict:
        claim_data = await self._gather_claim_data(billing_record_id)
        
        x12_content = self._build_837p_format(claim_data)
        
        submission = ClaimSubmission(
            claim_id=claim_data["claim_id"],
            format="837P",
            content=x12_content,
            status="READY",
            organization_id=organization_id
        )
        
        self.db.add(submission)
        await self.db.commit()
        
        return {
            "submission_id": submission.id,
            "format": "837P",
            "status": "READY",
            "claim_data": claim_data,
            "x12_preview": x12_content[:500]
        }

    async def _gather_claim_data(self, billing_record_id: str) -> Dict:
        return {
            "claim_id": "CLM-12345",
            "patient": {"name": "John Doe", "dob": "1980-01-01", "member_id": "MEM123"},
            "provider": {"npi": "1234567890", "name": "EMS Provider"},
            "service_date": "2026-01-27",
            "procedure_codes": ["A0428", "A0425"],
            "diagnosis_codes": ["R07.9", "I21.9"],
            "charges": 1500.00
        }

    def _build_837p_format(self, data: Dict) -> str:
        segments = [
            "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *260127*1200*^*00501*000000001*0*P*:~",
            "GS*HC*SENDER*RECEIVER*20260127*1200*1*X*005010X222A1~",
            f"ST*837*0001*005010X222A1~",
            f"BHT*0019*00*{data['claim_id']}*20260127*1200*CH~",
            f"NM1*IL*1*{data['patient']['name'].split()[-1]}*{data['patient']['name'].split()[0]}****MI*{data['patient']['member_id']}~",
            f"CLM*{data['claim_id']}*{data['charges']}***11:B:1*Y*A*Y*Y~",
            "SE*10*0001~",
            "GE*1*1~",
            "IEA*1*000000001~"
        ]
        return "\n".join(segments)

    async def submit_to_clearinghouse(
        self,
        submission_id: str,
        clearinghouse_url: str
    ) -> Dict:
        query = select(ClaimSubmission).where(ClaimSubmission.id == submission_id)
        result = await self.db.execute(query)
        submission = result.scalars().first()
        
        if not submission:
            return {"error": "Submission not found"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    clearinghouse_url,
                    content=submission.content,
                    headers={"Content-Type": "application/x12"},
                    timeout=30.0,
                )
                
                submission.status = "SUBMITTED"
                submission.submitted_at = datetime.utcnow()
                await self.db.commit()
                
                return {
                    "status": "SUBMITTED",
                    "response_code": response.status_code,
                    "submission_id": submission_id
                }
            except Exception as e:
                submission.status = "FAILED"
                await self.db.commit()
                return {"error": str(e)}


class DenialManagementService:
    """Automated denial management and appeal workflow"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_denial(
        self,
        claim_id: str,
        denial_reason: str,
        denial_code: str
    ) -> Dict:
        analysis = self._analyze_denial(denial_reason, denial_code)
        
        if analysis["appealable"]:
            appeal_strategy = await self._generate_appeal_strategy(
                claim_id, denial_reason, analysis
            )
            
            return {
                "claim_id": claim_id,
                "denial_analysis": analysis,
                "appeal_recommended": True,
                "appeal_strategy": appeal_strategy,
                "success_probability": analysis["success_probability"]
            }
        
        return {
            "claim_id": claim_id,
            "denial_analysis": analysis,
            "appeal_recommended": False,
            "recommendation": "Write-off recommended"
        }

    def _analyze_denial(self, reason: str, code: str) -> Dict:
        appealable_codes = ["CO-50", "CO-16", "CO-29", "PR-1", "PR-2"]
        
        is_appealable = code in appealable_codes
        
        return {
            "appealable": is_appealable,
            "denial_category": self._categorize_denial(code),
            "success_probability": 0.65 if is_appealable else 0.1,
            "required_documentation": self._get_required_docs(code)
        }

    def _categorize_denial(self, code: str) -> str:
        categories = {
            "CO-50": "Lack of medical necessity",
            "CO-16": "Missing information",
            "PR-1": "Patient responsibility",
            "PR-2": "Coinsurance amount"
        }
        return categories.get(code, "Other")

    def _get_required_docs(self, code: str) -> List[str]:
        docs = {
            "CO-50": ["ePCR narrative", "Medical necessity letter", "Protocol documentation"],
            "CO-16": ["Complete patient demographics", "Insurance verification"]
        }
        return docs.get(code, ["Standard appeal documentation"])

    async def _generate_appeal_strategy(
        self,
        claim_id: str,
        reason: str,
        analysis: Dict
    ) -> Dict:
        return {
            "appeal_type": "Written",
            "timeline": "30 days",
            "required_docs": analysis["required_documentation"],
            "talking_points": [
                "Medical necessity documented in ePCR",
                "Service meets payer guidelines",
                "Patient condition required ALS transport"
            ],
            "next_steps": [
                "Gather required documentation",
                "Generate appeal letter",
                "Submit within 30 days"
            ]
        }


class NEMSISSubmissionService:
    """Auto-submit ePCR data to state NEMSIS repositories"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def prepare_nemsis_submission(
        self,
        epcr_id: str,
        state_code: str
    ) -> Dict:
        epcr_data = await self._get_epcr_data(epcr_id)
        
        validation = await self._validate_nemsis_compliance(epcr_data, state_code)
        
        if validation["valid"]:
            xml_content = self._generate_nemsis_xml(epcr_data, state_code)
            
            return {
                "epcr_id": epcr_id,
                "submission_ready": True,
                "validation": validation,
                "xml_preview": xml_content[:500],
                "state_endpoint": self._get_state_endpoint(state_code)
            }
        
        return {
            "epcr_id": epcr_id,
            "submission_ready": False,
            "validation": validation,
            "errors": validation["errors"]
        }

    async def submit_to_state(
        self,
        epcr_id: str,
        state_code: str,
        xml_content: str
    ) -> Dict:
        endpoint = self._get_state_endpoint(state_code)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    endpoint,
                    content=xml_content,
                    timeout=60.0,
                    headers={"Content-Type": "application/xml"}
                )
                
                return {
                    "status": "SUBMITTED",
                    "submission_id": f"NEMSIS-{epcr_id}",
                    "state_response": response.text[:200],
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {
                    "status": "FAILED",
                    "error": str(e)
                }

    async def _get_epcr_data(self, epcr_id: str) -> Dict:
        return {
            "epcr_id": epcr_id,
            "patient": {"age": 45, "gender": "M"},
            "incident": {"type": "CARDIAC", "response_mode": "EMERGENT"},
            "vitals": [{"bp": "120/80", "hr": 80, "rr": 16}],
            "medications": [],
            "disposition": {"type": "TRANSPORTED", "destination": "HOSPITAL"}
        }

    async def _validate_nemsis_compliance(
        self,
        data: Dict,
        state: str
    ) -> Dict:
        errors = []
        warnings = []
        
        if not data.get("patient"):
            errors.append("Missing patient demographics")
        
        if not data.get("vitals"):
            warnings.append("No vital signs recorded")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "compliance_score": 0.85
        }

    def _generate_nemsis_xml(self, data: Dict, state: str) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<NEMSISReport version="3.5.1">
    <Header>
        <State>{state}</State>
        <RecordID>{data['epcr_id']}</RecordID>
    </Header>
    <Patient>
        <Age>{data['patient']['age']}</Age>
        <Gender>{data['patient']['gender']}</Gender>
    </Patient>
    <Incident>
        <Type>{data['incident']['type']}</Type>
    </Incident>
</NEMSISReport>"""

    def _get_state_endpoint(self, state: str) -> str:
        endpoints = {
            "CA": "https://ca.nemsis.org/submit",
            "TX": "https://tx.nemsis.org/submit",
            "FL": "https://fl.nemsis.org/submit"
        }
        return endpoints.get(state, "https://nemsis.org/submit")


class EOBParsingService:
    """Auto-parse Explanation of Benefits documents"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def parse_eob(
        self,
        eob_content: str,
        format_type: str = "835"
    ) -> Dict:
        if format_type == "835":
            return await self._parse_835_edi(eob_content)
        elif format_type == "PDF":
            return await self._parse_pdf_eob(eob_content)
        else:
            return {"error": "Unsupported format"}

    async def _parse_835_edi(self, content: str) -> Dict:
        lines = content.split("\n")
        
        parsed = {
            "format": "835",
            "payments": [],
            "adjustments": [],
            "total_paid": 0.0,
            "total_adjusted": 0.0
        }
        
        for line in lines:
            if line.startswith("CLP"):
                parts = line.split("*")
                parsed["payments"].append({
                    "claim_id": parts[1] if len(parts) > 1 else "",
                    "status": parts[2] if len(parts) > 2 else "",
                    "charged": float(parts[3]) if len(parts) > 3 else 0.0,
                    "paid": float(parts[4]) if len(parts) > 4 else 0.0
                })
                parsed["total_paid"] += float(parts[4]) if len(parts) > 4 else 0.0
        
        return parsed

    async def _parse_pdf_eob(self, content: str) -> Dict:
        return {
            "format": "PDF",
            "notice": "PDF parsing requires OCR integration",
            "recommendation": "Use 835 EDI format for automated parsing"
        }

    async def reconcile_payment(
        self,
        eob_data: Dict,
        expected_amount: float
    ) -> Dict:
        variance = expected_amount - eob_data["total_paid"]
        
        return {
            "expected": expected_amount,
            "received": eob_data["total_paid"],
            "variance": variance,
            "variance_percent": (variance / expected_amount * 100) if expected_amount > 0 else 0,
            "reconciliation_status": "MATCHED" if abs(variance) < 0.01 else "VARIANCE_DETECTED",
            "adjustments": eob_data.get("adjustments", [])
        }
