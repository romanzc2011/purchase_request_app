from collections import defaultdict

"""
AUTHOR: ROMAN CAMPBELL
DATE: 09/09/2025
SOCKET STATE -- tracks socketio state

This is necessary to map sid to users to prevent race condition like behavior. Executing
an sio.emit will broadcast to all connected clients. This will cause issues if multiple
users make requests at the sametime. This way each emit will send only to it mapped sid.
"""

# Map username -> sids
user_sids = defaultdict(set)

# Map sid -> username
sid_user: dict[str, str] = {}