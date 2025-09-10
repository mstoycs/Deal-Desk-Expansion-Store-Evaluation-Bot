# Eddie - Deal Desk Expansion Store Evaluation Bot

## Overview
Eddie is an intelligent expansion store evaluation bot designed to analyze and assess potential expansion stores for Shopify merchants. It provides comprehensive analysis of product overlap, store features, and expansion readiness.

## Features
- 🔍 **Product Extraction & Matching**: Sophisticated algorithms to identify identical products across stores
- 📊 **Multi-Criteria Evaluation**: Analyzes product identity, services, branding, and B2B capabilities
- 🌐 **Web Interface**: User-friendly HTML interface for easy interaction
- 🚀 **API-First Design**: RESTful API for integration with other systems
- 📈 **Learning System**: Continuously improves through dynamic knowledge base updates

## Architecture
```
Eddie Platform
├── Core Components
│   ├── app.py                      # Flask API server
│   ├── expansion_store_evaluator.py # Core evaluation logic
│   ├── product_extractor.py        # Product discovery and extraction
│   ├── image_analyzer.py           # Visual similarity analysis
│   └── web_content_fetcher.py      # Web scraping utilities
├── Data Storage
│   └── dynamic_knowledge_base.json # Learned patterns and data
├── Web Interface
│   ├── eddie_localhost.html        # Local development UI
│   └── static/                     # Static assets
└── Deployment
    ├── Dockerfile                   # Container configuration
    ├── docker-compose.yml          # Multi-container setup
    └── .github/workflows/          # CI/CD pipelines
```

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git
- (Optional) Docker for containerized deployment

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git
cd Deal-Desk-Expansion-Store-Evaluation-Bot
```

2. **Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.template .env
# Edit .env with your configuration
```

5. **Start the Flask server**
```bash
python app.py
# Or use the provided script:
./start_eddie_localhost.sh
```

6. **Access Eddie**
- API: http://localhost:5001
- Web Interface: Open `eddie_localhost.html` in your browser

## Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f eddie

# Stop services
docker-compose down
```

### Using Dockerfile
```bash
# Build the image
docker build -t eddie-bot .

# Run the container
docker run -d -p 5001:5001 --name eddie eddie-bot

# View logs
docker logs -f eddie

# Stop the container
docker stop eddie
```

## Cloud Deployment

### Heroku
```bash
# Install Heroku CLI
# Create a new Heroku app
heroku create eddie-expansion-bot

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### AWS EC2
See [deployment/aws/README.md](deployment/aws/README.md) for detailed AWS deployment instructions.

### Google Cloud Run
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/eddie

# Deploy to Cloud Run
gcloud run deploy eddie --image gcr.io/PROJECT-ID/eddie --platform managed
```

## API Documentation

### Evaluate Expansion Store
**POST** `/evaluate`

Request body:
```json
{
  "main_store_url": "https://example.com",
  "expansion_store_url": "https://expansion.example.com"
}
```

Response:
```json
{
  "qualification": "qualified",
  "confidence_score": 0.92,
  "products_identical": true,
  "services_identical": false,
  "branding_similar": true,
  "b2b_analysis": {...},
  "recommendations": [...]
}
```

### Health Check
**GET** `/health`

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600
}
```

## Configuration

### Environment Variables
Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
FLASK_PORT=5001

# CORS Settings
CORS_ORIGINS=http://localhost:*,https://yourdomain.com

# Feature Flags
ENABLE_IMAGE_ANALYSIS=true
ENABLE_B2B_ANALYSIS=true
MAX_PRODUCTS_TO_EXTRACT=100

# Performance
REQUEST_TIMEOUT=120
MAX_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=eddie.log
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest test_product_extraction.py
```

### Code Style
```bash
# Format code with Black
black .

# Check style with flake8
flake8 .
```

### Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Troubleshooting

### Common Issues

1. **Port 5000/5001 already in use**
```bash
# Find and kill the process
lsof -i :5001
kill -9 <PID>
```

2. **Module not found errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

3. **CORS errors in browser**
- Check that `CORS_ORIGINS` in `.env` includes your domain
- Ensure Flask-CORS is properly configured in `app.py`

## Project Structure
```
.
├── app.py                          # Main Flask application
├── expansion_store_evaluator.py    # Core evaluation logic
├── product_extractor.py            # Product discovery engine
├── image_analyzer.py               # Visual analysis module
├── web_content_fetcher.py          # Web scraping utilities
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── docker-compose.yml             # Multi-container orchestration
├── .env.template                  # Environment variables template
├── .gitignore                     # Git ignore rules
├── eddie_localhost.html           # Web interface
├── static/                        # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                     # Flask templates (if needed)
├── tests/                        # Test suite
│   ├── test_evaluation.py
│   ├── test_extraction.py
│   └── test_api.py
├── deployment/                   # Deployment configurations
│   ├── kubernetes/
│   ├── aws/
│   └── scripts/
└── docs/                        # Additional documentation
    ├── API.md
    ├── ARCHITECTURE.md
    └── DEPLOYMENT.md
```

## Performance Considerations

- **Caching**: Implements intelligent caching for repeated store evaluations
- **Rate Limiting**: Respects robots.txt and implements polite crawling
- **Async Processing**: Uses threading for parallel product extraction
- **Resource Management**: Automatic cleanup of temporary files and connections

## Security

- Input validation on all API endpoints
- XSS protection in web interface
- Rate limiting to prevent abuse
- No storage of sensitive merchant data
- HTTPS enforcement in production

## License
This project is proprietary to Shopify Inc. See [LICENSE](LICENSE) for details.

## Support
For issues, questions, or contributions:
- Create an issue in the GitHub repository
- Contact the Deal Desk team
- Slack: #deal-desk-tools

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Roadmap
- [ ] Cloud deployment automation
- [ ] Enhanced machine learning models
- [ ] Multi-language support
- [ ] Advanced B2B analysis features
- [ ] Integration with Shopify Admin API
- [ ] Real-time monitoring dashboard

---
Built with ❤️ by the Shopify Deal Desk Team
