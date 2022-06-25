from src.rpc_rabbitmq.RabbitRpcServer import RabbitRpcServer
from examples.HelloWorld import HelloWorld

methods = [HelloWorld()]

server = RabbitRpcServer(methods, 'localhost')

print('Starting Server')

try:
    server.start()
except:
    server.close()