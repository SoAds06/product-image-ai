# API Reference

## Base URL
```
http://localhost:8000
```

## Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Endpoints

### 1. API Information
```http
GET /
```

**Description**: Get API information and status

**Response**:
```json
{
  "project": "Product Image AI",
  "version": "3.0.0",
  "status": "running",
  "debug": false
}
```

---

### 2. Health Check
```http
GET /health
```

**Description**: Check if API is healthy

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-07-19T20:37:55.922433Z"
}
```

---

### 3. Upload Single Image
```http
POST /upload
Content-Type: multipart/form-data
```

**Description**: Upload and process a single image

**Parameters**:
| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| file | file | - | ✓ | Image file (JPG, PNG, etc.) |
| scale | int | 92 | - | Scale percentage (10-100) |
| canvas_width | int | 1200 | - | Canvas width in pixels |
| canvas_height | int | 1500 | - | Canvas height in pixels |
| offset_y | int | 0 | - | Y-axis offset from center |
| background_r | int | 236 | - | Red channel (0-255) |
| background_g | int | 236 | - | Green channel (0-255) |
| background_b | int | 236 | - | Blue channel (0-255) |

**Example**:
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@product.jpg" \
  -F "scale=95" \
  -F "canvas_width=1200" \
  -F "canvas_height=1500"
```

**Response**:
```json
{
  "success": true,
  "output": "processed/product.png"
}
```

---

### 4. Upload CSV (Batch)
```http
POST /upload-csv
Content-Type: multipart/form-data
```

**Description**: Upload CSV file for batch processing

**Parameters**:
| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| file | file | - | ✓ | CSV file |
| scale | int | 92 | - | Scale percentage (10-100) |
| canvas_width | int | 1200 | - | Canvas width |
| canvas_height | int | 1500 | - | Canvas height |
| offset_y | int | 0 | - | Y-axis offset |
| background_r | int | 236 | - | Red (0-255) |
| background_g | int | 236 | - | Green (0-255) |
| background_b | int | 236 | - | Blue (0-255) |

**CSV Format**:
```csv
product_code,image_url_1,image_url_2,image_url_3
SKU001,https://example.com/img1.jpg,https://example.com/img2.jpg
SKU002,https://example.com/img3.jpg
SKU003,https://example.com/img4.jpg,https://example.com/img5.jpg
```

**Example**:
```bash
curl -X POST "http://localhost:8000/upload-csv" \
  -F "file=@products.csv" \
  -F "scale=92"
```

**Response**:
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

---

### 5. Get Job Status
```http
GET /job/{job_id}
```

**Description**: Get job status and progress

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| job_id | string | ✓ | Job identifier (UUID) |

**Example**:
```bash
curl "http://localhost:8000/job/550e8400-e29b-41d4-a716-446655440000"
```

**Response**:
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
  "download_url": null,
  "created_at": "2026-07-19T10:30:00",
  "updated_at": "2026-07-19T10:32:05",
  "completed_at": null
}
```

---

### 6. List Jobs
```http
GET /jobs?limit=100&offset=0
```

**Description**: List all jobs with pagination

**Parameters**:
| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| limit | int | 100 | - | Max jobs to return (1-1000) |
| offset | int | 0 | - | Pagination offset |

**Example**:
```bash
curl "http://localhost:8000/jobs?limit=50&offset=0"
```

**Response**:
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": 100,
      "total": 100,
      "processed": 100,
      "success": 98,
      "failed": 2,
      "message": "Tamamlandı.",
      "elapsed_time": 285.4,
      "remaining_time": null,
      "download_url": null,
      "created_at": "2026-07-19T10:30:00",
      "updated_at": "2026-07-19T10:37:45",
      "completed_at": "2026-07-19T10:37:45"
    }
  ],
  "total": 1
}
```

---

### 7. Download Job Results
```http
GET /download-job/{job_id}
```

**Description**: Download processed images as ZIP file

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| job_id | string | ✓ | Job identifier (UUID) |

**Example**:
```bash
curl -O "http://localhost:8000/download-job/550e8400-e29b-41d4-a716-446655440000"
```

**Response**: ZIP file binary stream
- Content-Type: `application/zip`
- Filename: `{job_id}.zip`

**Error Response** (if job not found):
```json
{
  "detail": "Job not found"
}
```

---

### 8. Delete Job
```http
DELETE /job/{job_id}
```

**Description**: Delete job and all associated files

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| job_id | string | ✓ | Job identifier (UUID) |

