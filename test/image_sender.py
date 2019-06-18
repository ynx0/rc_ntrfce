import cv2
import numpy as np

import imagezmq.imagezmq as imagezmq

HOST = 'localhost'
PORT = 27427


def main():
	image1 = np.zeros((400, 400, 3), dtype='uint8')
	green = (0, 255, 0)
	cv2.rectangle(image1, (50, 50), (300, 300), green, 40)
	# A red square on a black background
	image2 = np.zeros((400, 400, 3), dtype='uint8')
	red = (0, 0, 255)
	cv2.rectangle(image2, (100, 100), (350, 350), red, 40)

	sender = imagezmq.ImageSender(connect_to="tcp://{}:{}".format(HOST, PORT))
	while True:  # press Ctrl-C to stop images sending program
		sender.send_image("TEST CLIENT", image1)
		print(image1.shape)
		sender.send_image("TEST CLIENT", image2)
		# time.sleep(1)


if __name__ == '__main__':

	try:
		main()
	except KeyboardInterrupt:
		print("Exitting")
