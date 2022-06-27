# RabbitMQ RPC Implementation

A RPC Server and Client implementation working with RabbitMQ.

## RabbitRpc

Base class that both the server and client implementations utilize. Handles basic connection logic, reconnection, starting and stopping of the ioloop and standup of channels.

## RabbitRpcServer

Inherits from `RabbitRpc` and provides a way to respond to incoming requests. Expects to be passed in an array of methods (inherited from `RpcBaseMethod`) that handles the requests.

## RabbitRpcClient

Inherits from `RabbitRpc` and provides the framework to send requests and wait for responses. Handles multiple requests at a time and relaying back to the caller. Depends on using Requests inherited from `RpcBaseRequest`

## RpcBaseMethod

Works with `RabbitRpcServer` and handes the logic needed to respond to a given request. New methods inherit from this to provide needed functionality. Methods inheriting from this, need to set the name of the queue, typically tied to method name, that they listen to.

```python
from json import dumps
from RpcBaseMethod import RpcBaseMethod
class HelloWorld(RpcBaseMethod):

    def __init__(self):
        super().__init__()
        self.queue = 'hello_world'

    def method(self, channel, pika_method, props, body):
        self._logger.info('Response Received')
        self.response = dumps({'msg': 'Hello World'})
        super().method(channel, pika_method, props, body)
```

The above is an example method. It is listening for requests on the `hello_world` queue and responding back with hello world

#### Example

Below is an example script for running a server to respond to `HelloWorld`
```python
from RabbitRpc import RabbitRpcServer
from HelloWorld import HelloWorld

methods = [HelloWorld()]

server = RabbitRpcServer('testrpc', methods, 'localhost')

print('Starting Server...')

try:
   server.start()
except:
   server.close()
```

An example client script is Below

```python
from RabbitRpc import RabbitRpcClient
import threading
from RequestHelloWorld import RequestHelloWorld
import time

def main(client):
    request = RequestHelloWorld(client)
    while not client.ready:
        time.sleep(0.2)
        print('waiting to start...')
    print('Making Request...')
    request.make_request()

if __name__ == '__main__':

    client = RabbitRpcClient('testrpc', 'localhost')

    print('Starting Client...')
    try:
        cl_thread = threading.Thread(target=main, args=[client])
        cl_thread.start()
        client.start()
    except (RuntimeError, RuntimeWarning, KeyboardInterrupt, Exception) as e:
        print(e)
        client.close()
```
This defines a process to run to send requests and starts up the client main io loop. It sends a request for `HelloWorld` and prints the response once received. 

In order to run these examples, be sure to replace `localhost` with the url of the broker being used.