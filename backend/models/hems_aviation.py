from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Date, Time
from datetime import datetime, date
from core.config import settings
from core.database import HemsBase

HEMS_SCHEMA = None if settings.DATABASE_URL.startswith("sqlite") else "hems"
SCHEMA_PREFIX = f"{HEMS_SCHEMA}." if HEMS_SCHEMA else ""
SCHEMA_ARGS = {"schema": HEMS_SCHEMA} if HEMS_SCHEMA else {}


class HemsFlightLog(HemsBase):
    """Flight hour logging for FAA compliance"""
    __tablename__ = "hems_flight_logs"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"), nullable=True)
    aircraft_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_aircraft.id"), nullable=False)
    pilot_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_crew.id"), nullable=False)
    
    flight_date = Column(Date, nullable=False)
    departure_airport = Column(String(4))
    arrival_airport = Column(String(4))
    
    hobbs_start = Column(Float, nullable=False)
    hobbs_end = Column(Float, nullable=False)
    tach_start = Column(Float)
    tach_end = Column(Float)
    
    flight_time_minutes = Column(Integer, nullable=False)
    fuel_gallons_used = Column(Float)
    fuel_gallons_added = Column(Float)
    
    day_vfr_time = Column(Integer, default=0)
    night_vfr_time = Column(Integer, default=0)
    day_ifr_time = Column(Integer, default=0)
    night_ifr_time = Column(Integer, default=0)
    
    landings_day = Column(Integer, default=0)
    landings_night = Column(Integer, default=0)
    
    gps_track = Column(JSON)
    
    remarks = Column(Text)
    pilot_signature = Column(String)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)


class HemsAircraftMaintenance(HemsBase):
    """Aircraft maintenance tracking for FAA Part 135"""
    __tablename__ = "hems_aircraft_maintenance"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    aircraft_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_aircraft.id"), nullable=False)
    
    maintenance_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    hobbs_at_maintenance = Column(Float)
    tach_at_maintenance = Column(Float)
    airframe_hours_at_maintenance = Column(Float)
    
    completed_date = Column(Date, nullable=False)
    mechanic_name = Column(String, nullable=False)
    mechanic_certificate_number = Column(String, nullable=False)
    inspector_approval = Column(String)
    
    parts_replaced = Column(JSON)
    work_order_number = Column(String)
    cost = Column(Float)
    
    next_due_hobbs = Column(Float)
    next_due_date = Column(Date)
    next_due_type = Column(String)
    
    return_to_service = Column(Boolean, default=True)
    discrepancies_remaining = Column(Text)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)


class HemsAirworthinessDirective(HemsBase):
    """FAA Airworthiness Directive compliance tracking"""
    __tablename__ = "hems_airworthiness_directives"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    aircraft_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_aircraft.id"), nullable=False)
    
    ad_number = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    effective_date = Column(Date)
    
    compliance_status = Column(String, default="open")
    compliance_date = Column(Date)
    compliance_method = Column(Text)
    compliance_hobbs = Column(Float)
    
    recurring = Column(Boolean, default=False)
    recurring_interval_hours = Column(Float)
    recurring_interval_calendar = Column(String)
    
    next_due_hobbs = Column(Float)
    next_due_date = Column(Date)
    
    mechanic_name = Column(String)
    mechanic_certificate = Column(String)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HemsWeatherMinimums(HemsBase):
    """VFR/IFR weather minimums configuration"""
    __tablename__ = "hems_weather_minimums"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    base_name = Column(String, nullable=False)
    
    day_vfr_ceiling_feet = Column(Integer, default=800)
    day_vfr_visibility_miles = Column(Float, default=2.0)
    
    night_vfr_ceiling_feet = Column(Integer, default=1000)
    night_vfr_visibility_miles = Column(Float, default=3.0)
    
    ifr_ceiling_feet = Column(Integer, default=200)
    ifr_visibility_miles = Column(Float, default=0.5)
    
    max_wind_knots = Column(Integer, default=35)
    max_gusts_knots = Column(Integer, default=45)
    max_crosswind_knots = Column(Integer, default=20)
    
    icing_prohibited = Column(Boolean, default=True)
    thunderstorm_distance_nm = Column(Integer, default=20)
    
    night_operations_allowed = Column(Boolean, default=True)
    ifr_operations_allowed = Column(Boolean, default=False)
    
    special_minimums = Column(JSON)
    
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HemsWeatherDecisionLog(HemsBase):
    """Weather decision documentation for each flight"""
    __tablename__ = "hems_weather_decision_logs"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"))
    request_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_flight_requests.id"))
    
    decision = Column(String, nullable=False)
    decision_time = Column(DateTime, default=datetime.utcnow)
    decision_maker_id = Column(Integer, ForeignKey("users.id"))
    
    metar_text = Column(Text)
    taf_text = Column(Text)
    
    ceiling_feet = Column(Integer)
    visibility_miles = Column(Float)
    wind_direction = Column(Integer)
    wind_speed_knots = Column(Integer)
    wind_gusts_knots = Column(Integer)
    temperature_c = Column(Integer)
    dewpoint_c = Column(Integer)
    altimeter = Column(Float)
    
    flight_category = Column(String)
    
    tfrs_checked = Column(Boolean, default=True)
    tfrs_active = Column(JSON)
    notams_reviewed = Column(Boolean, default=True)
    notams_relevant = Column(JSON)
    
    icing_conditions = Column(Boolean, default=False)
    thunderstorms = Column(Boolean, default=False)
    
    justification = Column(Text)
    supervisor_override = Column(Boolean, default=False)
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)


