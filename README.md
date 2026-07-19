# Product Image AI

Professional image processing API for e-commerce product images using FastAPI, BiRefNet, and advanced image optimization.

## Features

- 🎯 **Batch Processing**: Process multiple product images from CSV files
- 🤖 **AI Background Removal**: BiRefNet-powered automatic background removal
- 📐 **Smart Resizing**: Intelligent scaling and centering
- 🎨 **Canvas Composition**: Professional product image framing
- 🔄 **Parallel Processing**: Multi-threaded image and download operations
- 📊 **Job Management**: Real-time progress tracking and job status
- 📦 **ZIP Export**: Automatic compression of results
- 🐳 **Docker Ready**: CPU and GPU containerization
- 📈 **Production Ready**: Logging, error handling, and monitoring

## Quick Start

### Prerequisites

- Python 3.11+
- CUDA 11.8+ (for GPU support, optional)
- 8GB+ RAM (16GB recommended)

### Installation

1. **Clone and setup**:
```bash
git clone <repo>
cd product-image-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Run development server**:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

API Documentation: http://localhost:8000/docs

## Docker Usage

### CPU Version
```bash
docker-compose up -d app-cpu
```

### GPU Version
Uncomment `app-gpu` in `docker-compose.yml` and run:
```bash
docker-compose up -d app-gpu
```

## API Endpoints

### Image Upload (Single)
```http
POST /upload
```
- Upload and process a single image
- Returns processed image path

### Batch Processing
```http
POST /upload-csv
```
- Upload CSV with product codes and image URLs
- Returns job ID for tracking

### Job Status
```http
GET /job/{job_id}
```
- Get real-time job progress
- Returns status, progress %, processed count, etc.

### Job List
```http
GET /jobs?limit=100&offset=0
```
- List all jobs with pagination
- Returns job summary list

### Download Results
```http
GET /download-job/{job_id}
```
- Download processed images as ZIP
- Automatically compresses results

### Delete Job
```http
DELETE /job/{job_id}
```
- Delete job and all associated files

## CSV Format

```csv
product_code,image_url_1,image_url_2,image_url_3
SKU001,https://example.com/image1.jpg,https://example.com/image2.jpg
SKU002,https://example.com/image3.jpg
SKU003,https://example.com/image4.jpg,https://example.com/image5.jpg,https://example.com/image6.jpg
```

## Configuration

Edit `.env` to customize:

```env
# Canvas
CANVAS_WIDTH=1200
CANVAS_HEIGHT=1500
DEFAULT_SCALE=92

# Background Color (RGB)
BACKGROUND_R=236
BACKGROUND_G=236
BACKGROUND_B=236

# Processing
MAX_WORKERS=8
REQUEST_TIMEOUT=30

# Folders
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=processed

# Features
ENABLE_GPU=true
CLEANUP_ON_DELETE=true
```

## Response Examples

### Job Status Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 45,
  "total": 100,
  "processed": 45,
  "success": 44,
  "failed": 1,
  "message": "45/100 ürün işlendi.",
  "elapsed_time": 125.4,
  "remaining_time": 152.3,
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T10:32:05.000000"
}
```

## Performance

### Throughput
- Single image: ~2-3 seconds
- Batch (100 images): ~300-400 seconds with 8 workers
- Network dependent on image size and URL reliability

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 16GB+ (model + processing)
- **Storage**: SSD for faster I/O
- **Network**: 100Mbps+ for optimal download speeds

## Architecture

```
FastAPI Application
├── Image Processing
│   ├── Background Removal (BiRefNet)
│   ├── Transparent Crop
│   ├── Smart Resize (LANCZOS)
│   └── Canvas Composition
├── Batch Processing
│   ├── CSV Parser
│   ├── Download Manager (httpx)
│   ├── Parallel Processing (ThreadPoolExecutor)
│   └── Progress Tracking
├── Job Management
│   ├── UUID-based tracking
│   ├── Persistent storage (JSON)
│   ├── Status transitions
│   └── Time estimation
└── Export
    ├── ZIP compression
    ├── Cleanup handlers
    └── File management
```

## Monitoring

### Logs
```bash
tail -f logs/product_image_ai.log
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Development

### Code Style
```bash
# Format code
black .

# Lint code
ruff check .
```

### Testing
```bash
pytest tests/ -v
```

## Troubleshooting

### Out of Memory
- Reduce `MAX_WORKERS` in `.env`
- Reduce `CANVAS_WIDTH` and `CANVAS_HEIGHT`

### Slow Processing
- Increase `MAX_WORKERS` (if hardware allows)
- Check network connectivity for batch processing
- Monitor system resources

### Model Loading Issues
- Ensure 8GB+ free RAM
- Check CUDA drivers (for GPU)
- Verify internet for model download

## License

MIT

## Support

For issues, feature requests, or contributions, please create an issue or pull request.

---

Made with ❤️ for e-commerce excellence
