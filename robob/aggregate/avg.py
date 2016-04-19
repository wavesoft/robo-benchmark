
from robob.metrics import MetricAggregator

class Aggregate(MetricAggregator):
	"""
	Average aggregator calculates the average of the collected values
	"""

	def configure(self, config):
		"""
		Configure aggregator
		"""
		self.title = "(Avg)"
		if 'title' in config:
			self.title = config['title']

	def collect(self, values):
		"""
		Run aggregator for the specified values and collect results
		"""

		# Summarize
		num = 0
		for v in values:
			num += v.v

		# Return average suffix
		return [ num / len(values) ]

	def titles(self):
		"""
		Return the titles of this aggregator values
		"""
		return [ self.title ]