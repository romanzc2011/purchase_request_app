from collections import defaultdict

# Map username -> sids
user_sids = defaultdict(set)

# Map sid -> username
sid_user: dict[str, str] = {}