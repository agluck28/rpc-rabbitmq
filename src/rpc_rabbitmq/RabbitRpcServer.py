import pika

class RabbitRpcServer():
    '''
    RPC Server for handling requests via RabbitMQ \n
    Provides connection to the server, routing of requests and handling of responses \n
    Designed to work with classes inherited from rabbit_rpc_methods \n
    A byte array or string needs to be provided as the message of the request and will also be the response \n
    The methods are responsible for serialization and de-serialization of data
    '''

    def __init__(self, methods: list, rabbit_url: str, rabbit_port: int = 5672,
                 rabbit_user_name: str = None, rabbit_password: str = None):
        self.credentials = None
        self.channel = None
        self.methods = methods
        self.credentials = None
        if rabbit_user_name is not None and rabbit_password is not None:
            self.credentials = pika.PlainCredentials(
                rabbit_user_name, rabbit_password)
        self.connection = pika.SelectConnection(
            pika.ConnectionParameters(
                rabbit_url, rabbit_port,
                credentials=self.credentials if self.credentials is not None else
                pika.ConnectionParameters.DEFAULT_CREDENTIALS),
            on_open_callback=self._on_open,
            on_close_callback=self._on_close,
            on_open_error_callback=self._on_open_error)

    def _on_open(self, connection):
        self.channel = connection.channel(
            on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        for method in self.methods:
            method.response_callback = self.send_response
            self.channel.queue_declare(queue=method.queue)
            self.channel.basic_consume(
                queue=method.queue, on_message_callback=method.method)

    def _on_close(self, connection, exception):
        print(exception)
        print('The Channel Closed')
        #attempt to reconnect
        self._on_open(connection)

    def _on_open_error(self, connection, exception):
        print(exception)
        print('A channel open error happened')

    def send_response(self, channel, props, method, response: dict):
        channel.basic_publish(exchange='',
                              routing_key=props.reply_to,
                              properties=pika.BasicProperties(
                                  correlation_id=props.correlation_id
                              ),
                              body=response)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        self.connection.ioloop.start()

    def close(self):
        self.channel.close()
        self.connection.close()