import json

import numpy as np


# big mcthankies to https://stackoverflow.com/a/47626762
class NumpyEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, np.ndarray):
			return obj.tolist()
		return json.JSONEncoder.default(self, obj)
