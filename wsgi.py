#!/usr/bin/python3

"""
WSGI configuration for KDP Cover Creator on PythonAnywhere

This file contains the WSGI configuration required for deploying
the Flask application on PythonAnywhere hosting platform.
"""

import sys
import os

# Add your project directory to the Python path
project_home = '/home/yourusername/mysite'  # Replace with your actual path
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['SESSION_SECRET'] = 'your-secret-key-here'  # Replace with a secure secret key

# Import your Flask application
from main import app as application

if __name__ == "__main__":
    application.run()