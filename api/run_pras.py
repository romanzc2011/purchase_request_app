import os, sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    os.chdir(Path(sys.executable).parent)
    
from api.pras_api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5004)