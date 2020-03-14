import logging
from six.moves.urllib.parse import urljoin

from w3lib.url import safe_url_string

from scrapy.http import HtmlResponse
from scrapy.utils.response import get_meta_refresh
from scrapy.exceptions import IgnoreRequest, NotConfigured

logger = logging.getLogger(__name__)


class BaseRedirectMiddleware(object):
    # 重定向设置
    enabled_setting = 'REDIRECT_ENABLED'

    def __init__(self, settings):
        # 如果 settings 中，`REDIRECT_ENABLED`属性的bool判断类型为 False，则抛出 NotConfigured 异常，即相当于跳过重定向中间件
        # 默认 REDIRECT_ENABLED = True
        if not settings.getbool(self.enabled_setting):
            raise NotConfigured
        # 获取获取重定向最大次数，默认 REDIRECT_MAX_TIMES = 20  # uses Firefox default setting
        self.max_redirect_times = settings.getint('REDIRECT_MAX_TIMES')
        # 获取重定向优先级调整，默认 REDIRECT_PRIORITY_ADJUST = +2
        self.priority_adjust = settings.getint('REDIRECT_PRIORITY_ADJUST')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def _redirect(self, redirected, request, spider, reason):
        # 如果 meta 存在键 `redirect_ttl`，则将其键值赋值给 ttl；如果不存在，则设置默认值为 self.max_redirect_times,然后将默认值赋值给 ttl
        ttl = request.meta.setdefault('redirect_ttl', self.max_redirect_times)
        # 获取当前重定向次数
        redirects = request.meta.get('redirect_times', 0) + 1

        # 如果 ttl的bool类型判断不为False 且当前重定向次数小于最大重定向次数
        if ttl and redirects <= self.max_redirect_times:
            # 将当前重定向次数赋值给meta里的键`redirect_times`
            redirected.meta['redirect_times'] = redirects
            # 相当于redirect_ttl自减1
            redirected.meta['redirect_ttl'] = ttl - 1
            # 获取重定向的 url
            redirected.meta['redirect_urls'] = request.meta.get('redirect_urls', []) + \
                                               [request.url]
            # 获取重定向的原因
            redirected.meta['redirect_reasons'] = request.meta.get('redirect_reasons', []) + \
                                                  [reason]
            # 设置不去重
            redirected.dont_filter = request.dont_filter
            # 调整优先级
            redirected.priority = request.priority + self.priority_adjust
            logger.debug("Redirecting (%(reason)s) to %(redirected)s from %(request)s",
                         {'reason': reason, 'redirected': redirected, 'request': request},
                         extra={'spider': spider})
            return redirected
        else:
            logger.debug("Discarding %(request)s: max redirections reached",
                         {'request': request}, extra={'spider': spider})
            # 抛出异常
            raise IgnoreRequest("max redirections reached")

    def _redirect_request_using_get(self, request, redirect_url):
        # 更换请求信息，从这里可以看出，可以通过 request.replace 来替换请求参数
        redirected = request.replace(url=redirect_url, method='GET', body='')
        # 删除请求头中的 `Content-Type`
        redirected.headers.pop('Content-Type', None)
        # 删除请求头中的 `Content-Length`
        redirected.headers.pop('Content-Length', None)
        return redirected


class RedirectMiddleware(BaseRedirectMiddleware):
    """
    Handle redirection of requests based on response status
    and meta-refresh html tag.
    """

    def process_response(self, request, response, spider):
        # 如果 meta 中有键 `dont_redirect`，且bool类型判断为 True，则返回 response，那么直接进入其他优先级更低中间件的 `process_response()`方法
        # 所以该作用和上面 `REDIRECT_ENABLED=False`效果一样，都可以看作是不使用重试中间件
        if (request.meta.get('dont_redirect', False) or
                # 状态码在 spider 的属性变量`handle_httpstatus_list`（如果存在该属性）之中
                response.status in getattr(spider, 'handle_httpstatus_list', []) or
                # 状态码在 meta 的键`handle_httpstatus_list`（如果存在该键）之中
                response.status in request.meta.get('handle_httpstatus_list', []) or
                # meta 存在键 `handle_httpstatus_all`
                request.meta.get('handle_httpstatus_all', False)):
            # 如果上面有一个为 True，则返回 response
            return response

        # 重定向的状态码
        allowed_status = (301, 302, 303, 307, 308)
        # 如果 response.headers 没有键 `Location` 或者 response的状态码不在上面定义的状态码中，返回response
        if 'Location' not in response.headers or response.status not in allowed_status:
            return response
        # 获取 response.headers的键 `location`,并进行处理
        location = safe_url_string(response.headers['location'])
        # 拼接重定向链接，但为什么用 request.url 来拼接？
        redirected_url = urljoin(request.url, location)
        # 如果是 301,307或308状态码，又或者请求方式是 'HEAD'
        if response.status in (301, 307, 308) or request.method == 'HEAD':
            # 将替换参数后的 request 对象从新赋值给 redirected
            redirected = request.replace(url=redirected_url)
            # 返回重新构建的request 对象，即重新放回调度队列
            return self._redirect(redirected, request, spider, response.status)

        # 更换请求信息,其中包括，设置url，请求方法改为 'GET'，删掉请求头中的 `Content-Type` 和 `Content-Length`
        redirected = self._redirect_request_using_get(request, redirected_url)
        # 返回重新构建的request 对象，即重新放回调度队列
        return self._redirect(redirected, request, spider, response.status)


class MetaRefreshMiddleware(BaseRedirectMiddleware):
    enabled_setting = 'METAREFRESH_ENABLED'

    def __init__(self, settings):
        super(MetaRefreshMiddleware, self).__init__(settings)
        self._ignore_tags = settings.getlist('METAREFRESH_IGNORE_TAGS')
        self._maxdelay = settings.getint('REDIRECT_MAX_METAREFRESH_DELAY',
                                         settings.getint('METAREFRESH_MAXDELAY'))

    def process_response(self, request, response, spider):
        if request.meta.get('dont_redirect', False) or request.method == 'HEAD' or \
                not isinstance(response, HtmlResponse):
            return response

        interval, url = get_meta_refresh(response,
                                         ignore_tags=self._ignore_tags)
        if url and interval < self._maxdelay:
            redirected = self._redirect_request_using_get(request, url)
            return self._redirect(redirected, request, spider, 'meta refresh')

        return response
