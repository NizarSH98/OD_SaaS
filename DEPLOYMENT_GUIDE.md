# 🚀 Free Self-Hosted Website Deployment Guide

This guide will help you publish your Video Labeling Tool as a free self-hosted website with a domain name that's searchable on Google.

## 📋 Prerequisites

- Your Flask app is ready (✅ Done)
- Ubuntu/Linux server or your home computer
- Internet connection with a public IP
- Router with port forwarding capabilities
- FreeDomain.one account (✅ You have this!)

## 🚀 Quick Start for FreeDomain.one Users

Since you already have a FreeDomain.one account, here's the fastest path to get your site live:

1. **Get your public IP:**
   ```bash
   curl ifconfig.me
   ```

2. **Register your domain:**
   - Log into [FreeDomain.one](https://freedomain.one/Login.sv)
   - Choose and register your free domain
   - Note the domain name (e.g., `yourdomain.com`)

3. **Deploy your app:**
   ```bash
   ./deploy.sh
   ```

4. **Configure DNS:**
   - In FreeDomain.one, set A record: `@` → `YOUR_PUBLIC_IP`
   - Set A record: `www` → `YOUR_PUBLIC_IP`

5. **Configure router:**
   - Port forward 80 and 443 to your computer's local IP

6. **Test:** Visit `http://yourdomain.com`

## 🌐 Step 1: Get a Free Domain Name

### Option A: FreeDomain.one (Recommended - ICANN Accredited)
1. Go to [FreeDomain.one](https://freedomain.one/Login.sv)
2. Log in to your account (you've already created one!)
3. Navigate to "Services" or "Domain Registration"
4. Search for your desired domain name (e.g., `videolabeling`)
5. Choose from available free TLDs (check their current offerings)
6. Complete the registration process
7. **Important**: Note down your domain management credentials

### Option B: Freenom (Alternative - Completely Free)
1. Go to [Freenom.com](https://www.freenom.com)
2. Search for your desired domain name (e.g., `videolabeling`)
3. Choose from free TLDs: `.tk`, `.ml`, `.ga`, `.cf`, `.gq`
4. Register for free (no credit card required)
5. Complete the registration process

### Option C: DuckDNS (Free Subdomain)
1. Go to [DuckDNS.org](https://www.duck
yes


dns.org)
2. Sign up with Google/GitHub/Twitter
3. Choose a subdomain (e.g., `yourname.duckdns.org`)
4. Add your current public IP

## 🔧 Step 2: Set Up Dynamic DNS

Since your home IP changes, you need dynamic DNS to keep your domain pointing to your current IP.

### For FreeDomain.one domains:
1. **Get your current public IP:**
```bash
curl ifconfig.me
# Note this IP address
```

2. **Configure DNS in FreeDomain.one:**
   - Log into your [FreeDomain.one account](https://freedomain.one/Login.sv)
   - Go to "Domain Management" or "DNS Settings"
   - Add these DNS records:
     - **A Record**: `@` → `YOUR_PUBLIC_IP`
     - **A Record**: `www` → `YOUR_PUBLIC_IP`
     - **CNAME Record**: `*` → `@` (for wildcard subdomains)

3. **Set up dynamic DNS client:**
```bash
# Install ddclient
sudo apt update
sudo apt install ddclient

# Configure ddclient for FreeDomain.one
sudo nano /etc/ddclient.conf
```

4. **Add this configuration:**
```
# FreeDomain.one configuration
use=web, web=checkip.dyndns.com/, web-skip='IP Address'
protocol=namecheap
server=dynamicdns.park-your-domain.com
login=yourdomain.com
password=your-dyndns-password
yourdomain.com
```

5. **Start the service:**
```bash
sudo systemctl enable ddclient
sudo systemctl start ddclient
```

### For Freenom domains (Alternative):
1. Install a dynamic DNS client:
```bash
# Install ddclient
sudo apt update
sudo apt install ddclient

# Configure ddclient
sudo nano /etc/ddclient.conf
```

2. Add this configuration:
```
protocol=freedns
server=freedns.afraid.org
login=your-freenom-username
password=your-freenom-password
yourdomain.tk
```

3. Start the service:
```bash
sudo systemctl enable ddclient
sudo systemctl start ddclient
```

### For DuckDNS:
1. Install DuckDNS updater:
```bash
# Create DuckDNS updater script
sudo nano /usr/local/bin/duckdns-update.sh
```

2. Add this content:
```bash
#!/bin/bash
DOMAIN="yourname"
TOKEN="your-duckdns-token"
curl "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip="
```

3. Make it executable and add to crontab:
```bash
sudo chmod +x /usr/local/bin/duckdns-update.sh
sudo crontab -e
# Add this line:
*/5 * * * * /usr/local/bin/duckdns-update.sh
```

## 🔌 Step 3: Configure Router Port Forwarding

1. Access your router admin panel (usually `192.168.1.1` or `192.168.0.1`)
2. Find "Port Forwarding" or "Virtual Server" settings
3. Add these rules:
   - **Port 80** → Your computer's local IP (port 5000)
   - **Port 443** → Your computer's local IP (port 5000)
4. Save and restart router

## 🚀 Step 4: Deploy Your Application

1. **Run the deployment script:**
```bash
./deploy.sh
```

2. **Check if it's working:**
```bash
# Check service status
sudo systemctl status video-labeling-tool

# Check logs
sudo journalctl -u video-labeling-tool -f

# Test locally
curl http://localhost:5000
```

3. **Test from outside:**
Visit `http://yourdomain.tk` in your browser

## 🔒 Step 5: Set Up SSL Certificate (HTTPS)

### Install Certbot:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

### Get SSL certificate:
```bash
# Stop nginx if running
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.tk

# Update Gunicorn config
sudo nano /home/nizar/Documents/OD_SaaS/gunicorn.conf.py
```

### Update Gunicorn config for SSL:
```python
# Add these lines to gunicorn.conf.py
keyfile = "/etc/letsencrypt/live/yourdomain.tk/privkey.pem"
certfile = "/etc/letsencrypt/live/yourdomain.tk/fullchain.pem"
```

### Restart service:
```bash
sudo systemctl restart video-labeling-tool
```

## 🔍 Step 6: Make It Searchable on Google

### 1. Submit to Google Search Console:
1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add your property: `https://yourdomain.tk`
3. Verify ownership (HTML file upload method)
4. Submit your sitemap: `https://yourdomain.tk/sitemap.xml`

### 2. Submit to other search engines:
- **Bing Webmaster Tools**: [Bing.com/webmasters](https://www.bing.com/webmasters)
- **Yandex Webmaster**: [webmaster.yandex.com](https://webmaster.yandex.com)

### 3. Create backlinks:
- Share on social media
- Submit to directories like:
  - [Product Hunt](https://producthunt.com)
  - [GitHub](https://github.com) (if you open source it)
  - [Reddit](https://reddit.com) relevant communities

## 📊 Step 7: Monitor and Maintain

### Set up monitoring:
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Create monitoring script
nano /home/nizar/monitor.sh
```

### Monitoring script content:
```bash
#!/bin/bash
# Check if service is running
if ! systemctl is-active --quiet video-labeling-tool; then
    echo "Service is down! Restarting..."
    sudo systemctl restart video-labeling-tool
    # Send notification (optional)
    # curl -X POST "https://api.telegram.org/bot<token>/sendMessage" -d "chat_id=<chat_id>&text=Service restarted"
fi

# Check disk space
if [ $(df / | awk 'NR==2 {print $5}' | sed 's/%//') -gt 80 ]; then
    echo "Disk space low!"
fi
```

### Add to crontab:
```bash
crontab -e
# Add this line to check every 5 minutes:
*/5 * * * * /home/nizar/monitor.sh
```

## 🎯 SEO Optimization Checklist

- ✅ Meta tags and Open Graph tags
- ✅ XML sitemap (`/sitemap.xml`)
- ✅ Robots.txt (`/robots.txt`)
- ✅ Structured data (JSON-LD)
- ✅ Mobile-responsive design
- ✅ Fast loading times
- ✅ HTTPS enabled
- ✅ Submitted to search engines

## 🆘 Troubleshooting

### Common Issues:

1. **Domain not resolving:**
   - Check DNS propagation: [whatsmydns.net](https://www.whatsmydns.net)
   - Verify dynamic DNS is updating
   - Wait 24-48 hours for full propagation

2. **Can't access from outside:**
   - Check router port forwarding
   - Verify firewall settings
   - Test with different network

3. **SSL certificate issues:**
   - Ensure domain points to your server
   - Check if ports 80 and 443 are open
   - Verify certificate files exist

4. **Service not starting:**
   - Check logs: `sudo journalctl -u video-labeling-tool -f`
   - Verify file permissions
   - Check if port 5000 is available

## 📈 Performance Tips

1. **Enable gzip compression** in your web server
2. **Use a CDN** like Cloudflare (free tier)
3. **Optimize images** and static files
4. **Monitor resource usage** regularly
5. **Keep dependencies updated**

## 🎉 You're Done!

Your Video Labeling Tool is now:
- ✅ Live on the internet
- ✅ Accessible via domain name
- ✅ Searchable on Google
- ✅ Secured with HTTPS
- ✅ SEO optimized

Visit your site at `https://yourdomain.tk` and start sharing it with the world!
