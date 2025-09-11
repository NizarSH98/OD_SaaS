#!/usr/bin/env python3
"""
Simple Flask app with ngrok integration for testing
"""

from flask import Flask, render_template_string
from flask_ngrok import run_with_ngrok
import os

app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Video Labeling Tool - Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .success { color: green; font-size: 24px; }
        .info { background: #f0f0f0; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="success">🎉 Success! Your Video Labeling Tool is Live!</h1>
        <div class="info">
            <h2>Your Flask app is now accessible from the internet!</h2>
            <p><strong>Status:</strong> ✅ Running</p>
            <p><strong>Port:</strong> 5000</p>
            <p><strong>Public URL:</strong> This page (via ngrok)</p>
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Share this URL with others</li>
                <li>Test your video labeling features</li>
                <li>Configure your custom domain later</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/test')
def test():
    return "Test endpoint working! 🚀"

if __name__ == '__main__':
    print("🚀 Starting Video Labeling Tool with ngrok...")
    print("📱 This will create a public URL for your app")
    print("⏳ Please wait for ngrok to start...")
    
    # Run with ngrok
    run_with_ngrok(app)
    app.run()
