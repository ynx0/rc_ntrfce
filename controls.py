import asyncio
import base64
import io
import json
import os
from dataclasses import dataclass
from glob import glob
from typing import Any

import cv2
import numpy as np
import socketio
from PIL import Image
from aiohttp import web

# MARK - setup variables


# warning, don't use ngrok because it forwards everything from localhost, essentially bypassing the whitelist

whitelist = ['127.0.0.1', '73.237.101.174', '192.168.0.112']
CONTROL_PORT = 23484
RC_CAR1_NS = '/rc1'
active_clients: dict = []

num = 0

@dataclass
class Client:
	ip: Any
	connection_timestamp: Any
	sid: Any


sio = socketio.AsyncServer(ping_timeout=60000, pingInterval=1, max_http_buffer_size=1_000_000)
app = web.Application()
sio.attach(app)


async def index(request):
	"""Serve the client-side application."""
	with open('index.html') as f:
		return web.Response(text=f.read(), content_type='text/html')


class ControlsServer:

	def __init__(self):
		app.router.add_static('/static', 'static')
		app.router.add_get('/', index)
		self.cleanup_img()

	@staticmethod
	def cleanup_img():
		img_files = glob('./images/*.jpg')
		for f in img_files:
			os.remove(f)

	# give all http reqs a valid page
	@staticmethod
	@sio.on('connect', namespace=RC_CAR1_NS)
	def connection_handler(sid, environ):
		client_ip = environ['REMOTE_ADDR']
		if client_ip not in whitelist:
			print("Client {} tried to connect but is not in whitelist. Denying...".format(client_ip), sid)
			return False
		else:
			print("Client {} successfully connected".format(client_ip))

	@staticmethod
	@sio.on('control-event', namespace=RC_CAR1_NS)
	async def control_handler(sid, data):
		print("Received control event ", data)

		await sio.emit('ACK', room=sid)

	@staticmethod
	@sio.event
	def disconnect(sid):
		print('disconnect ', sid)

	@staticmethod
	async def push_image(image):
		global num
		num += 1
		# todo add brotli or some other compression
		# from https://stackoverflow.com/a/53443893
		# images = np.reshape(images, (400, 400, 3))
		jpg_bytes = io.BytesIO()
		im = Image.fromarray(image)
		im.save(jpg_bytes, format="jpeg")
		# im.save("images/test{}.jpg".format(num))

		jpg_bytes = base64.b64encode(jpg_bytes.getvalue()).decode('utf8')
		# image_sz = json.dumps(jpg_bytes)
		await sio.emit('image', data={'image': jpg_bytes}, namespace=RC_CAR1_NS, )

	def start_sync(self):
		web.run_app(app, host='localhost', port=CONTROL_PORT, reuse_address=True)

	async def runner(self):
		runner = web.AppRunner(app)
		await runner.setup()
		site = web.TCPSite(runner, "localhost", port=CONTROL_PORT, reuse_address=True)
		await site.start()
		print("Controls Server is Operational")

	def start_async(self):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(self.runner())
		loop.run_forever()


# from https://stackoverflow.com/a/48726076


if __name__ == '__main__':
	server = ControlsServer()
	server.start_async()

	image1 = np.zeros((400, 400, 3), dtype='uint8')
	green = (0, 255, 0)
	cv2.rectangle(image1, (50, 50), (300, 300), green, 5)

	sio.emit('images', data=image1)
