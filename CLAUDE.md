# CLAUDE.md — Data Drift Monitoring Project

## Project Overview
A data drift monitoring system for a customer churn prediction ML model.
Uses FastAPI, Prometheus, Grafana, PostgreSQL, Docker, and AWS.

## Project Structure
- fastapi-app/ — FastAPI app with Prometheus metrics
- drift-simulation/ — Data drift simulator script
- infrastructure/ — Pulumi AWS infrastructure code
- monitoring/ — Prometheus configuration
- docker-compose.yml — Runs all containers together

## How to Run

### Start all containers
docker-compose up -d

### Stop all containers
docker-compose down

### Check running containers
docker ps

### View logs
docker logs churn-api
docker logs prometheus
docker logs grafana

## Key URLs
- FastAPI docs: http://<EC2-IP>:8000/docs
- Prometheus: http://<EC2-IP>:9090
- Grafana: http://<EC2-IP>:3000 (admin/admin)

## API Endpoints
- POST /predict — Make churn predictions
- GET /drift — Get current drift scores
- GET /health — Health check
- GET /metrics — Prometheus metrics

## Important Rules
- Never push .pem files, .env, model.pkl or *.csv
- Always run git status before pushing
- Use feature branches for new features

## Tech Stack
- FastAPI, Prometheus, Grafana, PostgreSQL
- Docker, AWS EC2, AWS S3, Pulumi

## Current Status
- [x] Phase 1 — Basic drift monitoring
- [ ] Phase 2 — Model drift detection
- [ ] Phase 3 — Automated retraining