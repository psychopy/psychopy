"""
Liaison provides a simple server for Remote Process Communication (RPC),
using WebSockets as communication protocol and JSON for message packing

This is a simple, secure alternative to existing general-purpose options such as
zeroRPC

**This is a work in progress and all subject to change [2023]**

@author Alain Pitiot
@copyright (c) 2023 Open Science Tools Ltd.
"""


import inspect
import logging
import asyncio
import signal
import json
import sys
import traceback

from psychopy.localization import _translate

try:
	import websockets
except ModuleNotFoundError as err:
	err.msg = _translate(
		"`psychopy.liaison` requires the package `websockets`, this can be installed via command line:\n"
		"`pip install websockets`."
	)


class LiaisonJSONEncoder(json.JSONEncoder):
	"""
	JSON encoder which calls the `getJSON` method of an object (if it has one) to convert to a
	string before JSONifying.
	"""
	def default(self, o):
		# if object has a getJSON method, use it
		if hasattr(o, "getJSON"):
			return o.getJSON(asString=False)
		# otherwise behave as normal
		try:
			return json.JSONEncoder.default(self, o=o)
		except TypeError:
			return str(o)


class WebSocketServer:
	"""
	A simple Liaison server, using WebSockets as communication protocol.
	"""

	def __init__(self):
		"""
		Create an instance of a Liaison WebSocket server, to which clients can connect to run the methods of class instances.
		"""
		# the set of currently established connections:
		self._connections = set()

		# setup a logger:
		self._logger = logging.getLogger('liaison.WebSocketServer')
		self._logger.setLevel(logging.DEBUG)
		consoleHandler = logging.StreamHandler()
		consoleHandler.setLevel(logging.DEBUG)
		consoleHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
		self._logger.addHandler(consoleHandler)

		# register the Liaison methods available to clients:
		self._methods = {
			'liaison': (self, ['listRegisteredMethods', 'pingPong'])
		}

	def registerObject(self, targetObject, referenceName):
		"""
		Register handle of the given target object, so it can be acted upon by clients of the server.

		Parameters
		----------
		targetObject : 	object
			the object whose handle will be registered as <reference name>
		referenceName : string
			the name used to refer to the given target object when calling its method
		"""
		self._methods[referenceName] = (targetObject, ['registerMethods'])
		# create, log and return success message
		msg = f"Registered object of class: {type(targetObject).__name__} with reference name: {referenceName}"
		self._logger.info(msg)

		return msg

	def registerMethods(self, targetObject, referenceName):
		"""
		Register all public methods of the given target object, so they can be called by clients of the server.

		Parameters
		----------
		targetObject : 	object
			the object whose methods will be registered as <reference name>.<method name>
		referenceName : string
			the name used to refer to the given target object when calling its method
		"""
		targetCls = type(targetObject)
		# choose methods
		targetMethods = []
		for name in dir(targetObject):
			# if function is callable and not private, register it
			fnct = getattr(targetObject, name)
			if callable(fnct) and not name.startswith("__"):
				targetMethods.append(name)
			# if function is a property and not private, register its fget method
			clsfnct = getattr(targetCls, name, None)
			if isinstance(clsfnct, property) and not name.startswith("__"):
				targetMethods.append(name)

		self._methods[referenceName] = (targetObject, targetMethods)
		# create, log and return success message
		msg = (
			f"Registered the following methods: {self._methods[referenceName][1]} for object of class: "
			f"{type(targetObject).__name__} with reference name: {referenceName}"
		)
		self._logger.info(msg)

		return msg

	def registerClass(self, targetCls, referenceName):
		"""
		Register a given class, so that an instance can be created by clients of the server.

		Parameters
		----------
		targetCls : class
			Class to register as <reference name>
		referenceName : str
			Name used to refer to the target class when calling its constructor
		"""
		# register init
		self._methods[referenceName] = (targetCls, ['init'])
		# create, log and return success message
		msg = f"Registered class: {targetCls} with reference name: {referenceName}"
		self._logger.info(msg)

		return msg

	def listRegisteredMethods(self):
		"""
		Get the list of all registered methods for all objects.

		Returns
		-----
		list of str
			the list of registered methods, as strings in the format: <object reference name>.<method name>
		"""
		registeredMethods = []
		for name in self._methods:
			for method in self._methods[name][1]:
				registeredMethods.append(f"{name}.{method}")
		return registeredMethods

	def actualizeAttributes(self, arg):
		"""
		Convert a string pointing to an attribute of a registered object into the value of that
		attribute.

		Parameters
		----------
		arg : str
			String in the format `object.attribute` pointing to the target attribute
		"""
		self._logger.debug(
			f"Parsing raw arg: {arg}"
		)

		if isinstance(arg, str) and "." in arg:
			_name, _attr = arg.split(".", 1)
			if _name in self._methods:
				_obj, _methods = self._methods[_name]
				if _attr in _methods:
					arg = getattr(_obj, _attr)
		elif isinstance(arg, dict):
			# actualize all values if given a dict of params
			for key in arg:
				arg[key] = self.actualizeAttributes(arg[key])

		return arg

	def start(self, host, port):
		"""
		Start the Liaison WebSocket server at the given address.

		Notes
		----
		This is a blocking call.

		Parameters
		----------
		host : string
			the hostname, e.g. 'localhost'
		port : int
			the port number, e.g. 8001
		"""
		asyncio.run(self.run(host, port))

	def pingPong(self):
		"""
		This method provides the server-side pong to the client-side ping that acts as
		a keep-alive approach for the WebSocket connection.
		"""
		pass

	async def run(self, host, port):
		"""
		Run a Liaison WebSocket server at the given address.

		Parameters
		----------
		host : string
			the hostname, e.g. 'localhost'
		port : int
			the port number, e.g. 8001
		"""
		# set the loop future on SIGTERM or SIGINT for clean interruptions:
		loop = asyncio.get_running_loop()
		loopFuture = loop.create_future()
		if sys.platform in ("linux", "linux2"):
			loop.add_signal_handler(signal.SIGINT, loopFuture.set_result, None)

		async with websockets.serve(self._connectionHandler, host, port):
			self._logger.info(f"Liaison Server started on: {host}:{port}")
			await loopFuture
			# await asyncio.Future()  # run forever

		self._logger.info('Liaison Server terminated.')

	async def broadcast(self, message):
		"""
		Send a message to all connected clients:

		Parameters
		----------
		message : string
			the message to be sent to all clients
		"""
		if not isinstance(message, str):
			message = json.dumps(message, cls=LiaisonJSONEncoder)
		for websocket in self._connections:
			await websocket.send(message)

	def broadcastSync(self, message):
		"""
		Call Liaison.broadcast from a synchronous context.

		Parameters
		----------
		message : string
			the message to be sent to all clients
		"""
		try:
			# try to run in new loop
			asyncio.run(self.broadcast(message))
		except RuntimeError:
			# use existing if there's already a loop
			loop = asyncio.get_event_loop()
			loop.create_task(self.broadcast(message))

	async def _connectionHandler(self, websocket):
		"""
		Handler managing all communications received from a client connected to the server.

		Parameters
		----------
		websocket : WebSocketServerProtocol
			the websocket connection established when the client connected to the server
		"""
		clientIP = websocket.remote_address[0]
		self._logger.info(f"New connection established with client at IP: {clientIP}")
		self._connections.add(websocket)

		while True:
			try:
				message = await websocket.recv()
				self._logger.debug(f"New message received from client at IP: {clientIP}: {message}")

				# process the message:
				await self._processMessage(websocket, message)

			except websockets.ConnectionClosedOK as error:
				self._logger.info(f"Connection closed cleanly with client at IP: {clientIP}: {error}")
				self._connections.remove(websocket)
				break
			except websockets.ConnectionClosedError as error:
				self._logger.info(f"Connection closed uncleanly (protocol error or network failure) with client at IP: {clientIP}: {error}")
				self._connections.remove(websocket)
				break

	async def _processMessage(self, websocket, message):
		"""
		Process a message received from a client.

		Currently, only method calls are processed.
		They should be in the following format:
			{
				"object": <object reference name>,
				"method": <method name>,
				"args": [<arg>,<arg>,...],
				"messageId": <uuid>
			}
		"args" and "messageId" are optional. messageId's are used to match results to messages, they enable
		a single client to make multiple concurrent calls.
		To instantiate a registered class, use the keyword "init" as the method name. To register the methods of
		an instantiated object, use the keyword "registerMethods" as the method name.

		The result of the method call is sent back to the client in the following format:
			{"result": <result as string>, "messageId": <uuid>}

		If an error occurred when the method was called, the error is return to the client in the following format:
			{"error": <result as string>, "messageId": <uuid>}

		Parameters
		----------
		websocket : WebSocketServerProtocol
			the websocket connection on which the message was received
		message : string
			the message sent by the client to the server, as a JSON string
		"""
		# decode the message:
		try:
			decodedMessage = json.loads(message)
		except Exception as error:
			self._logger.debug(f"unable to json decode the message: {error}")
			return
		self._logger.debug(f"decoded message: {decodedMessage}")

		# process the decoded message:
		try:
			# - if the message has an object and a method field, check whether a corresponding method was registered
			if 'object' in decodedMessage:
				# get object
				queryObject = decodedMessage['object']
				if queryObject not in self._methods:
					raise Exception(f"No methods of the object {queryObject} have been registered with the server")
				# get method
				queryMethod = decodedMessage['method']
				if queryMethod not in self._methods[queryObject][1]:
					raise Exception(f"{queryObject}.{queryMethod} has not been registered with the server")
				# extract and unpack args
				rawArgs = decodedMessage['args'] if 'args' in decodedMessage else []
				args = []
				for arg in rawArgs:
					# try to parse json string
					try:
						arg = json.loads(arg)
					except json.decoder.JSONDecodeError:
						pass
					# if arg is a known property, get its value
					arg = self.actualizeAttributes(arg)
					# append to list of args
					args.append(arg)

				if 'method' in decodedMessage:
					# if method is init, initialise object from class and register it under reference name
					if queryMethod == "init":
						cls = self._methods[queryObject][0]
						# add self to args if relevant
						kwargs = {}
						if "liaison" in inspect.getfullargspec(cls.__init__).args:
							kwargs['liaison'] = self
						# create instance
						obj = cls(*args, **kwargs)
						# register object (but not its methods yet)
						rawResult = self.registerObject(obj, referenceName=queryObject)

					# if method is register, register methods of object
					elif queryMethod == "registerMethods":
						# get object
						obj = self._methods[queryObject][0]
						# register its methods
						rawResult = self.registerMethods(obj, referenceName=queryObject)

					# any other method, call as normal
					else:
						self._logger.debug(f"running the registered method: {queryObject}.{queryMethod}")

						# get the method and determine whether it needs to be awaited:
						method = getattr(self._methods[queryObject][0], queryMethod)
						methodIsCoroutine = inspect.iscoroutinefunction(method)

						# run the method, with arguments if need be:
						if methodIsCoroutine:
							rawResult = await method(*args)
						else:
							rawResult = method(*args)

					# convert result to a string
					result = json.dumps(rawResult, cls=LiaisonJSONEncoder)

					# send a response back to the client:
					response = {
						"result": result
					}

					# if there is a messageId in the message, add it to the response:
					if 'messageId' in decodedMessage:
						response['messageId'] = decodedMessage['messageId']

					await websocket.send(json.dumps(response))

		except Exception as err:
			# send any errors to server
			tb = traceback.format_exception(type(err), err, err.__traceback__)
			msg = "".join(tb)
			err = json.dumps({
				'type': "error",
				'msg': msg,
				'context': getattr(err, "userdata", None)
			}, cls=LiaisonJSONEncoder)
			await websocket.send(err)
			