class HemsPilotCurrency(HemsBase):
    """Pilot currency and certification tracking for Part 135"""
    __tablename__ = "hems_pilot_currency"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    pilot_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_crew.id"), nullable=False, unique=True)
    
    certificate_number = Column(String, nullable=False)
    certificate_type = Column(String)
    
    medical_class = Column(String, nullable=False)
    medical_issued = Column(Date)
    medical_expires = Column(Date)
    
    flight_review_date = Column(Date)
    flight_review_due = Column(Date)
    
    instrument_proficiency_check = Column(Date)
    instrument_currency_expires = Column(Date)
    
    last_6_approaches_date = Column(Date)
    last_3_takeoffs_day = Column(Date)
    last_3_landings_day = Column(Date)
    last_3_takeoffs_night = Column(Date)
    last_3_landings_night = Column(Date)
    
    nvg_currency_date = Column(Date)
    nvg_currency_expires = Column(Date)
    
    part_135_checkride_date = Column(Date)
    part_135_checkride_due = Column(Date)
    
    annual_recurrent_training = Column(Date)
    annual_training_due = Column(Date)
    
    crm_training_date = Column(Date)
    crm_training_due = Column(Date)
    
    total_flight_hours = Column(Float, default=0)
    total_pic_hours = Column(Float, default=0)
    total_night_hours = Column(Float, default=0)
    total_ifr_hours = Column(Float, default=0)
    total_nvg_hours = Column(Float, default=0)
    hours_in_type = Column(Float, default=0)
    
    type_ratings = Column(JSON)
    endorsements = Column(JSON)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HemsFlightDutyRecord(HemsBase):
    """Part 135 flight/duty time tracking"""
    __tablename__ = "hems_flight_duty_records"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    crew_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_crew.id"), nullable=False)
    
    duty_date = Column(Date, nullable=False)
    
    duty_start = Column(DateTime, nullable=False)
    duty_end = Column(DateTime)
    
    flight_time_minutes = Column(Integer, default=0)
    
    rest_start = Column(DateTime)
    rest_end = Column(DateTime)
    rest_adequate = Column(Boolean, default=True)
    
    rolling_7_day_flight_hours = Column(Float)
    rolling_7_day_duty_hours = Column(Float)
    rolling_30_day_flight_hours = Column(Float)
    
    consecutive_duty_days = Column(Integer, default=1)
    
    fatigue_call_used = Column(Boolean, default=False)
    fatigue_reason = Column(Text)
    
    violations = Column(JSON)
    compliance_notes = Column(Text)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)


class HemsChecklist(HemsBase):
    """Pre-flight and post-flight checklist definitions"""
    __tablename__ = "hems_checklists"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    checklist_name = Column(String, nullable=False)
    checklist_type = Column(String, nullable=False)
    aircraft_type = Column(String)
    
    version = Column(String, default="1.0")
    effective_date = Column(Date)
    
    items = Column(JSON, nullable=False)
    
    active = Column(Boolean, default=True)
    
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HemsChecklistCompletion(HemsBase):
    """Completed checklist records"""
    __tablename__ = "hems_checklist_completions"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    checklist_id = Column(Integer, ForeignKey("hems_checklists.id"), nullable=False)
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"))
    aircraft_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_aircraft.id"), nullable=False)
    
    completed_by_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_crew.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    hobbs_reading = Column(Float)
    fuel_quantity = Column(Float)
    
    item_results = Column(JSON, nullable=False)
    
    all_items_satisfactory = Column(Boolean, default=True)
    discrepancies = Column(JSON)
    
    signature = Column(String)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)


class HemsFRATAssessment(HemsBase):
    """Flight Risk Assessment Tool scoring"""
    __tablename__ = "hems_frat_assessments"
    __table_args__ = SCHEMA_ARGS
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    mission_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_missions.id"))
    request_id = Column(Integer, ForeignKey(f"{SCHEMA_PREFIX}hems_flight_requests.id"))
    
    assessed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessed_at = Column(DateTime, default=datetime.utcnow)
    
    weather_score = Column(Integer, default=0)
    crew_score = Column(Integer, default=0)
    aircraft_score = Column(Integer, default=0)
    mission_score = Column(Integer, default=0)
    patient_score = Column(Integer, default=0)
    environment_score = Column(Integer, default=0)
    
    total_score = Column(Integer, default=0)
    risk_level = Column(String)
    
    weather_factors = Column(JSON)
    crew_factors = Column(JSON)
    aircraft_factors = Column(JSON)
    mission_factors = Column(JSON)
    patient_factors = Column(JSON)
    environment_factors = Column(JSON)
    
    mitigations = Column(JSON)
    
    decision = Column(String)
    supervisor_required = Column(Boolean, default=False)
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    supervisor_decision = Column(String)
    supervisor_notes = Column(Text)
    
    training_mode = Column(Boolean, default=False)
    classification = Column(String, default="AVIATION_SAFETY")
    created_at = Column(DateTime, default=datetime.utcnow)
