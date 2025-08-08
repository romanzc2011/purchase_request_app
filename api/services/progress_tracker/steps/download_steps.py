from enum import Enum, auto
from dataclasses import dataclass
from typing import List

# -----------------------------------------------------------------------------
# DOWNLOAD STEPS
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