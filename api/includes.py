# api/includes.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uvicorn
import jwt  # PyJWT
import os, threading, time, uuid, json

from fastapi import (
    FastAPI, APIRouter, Request, Depends, HTTPException, 
    Query, status, UploadFile, File, Form, Path
)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from cachetools import TTLCache, cached
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from multiprocessing.dummy import Pool as ThreadPool
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from docxtpl import DocxTemplate
from pathlib import Path
from pydantic import BaseModel