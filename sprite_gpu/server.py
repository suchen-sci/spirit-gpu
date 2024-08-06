import asyncio
import json
import os
from typing import Dict, Any
from aiohttp import web

from sprite_gpu.env import Env
from sprite_gpu.log import logger
from sprite_gpu.settings import EASE_TEST_PORT
from sprite_gpu.worker import wrap_handler


class Handler:
    async def init(self, handlers: Dict[str, Any], env: Env):
        self.handler = await wrap_handler(handlers["handler"], env)
        self.env = env

    async def handle_post(self, request: web.Request):
        body = await request.read()
        try:
            data = json.loads(body)
        except Exception as e:
            logger.error(f"failed to parse request data: {e}")
            raise web.HTTPBadRequest()

        res = await self.handler(data)
        if type(res) == bytes:
            return web.Response(body=res)
        else:
            return web.json_response(res)


def run(handlers: Dict[str, Any], env: Env):
    handler = Handler()
    asyncio.run(handler.init(handlers, env))

    app = web.Application()
    app.router.add_post("/", handler.handle_post)
    port = int(os.environ.get(EASE_TEST_PORT, 8080))
    web.run_app(app, port=port)  # pyright: ignore
