from dataclasses import dataclass
from typing import List

@dataclass
class User:
    username: str
    email: str
    group: List[str] 