**Example**:
```bash
curl -X DELETE "http://localhost:8000/job/550e8400-e29b-41d4-a716-446655440000"
```

**Response**:
```json
{
  "success": true
}
```

---

## Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Job found, file exists |
| 400 | Bad Request | Invalid parameters, processing error |
| 404 | Not Found | Job doesn't exist |
| 500 | Server Error | Internal server error |

---

## Error Responses

### Invalid Job ID
```json
{
  "detail": "Job not found"
}
```

### Processing Error
```json
{
  "detail": "Processing error: specific error message"
}
```

### General Error
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE"
}
```

---

## Job Status Values

| Status | Meaning | Progress |
|--------|---------|----------|
| `queued` | Waiting to start | 0% |
| `running` | Currently processing | 0-99% |
| `completed` | Finished successfully | 100% |
| `failed` | Processing failed | Variable |

---

## Rate Limiting

Currently no rate limiting. Can be added via middleware if needed.

---

## Authentication

Currently no authentication required. Can be added via FastAPI security schemes.

---

## CORS

Cross-Origin Resource Sharing can be enabled via FastAPI CORSMiddleware if needed.

---

## WebSocket Support

Not currently implemented. Can be added for real-time progress updates.

---

## Examples

### Python
```python
import requests
import time

# Upload CSV
with open('products.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload-csv',
        files={'file': f},
        data={'scale': 92}
    )
    job_id = response.json()['job_id']

# Poll job status
while True:
    status = requests.get(f'http://localhost:8000/job/{job_id}').json()
    print(f"Progress: {status['progress']}%")
    
    if status['status'] == 'completed':
        break
    
    time.sleep(5)

# Download results
response = requests.get(f'http://localhost:8000/download-job/{job_id}')
with open('results.zip', 'wb') as f:
    f.write(response.content)
```

### JavaScript
```javascript
async function processBatch() {
    const formData = new FormData();
    formData.append('file', document.getElementById('csvInput').files[0]);
    
    // Upload
    const uploadRes = await fetch('http://localhost:8000/upload-csv', {
        method: 'POST',
        body: formData
    });
    const { job_id } = await uploadRes.json();
    
    // Poll status
    let completed = false;
    while (!completed) {
        const statusRes = await fetch(`http://localhost:8000/job/${job_id}`);
        const status = await statusRes.json();
        console.log(`Progress: ${status.progress}%`);
        
        if (status.status === 'completed') {
            completed = true;
        } else {
            await new Promise(r => setTimeout(r, 5000));
        }
    }
    
    // Download
    window.location.href = `http://localhost:8000/download-job/${job_id}`;
}
```

### cURL
```bash
# Upload CSV
JOB_ID=$(curl -s -X POST http://localhost:8000/upload-csv \
  -F "file=@products.csv" | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Monitor progress
while true; do
    STATUS=$(curl -s http://localhost:8000/job/$JOB_ID)
    PROGRESS=$(echo $STATUS | jq '.progress')
    echo "Progress: $PROGRESS%"
    
    if [ $PROGRESS -eq 100 ]; then
        break
    fi
    
    sleep 5
done

# Download results
curl -O http://localhost:8000/download-job/$JOB_ID
```

---

## Performance Tips

1. **Batch Processing**: Use CSV upload for multiple images
2. **Worker Configuration**: Adjust `MAX_WORKERS` in `.env`
3. **Network**: Ensure stable internet for batch jobs
4. **Resource Monitoring**: Watch disk space and memory
5. **Timeouts**: Increase if processing large images

---

## Limits

| Item | Limit | Note |
|------|-------|------|
| File Size | No limit* | Limited by disk space |
| Batch Size | No limit* | Process in chunks if needed |
| Concurrent Jobs | No limit* | Limited by `MAX_WORKERS` |
| Request Timeout | 30s | Configurable in `.env` |

*Practical limits depend on available resources

---

## Content Types

**Accepted Image Formats**:
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- BMP (.bmp)
- GIF (.gif)

**Output Format**:
- PNG (.png) with transparency support

---

## Headers

### Request Headers
```
Content-Type: multipart/form-data
Accept: application/json
```

### Response Headers
```
Content-Type: application/json
Content-Length: {size}
Date: {timestamp}
```

---

## Versioning

API Version: **3.0.0**

Future breaking changes will be versioned as `/v2/`, `/v3/`, etc.

---

For more information, visit:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- README: See README.md
- Deployment: See DEPLOYMENT.md
