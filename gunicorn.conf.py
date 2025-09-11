# Gunicorn configuration file for production deployment

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2  # Adjust based on your CPU cores
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging - use stdout/stderr for Render compatibility
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "video-labeling-tool"

# Server mechanics
daemon = False
pidfile = None  # Don't create pid file in Render
user = None
group = None
tmp_upload_dir = None

# SSL (will be configured later with Let's Encrypt)
# keyfile = "/etc/letsencrypt/live/yourdomain.com/privkey.pem"
# certfile = "/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
