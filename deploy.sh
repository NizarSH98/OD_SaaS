#!/bin/bash
# Production deployment script for Video Labeling Tool

set -e  # Exit on any error

echo "🚀 Starting Video Labeling Tool deployment..."

# Create necessary directories
mkdir -p logs
mkdir -p uploads
mkdir -p frames
mkdir -p datasets

# Set proper permissions
chmod 755 logs
chmod 755 uploads
chmod 755 frames
chmod 755 datasets

# Install/update dependencies
echo "📦 Installing dependencies..."
export PATH="/home/nizar/.local/bin:$PATH"
poetry install --no-dev

# Install Gunicorn if not already installed
poetry add gunicorn

# Create systemd service file
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/video-labeling-tool.service > /dev/null <<EOF
[Unit]
Description=Video Labeling Tool Flask Application
After=network.target

[Service]
Type=notify
User=nizar
Group=nizar
WorkingDirectory=/home/nizar/Documents/OD_SaaS
Environment=PATH=/home/nizar/.cache/pypoetry/virtualenvs/video-labeling-tool-nEkpTu6S-py3.10/bin
ExecStart=/home/nizar/.cache/pypoetry/virtualenvs/video-labeling-tool-nEkpTu6S-py3.10/bin/gunicorn --config gunicorn.conf.py wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "🔄 Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable video-labeling-tool
sudo systemctl start video-labeling-tool

# Check service status
echo "📊 Service status:"
sudo systemctl status video-labeling-tool --no-pager

echo "✅ Deployment complete!"
echo "🌐 Your app should be running at http://$(curl -s ifconfig.me):5000"
echo "📝 Check logs with: sudo journalctl -u video-labeling-tool -f"
