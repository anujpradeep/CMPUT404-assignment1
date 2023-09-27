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
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        # print("Got a request of: %s\n" % self.data)

        request_lines: list[str] = self.data.decode("utf-8").split("\r\n")

        # print(request_lines)
        
        if len(request_lines) > 0:
            request_type, path, _ = request_lines[0].split(" ")
            print("request_type = ", request_type)
            print("path = ", path)
            if request_type == "GET":
                self.handle_get_request(path)
            else:
                self.send_response(405, "Method Not Allowed")
        else:
            self.send_response(400, "Bad Request")

    def send_response(self, status_code, status_message, content_type="text/html"):
        response = f"HTTP/1.1 {status_code} {status_message}\r\n"
        response += "Content-Type: {}\r\n".format(content_type)
        response += "\r\n"
        self.request.sendall(response.encode())

    def handle_get_request(self, path):
        www_dir = "www"

        # Joins the path given from the request to www directory to create a file path
        # The file path might or might not exist in ./www
        requested_file_path = os.path.join(www_dir, path.lstrip("/"))

        print("www_dir", www_dir)
        print("file_path", requested_file_path)

        # Check if the requested path is within the ./www directory
        if os.path.abspath(requested_file_path).startswith(os.path.abspath(www_dir)):

            # If the path exists, can be a directory or a file
            if os.path.exists(requested_file_path):

                # If the path exists, and is a file
                if os.path.isfile(requested_file_path):
                    # Determine the content type based on the file extension
                    content_type = "text/html" if requested_file_path.endswith(".html") else "text/css"

                    # Read and send the file content
                    with open(requested_file_path, "rb") as file:
                        content = file.read()
                    self.send_response(200, "OK", content_type)
                    self.request.sendall(content)

                # is inside ./www but is a directory
                elif os.path.isdir(requested_file_path):
                    if requested_file_path.endswith("/"):
                        index_file_path = os.path.join(requested_file_path.lstrip("/"), "index.html")
                        if os.path.exists(index_file_path) and os.path.isfile(index_file_path):
                            with open(index_file_path, "rb") as file:
                                content = file.read()
                            self.send_response(200, "OK", "text/html")
                            self.request.sendall(content)
                        else:
                            self.send_response(404, "Not Found")
                    # Path does not end with /, will have to redirect
                    else:
                        self.send_response(301, "Moved Permanently")
                        new_location = requested_file_path + "/"
                        self.request.sendall(f"Location: {new_location}/\r\n\r\n".encode())

            else:
                self.send_response(404, "Not Found")
        else:
            # there is no file path that matches the requested file path inside ./www
            self.send_response(403, "Not Found")

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
