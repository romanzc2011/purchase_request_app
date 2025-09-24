from .progress_tracker import ProgressTracker, ProgressTrackerType
from loguru import logger

download_progress: ProgressTracker | None = None
approval_progress: ProgressTracker | None = None
submit_request_tracker: ProgressTracker | None = None

# -----------------------------------------------------------------------------
# CREATE TRACKERS
# -----------------------------------------------------------------------------
def create_download_tracker() -> ProgressTracker:
    global download_progress
    
    # Turn off the other trackers
    if approval_progress is not None:
        approval_progress.start_approval_tracking = False
        
    if submit_request_tracker is not None:
        submit_request_tracker.start_submit_request_tracking = False
        
    # Create the new tracker
    download_progress = ProgressTracker()
    download_progress.start_download_tracking = True
    return download_progress

# -----------------------------------------------------------------------------
# GET DOWNLOAD TRACKER
# -----------------------------------------------------------------------------
def get_download_tracker() -> ProgressTracker:
    if download_progress is None:
        raise RuntimeError("Download tracker not created")
    return download_progress

# -----------------------------------------------------------------------------
# CREATE APPROVAL TRACKER
# -----------------------------------------------------------------------------
def create_approval_tracker() -> ProgressTracker:
    global approval_progress
    
    # Turn off the other trackers
    if download_progress is not None:
        download_progress.start_download_tracking = False
        
    if submit_request_tracker is not None:
        submit_request_tracker.start_submit_request_tracking = False
        
    # Create the new tracker
    approval_progress = ProgressTracker()
    approval_progress.start_approval_tracking = True
    return approval_progress

# -----------------------------------------------------------------------------
# GET APPROVAL TRACKER
# -----------------------------------------------------------------------------
def get_approval_tracker() -> ProgressTracker:
    if approval_progress is None:
        raise RuntimeError("Approval tracker not created")
    return approval_progress

# -----------------------------------------------------------------------------
# CREATE SUBMIT REQUEST TRACKER
# -----------------------------------------------------------------------------
def create_submit_request_tracker() -> ProgressTracker:
    global submit_request_tracker
    
    # Turn off the other trackers
    if download_progress is not None:
        download_progress.start_download_tracking = False
        
    if approval_progress is not None:
        approval_progress.start_approval_tracking = False
        
    # Create the new tracker
    submit_request_tracker = ProgressTracker()
    submit_request_tracker.start_submit_request_tracking = True
    return submit_request_tracker

# -----------------------------------------------------------------------------
# GET SUBMIT REQUEST TRACKER
# -----------------------------------------------------------------------------
def get_submit_request_tracker() -> ProgressTracker:
    if submit_request_tracker is None:
        raise RuntimeError("Submit request tracker not created")
    return submit_request_tracker

# -----------------------------------------------------------------------------
# GET ACTIVE TRACKER
# -----------------------------------------------------------------------------
def get_active_tracker() -> ProgressTracker:
    for getter, mode in (
        (get_download_tracker,       ProgressTrackerType.DOWNLOAD),
        (get_approval_tracker,       ProgressTrackerType.APPROVAL),
        (get_submit_request_tracker, ProgressTrackerType.SUBMIT_REQUEST),
    ):
        try:
            tracker = getter()
            if tracker.active_tracker == mode:
                return tracker
        except RuntimeError:
            continue
    return None

def print_tracker_statuses():
    logger.success(f"Download tracker: {download_progress.start_download_tracking}")
    logger.success(f"Approval tracker: {approval_progress.start_approval_tracking}")
    logger.success(f"Submit request tracker: {submit_request_tracker.start_submit_request_tracking}")