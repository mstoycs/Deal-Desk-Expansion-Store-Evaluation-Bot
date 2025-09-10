# Eddie Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying Eddie to various environments.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [GitHub Upload](#github-upload)
5. [Production Checklist](#production-checklist)

## Local Development

### Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git
cd Deal-Desk-Expansion-Store-Evaluation-Bot

# 2. Run setup script
./scripts/setup.sh

# 3. Configure environment
cp env.template .env
# Edit .env with your settings

# 4. Start Eddie
./scripts/start_local.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app.py
```

## Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f eddie

# Stop
docker-compose down
```

### Using Dockerfile Only
```bash
# Build image
docker build -t eddie-bot .

# Run container
docker run -d \
  -p 5001:5001 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  --name eddie \
  eddie-bot

# Stop container
docker stop eddie
```

## Cloud Deployment

### Option 1: Heroku

1. **Install Heroku CLI**
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **Create Heroku App**
```bash
heroku create eddie-expansion-bot
```

3. **Add Buildpacks**
```bash
heroku buildpacks:add heroku/python
```

4. **Create Procfile**
```bash
echo "web: gunicorn app:app" > Procfile
```

5. **Deploy**
```bash
git push heroku main
```

6. **Scale Dynos**
```bash
heroku ps:scale web=1
```

### Option 2: AWS EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t3.medium (minimum)
   - Security Group: Open ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

2. **Connect and Setup**
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Clone repository
git clone https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git
cd Deal-Desk-Expansion-Store-Evaluation-Bot

# Start with Docker Compose
sudo docker-compose up -d
```

3. **Setup Nginx (Optional)**
```bash
# Install Nginx
sudo apt install nginx -y

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/eddie

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/eddie /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 3: Google Cloud Run

1. **Install gcloud CLI**
```bash
# Download and install from https://cloud.google.com/sdk/docs/install
```

2. **Build and Push Image**
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and tag
docker build -t gcr.io/YOUR-PROJECT-ID/eddie:latest .

# Push to GCR
docker push gcr.io/YOUR-PROJECT-ID/eddie:latest
```

3. **Deploy to Cloud Run**
```bash
gcloud run deploy eddie \
  --image gcr.io/YOUR-PROJECT-ID/eddie:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 5001 \
  --memory 2Gi \
  --cpu 2
```

### Option 4: DigitalOcean App Platform

1. **Connect GitHub Repository**
   - Go to DigitalOcean App Platform
   - Click "Create App"
   - Connect GitHub repository

2. **Configure App**
   - Choose Python buildpack
   - Set run command: `gunicorn app:app`
   - Configure environment variables

3. **Deploy**
   - Click "Deploy"
   - App will auto-deploy on push to main

## GitHub Upload

### Initial Setup

1. **Prepare Repository**
```bash
cd /Users/mattstoycos/Eddie-GitHub-Package
./upload_to_github.sh
```

2. **Configure Git**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

3. **Push to GitHub**
```bash
# If using HTTPS
git push -u origin main

# If using SSH
git remote set-url origin git@github.com:mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git
git push -u origin main
```

### GitHub Actions Setup

1. **Add Secrets**
   - Go to Settings → Secrets → Actions
   - Add required secrets:
     - `HEROKU_API_KEY`
     - `HEROKU_APP_NAME`
     - `HEROKU_EMAIL`
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`

2. **Enable Actions**
   - Go to Actions tab
   - Enable workflows

## Production Checklist

### Security
- [ ] Change default SECRET_KEY in .env
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Regular security updates

### Performance
- [ ] Configure caching
- [ ] Set up CDN for static assets
- [ ] Optimize Docker image size
- [ ] Configure auto-scaling
- [ ] Set up monitoring

### Monitoring
- [ ] Set up logging aggregation
- [ ] Configure error tracking (Sentry)
- [ ] Set up uptime monitoring
- [ ] Configure alerting
- [ ] Create dashboards

### Backup
- [ ] Regular data backups
- [ ] Test restore procedures
- [ ] Document recovery process

### Documentation
- [ ] Update README with deployment URL
- [ ] Document environment variables
- [ ] Create runbook for common issues
- [ ] Update API documentation

## Troubleshooting

### Common Issues

1. **Port Already in Use**
```bash
# Find process using port
lsof -i :5001
# Kill process
kill -9 <PID>
```

2. **Docker Build Fails**
```bash
# Clean Docker cache
docker system prune -a
# Rebuild without cache
docker build --no-cache -t eddie-bot .
```

3. **Module Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

4. **CORS Errors**
   - Check CORS_ORIGINS in .env
   - Ensure frontend URL is whitelisted
   - Verify headers in Flask app

## Support

For deployment issues:
1. Check logs: `docker-compose logs` or `heroku logs --tail`
2. Review this guide
3. Create GitHub issue
4. Contact #deal-desk-tools on Slack

---
Last Updated: September 2024
