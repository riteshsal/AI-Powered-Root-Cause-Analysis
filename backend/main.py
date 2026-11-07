import json

from fastapi import FastAPI
from pydantic import BaseModel

from database import get_db
from models import (
    Investigation,
    Evidence,
    FiveWhy,
    RootCause,
    MissingEvidence,
    CapaAction,
)
from rca import rca_graph


app = FastAPI(title="AI RCA Investigator")


class RCARequest(BaseModel):
    source_text: str


@app.get("/")
def root():
    return {"message": "AI RCA Investigator API is running"}


@app.post("/api/rca/analyze")
def analyze_rca(request: RCARequest):

    # 1. Run LangGraph
    initial_state = {
        "source_text": request.source_text
    }

    result = rca_graph.invoke(initial_state)

    # 2. Convert AI JSON strings into Python objects
    incident = json.loads(result["incident"])
    evidence_data = json.loads(result["evidence"])
    five_whys_data = json.loads(result["five_whys"])
    root_causes_data = json.loads(result["root_causes"])
    missing_evidence_data = json.loads(result["missing_evidence"])
    capa_data = json.loads(result["capa"])

    # 3. Open database session
    db = next(get_db())

    try:

        # -----------------------------------
        # Save Investigation
        # -----------------------------------

        investigation = Investigation(
            product_name=incident.get("product_name"),
            batch_number=incident.get("batch_number"),
            incident_type=incident.get("incident_type"),
            incident_date=incident.get("incident_date") or None,
            process_step=incident.get("process_step"),
            description=incident.get("description"),
            observed_result=incident.get("observed_result"),
            specification=incident.get("specification"),
            status="AI Suggested"
        )

        db.add(investigation)
        db.commit()
        db.refresh(investigation)

        # -----------------------------------
        # Save Evidence
        # -----------------------------------

        for item in evidence_data.get("evidence", []):

            evidence = Evidence(
                investigation_id=investigation.id,
                evidence_text=item.get("evidence_text"),
                source=item.get("source"),
                confidence=item.get("confidence")
            )

            db.add(evidence)

        # -----------------------------------
        # Save 5 Whys
        # -----------------------------------

        for item in five_whys_data.get("five_whys", []):

            why = FiveWhy(
                investigation_id=investigation.id,
                why_number=item.get("why_number"),
                question=item.get("question"),
                answer=item.get("answer"),
                evidence=item.get("evidence"),
                status=item.get("status")
            )

            db.add(why)

        # -----------------------------------
        # Save Root Causes
        # -----------------------------------

        for item in root_causes_data.get("root_causes", []):

            root_cause = RootCause(
                investigation_id=investigation.id,
                cause=item.get("cause"),
                category=item.get("category"),
                supporting_evidence=item.get("supporting_evidence"),
                confidence=item.get("confidence"),
                status=item.get("status", "Pending Review")
            )

            db.add(root_cause)

        # -----------------------------------
        # Save Missing Evidence
        # -----------------------------------

        for item in missing_evidence_data.get("missing_evidence", []):

            missing = MissingEvidence(
                investigation_id=investigation.id,
                evidence_required=item.get("evidence_required"),
                reason=item.get("reason"),
                status=item.get("status")
            )

            db.add(missing)

        # -----------------------------------
        # Save CAPA
        # -----------------------------------

        for item in capa_data.get("capa", []):

            capa = CapaAction(
                investigation_id=investigation.id,
                action_type=item.get("action_type"),
                action=item.get("action"),
                reason=item.get("reason"),
                effectiveness_check=item.get("effectiveness_check"),
                status=item.get("status", "Proposed"),
                owner=item.get("owner") or None,
                due_date=item.get("due_date") or None
            )

            db.add(capa)

        # Save all related records
        db.commit()

        return {
            "investigation_id": investigation.id,
            "incident": incident,
            "evidence": evidence_data,
            "five_whys": five_whys_data,
            "root_causes": root_causes_data,
            "missing_evidence": missing_evidence_data,
            "capa": capa_data
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



@app.get("/api/rca/investigations")
def get_investigations():
    db = next(get_db())

    try:
        investigations = db.query(Investigation).order_by(
            Investigation.created_at.desc()
        ).all()

        return [
            {
                "id": investigation.id,
                "product_name": investigation.product_name,
                "batch_number": investigation.batch_number,
                "incident_type": investigation.incident_type,
                "incident_date": investigation.incident_date,
                "process_step": investigation.process_step,
                "description": investigation.description,
                "observed_result": investigation.observed_result,
                "specification": investigation.specification,
                "status": investigation.status,
            }
            for investigation in investigations
        ]

    finally:
        db.close()


@app.get("/api/rca/investigations/{investigation_id}")
def get_investigation(investigation_id: int):
    db = next(get_db())

    try:
        investigation = (
            db.query(Investigation)
            .filter(Investigation.id == investigation_id)
            .first()
        )

        if not investigation:
            return {"error": "Investigation not found"}

        evidence = (
            db.query(Evidence)
            .filter(Evidence.investigation_id == investigation_id)
            .all()
        )

        five_whys = (
            db.query(FiveWhy)
            .filter(FiveWhy.investigation_id == investigation_id)
            .order_by(FiveWhy.why_number)
            .all()
        )

        root_causes = (
            db.query(RootCause)
            .filter(RootCause.investigation_id == investigation_id)
            .all()
        )

        missing_evidence = (
            db.query(MissingEvidence)
            .filter(MissingEvidence.investigation_id == investigation_id)
            .all()
        )

        capa = (
            db.query(CapaAction)
            .filter(CapaAction.investigation_id == investigation_id)
            .all()
        )

        return {
            "investigation": {
                "id": investigation.id,
                "product_name": investigation.product_name,
                "batch_number": investigation.batch_number,
                "incident_type": investigation.incident_type,
                "incident_date": investigation.incident_date,
                "process_step": investigation.process_step,
                "description": investigation.description,
                "observed_result": investigation.observed_result,
                "specification": investigation.specification,
                "status": investigation.status,
            },

            "evidence": [
                {
                    "id": item.id,
                    "evidence_text": item.evidence_text,
                    "source": item.source,
                    "confidence": item.confidence,
                }
                for item in evidence
            ],

            "five_whys": [
                {
                    "id": item.id,
                    "why_number": item.why_number,
                    "question": item.question,
                    "answer": item.answer,
                    "evidence": item.evidence,
                    "status": item.status,
                }
                for item in five_whys
            ],

            "root_causes": [
                {
                    "id": item.id,
                    "cause": item.cause,
                    "category": item.category,
                    "supporting_evidence": item.supporting_evidence,
                    "confidence": item.confidence,
                    "status": item.status,
                }
                for item in root_causes
            ],

            "missing_evidence": [
                {
                    "id": item.id,
                    "evidence_required": item.evidence_required,
                    "reason": item.reason,
                    "status": item.status,
                }
                for item in missing_evidence
            ],

            "capa": [
                {
                    "id": item.id,
                    "action_type": item.action_type,
                    "action": item.action,
                    "reason": item.reason,
                    "effectiveness_check": item.effectiveness_check,
                    "status": item.status,
                    "owner": item.owner,
                    "due_date": item.due_date,
                }
                for item in capa
            ],
        }

    finally:
        db.close()




