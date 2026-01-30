import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.epcr_core import EpcrRecord

logger = logging.getLogger(__name__)


class NEMSISExporter:
    """NEMSIS 3.5.1 export: payload dict and optional XML for state submission."""

    @staticmethod
    def export_record_to_nemsis(record: EpcrRecord, db: Optional[Session] = None) -> Dict[str, Any]:
        """Return NEMSIS payload (backward compatible: minimal if no db)."""
        if db is not None:
            from services.epcr.schematron_service import build_nemsis_element_map
            elements = build_nemsis_element_map(db, record)
            payload = {
                "record_id": record.id,
                "nemsis_version": record.nemsis_version or "3.5.1",
                "state": record.nemsis_state or "WI",
                "patient_id": record.patient_id,
                "incident_number": record.incident_number,
                "elements": elements,
            }
        else:
            disposition_ts = record.hospital_arrival_datetime.isoformat() if record.hospital_arrival_datetime else None
            payload = {
                "record_id": record.id,
                "nemsis_version": record.nemsis_version or "3.5.1",
                "state": record.nemsis_state or "WI",
                "patient_id": record.patient_id,
                "incident_number": record.incident_number,
                "eDisposition.24": disposition_ts,
                "protocol_pathway": record.protocol_pathway_id,
            }
        logger.info("NEMSIS export payload prepared: record_id=%s", record.id)
        return payload

    @staticmethod
    def elements_to_xml(elements: Dict[str, Any], state: str = "WI", nemsis_version: str = "3.5.1") -> str:
        """Produce NEMSIS 3.x-style XML fragment from element map for state submission."""
        root = ET.Element("EMSDataSet")
        root.set("version", nemsis_version)
        root.set("state", state)
        data = ET.SubElement(root, "Data")
        for eid, value in elements.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            elem = ET.SubElement(data, "Element")
            elem.set("id", eid)
            elem.text = str(value).strip()
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode", method="xml")
