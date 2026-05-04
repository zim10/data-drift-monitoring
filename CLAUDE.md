# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A data drift monitoring system for a customer churn prediction ML model. Detects feature drift, concept drift, and seasonal drift in production using FastAPI, Prometheus, Grafana, PostgreSQL, Docker, and AWS.

## Architecture

```
Real Users → FastAPI App → ML Model (from S3) → Predictions
                 ↓
           Prometheus         (collects metrics every 5s)
                 ↓
             Grafana           (visualizes drift trends)
                 ↓
           PostgreSQL          (stores prediction history)
```

All services run on AWS EC2 via Docker Compose, infrastructure provisioned with Pulumi.

## Project Structure

```
data-drift-monitoring/
├── fastapi-app/              # FastAPI with Prometheus metrics
├── drift-simulation/         # Simulates 4 phases of data drift
├── infrastructure/           # Pulumi AWS infrastructure
├── model-drift/              # Evidently AI drift detection
├── monitoring/               # Prometheus config
├── docker-compose.yml        # All 4 containers
└── requirements.txt
```

## Two Virtual Environments

This project has two venvs — this is normal:
- `.venv/` — your venv (awscli, boto3, pandas)
- `infrastructure/.venv/` — Pulumi's venv (auto-created)

## ⚠️ Poridhi Server Context

Every new session provides **fresh AWS credentials** — EC2, S3, and key pairs are all recreated. This means:

1. Run `pulumi refresh --yes` before `pulumi up --yes` to sync state
2. Create new SSH key pair each session: `aws ec2 create-key-pair --key-name key-pair-poridhi-poc ...`
3. Update S3 bucket name in multiple files (see Known Issues)

## Quick Start Commands

```bash
# Infrastructure
cd infrastructure
pulumi stack select zim10/data-drift-monitoring/dev
pulumi refresh --yes && pulumi up --yes

# Get outputs
pulumi stack output models_bucket_name

# Deploy on EC2
ssh -i infrastructure/key-pair-poridhi-poc.pem ubuntu@<EC2-IP>
docker-compose up -d
```

## Key Services

| Service | Port | URL |
|---------|------|-----|
| FastAPI | 8000 | http://<EC2-IP>:8000/docs |
| Prometheus | 9090 | http://<EC2-IP>:9090 |
| Grafana | 3000 | http://<EC2-IP>:3000 |

## API Endpoints

- `POST /predict` — Make churn predictions
- `GET /drift` — Get current drift scores
- `GET /health` — Health check
- `GET /metrics` — Prometheus metrics

## Model Drift (Evidently AI)

Scripts in `model-drift/scripts/`:
- `prediction-generator.py` — generates predictions from reference data
- `monitor.py` — generates HTML drift reports to S3

Run on EC2, not locally.

## Drift Simulation

`drift-simulation/drift_simulator.py` simulates 4 phases:
1. Phase 1 (50 batches) — Baseline, no drift
2. Phase 2 (100 batches) — Feature drift (charges increase)
3. Phase 3 (50 batches) — Concept drift
4. Phase 4 (50 batches) — Back to normal

Run locally, targets EC2 API.

## Known Issues

1. **Docker fails on EC2**: Use `docker.io` (not docker-ce), reboot if needed
2. **Pulumi state mismatch**: Run `pulumi refresh --yes` before `pulumi up`
3. **S3 bucket changes each session**: Update in `docker-compose.yml`, `model-drift/scripts/dataset-upload.py`, `model-drift/scripts/monitor.py`

## Files to Never Commit

- `.pem` files, `.env`, `model.pkl`, `*.csv`, `.venv/`
- Any file containing S3 bucket names

## For Detailed Setup

See README.md for full step-by-step instructions.