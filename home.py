import tornado.web
import tornado.options
import tornado.ioloop
import tornado.httpserver
import json

from datetime import timedelta
from tornado.web import RequestHandler
from tornado.web import addslash
from tornado import httpclient
from utils import *

ROOT = op.normpath(op.dirname(__file__))

class MapController(RequestHandler):
    @addslash
    def get(self, map_id):
        if len(map_id) <= 0:
            raise httpclient.HTTPError(404)
        map_obj = {}
        map_obj['places'] = get_map_places(map_id)
        name = map_id
        if name is not None:
            map_obj['name'] = name
        if self.get_argument('fmt', 'html') == 'json':
            return write_json_response(self, json.dumps(map_obj))
        else:
            return self.render('map_view.html', 
                  map_obj = json.dumps(map_obj))
  
    @addslash
    def put(self, map_id):
        if (len(map_id) <= 0 or 
            not (redis_client.exists(map_key(map_id)))):
            raise httpclient.HTTPError(404)

        try:
            new_list = json.loads(self.request.body)
        except Exception:
            raise HTTPError(500)

        for place in new_list:
            add_new_place(map_id, place)
        return self.write('') 

class MapsController(RequestHandler):
    @addslash
    def post(self):
        #create new map
        map_obj = json.loads(self.request.body)
        if redis_client.exists(map_key(map_obj['name'])):
            self.set_status(409)
            return self.write('map name already taken')
        redis_client.hset(map_key(map_obj['name']), 'name', map_obj['name'])
        self.set_header('Location', '/Maps/{}/'.format(
                                    str(map_obj['name'])))
        self.set_status(201)
        return self.write('')

class PlacesController(RequestHandler):
    @jsonresult
    def post(self, map_name):
        try:
            new_item = json.loads(self.request.body)
        except Exception:
            raise HTTPError(500)

        place_id = add_new_place(map_name, new_item)
    
        self.set_header('Location', '/Maps/{}/Places/{}/'.format( 
                       map_name, place_id))
        self.set_status(201)
        return json.dumps({'id':place_id})

    @addslash
    @jsonresult
    def get(self, map_name):
        places = json.dumps(get_map_places(map_name))
        return places

class PlaceController(RequestHandler):

    @addslash
    @jsonresult
    def get(self, map_name, place_id):
        place_json = json.dumps(
                redis_client.hgetall(place_key(map_name, place_id)))
        return place_json

    @addslash
    def delete(self, map_name, place_id):
        if len(map_name) <= 0 or len(place_id) <= 0:
            raise httpclient.HTTPError(404)

        pipe = redis_client.pipeline()
        pipe.srem(places_key(map_name), place_id)
        pipe.delete(place_key(map_name, place_id))
        pipe.execute()
        self.set_status(204)
        return self.write('')

    @addslash
    def put(self, map_name, place_id):
        new_info = json.loads(self.request.body)
        write_place_info(map_name, place_id, new_info)
        #return empty 200 on success
        return self.write('') 

class Index(RequestHandler):
    @addslash
    def get(self):
        return self.render('index.html')


_settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
}

_application = tornado.web.Application([
        (r'/Maps/([^/]+)/Places/([^/]+)/?', PlaceController),
        (r'/Maps/([^/]+)/Places/?', PlacesController),
        (r'/Maps/([^/]+)/?', MapController),
        (r'/Maps/?', MapsController),
        (r'/', Index)],
    **_settings)

def set_ping(io_loop, timeout):
    io_loop.add_timeout(timeout, lambda: set_ping(io_loop, timeout))

if __name__ == '__main__':
    _application.listen(os.environ.get('PORT', 8888))

    _ioloop = tornado.ioloop.IOLoop.instance()
    set_ping(_ioloop, timedelta(seconds=2))
    _ioloop.start()
