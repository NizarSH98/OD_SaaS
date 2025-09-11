#!/usr/bin/env python3
"""
Simple tunnel starter for the Video Labeling Tool
"""

from pyngrok import ngrok
import time
import sys

def start_tunnel():
    """Start ngrok tunnel for the Flask app"""
    try:
        print("🚀 Starting tunnel for Video Labeling Tool...")
        print("📱 Your app is running on port 5000")
        
        # Start tunnel
        public_url = ngrok.connect(5000)
        
        print("✅ Tunnel started successfully!")
        print(f"🌐 Public URL: {public_url}")
        print(f"🔗 Share this link: {public_url}")
        print("\n📝 Press Ctrl+C to stop the tunnel")
        
        # Keep the tunnel running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopping tunnel...")
            ngrok.disconnect(public_url)
            ngrok.kill()
            print("✅ Tunnel stopped")
            
    except Exception as e:
        print(f"❌ Error starting tunnel: {e}")
        print("💡 Make sure you have an ngrok account and authtoken configured")
        sys.exit(1)

if __name__ == "__main__":
    start_tunnel()
