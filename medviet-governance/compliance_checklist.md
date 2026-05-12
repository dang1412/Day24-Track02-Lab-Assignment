# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam — deploy on VN-based cloud (VNG Cloud / FPT Cloud)
- [x] Backup cũng phải ở trong lãnh thổ VN — replication chỉ sang AZ trong VN
- [x] Log việc transfer data ra ngoài nếu có — OPA policy block export khi `destination_country != "VN"`

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training — consent form + digital signature lúc đăng ký
- [x] Có mechanism để user rút consent (Right to Erasure) — DELETE /api/patients/{id} endpoint (admin-only)
- [x] Lưu consent record với timestamp — bảng `consent_records` trong DB với created_at, revoked_at

## C. Breach Notification (72h)
- [x] Có incident response plan — IRP document tại `docs/incident_response_plan.md`
- [x] Alert tự động khi phát hiện breach — Prometheus alerting rule kích hoạt khi anomaly access pattern
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h — on-call runbook với template báo cáo đến Bộ TT&TT

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn | +84-28-XXXX-XXXX

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256-GCM at rest (SimpleVault), TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | FastAPI middleware ghi request log → ELK Stack | ✅ Done | Platform Team |
| Breach detection | Prometheus + Alertmanager: alert khi >100 failed auth/5min | ✅ Done | Security Team |

## F. Technical Solution cho các Todo

### Audit Logging — đã implement
- **Giải pháp:** FastAPI middleware bắt mọi request ghi vào structured log (JSON) bao gồm: `user_id`, `role`, `endpoint`, `action`, `timestamp`, `ip_address`, `status_code`.
- **Storage:** Log ship tới ELK Stack (Elasticsearch + Logstash + Kibana).
- **Retention:** 1 năm theo yêu cầu NĐ13 Điều 26.
- **Sample code:**
  ```python
  @app.middleware("http")
  async def audit_log_middleware(request: Request, call_next):
      response = await call_next(request)
      logger.info({
          "timestamp": datetime.utcnow().isoformat(),
          "path": request.url.path,
          "method": request.method,
          "status": response.status_code,
          "user": request.headers.get("X-User-Id", "anonymous"),
      })
      return response
  ```

### Breach Detection — đã implement
- **Giải pháp:** Prometheus scrape metrics từ FastAPI (via `prometheus-fastapi-instrumentator`).
- **Alert rules:**
  - `ALERT HighFailedAuth`: `rate(http_requests_total{status="401"}[5m]) > 20` → page on-call
  - `ALERT UnauthorizedDataAccess`: `rate(http_requests_total{status="403",path=~"/api/patients.*"}[5m]) > 5` → page security team
  - `ALERT BulkDataExport`: `increase(http_requests_total{path="/api/patients/raw"}[1h]) > 100` → suspicious bulk access
- **Response:** Alertmanager gửi PagerDuty + email DPO; auto-lock account nếu threshold vượt 3 lần trong 1h.

## G. Data Retention Policy
| Data Type | Retention Period | Deletion Method |
|-----------|-----------------|-----------------|
| Raw patient records | 10 năm (quy định y tế) | Secure erase + audit log |
| Anonymized training data | Vô thời hạn | N/A |
| Audit logs | 1 năm | Auto-archive then delete |
| Consent records | Suốt vòng đời + 5 năm | Soft delete với timestamp |
| Encryption keys (DEK) | Theo vòng đời dữ liệu | Key revocation + re-encryption |
