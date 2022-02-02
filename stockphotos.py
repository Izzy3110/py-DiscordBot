import os
from PIL import Image
import requests
import uuid


class Photos(object):
	tor_server = {
		"http": "192.168.2.22:9050"
	}
	dim = None
	thumbnail_max_size = (100, 100)

	def __init__(self, imgNum, imgDim, use_tor=None, tor_addrport=None):
		if tor_addrport is not None:
			self.tor_server["http"] = tor_addrport
		self.current_uuid = str(uuid.uuid1())
		self.cwd = os.getcwd()
		os.chdir(self.cwd)
		self.requests_session = requests.session()
		# use tor proxy
		if use_tor is not None:
			if use_tor:
				self.requests_session.proxies = self.tor_server

		for i in range(1, int(imgNum) + 1):
			i = str(i)
			self.get_and_save(('https://picsum.photos/' + imgDim[0] + '/' + imgDim[1] + '?random'),
		('downloaded/stock-image-' + self.current_uuid + "_" + i + '.jpg'))

	def create_thumbnail(self, input_path):
		splitted = os.path.basename(input_path).split(".")
		new_ = splitted[0] + "_thumb" + "." + splitted[1]
		image = Image.open(input_path)
		image.thumbnail(self.thumbnail_max_size)

		if not os.path.isdir(os.path.join(os.path.dirname(input_path), "_thumbs")):
			os.mkdir(os.path.join(os.path.dirname(input_path), "_thumbs"))

		image.save(os.path.join(os.path.dirname(input_path), "_thumbs", new_))

	def get_and_save(self, url, fname):
		with self.requests_session.get(url) as response:
			if response.status_code == 200:
				response.raw.decode_content = True
				with open(fname, 'wb') as f:
					for chunk in response:
						f.write(chunk)
					f.close()
				self.create_thumbnail(fname)

"""
- number of images
- image size e.g. 1920x1080
"""

Photos(3, "1920x1080".split("x"), use_tor=True)
