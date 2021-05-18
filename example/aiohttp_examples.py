from aiohttp.web_routedef import post
import pyqrcode
import asyncio
import json
import pprint
import logging
import secrets
import base64
import jwt

from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_response import Response, json_response


logging.basicConfig(level=logging.INFO)


async def handle_postbox(request):
    post_body = await request.read()
    post_body = json.loads(post_body)
    print(post_body)

    return json_response({'bo': 'yah'})
    pass

if __name__ == '__main__':
    PORT = 3001

    routes = []
    routes.append(web.post('/postbox', handle_postbox))

    app = web.Application()
    app.add_routes(routes)

    web.run_app(app, port=PORT)
