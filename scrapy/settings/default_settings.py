"""
This module contains the default values for all settings used by Scrapy.

For more information about these settings you can read the settings
documentation in docs/topics/settings.rst

Scrapy developers, if you add a setting here remember to:

* add it in alphabetical order
* group similar settings without leaving blank lines
* add its documentation to the available settings documentation
  (docs/topics/settings.rst)

"""

import sys
from importlib import import_module
from os.path import join, abspath, dirname

import six

AJAXCRAWL_ENABLED = False

AUTOTHROTTLE_ENABLED = False
AUTOTHROTTLE_DEBUG = False
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_START_DELAY = 5.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

BOT_NAME = 'scrapybot'

CLOSESPIDER_TIMEOUT = 0
CLOSESPIDER_PAGECOUNT = 0
CLOSESPIDER_ITEMCOUNT = 0
CLOSESPIDER_ERRORCOUNT = 0

COMMANDS_MODULE = ''

COMPRESSION_ENABLED = True

# 在Item的处理器中并发处理的最大Item数量。
CONCURRENT_ITEMS = 100

# Scrapy下载程序将执行的最大并发（即同时）请求数，即 Downloader 同时处理Request的最大数量。
CONCURRENT_REQUESTS = 16
# 将对任何单个域名执行的最大并发（即同时）请求数。用来控制单个域名的并发量。
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 将对任何单个IP执行的最大并发（即同时）请求数。如果非零， CONCURRENT_REQUESTS_PER_DOMAIN 设置被忽略，而是使用此设置。换句话说，并发限制将应用于每个IP，而不是每个域。
# 此设置还影响 DOWNLOAD_DELAY 和 AutoThrottle 扩展 如果 CONCURRENT_REQUESTS_PER_IP 是非零的，下载延迟是每个IP强制执行的，而不是每个域。
CONCURRENT_REQUESTS_PER_IP = 0

# 是否启用cookie中间件。如果禁用，则不会向Web服务器发送cookie。
COOKIES_ENABLED = True
# 如果启用，Scrapy将记录请求中发送的所有cookie（即 Cookie 标题）和响应中收到的所有cookie（即 Set-Cookie 标题）。
COOKIES_DEBUG = False

DEFAULT_ITEM_CLASS = 'scrapy.item.Item'

# Scrapy的Request中默认的请求头，将会在 DefaultHeadersMiddleware 中被填充。
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

# 作用域：scrapy.spidermiddlewares.depth.DepthMiddleware
# 对于任一网站，允许爬取的最大深度。如果值为0，则不会有任何限制。
DEPTH_LIMIT = 0
DEPTH_STATS_VERBOSE = False
DEPTH_PRIORITY = 0

# 是否启用 DNS 内存缓存
DNSCACHE_ENABLED = True
# DNS内存缓存大小
DNSCACHE_SIZE = 10000

# 处理DNS查询的超时（秒）
DNS_TIMEOUT = 60

# 下载者从同一网站下载连续页面之前应等待的时间（以秒计）。这可以用来限制爬行速度，以避免对服务器造成太大的冲击。
DOWNLOAD_DELAY = 0

# 项目中启用的请求下载器处理程序
DOWNLOAD_HANDLERS = {}
# 默认项目中启用的请求下载器处理程序
DOWNLOAD_HANDLERS_BASE = {
    'data': 'scrapy.core.downloader.handlers.datauri.DataURIDownloadHandler',
    'file': 'scrapy.core.downloader.handlers.file.FileDownloadHandler',
    'http': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
    'https': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
    's3': 'scrapy.core.downloader.handlers.s3.S3DownloadHandler',
    'ftp': 'scrapy.core.downloader.handlers.ftp.FTPDownloadHandler',
}

# 下载程序在超时前等待的时间（以秒计）。
DOWNLOAD_TIMEOUT = 180      # 3mins

# 下载程序将下载的最大响应大小（字节）。
DOWNLOAD_MAXSIZE = 1024*1024*1024   # 1024m
# 下载程序将开始警告的响应大小（字节）。
DOWNLOAD_WARNSIZE = 32*1024*1024    # 32m

DOWNLOAD_FAIL_ON_DATALOSS = True

# 下载器
DOWNLOADER = 'scrapy.core.downloader.Downloader'

DOWNLOADER_HTTPCLIENTFACTORY = 'scrapy.core.downloader.webclient.ScrapyHTTPClientFactory'
DOWNLOADER_CLIENTCONTEXTFACTORY = 'scrapy.core.downloader.contextfactory.ScrapyClientContextFactory'
DOWNLOADER_CLIENT_TLS_CIPHERS = 'DEFAULT'
DOWNLOADER_CLIENT_TLS_METHOD = 'TLS' # Use highest TLS/SSL protocol version supported by the platform,
                                     # also allowing negotiation
