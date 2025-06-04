import os
import sys
import warnings
from pathlib import Path

# Filter out pyasn1 deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pyasn1")

# Get the project root directory
project_root = str(Path(__file__).parent.parent)

# Add the project root directory to the Python path
sys.path.insert(0, project_root) 