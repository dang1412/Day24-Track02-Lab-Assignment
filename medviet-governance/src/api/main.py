# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

RAW_DATA_PATH = "data/raw/patients_raw.csv"


@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """Trả về raw patient data — chỉ admin được phép."""
    df = pd.read_csv(RAW_DATA_PATH)
    return JSONResponse(content=df.head(10).to_dict(orient="records"))


@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """Trả về anonymized data — ml_engineer và admin được phép."""
    df = pd.read_csv(RAW_DATA_PATH)
    df_anon = anonymizer.anonymize_dataframe(df.head(10))
    return JSONResponse(content=df_anon.to_dict(orient="records"))


@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Trả về aggregated metrics — data_analyst, ml_engineer, admin."""
    df = pd.read_csv(RAW_DATA_PATH)
    metrics = {
        "total_patients": len(df),
        "by_disease": df["benh"].value_counts().to_dict(),
        "avg_test_result": round(df["ket_qua_xet_nghiem"].mean(), 2),
        "min_test_result": round(df["ket_qua_xet_nghiem"].min(), 2),
        "max_test_result": round(df["ket_qua_xet_nghiem"].max(), 2),
    }
    return JSONResponse(content=metrics)


@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Chỉ admin được xóa bệnh nhân."""
    df = pd.read_csv(RAW_DATA_PATH)
    if patient_id not in df["patient_id"].values:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    df = df[df["patient_id"] != patient_id]
    df.to_csv(RAW_DATA_PATH, index=False)
    return {"status": "deleted", "patient_id": patient_id}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
