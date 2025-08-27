from __future__ import annotations
from enum import Enum, auto
from typing import List
import asyncio
from loguru import logger
from api.services.progress_tracker.steps.download_steps import DOWNLOAD_STEPS, DownloadStep
from api.services.progress_tracker.steps.approval_steps import APPROVAL_STEPS, ApprovalStep
from api.services.progress_tracker.steps.submit_request_steps import SUBMIT_REQUEST_STEPS, SubmitRequestStep

# Import the SSE broadcast function from the main API
try:
    from api.pras_api import broadcast_sse_event
except ImportError:
    # Fallback for when the function isn't available yet
    async def broadcast_sse_event(data: dict):
        logger.warning("SSE broadcast function not available")

# Import threading for async operations
import threading
 
# -----------------------------------------------------------------------------
# PROGRESS TRACKER TYPE
# -----------------------------------------------------------------------------
class ProgressTrackerType(Enum):
    DOWNLOAD = auto()
    APPROVAL = auto()
    SUBMIT_REQUEST = auto()

# ------------------------------------------
# Progress Tracker
# ------------------------------------------           
class ProgressTracker:
    def __init__(self):
        self.download_steps = [DownloadStep(s.step_name, s.weight) for s in DOWNLOAD_STEPS]
        self.approval_steps = [ApprovalStep(s.step_name, s.weight) for s in APPROVAL_STEPS]
        self.submit_request_steps = [SubmitRequestStep(s.step_name, s.weight) for s in SUBMIT_REQUEST_STEPS]
        self._start_download_tracking = False
        self._start_approval_tracking = False
        self._start_submit_request_tracking = False
        self._percent_complete = 0

    @property
    def start_download_tracking(self):
        return self._start_download_tracking
    
    @start_download_tracking.setter
    def start_download_tracking(self, value: bool):
        self._start_download_tracking = value
        
    @property
    def start_approval_tracking(self):
        return self._start_approval_tracking
    
    @start_approval_tracking.setter
    def start_approval_tracking(self, value: bool):
        self._start_approval_tracking = value
        
    @property
    def start_submit_request_tracking(self):
        return self._start_submit_request_tracking
    
    @start_submit_request_tracking.setter
    def start_submit_request_tracking(self, value: bool):
        self._start_submit_request_tracking = value
        
    @property
    def percent_complete(self):
        return self._percent_complete
    
    @percent_complete.setter
    def percent_complete(self, value: int):
        self._percent_complete = value
        
    @property
    def active_tracker(self) -> ProgressTrackerType | None:
        if self.start_download_tracking:
            return ProgressTrackerType.DOWNLOAD
        
        elif self.start_approval_tracking:
            return ProgressTrackerType.APPROVAL
        
        elif self.start_submit_request_tracking:
            return ProgressTrackerType.SUBMIT_REQUEST
        
        return None
        
    def reset(self):
        for step in self.download_steps:
            step.done = False
            
    def send_start_msg(self):
        # Run the async broadcast in a new thread to avoid blocking
        def run_broadcast():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(broadcast_sse_event({
                    "event": "START_TOAST",
                    "percent_complete": 0
                }))
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_broadcast)
        thread.start()
        logger.debug("Sent start toast message")
    
    def mark_step_done(self, step_name):
        
        """Mark a step as done and update progress"""
        if self.start_download_tracking:
            steps = self.download_steps
            
        elif self.start_approval_tracking:
            steps = self.approval_steps
            
        elif self.start_submit_request_tracking:
            steps = self.submit_request_steps
            
        else:
            return
        
        # Find and mark the step as done
        step = next((s for s in steps if s.step_name == step_name), None)
        if step:
            step.done = True
            self.percent_complete = self.calculate_progress()
            
            # Broadcast progress update
            def run_broadcast():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(broadcast_sse_event({
                        "event": "PROGRESS_UPDATE",
                        "percent_complete": self._percent_complete
                    }))
                finally:
                    loop.close()
            
            thread = threading.Thread(target=run_broadcast)
            thread.start()
    
    def remaining_steps(self) -> List[DownloadStep | ApprovalStep | SubmitRequestStep]:
        active = self.active_tracker
        if active is None:
            return []
        
        steps_map = {
            ProgressTrackerType.DOWNLOAD:       self.download_steps,
            ProgressTrackerType.APPROVAL:       self.approval_steps,
            ProgressTrackerType.SUBMIT_REQUEST: self.submit_request_steps
        }
        steps = steps_map[active]
        
        for s in steps:
            logger.info(f"Step: {s.step_name} :: {s.done}\n")
        
        return [step for step in steps if not step.done]
    
    #------------------------------------------------------------------
    # Calculate progress
    #------------------------------------------------------------------
    def calculate_progress(self) -> int:
        if self.start_download_tracking:
            steps = self.download_steps
            
        elif self.start_approval_tracking:
            steps = self.approval_steps
            
        elif self.start_submit_request_tracking:
            steps = self.submit_request_steps
            
        else:
            return self._percent_complete
        
        total_weight = sum(s.weight for s in steps)
        done_weight = sum(s.weight for s in steps if s.done)
        self._percent_complete = int((done_weight / total_weight) * 100)
        return self._percent_complete