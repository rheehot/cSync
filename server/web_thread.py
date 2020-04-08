import websockets
from uuid import uuid4
from asyncio import get_event_loop, wait
from json import dumps, loads
import logging
from RequestPacket import *
from ResponseHandler import ResponseHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WebThread(websockets.WebSocketServer):
    def __init__(self, **kwargs):
        self.handler = ResponseHandler()
        self.HANDLER_MAP = {
            "capture" : self.handler.capture,
            "getId" : self.handler.getId,
            "status" : self.handler.status,
            "timesync" : self.handler.timesync,
            "setup" : self.handler.setup
        }
        self.kwargs = kwargs
        self.users = dict()

    async def send_command_all(self, command : BasePacket):
        if self.users and command:
            message = dumps(command)
            await wait([user.send(message) for user in self.users])

    async def register(self, websocket):
        self.users[websocket] = uuid4()
        packet = SetIdPacket(self.users[websocket])
        await websocket.send(packet.toJson())

    async def unregister(self, websocket):
        del self.users[websocket]

    async def getId(self):
        await self.send_command_all(GetIdPacket())

    async def status(self):
        await self.send_command_all(StatusPacket())

    async def capture(self):
        from time import time
        parameter = dict()
        parameter["time"] = ((time() + 5) * 1000)
        parameter["format"] = "png"
        CapturePacket(parameter)
        await self.send_command_all(StatusPacket())

    async def setup(self):
        parameter = {
            'awb_mode' : "auto",
            "brightness" : 50,
            "exif_tags" : {
                'EXIF.UserComments' : 'Copyright (c) 2020 Gyeongsik Kim'
            },
            "exposure_mode" : "auto",
            "flash_mode" : "auto"
        }
        packet = SetupPacket(parameter)
        await self.send_command_all(packet)
    
    async def timesync(self):
        packet = TimeSyncPacket()
        await self.send_command_all(packet)
    
    async def response(self, websocket, path):
        await self.register(websocket)
        try:
            async for message in websocket:
                packet : dict = loads(message)
                if packet["action"] in self.HANDLER_MAP.keys():
                    await self.HANDLER_MAP[packet["action"]](self.users[websocket], packet)
                else:
                    logger.warning(f"unsupported event: {str(packet)}")
        finally:
            await self.unregister(websocket)
    
    async def server(self, stop):
        async with websockets.serve(self.response, "0.0.0.0", 8000):
            await stop