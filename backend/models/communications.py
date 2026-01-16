from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from core.database import Base


class CommsThread(Base):
    __tablename__ = "comms_threads"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    channel = Column(String, default="sms")
    subject = Column(String, default="")
    priority = Column(String, default="Normal")
    status = Column(String, default="open")
    linked_resource = Column(String, default="")
    participants = Column(JSON, nullable=False, default=list)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsMessage(Base):
    __tablename__ = "comms_messages"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    thread_id = Column(Integer, ForeignKey("comms_threads.id"), nullable=False)
    sender = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    media_url = Column(String, default="")
    delivery_status = Column(String, default="queued")
    tags = Column(JSON, nullable=False, default=list)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsCallLog(Base):
    __tablename__ = "comms_call_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    caller = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    direction = Column(String, default="outbound")
    duration_seconds = Column(Integer, default=0)
    recording_url = Column(String, default="")
    disposition = Column(String, default="unknown")
    call_state = Column(String, default="INITIATED")
    external_call_id = Column(String, default="", index=True)
    last_event = Column(String, default="")
    dtmf_digits = Column(String, default="")
    thread_id = Column(Integer, ForeignKey("comms_threads.id"), nullable=True)
    linked_object_type = Column(String, default="")
    linked_object_id = Column(String, default="")
    classification = Column(String, default="ops")
    answered_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsBroadcast(Base):
    __tablename__ = "comms_broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    target = Column(String, default="all")
    status = Column(String, default="draft")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsTask(Base):
    __tablename__ = "comms_tasks"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    thread_id = Column(Integer, ForeignKey("comms_threads.id"), nullable=True)
    title = Column(String, nullable=False)
    owner = Column(String, default="")
    status = Column(String, default="open")
    due_at = Column(DateTime(timezone=True), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsCallEvent(Base):
    __tablename__ = "comms_call_events"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    call_id = Column(Integer, ForeignKey("comms_call_logs.id"), nullable=True)
    external_call_id = Column(String, default="", index=True)
    event_type = Column(String, nullable=False, index=True)
    provider_event_id = Column(String, default="", index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsPhoneNumber(Base):
    __tablename__ = "comms_phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    e164 = Column(String, nullable=False)
    label = Column(String, default="")
    purpose = Column(String, default="ops")
    routing_policy_id = Column(Integer, ForeignKey("comms_routing_policies.id"), nullable=True)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsRoutingPolicy(Base):
    __tablename__ = "comms_routing_policies"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    mode = Column(String, default="ring_group")
    rules = Column(JSON, nullable=False, default=dict)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsRingGroup(Base):
    __tablename__ = "comms_ring_groups"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    members = Column(JSON, nullable=False, default=list)
    strategy = Column(String, default="simultaneous")
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsRecording(Base):
    __tablename__ = "comms_recordings"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    call_id = Column(Integer, ForeignKey("comms_call_logs.id"), nullable=True)
    provider_recording_id = Column(String, default="")
    recording_url = Column(String, default="")
    storage_key = Column(String, default="")
    sha256 = Column(String, default="")
    retention_policy_id = Column(Integer, ForeignKey("retention_policies.id"), nullable=True)
    legal_hold_count = Column(Integer, default=0)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsVoicemail(Base):
    __tablename__ = "comms_voicemails"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    call_id = Column(Integer, ForeignKey("comms_call_logs.id"), nullable=True)
    storage_key = Column(String, default="")
    recording_url = Column(String, default="")
    transcript = Column(Text, default="")
    retention_policy_id = Column(Integer, ForeignKey("retention_policies.id"), nullable=True)
    legal_hold_count = Column(Integer, default=0)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommsTranscript(Base):
    __tablename__ = "comms_transcripts"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    call_id = Column(Integer, ForeignKey("comms_call_logs.id"), nullable=True)
    classification = Column(String, default="ops")
    transcript_text = Column(Text, default="")
    segments = Column(JSON, nullable=False, default=list)
    confidence = Column(Integer, default=0)
    evidence_hash = Column(String, default="")
    method_used = Column(String, default="local")
    retention_policy_id = Column(Integer, ForeignKey("retention_policies.id"), nullable=True)
    legal_hold_count = Column(Integer, default=0)
    training_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
