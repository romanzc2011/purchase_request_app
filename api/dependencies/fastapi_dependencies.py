from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException,  Query, status, UploadFile, File, Form, APIRouter, Path
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm