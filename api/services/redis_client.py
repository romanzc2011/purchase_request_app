import redis
from loguru import logger

r = redis.Redis(host='localhost', port=5005, db=0, decode_responses=True)
logger.success("REDIS CLIENT INITIALIZED...")