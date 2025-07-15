#!/usr/bin/env python3
"""
Main entry point for the Video Labeling Tool application.

This script uses Poetry to run the Flask application for creating
labeled datasets from videos.
"""

import os
import sys
import subprocess

def main():
    """Main function to start the Flask application using Poetry."""
    try:
        print("🚀 Starting Video Labeling Tool with Poetry...")
        print("📁 Project directory:", os.getcwd())
        print("🔧 Using Poetry virtual environment")
        print("🎥 Running full application with OpenCV support")
        print("-" * 50)
        
        # Run the Flask app using Poetry
        cmd = ["poetry", "run", "python", "app.py"]
        
        # Start the application
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
        print("💡 Make sure Poetry is installed and dependencies are available")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Poetry not found. Please install Poetry first:")
        print("   curl -sSL https://install.python-poetry.org | python3 -")
        print("   or visit: https://python-poetry.org/docs/#installation")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 