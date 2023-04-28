import re       # for regex usage in path-processing functions
import socket       # for socket connection (essentially for establishing communication between the two socket nodes for connection)
import threading        # for multiple simultaneous connections

class HTTPServer:
    def __init__(self, host, port, paths):
        self.host = host
        """localhost or any other IP --> could be local device's IP (gethostname
        for intuitive retrieval of the executing machine's ip)"""
        self.port = port        # 8000 or any other unused port
        self.paths = paths      # json paths file
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """ create a socket which takes as mandatory parameters (as constants) the (1) address family for
        which addresses can the socket communicate with (AF_INET for IPv4 addresses), and
        (2) the type of connection protocol (here SOCK_STREAM for TCP (UDP is SOCK_DGRAM))"""
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        """setting socket option for in case a socket is closed before full
        transmission of data --> performs TIME_WAIT then reuses this same address to
        complete connection even if its "busy", with socket "on" (1)"""

    def match_path(self, path):
        for compiled_path in self.paths:        # pass through every key of the json dic
            if '<' in compiled_path:        # if potential variable (confined in <>) exists in path (which is technically only for the account html)
                if re.match(compiled_path.split('<')[0], path):     # if a known path is found in the first elt of the split url
                    # "/account/" ::: "/account/lea"
                    # return "/account/<username>"
                    return compiled_path
            else:
                if path == compiled_path:
                    return compiled_path
        return None     # will eventually be the instigator for 404.html

    def handle_request(self, client_connection):
        request = client_connection.recv(1024)
        decoded_request = request.decode('utf-8')       # receive and decode the request

        # Extract the HTTP method and path from the request
        method, path, _ = decoded_request.split(' ', 2)     # second parameter in split method to specify how many maximum spaces it should find (here 2, so max 2 splits --> 3 segments)
        """To parse the request which would technically take on the following form (HTTP request anatomy):
        
        GET(method) /somewhere.html(path) HTTP/1.1(protocol)
        Host: localhost:8000
        User-Agent: Mozilla/5.0
        Accept: text/html, text/xml, etc
        
        We are only interested in the first 2 elements in the request separated by spaces (method and path)
        (the following lines constitute the request header (and further on, body)) --> split to retrieve specifically
        these first two str sequences, respectively conveniently named "method" and "path".
        """

        # Match the path against the compiled paths dictionary
        matched_path = self.match_path(path)        # path retrieved from request is matched to json paths via above path-matching function
        # will return the exact json path if located within searched url
        # will return None if not matched to anything

        # Serve the file corresponding to the matched path
        if matched_path is not None:        # if matched_path actually exists in json
            param_name = ""
            # If the matched path is a dynamic path, extract the parameter value
            if '<' in matched_path:     # regex indicator of variable found in path (again technically only in "account")
                param_name = matched_path.split('<')[1].split('>')[0]       # isolating the actual variable from the rest of the symbols in path
                # path = "/account/lea"    ["","account","lea"]
                # path = "/account/<lea>" -> ["/account/","lea>"] (lea>) -> ["lea", ""] ???
                # param_value = "lea"
                param_value = path.split('/')[-1]
                file_path = self.paths[matched_path]#.replace(f'<{param_name}>', param_value)
            else:
                file_path = self.paths[matched_path]
            

            # "<" + param_name + ">" to bytes  // param_name for exmaple "username"
            param_before = bytes(f"<{param_name}>",'utf-8')

            # Open the file, read its contents, and replace the <username> placeholder if it exists
            with open(file_path, 'rb') as f:        # read in binary
                file_content = f.read()
                if param_before in file_content:
                    file_content = file_content.replace(param_before, param_value.encode('utf-8'))
            

            # Send the response headers and file content back to the client
            response = b'HTTP/1.0 200 OK\n\n' + file_content        # success status response code --> displays the corresponding matched html
            client_connection.sendall(response)
        else:       # in case entered url is not recognized within json config
            # If the path isn't found, send a 404 Not Found status response code
            with open('404.html', 'rb') as f:
                file_content = f.read()
            response = b'HTTP/1.0 404 Not Found\n\n' + file_content     # displays 404 error html
            client_connection.sendall(response)

        client_connection.close()

    def run_server(self):
        self.server_socket.bind((self.host, self.port))     # bind the socket server to its designated host and port it will communicate through
        self.server_socket.listen(5)
        """listening socket allows for a maximum of 5 pending requests (before accepted) (possibly slightly
        unnecessary since accessed only from one device so one single client request) so technically its not
        the number of connecting clients that is limited to 5, just the number of simultaneous requests before
        being accepted --> once accepted, pending spot is liberated for more requests from socket --> hence the need for
        MULTI-THREADING to handle multiple threads of clients at once"""
        print(f"Server listening on http://{self.host}:{self.port}")

        while True:     # infinite loop to continuously accept any requests
            client_connection, client_address = self.server_socket.accept()
            print(f"New client connected: {client_address}")
            client_handler = threading.Thread(target=self.handle_request, args=(client_connection,))        # thread taking on as parameters the funtion that is run several times simultaneously, and its argument
            client_handler.start()
