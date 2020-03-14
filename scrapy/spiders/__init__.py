"""
Base class for Scrapy spiders

See documentation in docs/topics/spiders.rst
"""
import logging
import warnings

from scrapy import signals
from scrapy.http import Request
from scrapy.utils.trackref import object_ref
from scrapy.utils.url import url_is_from_spider
from scrapy.exceptions import ScrapyDeprecationWarning
from scrapy.utils.deprecate import method_is_overridden


class Spider(object_ref):
    # scrapy Spider 的基类，用户自己写的 Spider 必须继承这个方法
    """Base class for scrapy spiders. All spiders must inherit from this
    class.
    """
    # 项目的唯一名称，用于区别不同的Spider
    name = None
    # 每个Spider的Settings，会覆盖项目全局的设置，在scrapy的设置启动中优先级排第二，仅次于命令行选项
    custom_settings = None

    # 可以看出，当我们 scrapy crawler xxxSpider，这里的 xxxSpider 其实就是传递给变量 `name` 的值
    def __init__(self, name=None, **kwargs):
        if name is not None:
            self.name = name
        # 继承Spider类的爬虫，需要赋值一个 name（且该名称必须是唯一的），否则会抛出异常
        elif not getattr(self, 'name', None):
            raise ValueError("%s must have a name" % type(self).__name__)
        # __dict__是一个字典，键为属性名，值为属性值，如果在实例Spider类的时候，传入关键字参数，则会更新到对象属性中
        self.__dict__.update(kwargs)
        # 如果类中不函数属性 "start_urls"，则默认创建一个，并赋值为一个空列表
        if not hasattr(self, 'start_urls'):
            self.start_urls = []

    # 把方法变成属性，即直接 self.logger.xxx 调用,如 self.logger.info('msg')
    @property
    def logger(self):
        # 用爬虫名称作为名称创建一个日志器
        logger = logging.getLogger(self.name)
        # 返回一个log适配器对象
        return logging.LoggerAdapter(logger, {'spider': self})

    def log(self, message, level=logging.DEBUG, **kw):
        """Log the given message at the given log level

        This helper wraps a log call to the logger within the spider, but you
        can use it directly (e.g. Spider.logger.info('msg')) or use any other
        Python logger too.
        """
        # 设置 log 日志级别
        self.logger.log(level, message, **kw)

    # 类方法
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # cls代表这个类，因此，以下是用给定的参数创建了一个cls类的实例spider。参数会经过 __init__ 方法，因为实例需要初始化。
        spider = cls(*args, **kwargs)
        # 设置spider实例的crawler属性，将 crawler 传递给实例，使新实例有crawler属性和settings参数
        spider._set_crawler(crawler)
        return spider

    def _set_crawler(self, crawler):
        # 设置 crawler 属性
        self.crawler = crawler
        # 设置 settings 属性
        self.settings = crawler.settings
        crawler.signals.connect(self.close, signals.spider_closed)

    def start_requests(self):
        cls = self.__class__
        if method_is_overridden(cls, Spider, 'make_requests_from_url'):
            warnings.warn(
                "Spider.make_requests_from_url method is deprecated; it "
                "won't be called in future Scrapy releases. Please "
                "override Spider.start_requests method instead (see %s.%s)." % (
                    cls.__module__, cls.__name__
                ),
            )
            # 遍历 start_urls 里的 url
            for url in self.start_urls:
                yield self.make_requests_from_url(url)
        else:
            for url in self.start_urls:
                yield Request(url, dont_filter=True)

    def make_requests_from_url(self, url):
        """ This method is deprecated. """
        return Request(url, dont_filter=True)

    def parse(self, response):
        # 子类必须重写parse方法，否则会抛出 NotImplementedError 异常
        # 下载器完成下载后，会请返回的相应作为唯一的参数传递给这个函数，该方法负责解析返回的响应、提取数据或者进一步生成要处理的请求
        raise NotImplementedError('{}.parse callback is not defined'.format(self.__class__.__name__))

    @classmethod
    # 更新设置
    def update_settings(cls, settings):
        settings.setdict(cls.custom_settings or {}, priority='spider')

    @classmethod
    def handles_request(cls, request):
        return url_is_from_spider(request.url, cls)

    @staticmethod
    def close(spider, reason):
        """Spider关闭时调用此方法。"""
        closed = getattr(spider, 'closed', None)
        if callable(closed):
            return closed(reason)

    def __str__(self):
        return "<%s %r at 0x%0x>" % (type(self).__name__, self.name, id(self))

    __repr__ = __str__


# Top-level imports
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.spiders.feed import XMLFeedSpider, CSVFeedSpider
from scrapy.spiders.sitemap import SitemapSpider
