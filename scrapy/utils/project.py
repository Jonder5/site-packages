import os
from six.moves import cPickle as pickle
import warnings

from importlib import import_module
from os.path import join, dirname, abspath, isabs, exists

from scrapy.utils.conf import closest_scrapy_cfg, get_config, init_env
from scrapy.settings import Settings
from scrapy.exceptions import NotConfigured
from scrapy.exceptions import ScrapyDeprecationWarning

ENVVAR = 'SCRAPY_SETTINGS_MODULE'
DATADIR_CFG_SECTION = 'datadir'


def inside_project():
    """scrapy 命令有的是依赖项目运行的，有的命令则是全局的，不依赖项目的。这里主要通过就近查找 scrapy.cfg 文件来确定是否在项目环境中。"""
    # 检查此环境变量是否存在，在 get_project_settings() 方法中已设置
    scrapy_module = os.environ.get('SCRAPY_SETTINGS_MODULE')
    # 如果该环境变量存在
    if scrapy_module is not None:
        try:
            import_module(scrapy_module)
        except ImportError as exc:
            warnings.warn("Cannot import scrapy settings module %s: %s" % (scrapy_module, exc))
        else:
            return True
    # 如果环境变量没有，就近查找 scrapy.cfg ，找得到就认为是在项目环境中
    return bool(closest_scrapy_cfg())


def project_data_dir(project='default'):
    """Return the current project data dir, creating it if it doesn't exist"""
    if not inside_project():
        raise NotConfigured("Not inside a project")
    cfg = get_config()
    if cfg.has_option(DATADIR_CFG_SECTION, project):
        d = cfg.get(DATADIR_CFG_SECTION, project)
    else:
        scrapy_cfg = closest_scrapy_cfg()
        if not scrapy_cfg:
            raise NotConfigured("Unable to find scrapy.cfg file to infer project data dir")
        d = abspath(join(dirname(scrapy_cfg), '.scrapy'))
    if not exists(d):
        os.makedirs(d)
    return d


def data_path(path, createdir=False):
    """
    Return the given path joined with the .scrapy data directory.
    If given an absolute path, return it unmodified.
    """
    if not isabs(path):
        if inside_project():
            path = join(project_data_dir(), path)
        else:
            path = join('.scrapy', path)
    if createdir and not exists(path):
        os.makedirs(path)
    return path


def get_project_settings():
    """根据环境变量和 scrapy.cfg 初始化环境，最终生成一个 Settings 实例"""
    # 环境变量中是否有 SCRAPY_SETTINGS_MODULE 配置
    if ENVVAR not in os.environ:
        # 如果没有，获取环境变量 SCRAPY_PROJECT，如果该变量也没有，则赋值默认值 'default' 给 project 变量
        project = os.environ.get('SCRAPY_PROJECT', 'default')
        # 初始化环境变量，例如将最近的一个 'scrapy.cfg' 所在目录添加到系统环境变量，声明并赋值环境变量 SCRAPY_SETTINGS_MODULE
        init_env(project)

    # 加载默认配置文件 default_settings.py，生成 settings 实例
    settings = Settings()
    # projects的settings所在路径，相对路径
    settings_module_path = os.environ.get(ENVVAR)
    if settings_module_path:
        # 设置 projects 中的 属性
        settings.setmodule(settings_module_path, priority='project')

    # XXX: remove this hack
    # 如果环境变量中有其他scrapy相关配置则覆盖
    pickled_settings = os.environ.get("SCRAPY_PICKLED_SETTINGS_TO_OVERRIDE")
    if pickled_settings:
        warnings.warn("Use of environment variable "
                      "'SCRAPY_PICKLED_SETTINGS_TO_OVERRIDE' "
                      "is deprecated.", ScrapyDeprecationWarning)
        settings.setdict(pickle.loads(pickled_settings), priority='project')

    # XXX: deprecate and remove this functionality
    env_overrides = {k[7:]: v for k, v in os.environ.items() if
                     k.startswith('SCRAPY_')}
    if env_overrides:
        settings.setdict(env_overrides, priority='project')

    return settings
