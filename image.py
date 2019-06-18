import asyncio

import cv2

import imagezmq.imagezmq as imagezmq
from controls import ControlsServer

image_hub = imagezmq.ImageHub(open_port='tcp://*:27427')


class ImageProcessor:

	def __init__(self, control_server: ControlsServer):
		self.image_hub = imagezmq.ImageHub()
		self.control_server = control_server

	def start(self):
		print("Starting Image Processor")
		# todo move the thing onto another thread?
		loop = asyncio.new_event_loop()
		while True:
			rpi_name, image = image_hub.recv_image()
			image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # fix colors lol, https://stackoverflow.com/a/9641163
			# cv2.imshow(rpi_name, images)  # just for debug
			# cv2.waitKey(1)
			# print("Received Image from {}".format(rpi_name))
			loop.run_until_complete(self.control_server.push_image(image))
			# loop.run_until_complete(self.control_server.push_image(cv2.imencode(".jpg", images)[1]))
			image_hub.send_reply(b'OK')
