#!/usr/bin/env python3
"""
Simple test runner that sets up the environment correctly
"""
import os
import sys
from pathlib import Path

# Set test database path BEFORE any imports
api_dir = Path(__file__).parent
os.environ['DATABASE_FILE_PATH'] = str(api_dir / "db" / "pras_test.db")

# Add the parent directory to Python path so 'api' module can be found
parent_dir = api_dir.parent
sys.path.insert(0, str(parent_dir))

# Now import and run
if __name__ == "__main__":
    import uvicorn
    from api.pras_api import app
    
    print("Starting PRAS API in test mode...")
    print(f"Test database: {os.environ['DATABASE_FILE_PATH']}")
    print("API will be available at: http://127.0.0.1:5004")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=5004, 
        log_level="info"
    )
