# Copyright 2023 Anuj Pradeep
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

import os
import socketserver
import socket

ERROR_301_CONTENT = """
		<!DOCTYPE html>
		<html>
			<head>
				<title>301 Moved Permanently</title>
			</head>
			<body>
				<h1>This page has been moved.</h1>
				<p>The requested resource has been permanently moved to a new location.follow this link to the new location:</p>
				<a href="{}">{}</a>
			</body>
		</html>
		"""

ERROR_400_CONTENT = """
			<!DOCTYPE html>
			<html>
				<head>
					<title>400 Bad Request</title>
				</head>
				<body>
					<h1>400 Bad Request</h1>
					<p>The request sent by the client was malformed or invalid.</p>
				</body>
			</html>
		""".encode()

ERROR_404_CONTENT = """
		<!DOCTYPE html>
		<html>
			<head>
				<title>404 Not Found</title>
			</head>
			<body>
				<h1>404 Not Found</h1>
				<p>The requested resource could not be found on the server.</p>
			</body>
		</html>
		""".encode()

ERROR_405_CONTENT = """
		<!DOCTYPE html>
		<html>
			<head>
				<title>405 Method Not Allowed</title>
			</head>
			<body>
				<h1>405 Method Not Allowed</h1>
				<p>The requested method is not allowed.</p>
			</body>
		</html>
		""".encode()


class MyWebServer(socketserver.BaseRequestHandler):
	'''
		Is a function for socketserver, it handles the requests
	'''
	def handle(self):
		
		self.data = self.request.recv(1024).strip()
		request_lines: list[str] = self.data.decode("utf-8").split("\r\n")

		print(request_lines)
		
		# requests might be an empty, but the length will be 1
		if len(request_lines) > 1:
			request_type, path, _ = request_lines[0].split(" ")
			_, self.host = request_lines[1].split(" ")
			if request_type == "GET":
				self.handle_get_request(path)
			else:
				self.send_response(405, "Method Not Allowed", "text/plain", ERROR_405_CONTENT)
		else:
			# catch for if there is a bad response/request. I was getting a empty list (list['']) so I added the check and catch for it.
			self.send_response(400, "Bad Request", "text/plain", ERROR_400_CONTENT)


	'''
		If the request we got is a GET request, this function will handle it, even if the path is valid or not
	'''
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
							self.send_response(404, "Not Found", "text/html", ERROR_404_CONTENT)

					# Path does not end with /, will have to redirect
					else:
						content = ERROR_301_CONTENT.format(path + "/",self.host + path + "/").encode()
						self.send_response(301, "Moved Permanently", "text/html", content)
			else:
				self.send_response(404, "Not Found", "text/html", ERROR_404_CONTENT)
		else:
			# there is no file path that matches the requested file path inside ./www
			self.send_response(404, "Not Found", "text/html", ERROR_404_CONTENT)


	'''
		Function will send the response to the client, the HTTP Header and the body content. 
	'''
	def send_response(self, status_code: int, status_message: str, content_type: str, content):
		header = f"HTTP/1.1 {status_code} {status_message}\r\nContent-Type: {content_type}\r\n\r\n".encode()
		self.request.sendall(header)
		self.request.sendall(content)

	'''
		This function will handle if the path is a file. will return the status code, content type and content
		This function will only be called if its the path exists in www, therefor we dont have to check if it exists here
	'''
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
	'''
		Function should be used when its a directory. It will return the status_code, content_type, content
		Will only return if said index.html exists inside the directory.
	'''
	def get_index(self, file_path: str):
		index_file_path = os.path.join(file_path.lstrip("/"), "index.html")

		if os.path.exists(index_file_path) and os.path.isfile(index_file_path):
			return self.handle_file(index_file_path)
		else:
			# sending 404 status code because the index.html file was not found.
			return 404

if __name__ == "__main__":
	HOST, PORT = "localhost", 8080

	socketserver.TCPServer.allow_reuse_address = True
	# Create the server, binding to localhost on port 8080
	server = socketserver.TCPServer((HOST, PORT), MyWebServer)

	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	server.serve_forever()