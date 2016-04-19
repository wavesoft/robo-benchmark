
from robob.factories import pipeFactory, parserFactory
from robob.pipe.bashwrap import Pipe as BashWrapPipe
from robob.metrics import Metrics
from robob.pipe.app import Pipe as AppPipe

class Stream(object):
	"""
	A stram on which tests can run
	"""

	def __init__(self, context, metrics):
		"""
		Initialize a new stream
		"""

		self.pipe = None
		self.bashPipe = None
		self.appPipe = None
		self.accessPipe = None
		self.metrics = metrics
		self.context = context

	def configure(self, specs):
		"""
		Configure stream from the specified specs context
		"""

		# Get node
		node = specs['node']
		if not "node.%s" % node in self.context:
			raise AssertionError("Node '%s' was not defined in the specs" % node)
		node = self.context["node.%s" % node]

		# Get app
		app = specs['app']
		if not "app.%s" % app in self.context:
			raise AssertionError("App '%s' was not defined in the specs" % app)
		app = self.context["app.%s" % app]

		# Get optional app env
		env = None
		if 'env' in app:
			env = app['env']
			if not "env.%s" % env in self.context:
				raise AssertionError("env '%s' was not defined in the specs" % env)
			env = self.context["env.%s" % env]

		########################################
		# Initialize context variables
		########################################

		# Define context of current node, parser, app
		self.context.set( "node", node )
		self.context.set( "app", app )
		if env:
			self.context.set( "env", env )
			self.context.update( env )

		# Update custom variable definitions
		if 'define' in node:
			self.context.update( node['define'] )
		if 'define' in app:
			self.context.update( app['define'] )
		if 'define' in specs:
			self.context.update( specs['define'] )

		# Render context
		self.context = self.context.render()

		########################################
		# Initialize pipes
		########################################

		# Factory app pipe
		self.appPipe = AppPipe( self.context )
		self.appPipe.configure( self.context['app'] )

		# Factory bash multiplexer/wrapper
		self.bashPipe = BashWrapPipe( self.context )
		self.bashPipe.plug( self.appPipe )

		########################################
		# Initialize metrics
		########################################

		self.metrics = Metrics()
		self.metrics.configure( self.context )

		########################################
		# Initialize parsers
		########################################

		# Locate parser names
		parser_names = []
		if 'parser' in specs:
			parser_names.append( specs['parser'] )
		elif 'parsers' in specs:
			parser_names += specs['parser']
		else:
			raise AssertionError("It's required to define at least one parser on stream")

		# Instantiate parsers
		for n in parser_names:
			if not "parser.%s" % n in self.context:
				raise AssertionError("Parser '%s' was not defined in the specs" % n)

			# Factory parser & listen for app output
			parser = parserFactory(self.context["parser.%s" % n], self.context, self.metrics )
			self.appPipe.listen( parser )

		# Instantiate streamlets
		if 'streamlets' in specs:
			for n in specs['streamlets']:

				# Get streamlet
				if not "streamlet.%s" % n in self.context:
					raise AssertionError("Streamlet '%s' was not defined in specs" % n)
				streamlet = self.context["streamlet.%s" % n]

				# Instantiate streamlet pipe
				if not 'class' in streamlet:
					streamlet['class'] = "robob.pipe.script"
				pipe = pipeFactory( streamlet, self.context )

				# Plug it on bash pipe
				self.bashPipe.plug( pipe )

				# Get parser(s)
				parser_names = []
				if 'parser' in streamlet:
					parser_names.append( streamlet['parser'] )
				elif 'parsers' in streamlet:
					parser_names += streamlet['parser']

				# Instantiate parsers
				for n in parser_names:
					if not "parser.%s" % n in self.context:
						raise AssertionError("Parser '%s' was not defined in the specs" % n)

					# Factory parser & listen for app output
					parser = parserFactory(self.context["parser.%s" % n], self.context, self.metrics )
					pipe.listen( parser )

		########################################
		# Initialize host accessor
		########################################

		# Get node configuration
		node = self.context['node']
		if not 'access' in node:
			raise AssertionError("Required at least one access component on node specs")

		# Create and chain accessor component
		for a in node['access']:

			# Merge node components into the accessor configuration
			specs = dict(node)
			specs.update( a )

			# Create accessor pipe
			pipe = pipeFactory( specs, self.context )

			# Chain them all the way to the bash pipe
			if self.accessPipe is None:
				self.accessPipe = pipe
				self.accessPipe.plug( self.bashPipe )
			else:
				pipe.plug( self.accessPipe )
				self.accessPipe = pipe

		# That's now our master pipe and we are ready to go!
		self.pipe = self.accessPipe


