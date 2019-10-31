import struct
import time

class MessageType(object):
	"""
	Enum class that holds the different message types
	"""
	
	GPS_MESSAGE = 1

class MessageHandler():
	"""
	Class used to send and receive messages over a socket
	"""
	
	_msgTimeout = 15
	
	@staticmethod
	def sendMsg(sock, msg, msgType):
		"""
		Sends a message on the specified socket
		
		@param sock:    The socket to send the message on
		@param msg:     The message (string)
		@param msgType: The type of message being sent
		
		@return None
		"""

		encodedMsg = msg.encode()

		msgSize = struct.pack('!I', len(encodedMsg))
		packedMsgType = struct.pack('!I', msgType)

		sock.sendall(msgSize + packedMsgType + encodedMsg)
	
	@staticmethod
	def recvMsg(sock):
		"""
		Receives a message on the specified socket
		
		@param sock: The socket to receive the message on
		
		@return Returns a tuple (msgType, msg) if a valid message
				was received, otherwise returns None
		"""
		
		# Attempt to read the message size
		data = MessageHandler.recvAll(sock, 4)

		if data is not None:
			msgSize, = struct.unpack('!I', data)

			# Attempt to read the message type
			data = MessageHandler.recvAll(sock, 4)
			
			if data is not None:
				msgType, = struct.unpack('!I', data)
				
				# Attempt to read the message contents
				data = MessageHandler.recvAll(sock, msgSize)
				
				if data is not None:
					return (msgType, data.decode())

		return None

	@staticmethod
	def recvAll(sock, numBytesToRead):
		"""
		Attempts to read the specified number of
		bytes off of the specified socket
		
		@param sock:           The socket to receive the message on
		@param numBytesToRead: The number of bytes that must be read
		
		@return buf: The buffer containing the data
		"""
		
		buf = b''
		
		startTime = time.time()

		while numBytesToRead:
			# Check to see if a timeout has occurred
			if time.time() - startTime > MessageHandler._msgTimeout:
				return None
			
			try:
				data = sock.recv(numBytesToRead)

				# Check to see if there is no data to read
				if not data:
					return None

				buf += data
				numBytesToRead -= len(data)
			except:
				pass
		
		return buf