# FastAPI Server for URL to BibTeX Converter

A REST API server for converting academic paper URLs to BibTeX citations.

## Installation

### Option 1: Local Installation

Install with server dependencies:

```bash
pip install -e ".[server]"
```

### Option 2: Docker

```bash
# Build the Docker image
docker build -t url2bibtex:latest .

# Run the container
docker run -d -p 8000:8000 --name url2bibtex url2bibtex:latest
```

### Option 3: Docker Compose

```bash
# Start the service
docker-compose up -d

# Stop the service
docker-compose down
```

## Running the Server

### Basic Usage

```bash
python server.py
```

The server will start on `http://0.0.0.0:8000`

### With Custom Port

```bash
python server.py --port 3000
```

### Development Mode (with auto-reload)

```bash
python server.py --reload
```

### Custom Host and Port

```bash
python server.py --host 127.0.0.1 --port 8080
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### POST /convert

Convert a URL to BibTeX format.

**Request Body:**
```json
{
  "url": "https://arxiv.org/abs/2103.15348"
}
```

**Response:**
```json
{
  "url": "https://arxiv.org/abs/2103.15348",
  "bibtex": "@article{touvron2021,...}",
  "success": true
}
```

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://arxiv.org/abs/2103.15348"}'
```

### GET /convert

Convert a URL to BibTeX format (using query parameters).

**Example:**
```bash
curl "http://localhost:8000/convert?url=https://arxiv.org/abs/2103.15348"
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "handlers": 7
}
```

### GET /handlers

List all available handlers.

**Response:**
```json
{
  "handlers": [
    {
      "name": "ArxivHandler",
      "description": "ArXiv preprint papers"
    },
    ...
  ]
}
```

## Supported URL Types

The server supports all handlers:
- **ArXiv**: `https://arxiv.org/abs/XXXX.XXXXX`
- **OpenReview**: `https://openreview.net/forum?id=PAPER_ID`
- **Semantic Scholar**: `https://www.semanticscholar.org/paper/...`
- **GitHub**: `https://github.com/owner/repo`
- **DOI**: `https://doi.org/10.XXXX/XXXXX`
- **ACL Anthology**: `https://aclanthology.org/2024.findings-emnlp.746`
- **HTML Meta Tags**: Any publisher with citation meta tags (Nature, IEEE, Springer, etc.)

## Python Client Example

```python
import requests

# Convert a URL
response = requests.post(
    "http://localhost:8000/convert",
    json={"url": "https://arxiv.org/abs/2103.15348"}
)

data = response.json()
if data["success"]:
    print(data["bibtex"])
else:
    print(f"Error: {data['error']}")
```

## CORS

CORS is enabled for all origins by default. In production, you should configure specific origins in `server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment

### Using Docker (Recommended)

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers (if needed)
docker-compose up -d --scale url2bibtex=3
```

### Using Uvicorn directly

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn

```bash
gunicorn server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Commands

```bash
# Build image
docker build -t url2bibtex:latest .

# Run container
docker run -d -p 8000:8000 --name url2bibtex url2bibtex:latest

# View logs
docker logs -f url2bibtex

# Stop container
docker stop url2bibtex

# Remove container
docker rm url2bibtex

# Check container health
docker inspect --format='{{.State.Health.Status}}' url2bibtex
```
