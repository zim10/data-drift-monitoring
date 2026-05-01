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
│   └── Dockerfile           # Container for FastAPI app
├── drift-simulation/
│   └── drift_simulator.py   # Simulates 4 phases of data drift
├── infrastructure/
│   ├── __main__.py          # Pulumi AWS infrastructure code
│   ├── Pulumi.yaml          # Pulumi project config
│   ├── Pulumi.dev.yaml      # Pulumi dev stack config
│   └── requirements.txt     # Pulumi specific dependencies
├── monitoring/
│   └── prometheus.yml       # Prometheus scrape config
├── docker-compose.yml       # Runs all 4 containers together
├── requirements.txt         # ONE root level requirements for everything
├── CLAUDE.md                # This file
├── .gitignore
└── README.md
```

## ⚠️ Important: Two Virtual Environments

This project has two venvs — this is normal and expected:

```
data-drift-monitoring/
├── .venv/                ← YOUR venv (awscli, boto3, pandas...)
└── infrastructure/
    └── .venv/            ← PULUMI's venv (auto created by Pulumi)
```

Both are gitignored. Pulumi always manages its own venv automatically.

## Tech Stack
- **FastAPI** — serves ML model as REST API
- **Prometheus** — collects and stores metrics
- **Grafana** — visualizes drift trends (port 3000)
- **PostgreSQL** — stores prediction history
- **Docker + Docker Compose** — containerizes everything
- **AWS EC2** — cloud server to host all containers
- **AWS S3** — stores trained ML model (model.pkl)
- **Pulumi** — provisions AWS infrastructure with Python

---

## ⚠️ My Current Server Warning

Every new session gives you:
- NEW AWS Access Key and Secret Key
- FRESH AWS environment — EC2, S3, key pairs are all gone!
- Must reinstall tools every session (awscli, pulumi)
- Must run `pulumi refresh --yes` to clear old state

---

## How to Start Fresh on  Server

### Phase 1 — Install Tools

```bash
# Install Python venv
sudo apt update && sudo apt install python3-venv -y

# Clone repo
git clone https://github.com/zim10/data-drift-monitoring.git
cd data-drift-monitoring

# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install project packages
pip install -r requirements.txt

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version   # verify

# Install Pulumi
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin
pulumi version  # verify
```

### Phase 2 — Configure AWS and Deploy Infrastructure

```bash
# Configure new AWS credentials (new every Poridhi session!)
aws configure
# Enter: Access Key, Secret Key, region: us-east-1, format: json

# Verify credentials
aws sts get-caller-identity

# Go to infrastructure folder
cd infrastructure

# Create NEW SSH key pair (fresh every Poridhi session!)
aws ec2 create-key-pair \
  --key-name key-pair-poridhi-poc \
  --query 'KeyMaterial' \
  --output text > key-pair-poridhi-poc.pem
chmod 400 key-pair-poridhi-poc.pem

# Login to Pulumi
pulumi login

# Select existing stack
pulumi stack select zim10/data-drift-monitoring/dev

# Refresh state (clears old AWS resources — critical for Poridhi!)
pulumi refresh --yes

# Deploy fresh infrastructure
pulumi up --yes
# ✅ Note down EC2 Public IP and S3 Bucket Name from output!
```

### Phase 3 — Upload Model to S3

```bash
cd ..

# Download model
curl -o model.pkl https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Model/logistic_regression_model.pkl

# Create s3_model_deploy.py with your bucket name and run:
python3 s3_model_deploy.py
# ⚠️ Never push s3_model_deploy.py to GitHub!
```

### Phase 4 — Deploy on EC2

```bash
# SSH into EC2
ssh -i infrastructure/key-pair-poridhi-poc.pem ubuntu@<EC2-PUBLIC-IP>

# On EC2 — install Docker
# Install Docker on EC2
sudo apt update
sudo apt install -y docker.io    # use docker.io NOT docker-ce!
sudo systemctl start docker
sudo systemctl enable docker
sudo chmod 666 /var/run/docker.sock
sudo usermod -aG docker ${USER}
newgrp docker

# ⚠️ If Docker fails — reboot EC2 (kernel mismatch issue on AWS Ubuntu)
sudo reboot
# Wait 1-2 minutes then SSH back in
ssh -i infrastructure/key-pair-poridhi-poc.pem ubuntu@<EC2-PUBLIC-IP>
sudo chmod 666 /var/run/docker.sock
docker ps   # should work now!

# Clone repo and run containers
git clone https://github.com/zim10/data-drift-monitoring.git
cd data-drift-monitoring
docker-compose up -d

# Verify 4 containers running
docker ps
```

### Phase 5 — Run Drift Simulator

```bash
# Back on server (not EC2)
cd ~/data-drift-monitoring/drift-simulation

# Download dataset
curl -o WA_FnUseC_TelcoCustomerChurn.csv \
  https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Data/Telco-Customer-Churn.csv

# Update EC2 IP in drift_simulator.py first!
# Then run:
python3 drift_simulator.py
```

---

## Key Pulumi Commands

```bash
pulumi version                                        # check pulumi installed
pulumi login                                          # login to Pulumi cloud
pulumi stack select zim10/data-drift-monitoring/dev   # select stack
pulumi stack                                          # check stack and resources
pulumi preview                                        # preview what will be created
pulumi up --yes                                       # deploy infrastructure
pulumi refresh --yes                                  # sync state with real AWS
pulumi destroy --yes                                  # destroy all resources
pulumi stack ls                                       # list all stacks
```

---

## Docker Commands

```bash
docker-compose up -d          # start all containers
docker-compose down           # stop all containers
docker ps                     # check running containers
docker logs churn-api         # view API logs
docker logs prometheus        # view Prometheus logs
docker logs grafana           # view Grafana logs
docker logs postgres          # view DB logs
docker restart churn-api      # restart a container
```

---

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

---

## Important Rules
- NEVER push: .pem files, .env, model.pkl, *.csv, .venv/
- ALWAYS run git status before pushing
- s3_model_deploy.py contains bucket name — never push it
- Use feature branches for new features: git checkout -b feature/name

## Git Workflow
```bash
git status                          # always check first
git add fastapi-app/                # push specific folder
git add -A                          # push everything
git commit -m "your message"
git push
```

## Project Roadmap
- [x] Phase 1 — Basic drift monitoring (FastAPI + Prometheus + Grafana)
- [ ] Phase 2 — Model drift detection
- [ ] Phase 3 — Automated alerting in Grafana
- [ ] Phase 4 — Automated retraining trigger
- [ ] Phase 5 — CI/CD pipeline


## Known Issues

### Docker fails to start on EC2
**Error:** `Job for docker.service failed`
**Cause:** AWS Ubuntu EC2 has kernel mismatch
**Fix:**
1. Use `docker.io` instead of `docker-ce`
2. Run `sudo reboot`
3. SSH back in after 1-2 minutes
4. Run `sudo chmod 666 /var/run/docker.sock`

### Pulumi state mismatch
**Error:** Resources exist in state but not in AWS
**Cause:** Fresh Poridhi session = fresh AWS account
**Fix:** Run `pulumi refresh --yes` before `pulumi up --yes`