DOWNLOADER_CLIENT_TLS_VERBOSE_LOGGING = False

# 下载中间件
DOWNLOADER_MIDDLEWARES = {}

# 默认下载中间件
DOWNLOADER_MIDDLEWARES_BASE = {
    # Engine side
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 500,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.ajaxcrawl.AjaxCrawlMiddleware': 560,
    'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 580,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 590,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,
    # Downloader side
}

DOWNLOADER_STATS = True

DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'

EDITOR = 'vi'
if sys.platform == 'win32':
    EDITOR = '%s -m idlelib.idle'

# 拓展
EXTENSIONS = {}

# 默认拓展
EXTENSIONS_BASE = {
    'scrapy.extensions.corestats.CoreStats': 0,
    'scrapy.extensions.telnet.TelnetConsole': 0,
    'scrapy.extensions.memusage.MemoryUsage': 0,
    'scrapy.extensions.memdebug.MemoryDebugger': 0,
    'scrapy.extensions.closespider.CloseSpider': 0,
    'scrapy.extensions.feedexport.FeedExporter': 0,
    'scrapy.extensions.logstats.LogStats': 0,
    'scrapy.extensions.spiderstate.SpiderState': 0,
    'scrapy.extensions.throttle.AutoThrottle': 0,
}

FEED_TEMPDIR = None
FEED_URI = None
FEED_URI_PARAMS = None  # a function to extend uri arguments
FEED_FORMAT = 'jsonlines'
FEED_STORE_EMPTY = False
FEED_EXPORT_ENCODING = None
FEED_EXPORT_FIELDS = None
FEED_STORAGES = {}
FEED_STORAGES_BASE = {
    '': 'scrapy.extensions.feedexport.FileFeedStorage',
    'file': 'scrapy.extensions.feedexport.FileFeedStorage',
    'stdout': 'scrapy.extensions.feedexport.StdoutFeedStorage',
    's3': 'scrapy.extensions.feedexport.S3FeedStorage',
    'ftp': 'scrapy.extensions.feedexport.FTPFeedStorage',
}
FEED_EXPORTERS = {}
FEED_EXPORTERS_BASE = {
    'json': 'scrapy.exporters.JsonItemExporter',
    'jsonlines': 'scrapy.exporters.JsonLinesItemExporter',
    'jl': 'scrapy.exporters.JsonLinesItemExporter',
    'csv': 'scrapy.exporters.CsvItemExporter',
    'xml': 'scrapy.exporters.XmlItemExporter',
    'marshal': 'scrapy.exporters.MarshalItemExporter',
    'pickle': 'scrapy.exporters.PickleItemExporter',
}
FEED_EXPORT_INDENT = 0

FEED_STORAGE_FTP_ACTIVE = False
FEED_STORAGE_S3_ACL = ''

FILES_STORE_S3_ACL = 'private'
FILES_STORE_GCS_ACL = ''

FTP_USER = 'anonymous'
FTP_PASSWORD = 'guest'
FTP_PASSIVE_MODE = True

HTTPCACHE_ENABLED = False
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_MISSING = False
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_ALWAYS_STORE = False
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_IGNORE_SCHEMES = ['file']
HTTPCACHE_IGNORE_RESPONSE_CACHE_CONTROLS = []
HTTPCACHE_DBM_MODULE = 'anydbm' if six.PY2 else 'dbm'
HTTPCACHE_POLICY = 'scrapy.extensions.httpcache.DummyPolicy'
HTTPCACHE_GZIP = False

HTTPPROXY_ENABLED = True
HTTPPROXY_AUTH_ENCODING = 'latin-1'

IMAGES_STORE_S3_ACL = 'private'
IMAGES_STORE_GCS_ACL = ''

ITEM_PROCESSOR = 'scrapy.pipelines.ItemPipelineManager'

ITEM_PIPELINES = {}
ITEM_PIPELINES_BASE = {}

# 是否开启日志
LOG_ENABLED = True
# 用于记录的编码。
LOG_ENCODING = 'utf-8'
LOG_FORMATTER = 'scrapy.logformatter.LogFormatter'
# 日志格式
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
# 用于格式化日期/时间的字符串
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
# 如果True，进程的所有标准输出（和错误）将被重定向到日志
LOG_STDOUT = False
# 日志级别
LOG_LEVEL = 'DEBUG'
# 日志输出文件，如果设置了这个，那么日志就会输出到对应的日志文件，而不会在终端打印出来
LOG_FILE = None
# 如果True，日志将仅包含根路径。如果设置为False 则它显示负责日志输出的组件
LOG_SHORT_NAMES = False

SCHEDULER_DEBUG = False

LOGSTATS_INTERVAL = 60.0

MAIL_HOST = 'localhost'
MAIL_PORT = 25
MAIL_FROM = 'scrapy@localhost'
MAIL_PASS = None
MAIL_USER = None

