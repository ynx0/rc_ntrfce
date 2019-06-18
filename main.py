import threading

from controls import ControlsServer
from image import ImageProcessor


def main():
	controls_server = ControlsServer()
	image_processor = ImageProcessor(controls_server)

	controls_thread = threading.Thread(target=controls_server.start_async, name='SocketIO Thread')
	image_thread = threading.Thread(target=image_processor.start)
	controls_thread.setDaemon(True)
	image_thread.setDaemon(True)

	controls_thread.start()
	image_thread.start()

	while 1:
		pass


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print("Exitting")
