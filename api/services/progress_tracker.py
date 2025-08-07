# progress_tracker.py
from __future__ import annotations
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional, Callable, Any, Protocol
import asyncio
from loguru import logger
from blinker import signal
from api.services.websocket_manager import websock_conn

# -----------------------------------------------------------------------------
# Domain
# -----------------------------------------------------------------------------
class DownloadStepName(Enum):
    FETCH_APPROVAL_DATA = auto()
    FETCH_FLAT_APPROVALS = auto()
    GET_JUSTIFICATIONS_AND_COMMENTS = auto()
    GET_CONTRACTING_OFFICER_BY_ID = auto()
    GET_LINE_ITEMS = auto()
    GET_SON_COMMENTS = auto()
    GET_ORDER_TYPES = auto()
    LOAD_PDF_TEMPLATE = auto()
    MERGE_DATA_INTO_TEMPLATE = auto()
    RENDER_PDF_BINARY = auto()
    SAVE_PDF_TO_DISK = auto()
    VERIFY_FILE_EXISTS = auto()

@dataclass
class DownloadStep:
    step_name: DownloadStepName
    weight: int
    done: bool = False
    download_process: bool = False

DOWNLOAD_STEPS: List[DownloadStep] = [
    DownloadStep(DownloadStepName.FETCH_APPROVAL_DATA,             10),
    DownloadStep(DownloadStepName.FETCH_FLAT_APPROVALS,            10),
    DownloadStep(DownloadStepName.GET_JUSTIFICATIONS_AND_COMMENTS,  5),
    DownloadStep(DownloadStepName.GET_CONTRACTING_OFFICER_BY_ID,    5),
    DownloadStep(DownloadStepName.GET_LINE_ITEMS,                  10),
    DownloadStep(DownloadStepName.GET_SON_COMMENTS,                 5),
    DownloadStep(DownloadStepName.GET_ORDER_TYPES,                  5),

    DownloadStep(DownloadStepName.LOAD_PDF_TEMPLATE,                5),
    DownloadStep(DownloadStepName.MERGE_DATA_INTO_TEMPLATE,        15),
    DownloadStep(DownloadStepName.RENDER_PDF_BINARY,               15),
    DownloadStep(DownloadStepName.SAVE_PDF_TO_DISK,                 5),
    DownloadStep(DownloadStepName.VERIFY_FILE_EXISTS,               5),
]
 
# ------------------------------------------
# Progress Tracker
# ------------------------------------------           
class ProgressTracker:
    def __init__(self):
        self.steps = [DownloadStep(s.step_name, s.weight) for s in DOWNLOAD_STEPS]
        self._start_download_tracking = False
        self._percent_complete = 0

    @property
    def start_download_tracking(self):
        return self._start_download_tracking
    
    @start_download_tracking.setter
    def start_download_tracking(self, value: bool):
        self._start_download_tracking = value
        
    @property
    def set_percent(self):
        return self._percent_complete
    
    @start_download_tracking.setter
    def set_percent(self, value: int):
        self._percent_complete = value
        
    def reset(self):
        for step in self.steps:
            step.done = False
            
    def send_download_start_msg(self):
        asyncio.create_task(websock_conn.broadcast({
            "event": "START_TOAST",
            "percent_complete": 0
        }));
        logger.debug("Sent start toast message")
    
    #------------------------------------------------------------------
    # Calculate progress
    #------------------------------------------------------------------
    def calculate_progress(self) -> int:
        total_weight = sum(s.weight for s in self.steps)
        done_weight = sum(s.weight for s in self.steps if s.done)
        self._percent_complete = int((done_weight / total_weight) * 100)
        return self._percent_complete
    
    #------------------------------------------------------------------
    # Signal listener
    #------------------------------------------------------------------
    def progress_listener(self, *args, **kwargs):
        # Handle blinker signal pattern - sender is always the first positional arg
        sender = args[0] if args else None
        step_name = kwargs.get('step_name')
        if step_name is None:
            logger.error("No step_name provided to progress_listener")
            return
            
        logger.debug(f"STEP: {step_name} SENDER: {sender}")
        # Mark step as done
        step = next(s for s in self.steps if s.step_name == step_name)
        step.done = True
        self.set_percent = self.calculate_progress()
        
        asyncio.create_task(websock_conn.broadcast({
            "event": "PROGRESS_UPDATE",
            "percent_complete": self._percent_complete
        }))
        
download_progress = ProgressTracker()
download_sig = signal('download_sig')
download_sig.connect(download_progress.progress_listener)
logger.debug("MARK STEP DONE REGISTERED")