#  coding: utf-8 
import os
import socketserver

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):
	
	error404 = f"404 Page Not Found. The requested resource could not be found on the server.\r\n\r\n".encode()
	error405 = f"405 Method Not Allowed. The request type is not supported\r\n\r\n".encode()

	def handle(self):
		self.data = self.request.recv(1024).strip()
		request_lines: list[str] = self.data.decode("utf-8").split("\r\n")

		print(request_lines)
		
		# requests might be an empty, but the length will be 1
		if len(request_lines) > 1:
			request_type, path, _ = request_lines[0].split(" ")
			if request_type == "GET":
				self.handle_get_request(path)
			else:
				self.send_response(405, "Method Not Allowed", "text/html", self.error405)
		else:
			self.send_response(400, "Bad Request", "text/html", "")
			
	def send_response(self, status_code: int, status_message: str, content_type: str, content):
		response = f"HTTP/1.1 {status_code} {status_message}\r\n"
		response += "Content-Type: {}\r\n".format(content_type)
		response += "\r\n"
		self.request.sendall(response.encode())

		# Sending the actual content
		if (content != ""):
			self.request.sendall(content)

	def handle_file(self, file_path : str):
		content_type : str
		if file_path.endswith(".html"):
			content_type = "text/html"
		else:
			content_type = "text/css"


		# Read and send the file content
		with open(file_path, "rb") as file:
			content = file.read()
		status_code = 200

		return status_code, content_type, content
	
	# Function should be used when its a directory. It will return the status_code, content_type, content
	# Will only return if said index.html exists inside the directory.
	def get_index(self, file_path: str):
		index_file_path = os.path.join(file_path.lstrip("/"), "index.html")

		if os.path.exists(index_file_path) and os.path.isfile(index_file_path):
			return self.handle_file(index_file_path)
		else:
			# sending 404 status code because the index.html file was not found.
			return 404

	def handle_get_request(self, path: str):
		# Joins the path given from the request to www directory to create a file path
		# The file path might or might not exist in ./www
		requested_file_path = os.path.join("www", path.lstrip("/"))

		# Check if the requested path is within the ./www directory
		if os.path.abspath(requested_file_path).startswith(os.path.abspath("www")):

			# If the path exists, can be a directory or a file
			if os.path.exists(requested_file_path):

				# If the path exists, and is a file
				if os.path.isfile(requested_file_path):
					# Determine the content type based on the file extension

					status_code, content_type, content = self.handle_file(requested_file_path)
					self.send_response(status_code, "OK", content_type, content)

				# is inside ./www but is a directory
				elif os.path.isdir(requested_file_path):
					# if the actual path, not the joined one ends with /
					if path.endswith("/"):
						status_code, content_type, content = self.get_index(requested_file_path)

						if (status_code == 200):
							self.send_response(status_code, "OK", content_type, content)
						else:
							self.send_response(404, "Not Found", "text/html", self.error404)

					# Path does not end with /, will have to redirect
					else:
						content = f"New Location is : {path + '/'}\r\n\r\n".encode()
						self.send_response(301, "Moved Permanently", "text/html", content)
			else:
				self.send_response(404, "Not Found", "text/html", self.error404)
		else:
			# there is no file path that matches the requested file path inside ./www
			self.send_response(403, "Not Found", "text/html", self.error404)

if __name__ == "__main__":
	HOST, PORT = "localhost", 8080

	socketserver.TCPServer.allow_reuse_address = True
	# Create the server, binding to localhost on port 8080
	server = socketserver.TCPServer((HOST, PORT), MyWebServer)

	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	server.serve_forever()
