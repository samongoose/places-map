import tornado.web
import tornado.options
import tornado.ioloop
import tornado.httpserver
import redis
import json
import os

from datetime import timedelta
from tornado.web import RequestHandler
from tornado.web import addslash
from tornado import httpclient
from os import path as op

ROOT = op.normpath(op.dirname(__file__))

_redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
_redis_client = redis.from_url(_redis_url)

def _get_map_places(map_id):
    places = _redis_client.smembers(_places_key(map_id))
    pipe = _redis_client.pipeline()
    for place_id in places:
        pipe.hgetall(_place_key(map_id, place_id))
    return pipe.execute()

def _write_json_response(req, resp):
    req.set_header('Content-Type', 'application/json')
    return req.write(resp)

def _write_place_info(map_name, place_id, obj):
    pipe = _redis_client.pipeline()
    for key in obj:
        pipe.hset(_place_key(map_name, place_id), key, obj[key])
    pipe.execute()

def _places_key(map_id):
    return 'maps:%s:places' % (map_id)

def _places_next_key(map_id):
    return _places_key(map_id) + ':nextPlaceId'

def _place_key(map_id, place_id):
    return 'maps:%s:place:%s' % (map_id, place_id)

def _map_key(map_id):
    return 'maps:%s' % map_id


class MapController(RequestHandler):
    @addslash
    def get(self, map_id):
        if len(map_id) <= 0:
            raise httpclient.HTTPError(404)
        map_obj = {}
        map_obj['places'] = _get_map_places(map_id)
        name = map_id
        if name is not None:
            map_obj['name'] = name
        if (self.get_argument('fmt', 'html') == 'json'):
            return _write_json_response(self, json.dumps(map_obj))
        else:
            return self.render("map_view.html", 
                  map_obj = json.dumps(map_obj))
  
    @addslash
    def put(self, map_id):
        if (len(map_id) <= 0
                or not (_redis_client.exists(_map_key(map_id)))):
            raise httpclient.HTTPError(404)

        try:
            new_list = json.loads(self.request.body)
        except Exception:
            raise HTTPError(500)

        for place in new_list:
            PlacesController.add_new_place(map_id, place)

class MapsController(RequestHandler):
    @addslash
    def post(self):
        #create new map
        map_obj = json.loads(self.request.body)
        if (_redis_client.exists(_map_key(map_obj['name']))):
            self.set_status(409)
            return self.write("map name already taken")
        _redis_client.hset(_map_key(map_obj['name']), 'name', map_obj['name'])
        self.set_header('Location', '/Maps/' + str(map_obj['name']) + '/')
        self.set_status(201)
        return self.write("")

class PlacesController(RequestHandler):

    @staticmethod
    def add_new_place(map_name, place):
        place_id = _redis_client.incr(_places_next_key(map_name))
        _redis_client.sadd(_places_key(map_name), place_id)
        place['id'] = place_id
        _write_place_info(map_name, place_id, place)

        return place_id

    def post(self, map_name):
        try:
            new_item = json.loads(self.request.body)
        except Exception:
            raise HTTPError(500)

        place_id = PlacesController.add_new_place(map_name, new_item)
    
        self.set_header('Location', '/Maps/%s/Places/%s/' % 
                       (map_name, place_id))
        self.set_status(201)
        return _write_json_response(self, {'id':place_id})


    @addslash
    def get(self, map_name):
        places = json.dumps(_get_map_places(map_name))
        return _write_json_response(self, places)

class PlaceController(RequestHandler):

    @addslash
    def get(self, map_name, place_id):
        place_json = json.dumps(
                _redis_client.hgetall(_place_key(map_name, place_id)))
        return _write_json_response(self, place_json)

    @addslash
    def delete(self, map_name, place_id):
        if (len(map_name) <= 0
                or len(place_id) <= 0):
            raise httpclient.HTTPError(404)

        pipe = _redis_client.pipeline()
        pipe.srem(_places_key(map_name), place_id)
        pipe.delete(_place_key(map_name, place_id))
        pipe.execute()
        self.set_status(204)
        return self.write("")

    @addslash
    def put(self, map_name, place_id):
        new_info = json.loads(self.request.body)
        _write_place_info(map_name, place_id, new_info)
        #return empty 200 on success
        return self.write("") 

class Index(RequestHandler):
    @addslash
    def get(self):
        return self.render("index.html")


_settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "debug": "True",
}

_application = tornado.web.Application([
        (r"/Maps/([^/]+)/Places/([^/]+)/?", PlaceController),
        (r"/Maps/([^/]+)/Places/?", PlacesController),
        (r"/Maps/([^/]+)/?", MapController),
        (r"/Maps/?", MapsController),
        (r"/", Index)],
    **_settings)

def set_ping(io_loop, timeout):
    io_loop.add_timeout(timeout, lambda: set_ping(io_loop, timeout))

if __name__ == "__main__":
    _application.listen(8888)

    _ioloop = tornado.ioloop.IOLoop.instance()
    set_ping(_ioloop, timedelta(seconds=2))
    _ioloop.start()
