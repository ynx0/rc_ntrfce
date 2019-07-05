import asyncio
import base64
import os
from glob import glob
import io

import cv2
import numpy as np
import socketio
from PIL import Image
from aiohttp import web
from procbridge import Client

# warning, don't use ngrok because it forwards everything from localhost, essentially bypassing the whitelist
from WebCommands import WebCommands
from rc_common import netcfg

# MARK - setup variables
from rc_common.RC_Commands import Commands

whitelist = [
	'127.0.0.1',
	'192.168.0.112',  # NTRFCE Outward IP
	'192.168.0.111',  # Yaseen iPhone
	'192.168.0.110',  # Mom's Laptop
	'192.168.0.105',  # Dad's iPhone
]
CONTROL_PORT = 23484
RC_CAR1_NS = '/rc1'
active_clients: dict = []

num = 0

sio = socketio.AsyncServer(ping_timeout=60000, pingInterval=1, max_http_buffer_size=1_000_000, )
app = web.Application()
sio.attach(app)


async def index(request):
	"""Serve the client-side application."""
	with open('index.html') as f:
		return web.Response(text=f.read(), content_type='text/html')


def get_client() -> Client:
	client = None
	# noinspection PyBroadException
	try:
		client = Client(netcfg.HOST, netcfg.HDW_PORT)
		print("[+] RPi connection nominal")
	except Exception:
		print("Error: unable to connect to host {}:{}".format(netcfg.HOST, netcfg.HDW_PORT))

	return client


def try_request(command, payload):
	global client
	try:
		client.request(command, payload)
	except ConnectionRefusedError:

		# tries to reconnect to the rpi if it happened to go down in between commands
		client = get_client()


client = get_client()


class ControlsServer(socketio.Namespace):

	def __init__(self):
		super().__init__()
		app.router.add_static('/static', 'static')
		app.router.add_get('/', index)
		self.cleanup_img()

	# MARK - rpi rc controls setup
	# self.rpi_connection_nominal = False
	# self.client = get_client()
	# if self.client is not None:
	# 	self.rpi_connection_nominal = True

	@staticmethod
	def cleanup_img():
		img_files = glob('./images/*.jpg')
		for f in img_files:
			os.remove(f)

	# give all http reqs a valid page
	@staticmethod
	@sio.on('connect', namespace=RC_CAR1_NS)
	def connection_handler(sid, environ):
		# client_ip = environ['REMOTE_ADDR']
		request = environ['aiohttp.request']
		client_ip = request.transport.get_extra_info('peername')[0]
		print(client_ip)
		if client_ip not in whitelist:
			print("Client {} tried to connect but is not in whitelist. Denying...".format(client_ip), sid)
			return False
		else:
			print("Client {} successfully connected".format(client_ip))

	@staticmethod
	@sio.on('control-event', namespace=RC_CAR1_NS)
	async def control_handler(sid, data):

		print("Received control event ", data)
		# if self.rpi_connection_nominal:
		command = data['command']
		info = data['data']  # lol
		if command == WebCommands.CTRL_FORWARD.value:
			print('yo')
			try_request(Commands.FORWARD, {"speed": info['fwSpeed']})
		elif command == WebCommands.CTRL_BACKWARD.value:
			try_request(Commands.BACKWARD, {"speed": info['bwSpeed']})

		elif command == WebCommands.CTRL_LEFT.value:
			try_request(Commands.LEFT, {})
		elif command == WebCommands.CTRL_RIGHT.value:
			try_request(Commands.RIGHT, {})

		elif command == WebCommands.CTRL_STOP.value:
			try_request(Commands.STOP, {})

		await sio.emit('ACK', room=sid)  # command was successfully executed

	# else:
	# 	await sio.emit('NACK', room=sid)  # command was not successfully executed

	@staticmethod
	@sio.event
	def disconnect(sid, **kwargs):
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

	@staticmethod
	def start_sync():
		web.run_app(app, host='0.0.0.0', port=CONTROL_PORT, reuse_address=True)

	@staticmethod
	async def runner():
		runner = web.AppRunner(app)
		await runner.setup()
		site = web.TCPSite(runner, "0.0.0.0", port=CONTROL_PORT, reuse_address=True)
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
