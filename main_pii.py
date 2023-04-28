# from http_server import HTTPServer

from http_server import HTTPServer
import json

# Load JSON file containing routing paths
with open('paths.json', 'r') as f:
    paths = json.load(f)

# Create HTTPServer object with host, port, and config paths as parameters
server = HTTPServer('localhost', 8000, paths)
# Run server
server.run_server()