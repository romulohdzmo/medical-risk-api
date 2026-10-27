# Clinical Risk Analysis API (`medical-risk-api`)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-e92063.svg)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Production%20Ready-2496ED.svg)](https://www.docker.com/)
[![uv](https://img.shields.io/badge/uv-Package%20Manager-DE5FE9.svg)](https://github.com/astral-sh/uv)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)

A production-grade, containerized microservice for clinical physiological metrics, vital sign assessments, and calibrated cardiovascular risk modeling with explainable AI (XAI) and asynchronous regulatory audit trails.

Designed specifically for **HealthTech, Clinical Decision Support Systems (CDSS), and Remote Patient Monitoring (RPM)** workflows.

---

## Key Features

- **Strict Physiological Boundary Validation:** Implemented via Pydantic v2 schemas to reject clinically implausible vital signs at the API boundary before reaching inference engines.
- **Calibrated ML Inference:** 10-year cardiovascular risk probability calibrated via isotonic/sigmoid regressions on standardized clinical feature distributions.
- **Feature Explainability (XAI):** Real-time linear contribution scores detailing the top physiological drivers behind high-risk scores.
- **Regulatory Audit Trail:** Asynchronous event logging backed by SQLAlchemy 2.0 and SQLite/PostgreSQL, tracking correlation IDs (`X-Correlation-ID`), inputs, model versions, and latency headers.
- **Deterministic Toolchain:** Packaged with `uv`, fully typed with `mypy`, formatted with `ruff`, and verified through 17 automated integration tests with `pytest`.
- **Multi-Stage Containerization:** Minimal, non-root Docker builds with health checks and persistent volume storage.

---

## Architectural Overview

```text
[Client / EHR / Wearable]
            │
            ▼  (HTTP POST + X-Correlation-ID)
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Gateway                                             │
│  ├── ClinicalAuditMiddleware (Latency, UUID tracing)        │
│  ├── Pydantic v2 Validation (Physiological boundaries)       │
│  └── Router                                                 │
│       ├── /vitals/map (Mean Arterial Pressure)              │
│       ├── /vitals/bmi (Body Mass Index classification)      │
│       ├── /risk/cardiovascular (ML inference + XAI)         │
│       └── /audits/records (Regulatory compliance query)     │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ Scikit-Learn Calibrator      │ │ SQLAlchemy 2.0 Async ORM   │
│  - StandardScaler            │ │  - Audit Trail Log         │
│  - Logistic Regression (XAI) │ │  - SQLite / Postgres DB   │
│  - Calibrated Probabilities  │ │    (Persistent Volume)     │
└──────────────────────────────┘ └────────────────────────────┘