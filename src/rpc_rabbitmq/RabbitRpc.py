from abc import abstractmethod, ABCMeta
import pika
from pika.exchange_type import ExchangeType
from pika import exceptions
import logging
import json
import functools
import uuid

FORMAT = '%(asctime)s %(levelname)s: %(message)s'

class RabbitRpc(metaclass=ABCMeta):
    '''
    Base class to handle the common functionality between the Server \n
    and client implementations. Handles opening connections, handling \n
    connection drops and errors and starting and stopping the client or server
    '''

    def __init__(self, exchange: str, rabbit_url: str, rabbit_port: int = 5672,
                 rabbit_user_name: str = None, rabbit_password: str = None,
                 level: int = logging.INFO):

        self.channel = None
        self.exchange = exchange
        self.credentials = None
        self.ready = False
        self._reconnect = True
        self._logger = logging.getLogger(__name__)
        logging.basicConfig(level=level, format=FORMAT)
        self.exchange_type = ExchangeType.direct
        if rabbit_user_name is not None and rabbit_password is not None:
            self.credentials = pika.PlainCredentials(
                rabbit_user_name, rabbit_password)
        self.connection = pika.SelectConnection(
            pika.ConnectionParameters(
                rabbit_url, rabbit_port,
                credentials=self.credentials if self.credentials is not None else
                pika.ConnectionParameters.DEFAULT_CREDENTIALS),
            on_open_callback=self._on_connection_open,
            on_close_callback=self._on_connection_close,
            on_open_error_callback=self._on_open_connection_error)

    def _on_connection_open(self, connection):
        self._logger.info('Connection Opened')
        self.channel = connection.channel(
            on_open_callback=self._on_channel_open)

    def _on_connection_close(self, connection, exception):
        self.ready = False
        self._logger.warning('Connection Closed: %s', exception)
        if self._reconnect:
            self._on_open(connection)

    def _on_open_connection_error(self, connection, exception):
        self.ready = False
        self._logger.warning('Channel Connection Error: %s', exception)
        self.close()

    def _on_channel_open(self, channel):
        self._logger.info('Channel Opened')
        self.channel = channel
        self.channel.add_on_close_callback(self._on_channel_closed)
        self._setup_exchange()
        

    def _on_channel_closed(self, channel, reason):
        self._logger.warning('Channel Closed: %s', reason)

    def _setup_exchange(self):
        self.channel.exchange_declare(
            exchange=self.exchange,
            exchange_type=self.exchange_type,
            callback=self._on_exchange_declareok
        )

    @abstractmethod
    def _on_exchange_declareok(self, _):
        #child class must override
        pass

    def start(self):
        self.connection.ioloop.start()

    def close(self):
        self.ready = False
        self._reconnect = False
        self.connection.close()

class RabbitRpcClient(RabbitRpc):
    '''
    Rpc Client implementation for sending and receiving request via \n
    a RabbitMQ broker. Provides base functionality for handling the conenction, \n
    sending requests and handling responses. \n
    Provides JSON serialization and de-serialization for the messages
    '''

    def __init__(self, exchange: str, rabbit_url: str, rabbit_port: int = 5672,
                 rabbit_user_name: str = None, rabbit_password: str = None):

        super().__init__(exchange, rabbit_url, rabbit_port,
                         rabbit_user_name, rabbit_password)
        self.callback_queue = None
        self.requests = {}

    def _on_exchange_declareok(self, _):
        self._logger.info('Exchange Declared')
        self.channel.queue_declare(queue='', exclusive=True,
                                   auto_delete=True,
                                   callback=self._on_queue_open)

    def _on_response(self, _, _2, props, body):
        if props.correlation_id in self.requests:
            # received response for sent request, relay to caller
            request = self.requests.pop(props.correlation_id)
            request.response = json.loads(body.decode('utf-8'))
        else:
            self._logger.warning('Unexpected response received: %s',
                                 props.correlation_id)

    def _on_queue_open(self, method):
        self._logger.info('Queue Opened')
        self.callback_queue = method.method.queue
        self.channel.queue_bind(
            self.callback_queue,
            self.exchange,
            callback=self._on_bindok
        )

    def _on_bindok(self, _):
        self._logger.info('Queue bound, starting consumer')
        try:
            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self._on_response,
                auto_ack=True)
            self.ready = True
        except exceptions as e:
            self._logger.warning('Issue starting consumer: %s', e)

    def _publish(self, request):
        corr_id = str(uuid.uuid4())
        self._logger.info('Sending Request...')
        try:
            self.requests[corr_id] = request
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=request.routing_key,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=corr_id
                ),
                body=json.dumps(request.request)
            )
            self._logger.info('Request Sent')
        except (RuntimeError, RuntimeWarning, AttributeError, TypeError,
                exceptions.AMQPChannelError, exceptions.BodyTooLongError,
                exceptions.ChannelError) as e:
            request = self.requests.pop(corr_id)
            request.error = e

    def send_request(self, request):
        if self.ready:
            try:
                cb = functools.partial(self._publish, request=request)
                self.connection.ioloop.add_callback_threadsafe(cb)
            except (RuntimeError, RuntimeWarning, AttributeError, TypeError) as e:
                raise Exception('Unable to send Request') from e
        else:
            raise RuntimeWarning('Cannot Send Request, connection not ready')

class RabbitRpcServer(RabbitRpc):
    '''
    RPC Server for handling requests via RabbitMQ \n
    Provides connection to the server, routing of requests and handling of responses \n
    Designed to work with classes inherited from rabbit_rpc_methods \n
    A byte array or string needs to be provided as the message of the request and will also be the response \n
    The methods are responsible for serialization and de-serialization of data
    '''

    def __init__(self, exchange: str, methods: list, rabbit_url: str, rabbit_port: int = 5672,
                 rabbit_user_name: str = None, rabbit_password: str = None):

        super().__init__(exchange, rabbit_url, rabbit_port, rabbit_user_name, rabbit_password)
        self.methods = methods

    def _on_exchange_declareok(self, _):
        self.ready = True
        for method in self.methods:
            method.response_callback = self.send_response
            self.channel.queue_declare(queue=method.queue)
            self.channel.queue_bind(queue=method.queue,
            exchange=self.exchange)
            self.channel.basic_consume(
                queue=method.queue, on_message_callback=method.method)
            self._logger.info('Started consuming method: %s', method.queue)

    def send_response(self, channel, props, method, response: dict):
        self._logger.info('Sending Response, id: %s', props.correlation_id)
        channel.basic_publish(exchange=self.exchange,
                              routing_key=props.reply_to,
                              properties=pika.BasicProperties(
                                  correlation_id=props.correlation_id
                              ),
                              body=response)
        channel.basic_ack(delivery_tag=method.delivery_tag)