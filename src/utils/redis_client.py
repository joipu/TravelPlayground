import redis

# Initialize Redis client for caching
redis_client = redis.StrictRedis(host='localhost', port=6380, db=0)
