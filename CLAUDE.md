# CLAUDE.md — Data Drift Monitoring Project

## Project Overview
A data drift monitoring system for a customer churn prediction ML model.
Detects feature drift, concept drift, and seasonal drift in production using
FastAPI, Prometheus, Grafana, PostgreSQL, Docker, and AWS.

## Project Structure
```
data-drift-monitoring/
├── fastapi-app/
│   ├── main.py              # FastAPI app with Prometheus metrics
│   ├── models.py            # PostgreSQL models (SQLAlchemy)
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Container for FastAPI app
├── drift-simulation/
│   ├── drift_simulator.py   # Simulates 4 phases of data drift
│   └── requirements.txt     # Simulator dependencies
├── infrastructure/
│   ├── __main__.py          # Pulumi AWS infrastructure code
│   ├── Pulumi.yaml          # Pulumi project config
│   ├── Pulumi.dev.yaml      # Pulumi dev stack config
│   └── requirements.txt     # Pulumi dependencies
├── monitoring/
│   └── prometheus.yml       # Prometheus scrape config
├── docker-compose.yml       # Runs all 4 containers together
├── CLAUDE.md                # This file
├── .gitignore
└── README.md
```

## Tech Stack
- **FastAPI** — serves ML model as REST API
- **Prometheus** — collects and stores metrics
- **Grafana** — visualizes drift trends (port 3000)
- **PostgreSQL** — stores prediction history
- **Docker + Docker Compose** — containerizes everything
- **AWS EC2** — cloud server to host all containers
- **AWS S3** — stores trained ML model (model.pkl)
- **Pulumi** — provisions AWS infrastructure with Python

## How to Start Fresh on Poridhi Server

### 1. Clone the repo
```bash
git clone https://github.com/your-username/data-drift-monitoring.git
cd data-drift-monitoring
```

### 2. Setup infrastructure virtual environment
```bash
cd infrastructure
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure AWS credentials
```bash
aws configure
# Enter: Access Key, Secret Key, region (us-east-1), format (json)
```

### 4. Create SSH key pair (if not exists)
```bash
aws ec2 create-key-pair \
  --key-name key-pair-poridhi-poc \
  --query 'KeyMaterial' \
  --output text > key-pair-poridhi-poc.pem
chmod 400 key-pair-poridhi-poc.pem
```

### 5. Deploy AWS infrastructure
```bash
pulumi up --yes
# Note down: EC2 Public IP and S3 Bucket Name from output
```

### 6. Upload model to S3
```bash
cd ..
curl -o model.pkl https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Model/logistic_regression_model.pkl
# Create and run s3_model_deploy.py with your bucket name
# (do not push this file to GitHub)
```

### 7. SSH into EC2 and deploy
```bash
ssh -i infrastructure/key-pair-poridhi-poc.pem ubuntu@<EC2-PUBLIC-IP>
git clone https://github.com/your-username/data-drift-monitoring.git
cd data-drift-monitoring
docker-compose up -d
```

### 8. Run drift simulator (on Poridhi, not EC2)
```bash
cd drift-simulation
pip install -r requirements.txt
curl -o WA_FnUseC_TelcoCustomerChurn.csv \
  https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Data/Telco-Customer-Churn.csv
# Update EC2 IP in drift_simulator.py first!
python3 drift_simulator.py
```

## Docker Commands

```bash
# Start all containers
docker-compose up -d

# Stop all containers
docker-compose down

# Check running containers
docker ps

# View logs
docker logs churn-api
docker logs prometheus
docker logs grafana
docker logs postgres

# Restart a specific container
docker restart churn-api
```

## Key URLs (replace with your EC2 IP)
- FastAPI Docs: http://<EC2-IP>:8000/docs
- FastAPI Health: http://<EC2-IP>:8000/health
- FastAPI Drift: http://<EC2-IP>:8000/drift
- Prometheus: http://<EC2-IP>:9090
- Grafana: http://<EC2-IP>:3000 (admin/admin)

## API Endpoints
- POST /predict — Make churn predictions
- GET /drift — Get current drift scores
- GET /health — Health check
- GET /metrics — Prometheus metrics endpoint

## Prometheus Queries for Grafana
- Feature drift score: `churn_feature_drift`
- Total predictions: `churn_prediction_count_total`
- API latency: `churn_prediction_latency_seconds`
- Input feature values: `churn_input_feature`
- Prediction distribution: `churn_prediction_distribution`

## Drift Simulation Phases
- Phase 1 (50 batches) — No drift, baseline data
- Phase 2 (100 batches) — Gradual feature drift, charges increase
- Phase 3 (50 batches) — Concept drift, behavior patterns change
- Phase 4 (50 batches) — Back to normal patterns

## Important Rules
- NEVER push: .pem files, .env, model.pkl, *.csv, .venv/
- ALWAYS run git status before pushing
- Use feature branches for new features: git checkout -b feature/name
- s3_model_deploy.py contains bucket name — never push it

## Git Workflow
```bash
# Check status before anything
git status

# Push specific folder
git add fastapi-app/
git commit -m "Update FastAPI app"
git push

# Push everything
git add -A
git commit -m "Your message"
git push
```

## Project Roadmap
- [x] Phase 1 — Basic drift monitoring (FastAPI + Prometheus + Grafana)
- [ ] Phase 2 — Model drift detection
- [ ] Phase 3 — Automated alerting in Grafana
- [ ] Phase 4 — Automated retraining trigger
- [ ] Phase 5 — CI/CD pipeline
