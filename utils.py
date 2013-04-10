import redis
import os

from os import path as op

_redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis_client = redis.from_url(_redis_url)

def get_map_places(map_id):
    places = redis_client.smembers(places_key(map_id))
    pipe = redis_client.pipeline()
    for place_id in places:
        pipe.hgetall(place_key(map_id, place_id))
    return pipe.execute()

def write_place_info(map_name, place_id, obj):
    pipe = redis_client.pipeline()
    for key in obj:
        pipe.hset(place_key(map_name, place_id), key, obj[key])
    pipe.execute()

def add_new_place(map_name, place):
    place_id = redis_client.incr(places_next_key(map_name))
    redis_client.sadd(places_key(map_name), place_id)
    place['id'] = place_id
    write_place_info(map_name, place_id, place)
    return place_id

def write_json_response(req, resp):
    req.set_header('Content-Type', 'application/json')
    return req.write(resp)

def jsonresult(fn):
    def wrapped(*args, **kwargs):
        return write_json_response(args[0], fn(*args, **kwargs))
    return wrapped

def places_key(map_id):
    return 'maps:{}:places'.format(map_id)

def places_next_key(map_id):
    return '{}:nextPlaceId'.format(places_key(map_id))

def place_key(map_id, place_id):
    return 'maps:{}:place:{}'.format(map_id, place_id)

def map_key(map_id):
    return 'maps:{}'.format(map_id)
