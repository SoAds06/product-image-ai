# Deployment Guide

## Development Environment

### Quick Start
```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

## Production Deployment

### Docker (Recommended)

#### CPU Only
```bash
docker-compose up -d app-cpu
```

#### With GPU Support
1. Uncomment `app-gpu` section in `docker-compose.yml`
2. Ensure NVIDIA Docker runtime is installed
3. Run: `docker-compose up -d app-gpu`

### Manual Linux/Ubuntu

1. **System Dependencies**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    build-essential \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1
```

2. **Setup Application**
```bash
git clone <repo> product-image-ai
cd product-image-ai
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Configuration**
```bash
cp .env.example .env
# Edit .env for production settings
nano .env
```

4. **Create Systemd Service**

Create `/etc/systemd/system/product-image-ai.service`:
```ini
[Unit]
Description=Product Image AI Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/product-image-ai
Environment="PATH=/var/www/product-image-ai/venv/bin"
ExecStart=/var/www/product-image-ai/venv/bin/gunicorn \
    app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

5. **Enable and Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable product-image-ai
sudo systemctl start product-image-ai
sudo systemctl status product-image-ai
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/product-image-ai`:
```nginx
upstream app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_request_buffering off;
        proxy_buffering off;
    }

    location /docs {
        proxy_pass http://app;
    }

    location /redoc {
        proxy_pass http://app;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/product-image-ai \
           /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### SSL/TLS (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

Update nginx config with SSL certs.

## Monitoring

### System Resources
```bash
# Monitor CPU and Memory
watch -n 1 'ps aux | grep gunicorn'

# Check disk usage
df -h
du -sh logs/ processed/ uploads/
```

### Application Logs
```bash
# Real-time logs
tail -f logs/product_image_ai.log

# Error logs only
grep ERROR logs/product_image_ai.log
```

### Health Monitoring
```bash
# Health check
curl http://localhost:8000/health

# Performance test
ab -n 100 -c 10 http://localhost:8000/health
```

## Scaling Considerations

### Load Balancing
For high traffic, use multiple instances behind a load balancer:

```nginx
upstream app_cluster {
    least_conn;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### Horizontal Scaling
Run multiple instances on different ports:
```bash
gunicorn app:app --workers 4 --bind 127.0.0.1:8001
gunicorn app:app --workers 4 --bind 127.0.0.1:8002
gunicorn app:app --workers 4 --bind 127.0.0.1:8003
```

### Performance Tuning

#### Gunicorn Workers
```bash
# Recommendation: (2 × CPU_cores) + 1
# Example: 8-core CPU = 17 workers
gunicorn app:app --workers 17
```

#### Worker Class
- `sync`: Default, good for CPU-bound tasks
- `uvicorn.workers.UvicornWorker`: For async operations (recommended)

#### Timeouts
```bash
# Increase for large batch processing
gunicorn app:app --timeout 600
```

## Maintenance

### Regular Tasks

**Daily**:
- Monitor logs for errors
- Check disk space
- Verify service health

**Weekly**:
- Review performance metrics
- Check for security updates
- Archive old logs

**Monthly**:
- Database cleanup (if using persistence)
- Performance optimization
- Security audits

### Cleanup Old Files
```bash
# Remove processed images older than 30 days
find processed/ -type f -mtime +30 -delete

# Remove upload files older than 7 days
find uploads/ -type f -mtime +7 -delete

# Compress old logs
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

## Backup

### Important Files
- `.env` configuration file
- `jobs/` directory (job history)
- Custom configurations

### Backup Script
```bash
#!/bin/bash
BACKUP_DIR="/backups/product-image-ai"
mkdir -p $BACKUP_DIR

# Backup configuration
cp .env $BACKUP_DIR/.env.backup-$(date +%Y%m%d)

# Backup job history
tar -czf $BACKUP_DIR/jobs-$(date +%Y%m%d).tar.gz jobs/

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
systemctl status product-image-ai -l

# Verify configuration
python -c "from config import settings; print(settings)"

# Test import
python -c "from app import app; print('OK')"
```

### High Memory Usage
```bash
# Reduce MAX_WORKERS in .env
MAX_WORKERS=4

# Monitor per-process memory
ps aux | grep gunicorn
```

### Slow Responses
```bash
# Enable debug logging
LOG_LEVEL=DEBUG

# Monitor system resources
top -c

# Check network connectivity for batch jobs
ping -c 5 8.8.8.8
```

### GPU Not Working
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Verify GPU memory
nvidia-smi

# Check CUDA version match
nvcc --version
```

## Updates

```bash
# Backup current version
cp -r . ~/product-image-ai-backup-$(date +%Y%m%d)

# Pull updates
git pull origin main

# Install new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart product-image-ai
```

## Security

### Important Practices
1. **Never commit `.env` file**
2. **Use strong file permissions**: `chmod 600 .env`
3. **Rotate log files** to prevent disk fill
4. **Keep dependencies updated**: `pip list --outdated`
5. **Run as non-root user**
6. **Use HTTPS in production**
7. **Implement rate limiting** if needed
8. **Regular security audits**

### Firewall Rules
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if remote)
sudo ufw allow 22/tcp

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw enable
```

## Performance Benchmarks

### Expected Performance (CPU: 4-core, RAM: 16GB)
- **Single image**: 2-3 seconds
- **Batch (100 images)**: 300-400 seconds
- **Throughput**: ~15-20 images/minute

### Expected Performance (GPU: NVIDIA RTX 3090, 24GB VRAM)
- **Single image**: 0.5-1 second
- **Batch (100 images)**: 50-80 seconds
- **Throughput**: ~75-120 images/minute

---

For production issues, check logs and refer to README.md for API documentation.
