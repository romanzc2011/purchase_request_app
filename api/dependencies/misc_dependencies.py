import sys
import os
import asyncio
import aiofiles
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uvicorn
import os, threading, time, uuid
import api.schemas.misc_schemas as ps
from typing import List, Optional
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from pathlib import Path