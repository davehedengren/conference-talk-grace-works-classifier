#!/usr/bin/env python3
"""
Main entry point for Replit deployment.
This file starts the Streamlit app for the Conference Talk Grace-Works Classifier.
"""

import subprocess
import sys

if __name__ == "__main__":
    # Run the Streamlit app
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app_typed.py",
        "--server.headless", "true",
        "--server.port", "8080",
        "--server.address", "0.0.0.0"
    ]) 