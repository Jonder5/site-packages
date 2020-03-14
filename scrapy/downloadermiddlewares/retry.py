"""
An extension to retry failed requests that are potentially caused by temporary
problems such as a connection timeout or HTTP 500 error.

You can change the behaviour of this middleware by modifing the scraping settings:
RETRY_TIMES - how many times to retry a failed page
RETRY_HTTP_CODES - which HTTP response codes to retry

Failed pages are collected on the scraping process and rescheduled at the end,
once the spider has finished crawling all regular (non failed) pages.
"""
import logging

from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
    ConnectionRefusedError, ConnectionDone, ConnectError, \
    ConnectionLost, TCPTimedOutError
from twisted.web.client import ResponseFailed

from scrapy.exceptions import NotConfigured
from scrapy.utils.response import response_status_message
from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.utils.python import global_object_name

logger = logging.getLogger(__name__)


class RetryMiddleware(object):
    """
    开启重试中间件的方法：settings中`RETRY_ENABLED`必须为 True,且meta中键 `dont_retry` 的值bool判断类型必须为 False
    主要逻辑是，先判断是否满足需要重试的条件，如果满足，判断当前重试次数是否超过最大重试次数，是则放弃重试，否则返回 request 对象，重新放回调度队列里等待被调度
    即是利用了 downloader middleware 的 return request的作用
    """
    # IOError is raised by the HttpCompression middleware when trying to
    # decompress an empty response
    # 列出需要重试的异常
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    def __init__(self, settings):
        # 从 settings 中 获取 `RETRY_ENABLED`，如果boole类型为 false，则抛出 NotConfigured 异常，但该异常不在需要重试的异常之中。
        # 所以如果 RETRY_ENABLED 设置为 False(默认为True),则相当于跳过该中间件,因此需要重试，RETRY_ENABLED 必须为 True
        if not settings.getbool('RETRY_ENABLED'):
            raise NotConfigured
        # 从 settings 中获取 `RETRY_TIMES` 作为重试次数，整数型，默认为2
        self.max_retry_times = settings.getint('RETRY_TIMES')
        # 从 settings 中获取 `RETRY_HTTP_CODES` 作为重试状态码，在这里会做一次int类型转换，所以赋值为字符串也没关系；然后再用python的set去重
        # 默认 RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        # 从 settings 中获取 `RETRY_PRIORITY_ADJUST` 作为重试优先级调整，整数型,默认为-1
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    @classmethod
    def from_crawler(cls, crawler):
        # 获取 settings
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        # 如果 meta 中有键 `dont_retry`，且bool类型判断为 True，则返回 response，那么直接进入其他优先级更低中间件的 `process_response()`方法
        # 所以该作用和上面 `REDIRECT_ENABLED=False`效果一样，都可以看作是不使用重试中间件
        if request.meta.get('dont_retry', False):
            return response
        # 如果该状态码在需要重试的状态码中
        if response.status in self.retry_http_codes:
            # 获取出现该状态码的原因
            reason = response_status_message(response.status)
            # 返回_retry()方法或 response，即如果_retry()方法返回为None，则会返回 response
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        # 如果该异常是属于需要重试的异常，则且 dont_retry的bool判断类型 为 False，则返回 _retry()的结果
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            return self._retry(request, exception, spider)

    def _retry(self, request, reason, spider):
        """这是重试中间件的核心处理逻辑"""
        # 获取当前重试的次数
        retries = request.meta.get('retry_times', 0) + 1
        # 获取最大值重试次数的值
        retry_times = self.max_retry_times
        # 如果 meta 中有键 max_retry_times
        if 'max_retry_times' in request.meta:
            # 那么将其赋值给变量`retry_times`
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        # 如果当前重试的次数小于最大重试次数
        if retries <= retry_times:
            logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            # 赋值 request 对象
            retryreq = request.copy()
            # 将变量`retries`赋值给meta['retry_times'],即记录当前的重试次数，用于下次重试的判断
            retryreq.meta['retry_times'] = retries
            # 设置不要过滤，因为 scrapy 本身会对相同的 request 对象进行过滤
            retryreq.dont_filter = True
            # 优先级调整，如果priority_adjust 为正，那重试优先级变高，为负则重试优先级变低，若想不改变重试优先级，设为0即可，默认为-1
            retryreq.priority = request.priority + self.priority_adjust
            # 如果该状态的原因是属于异常，则获取这个异常的名字
            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
            # 返回 重试的 request 对象,即将 request 重新放回调度队列里等待被调度
            return retryreq
        else:
            stats.inc_value('retry/max_reached')
            logger.debug("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
