import redis

pool = redis.ConnectionPool(host='112.126.58.87', port=6379, decode_responses=True)
redis_cli = redis.Redis(connection_pool=pool)

redis_cli.zrem("search_keywords_set","")