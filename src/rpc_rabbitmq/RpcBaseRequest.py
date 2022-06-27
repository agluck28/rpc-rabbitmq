from abc import ABCMeta, abstractmethod
import time
import logging

FORMAT = '%(asctime)s %(levelname)s: %(message)s'


class RpcBaseRequest(metaclass=ABCMeta):

    def __init__(self, RpcClient, timeout_ms: int = 1000, level=logging.INFO):
        self.routing_key = None
        self.request = None
        self.response = None
        self.error = None
        self.timeout = timeout_ms
        self.rpc = RpcClient
        self._logger = logging.getLogger(__name__)
        logging.basicConfig(level=level, format=FORMAT)

    @abstractmethod
    def make_request(self):
        self._logger.info('Sending Request: %s', self.request)
        self.rpc.send_request(self)
        timeout = self.timeout

        while timeout > 0:
            now = time.time()
            if self.response is not None:
                self._logger.info('Received Response')
                return self.response
            elif self.error is not None:
                self._logger.warn('No Response Received')
                return {'success': False, 'msg': self.error}
            else:
                timeout -= (time.time() - now)*1000
        return {'success': False, 'msg': 'Timeout'}
