import json

import cv2
import numpy as np
import socketio

RC_CAR1_NS = '/rc1'

sio = socketio.Client()

image_count = 0


@sio.on('images', namespace=RC_CAR1_NS)
def message(data):
	global image_count
	print("Received images")
	image = json.loads(data['images'])
	image = np.asarray(image, dtype='uint8')
	image_count += 1
	print(image_count)
	cv2.imshow('Test Image', image)
	cv2.waitKey(0)



# @sio.on('heartbeat', namespace=RC_CAR1_NS)
# def heartbeat_msg(sid, data):
# 	print("Received heartbeat from {}".format(sid))


@sio.on('connect', namespace=RC_CAR1_NS)
def on_connect():
	print("I'm connected to the /rc1 namespace!")


def main():
	sio.connect('http://localhost:23484', namespaces=[RC_CAR1_NS])
	print("hey")
	sio.wait()


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print("Exitting")
