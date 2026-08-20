# Cosmos 🌌
An open-source science fact-checking project that reviews viral claims, debunks common myths, and separates scientific evidence from misinformation using reliable sources.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview
Cosmos is a community-driven platform dedicated to combating scientific misinformation. We provide:
- **Claim Verification**: Review viral claims against peer-reviewed research
- **Myth Debunking**: Explore common scientific misconceptions and their explanations
- **Reliable Sources**: Every assertion backed by scientific evidence
- **Open Collaboration**: Community contributions from scientists and fact-checking enthusiasts

## Features
✅ Verify scientific claims with source citations  
✅ Debunk viral myths with evidence-based explanations  
✅ RESTful API for accessing fact-checked content  
✅ SQLite database for persistent storage  
✅ Professional web interface with responsive design  
✅ Easy-to-use JSON responses for integration  

## Tech Stack
- **Language**: Python 3.x
- **Framework**: Flask 3.0.0
- **Database**: SQLite
- **Frontend**: HTML5 + CSS3 (responsive design)
- **API**: RESTful JSON API

## Getting Started

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/kingkfra-droid/Cosmos.git
cd Cosmos
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python App.py
```

The application will start on `http://localhost:5000`

### Accessing the Application
- **Home Page**: http://localhost:5000/
- **API Status**: http://localhost:5000/api/
- **Health Check**: http://localhost:5000/health

## API Endpoints

### Health & Status
```
GET /health
```
Returns server health status
```json
{"status": "healthy"}
```

```
GET /
```
API information and available endpoints

### Claims Management

**Get All Claims**
```
GET /api/claims
```
Returns list of all verified claims with pagination support

**Get Specific Claim**
```
GET /api/claims/<id>
```
Returns a single claim by ID

**Create New Claim**
```
POST /api/claims
Content-Type: application/json

{
  "title": "Claim title",
  "claim_text": "The actual claim",
  "verification_status": "true|false|unverified",
  "description": "Detailed description",
  "sources": "Source citations"
}
```

### Myths Management

**Get All Myths**
```
GET /api/myths
```
Returns list of all debunked myths

**Get Specific Myth**
```
GET /api/myths/<id>
```
Returns a single myth debunking by ID

**Create New Myth Debunking**
```
POST /api/myths
Content-Type: application/json

{
  "myth_title": "The myth statement",
  "debunked_explanation": "Why it's false",
  "myth_description": "Background on the myth",
  "scientific_evidence": "Evidence and research",
  "sources": "Source citations"
}
```

## Project Structure
```
Cosmos/
├── App.py                 # Main Flask application and API endpoints
├── Home.html             # Professional landing page
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── cosmos_facts.db      # SQLite database (auto-created)

Database Schema:
├── claims               # Stores verified claims with status
│   ├── id              # Primary key
│   ├── title           # Claim title
│   ├── claim_text      # Full claim text
│   ├── verification_status # true/false/unverified
│   ├── sources         # Citation references
│   └── created_at      # Timestamp
│
└── myths                # Stores debunked myths
    ├── id              # Primary key
    ├── myth_title      # The myth being addressed
    ├── debunked_explanation # Why it's false
    ├── scientific_evidence  # Research backing
    ├── sources         # References
    └── created_at      # Timestamp
```

## How It Fits Together

**Request Flow:**
1. User visits http://localhost:5000/ → Served by Flask home route
2. Browser displays Home.html with landing page and API information
3. User clicks "View Claims" → Navigates to /api/claims
4. Flask retrieves claims from SQLite database
5. API returns JSON response with all claims
6. Browser displays formatted results

**Data Flow:**
- Claims and myths are stored in SQLite database (cosmos_facts.db)
- Flask App.py handles all HTTP requests and routes
- Database is initialized automatically on first run
- All responses follow standard JSON format with status indicators
- Error handling provides meaningful error messages

## Usage Examples

### Using cURL

**Get all claims:**
```bash
curl http://localhost:5000/api/claims
```

**Create a new claim:**
```bash
curl -X POST http://localhost:5000/api/claims \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Vaccines cause autism",
    "claim_text": "COVID vaccines cause autism spectrum disorder",
    "verification_status": "false",
    "description": "This claim has been thoroughly debunked by scientific research",
    "sources": "CDC, WHO, peer-reviewed studies"
  }'
```

**Get a specific myth:**
```bash
curl http://localhost:5000/api/myths/1
```

### Using Python

```python
import requests
import json

# Get all claims
response = requests.get('http://localhost:5000/api/claims')
claims = response.json()
print(json.dumps(claims, indent=2))

# Create a new myth debunking
myth_data = {
    "myth_title": "The Earth is flat",
    "debunked_explanation": "Multiple lines of evidence prove Earth is spherical",
    "scientific_evidence": "Satellite imagery, physics, circumnavigation",
    "sources": "NASA, scientific consensus"
}

response = requests.post(
    'http://localhost:5000/api/myths',
    json=myth_data
)
print(response.json())
```

## Contributing

We welcome contributions from scientists, fact-checkers, developers, and enthusiasts!

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** (add claims, debunk myths, improve code)
4. **Commit your changes** (`git commit -m 'Add amazing feature'`)
5. **Push to the branch** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

### Contribution Guidelines
- Ensure all claims are backed by reliable sources
- Reference peer-reviewed research when possible
- Include proper citations and links
- Follow existing code style and conventions
- Test your changes before submitting

## AI Assistant Context

This document serves as historical reference for AI assistants and developers working on the Cosmos project. When contributing or modifying code:

1. **Understand the Mission**: Cosmos combats misinformation through evidence-based fact-checking
2. **Database Schema**: Always refer to claims and myths tables defined in App.py
3. **API Standards**: All endpoints return JSON with `status`, `data`, and `message` fields
4. **Error Handling**: Use provided error handlers for consistent error responses
5. **Dependencies**: Flask and SQLite are the core dependencies - maintain compatibility
6. **Scalability**: Current SQLite implementation suitable for MVP; consider PostgreSQL for production scale

## Troubleshooting

**Port 5000 already in use:**
```bash
python App.py --port 5001
```

**Database connection error:**
- Ensure cosmos_facts.db can be created in the project directory
- Check file permissions
- Delete cosmos_facts.db to reinitialize

**Module not found errors:**
```bash
pip install -r requirements.txt
```

**Database is empty:**
- POST requests to /api/claims and /api/myths to add content
- No seed data is included by design - community drives content

## Future Roadmap
- [ ] User authentication and admin panel
- [ ] Advanced search and filtering
- [ ] User contribution voting system
- [ ] Integration with fact-checking databases (Snopes, PolitiFact)
- [ ] Machine learning for claim similarity detection
- [ ] Mobile application
- [ ] PostgreSQL migration for production
- [ ] Docker containerization

## License
This project is open source and available under the MIT License - see LICENSE file for details.

## Contact & Support
- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions
- **Pull Requests**: Submit improvements via Pull Requests

---

**Last Updated**: August 20, 2026  
**Status**: Active Development  
**Maintained By**: Community Contributors