# 是否开启内存调试。
MEMDEBUG_ENABLED = False        # enable memory debugging
# 当开启内存调试的时候，可以在这个列表中设置邮箱地址，那么内存调试的报告将会发送到邮箱中。
# 如 MEMDEBUG_NOTIFY = ['user@example.com']
MEMDEBUG_NOTIFY = []            # send memory debugging report by mail at engine shutdown

MEMUSAGE_CHECK_INTERVAL_SECONDS = 60.0
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 0
MEMUSAGE_NOTIFY_MAIL = []
MEMUSAGE_WARNING_MB = 0

METAREFRESH_ENABLED = True
METAREFRESH_IGNORE_TAGS = ['script', 'noscript']
METAREFRESH_MAXDELAY = 100

NEWSPIDER_MODULE = ''

RANDOMIZE_DOWNLOAD_DELAY = True

REACTOR_THREADPOOL_MAXSIZE = 10

# 是否启用重定向 middleware。
REDIRECT_ENABLED = True
# 请求的最大重定向次数。重定向的次数超过这个值后，相应将被原样返回。
REDIRECT_MAX_TIMES = 20  # uses Firefox default setting

# 用来调整重定向的请求的优先级,作用域：scrapy.downloadermiddlewares.redirect.RedirectMiddleware
# 值为正数表示重定向的请求优先级更高，值为负数表示原始请求优先级更高。
# 本次请求优先级 = 上次请求优先级 + REDIRECT_PRIORITY_ADJUST
REDIRECT_PRIORITY_ADJUST = +2

REFERER_ENABLED = True
REFERRER_POLICY = 'scrapy.spidermiddlewares.referer.DefaultReferrerPolicy'

# 是否启用重试middleware。
RETRY_ENABLED = True
# 重试次数，最大请求次数 = 1 + RETRY_TIMES
RETRY_TIMES = 2  # initial response + 2 retries = 3 requests
# 需要重试的状态码
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
# 调整重试优先级，作用域：scrapy.downloadermiddlewares.retry.RetryMiddleware
# 本次请求优先级 = 上次请求优先级 + RETRY_PRIORITY_ADJUST，值为正数则为提高重试请求的优先级，负数相反。如果想重试时，不改变优先级，设置为0即可
RETRY_PRIORITY_ADJUST = -1

ROBOTSTXT_OBEY = False
ROBOTSTXT_PARSER = 'scrapy.robotstxt.ProtegoRobotParser'
ROBOTSTXT_USER_AGENT = None

# 用于爬取的调度程序
SCHEDULER = 'scrapy.core.scheduler.Scheduler'
# 基于磁盘的任务队列（先进后出）
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleLifoDiskQueue'
# 基于内存的任务队列（先进后出）
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.LifoMemoryQueue'
# 优先级队列
SCHEDULER_PRIORITY_QUEUE = 'scrapy.pqueues.ScrapyPriorityQueue'

# 将用于加载爬虫程序的类，它必须实现 SpiderLoader API。
SPIDER_LOADER_CLASS = 'scrapy.spiderloader.SpiderLoader'
SPIDER_LOADER_WARN_ONLY = False

# Spider 爬虫中间件
SPIDER_MIDDLEWARES = {}

# Scrapy中默认启用的爬虫中间件的字典及其顺序
SPIDER_MIDDLEWARES_BASE = {
    # Engine side
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 500,
    'scrapy.spidermiddlewares.referer.RefererMiddleware': 700,
    'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware': 800,
    'scrapy.spidermiddlewares.depth.DepthMiddleware': 900,
    # Spider side
}

# Scrapy将寻找爬虫的模块列表。
SPIDER_MODULES = []

STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'
STATS_DUMP = True

STATSMAILER_RCPTS = []

TEMPLATES_DIR = abspath(join(dirname(__file__), '..', 'templates'))

URLLENGTH_LIMIT = 2083

# 检索时使用的默认用户代理，除非被覆盖。
USER_AGENT = 'Scrapy/%s (+https://scrapy.org)' % import_module('scrapy').__version__

TELNETCONSOLE_ENABLED = 1
# 用于telnet控制台的端口范围。如果设置为None或0，则使用动态分配的端口。有关详细信息，请参阅 telnet控制台。
TELNETCONSOLE_PORT = [6023, 6073]
TELNETCONSOLE_HOST = '127.0.0.1'
TELNETCONSOLE_USERNAME = 'scrapy'
TELNETCONSOLE_PASSWORD = None

SPIDER_CONTRACTS = {}
SPIDER_CONTRACTS_BASE = {
    'scrapy.contracts.default.UrlContract': 1,
    'scrapy.contracts.default.CallbackKeywordArgumentsContract': 1,
    'scrapy.contracts.default.ReturnsContract': 2,
    'scrapy.contracts.default.ScrapesContract': 3,
}
