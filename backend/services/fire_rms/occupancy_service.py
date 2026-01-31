"""
Fire RMS - Occupancy Database Service
Target hazards, high-risk properties, occupancy tracking, stakeholder management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from models.fire_rms import PreFirePlan, FireInspection
from pydantic import BaseModel


class OccupancyProfile(BaseModel):
    property_id: int
    risk_level: str
    last_inspection: Optional[date]
    last_incident: Optional[date]
    notes: str


class TargetHazardCreate(BaseModel):
    property_name: str
    property_address: str
    occupancy_type: str
    risk_factors: List[str]
    priority_level: int  # 1-5, 5 being highest
    contact_name: str
    contact_phone: str
    special_considerations: Optional[str] = None


class OccupancyService:
    """Occupancy database management and target hazard tracking"""
    
    # Risk factors
    RISK_FACTORS = [
        "high_occupancy",
        "hazardous_materials",
        "limited_access",
        "no_sprinklers",
        "elderly_residents",
        "disabled_occupants",
        "high_rise",
        "basement_occupancy",
        "wood_frame_construction",
        "previous_fire_history",
        "code_violations"
    ]
    
    # Occupancy risk levels
    RISK_LEVELS = {
        "low": 1,
        "moderate": 2,
        "elevated": 3,
        "high": 4,
        "critical": 5
    }
    
    @staticmethod
    async def get_all_occupancies(
        db: AsyncSession,
        org_id: int,
        training_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Get comprehensive occupancy database from pre-plans and inspections"""
        # Get all pre-plans
        preplans_result = await db.execute(
            select(PreFirePlan).where(
                and_(
                    PreFirePlan.org_id == org_id,
                    PreFirePlan.training_mode == training_mode
                )
            )
        )
        preplans = preplans_result.scalars().all()
        
        # Get all inspections for these properties in a single query
        property_addresses = [preplan.property_address for preplan in preplans]
        if property_addresses:
            inspections_result = await db.execute(
                select(FireInspection).where(
                    and_(
                        FireInspection.org_id == org_id,
                        FireInspection.property_address.in_(property_addresses)
                    )
                ).order_by(
                    FireInspection.property_address,
                    FireInspection.inspection_date.desc()
                )
            )
            all_inspections = inspections_result.scalars().all()
            
            # Group inspections by property_address, keeping only the latest for each
            latest_inspections = {}
            for inspection in all_inspections:
                if inspection.property_address not in latest_inspections:
                    latest_inspections[inspection.property_address] = inspection
        else:
            latest_inspections = {}
        
        occupancies = []
        for preplan in preplans:
            # Get latest inspection for this property from the pre-loaded dict
            latest_inspection = latest_inspections.get(preplan.property_address)
            
            # Calculate risk score
            risk_score = OccupancyService._calculate_risk_score(preplan, latest_inspection)
            
            occupancies.append({
                "id": preplan.id,
                "property_name": preplan.property_name,
                "property_address": preplan.property_address,
                "occupancy_type": preplan.occupancy_type,
                "occupant_load": preplan.occupant_load,
                "risk_score": risk_score,
                "risk_level": OccupancyService._risk_score_to_level(risk_score),
                "hazmat_present": preplan.hazardous_materials_present,
                "last_inspection": latest_inspection.inspection_date if latest_inspection else None,
                "inspection_status": latest_inspection.status if latest_inspection else "never_inspected",
                "preplan_exists": True,
                "contact": {
                    "name": preplan.property_manager_name,
                    "phone": preplan.property_manager_phone
                }
            })
        
        # Sort by risk score descending
        occupancies.sort(key=lambda x: x["risk_score"], reverse=True)
        return occupancies
    
    @staticmethod
    def _calculate_risk_score(
        preplan: PreFirePlan,
        inspection: Optional[FireInspection]
    ) -> int:
        """Calculate risk score based on multiple factors"""
        score = 0
        
        # Hazmat presence (highest risk)
        if preplan.hazardous_materials_present:
            score += 50
        
        # High occupancy
        if preplan.occupant_load:
            if preplan.occupant_load >= 100:
                score += 30
            elif preplan.occupant_load >= 50:
                score += 20
            elif preplan.occupant_load >= 25:
                score += 10
        
        # Height
        if preplan.number_of_floors:
            if preplan.number_of_floors >= 5:
                score += 25
            elif preplan.number_of_floors >= 3:
                score += 15
        
        # No sprinkler system
        if not preplan.sprinkler_system:
            score += 20
        
        # Construction type risk
        if preplan.construction_type:
            if "Wood Frame" in preplan.construction_type:
                score += 15
        
        # Inspection history
        if inspection:
            if inspection.violations_found > 0:
                score += inspection.violations_found * 2
            if inspection.critical_violations > 0:
                score += inspection.critical_violations * 10
        else:
            # Never inspected
            score += 25
        
        return min(score, 100)  # Cap at 100
    
    @staticmethod
    def _risk_score_to_level(score: int) -> str:
        """Convert numeric risk score to risk level"""
        if score >= 70:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 30:
            return "elevated"
        elif score >= 15:
            return "moderate"
        else:
            return "low"
    
    @staticmethod
    async def get_target_hazards(
        db: AsyncSession,
        org_id: int,
        min_risk_score: int = 50
    ) -> List[Dict[str, Any]]:
        """Get high-priority target hazards"""
        all_occupancies = await OccupancyService.get_all_occupancies(db, org_id)
        
        target_hazards = [
            occ for occ in all_occupancies
            if occ["risk_score"] >= min_risk_score
        ]
        
        return target_hazards
    
    @staticmethod
    async def get_occupancies_by_type(
        db: AsyncSession,
        org_id: int,
        occupancy_type: str
    ) -> List[Dict[str, Any]]:
        """Get all occupancies of specific type"""
        all_occupancies = await OccupancyService.get_all_occupancies(db, org_id)
        
        filtered = [
            occ for occ in all_occupancies
            if occ["occupancy_type"].lower() == occupancy_type.lower()
        ]
        
        return filtered
    
    @staticmethod
    async def get_hazmat_locations(
        db: AsyncSession,
        org_id: int,
        training_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all locations with hazardous materials"""
        result = await db.execute(
            select(PreFirePlan).where(
                and_(
                    PreFirePlan.org_id == org_id,
                    PreFirePlan.training_mode == training_mode,
                    PreFirePlan.hazardous_materials_present == True
                )
            ).order_by(PreFirePlan.property_name)
        )
        
        hazmat_locations = []
        for preplan in result.scalars().all():
            hazmat_locations.append({
                "id": preplan.id,
                "property_name": preplan.property_name,
                "property_address": preplan.property_address,
                "occupancy_type": preplan.occupancy_type,
                "hazmat_types": preplan.hazmat_types,
                "latitude": preplan.latitude,
                "longitude": preplan.longitude,
                "emergency_contact": {
                    "name": preplan.emergency_contact_name,
                    "phone": preplan.emergency_contact_phone
                }
            })
        
        return hazmat_locations
    
    @staticmethod
    async def get_unprotected_properties(
        db: AsyncSession,
        org_id: int,
        min_square_footage: int = 5000
    ) -> List[Dict[str, Any]]:
        """Get large properties without sprinkler systems"""
        result = await db.execute(
            select(PreFirePlan).where(
                and_(
                    PreFirePlan.org_id == org_id,
                    PreFirePlan.sprinkler_system == False,
                    PreFirePlan.square_footage >= min_square_footage
                )
            ).order_by(PreFirePlan.square_footage.desc())
        )
        
        unprotected = []
        for preplan in result.scalars().all():
            unprotected.append({
                "id": preplan.id,
                "property_name": preplan.property_name,
                "property_address": preplan.property_address,
                "square_footage": preplan.square_footage,
                "occupancy_type": preplan.occupancy_type,
                "occupant_load": preplan.occupant_load,
                "construction_type": preplan.construction_type,
                "recommendation": "Consider sprinkler system installation or increased inspection frequency"
            })
        
        return unprotected
    
    @staticmethod
    async def get_high_occupancy_locations(
        db: AsyncSession,
        org_id: int,
        min_occupant_load: int = 50
    ) -> List[Dict[str, Any]]:
        """Get locations with high occupant loads"""
        result = await db.execute(
            select(PreFirePlan).where(
                and_(
                    PreFirePlan.org_id == org_id,
                    PreFirePlan.occupant_load >= min_occupant_load
                )
            ).order_by(PreFirePlan.occupant_load.desc())
        )
        
        high_occupancy = []
        for preplan in result.scalars().all():
            high_occupancy.append({
                "id": preplan.id,
                "property_name": preplan.property_name,
                "property_address": preplan.property_address,
                "occupancy_type": preplan.occupancy_type,
                "occupant_load": preplan.occupant_load,
                "sprinkler_system": preplan.sprinkler_system,
                "fire_alarm_type": preplan.fire_alarm_type,
                "egress_considerations": f"{preplan.occupant_load} occupants require adequate exits"
            })
        
        return high_occupancy
    
    @staticmethod
    async def get_inspection_priority_list(
        db: AsyncSession,
        org_id: int,
        max_days_since_inspection: int = 365
    ) -> List[Dict[str, Any]]:
        """Generate inspection priority list based on risk and inspection date"""
        all_occupancies = await OccupancyService.get_all_occupancies(db, org_id)
        
        priority_list = []
        cutoff_date = date.today() - timedelta(days=max_days_since_inspection)
        
        for occ in all_occupancies:
            needs_inspection = False
            priority_reason = []
            
            # High risk
            if occ["risk_score"] >= 50:
                needs_inspection = True
                priority_reason.append(f"High risk score ({occ['risk_score']})")
            
            # Overdue inspection
            if occ["last_inspection"]:
                if occ["last_inspection"] < cutoff_date:
                    needs_inspection = True
                    days_since = (date.today() - occ["last_inspection"]).days
                    priority_reason.append(f"Overdue inspection ({days_since} days)")
            else:
                needs_inspection = True
                priority_reason.append("Never inspected")
            
            # Failed inspection
            if occ["inspection_status"] in ["failed", "failed_critical"]:
                needs_inspection = True
                priority_reason.append("Previous inspection failed")
            
            if needs_inspection:
                priority_list.append({
                    "property_name": occ["property_name"],
                    "property_address": occ["property_address"],
                    "risk_level": occ["risk_level"],
                    "risk_score": occ["risk_score"],
                    "last_inspection": occ["last_inspection"],
                    "priority_reasons": priority_reason,
                    "contact": occ["contact"]
                })
        
        # Sort by risk score
        priority_list.sort(key=lambda x: x["risk_score"], reverse=True)
        return priority_list
    
    @staticmethod
    async def generate_stakeholder_contact_list(
        db: AsyncSession,
        org_id: int,
        occupancy_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate contact list for stakeholder outreach"""
        conditions = [PreFirePlan.org_id == org_id]
        
        if occupancy_types:
            conditions.append(PreFirePlan.occupancy_type.in_(occupancy_types))
        
        result = await db.execute(
            select(PreFirePlan).where(and_(*conditions)).order_by(PreFirePlan.property_name)
        )
        
        contacts = []
        for preplan in result.scalars().all():
            contacts.append({
                "property_name": preplan.property_name,
                "property_address": preplan.property_address,
                "occupancy_type": preplan.occupancy_type,
                "property_manager": {
                    "name": preplan.property_manager_name,
                    "phone": preplan.property_manager_phone
                },
                "emergency_contact": {
                    "name": preplan.emergency_contact_name,
                    "phone": preplan.emergency_contact_phone
                }
            })
        
        return contacts
    
    @staticmethod
    async def get_occupancy_statistics(
        db: AsyncSession,
        org_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive occupancy database statistics"""
        all_occupancies = await OccupancyService.get_all_occupancies(db, org_id)
        
        # Risk level breakdown
        risk_breakdown = {
            "critical": 0,
            "high": 0,
            "elevated": 0,
            "moderate": 0,
            "low": 0
        }
        
        for occ in all_occupancies:
            risk_breakdown[occ["risk_level"]] += 1
        
        # Occupancy type breakdown
        type_breakdown = {}
        for occ in all_occupancies:
            occ_type = occ["occupancy_type"]
            if occ_type not in type_breakdown:
                type_breakdown[occ_type] = 0
            type_breakdown[occ_type] += 1
        
        # Protection statistics
        with_sprinklers = sum(1 for occ in all_occupancies if occ.get("sprinkler_system"))
        with_hazmat = sum(1 for occ in all_occupancies if occ["hazmat_present"])
        
        return {
            "total_occupancies": len(all_occupancies),
            "risk_level_breakdown": risk_breakdown,
            "occupancy_type_breakdown": type_breakdown,
            "protection_statistics": {
                "with_sprinklers": with_sprinklers,
                "without_sprinklers": len(all_occupancies) - with_sprinklers,
                "hazmat_locations": with_hazmat
            }
        }
