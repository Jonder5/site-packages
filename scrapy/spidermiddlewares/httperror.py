"""
HttpError Spider Middleware

See documentation in docs/topics/spider-middleware.rst
"""
import logging

from scrapy.exceptions import IgnoreRequest

logger = logging.getLogger(__name__)


class HttpError(IgnoreRequest):
    """A non-200 response was filtered"""

    def __init__(self, response, *args, **kwargs):
        self.response = response
        super(HttpError, self).__init__(*args, **kwargs)


class HttpErrorMiddleware(object):
    """
    该 Spider Middleware 主要是处理 HttpError，如果均不满足以下几个条件，就会抛出异常
    1. 状态码不在 200 到 300之间
    2. settins中该 HTTPERROR_ALLOW_ALL 不为 True，且 meta 中 没有键 `handle_httpstatus_all`
    3. 状态码不在 handle_httpstatus_list(list) 中， 该值可以通过 settings 的 `HTTPERROR_ALLOWED_CODES`属性 设置，或通过 spider的 属性变量 `handle_httpstatus_list` 设置，
        还可以通过 meta 定义键 `handle_httpstatus_all`
    """

    @classmethod
    # 获取 settings
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        # 从 settins 获取 `HTTPERROR_ALLOW_ALL` 变量
        self.handle_httpstatus_all = settings.getbool('HTTPERROR_ALLOW_ALL')
        # 从 settins 获取 `HTTPERROR_ALLOWED_CODES` 变量
        self.handle_httpstatus_list = settings.getlist('HTTPERROR_ALLOWED_CODES')

    def process_spider_input(self, response, spider):
        # 如果状态码这 200 到 300之间，则 return None，这表示scrapy会继续调用更低优先级的`spider middleware`来处理该response
        if 200 <= response.status < 300:  # common case
            return
        # 获取元数据
        meta = response.meta
        # 如果在 meta 中加入 `handle_httpstatus_all` 字段，则继续调用更低优先级的`spider middleware`来处理该response
        if 'handle_httpstatus_all' in meta:
            return
        # 如果在 meta 中加入 `handle_httpstatus_list`，则表示
        if 'handle_httpstatus_list' in meta:
            allowed_statuses = meta['handle_httpstatus_list']
        elif self.handle_httpstatus_all:
            return
        else:
            # 获取 spider 对象的 `handle_httpstatus_list` 的属性变量，如果不存在，默认为 settings 中设置的 `HTTPERROR_ALLOWED_CODES`
            allowed_statuses = getattr(spider, 'handle_httpstatus_list', self.handle_httpstatus_list)
        # 如果返回的 response 状态码在 allowed_statuses中，则继续调用更低优先级的`spider middleware`来处理该response
        if response.status in allowed_statuses:
            return
        # 如果该状态码在上面均未被处理到，则抛出 HttpError 异常
        raise HttpError(response, 'Ignoring non-200 response')

    def process_spider_exception(self, response, exception, spider):
        """主要作用是捕获上面抛出的 HttpError 异常"""
        # 如果该异常是 HttpError
        if isinstance(exception, HttpError):
            spider.crawler.stats.inc_value('httperror/response_ignored_count')
            spider.crawler.stats.inc_value(
                'httperror/response_ignored_status_count/%s' % response.status
            )
            logger.info(
                "Ignoring response %(response)r: HTTP status code is not handled or not allowed",
                {'response': response}, extra={'spider': spider},
            )
            return []
