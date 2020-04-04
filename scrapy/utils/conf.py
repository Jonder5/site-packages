import os
import sys
import numbers
from operator import itemgetter

import six
if six.PY2:
    from ConfigParser import SafeConfigParser as ConfigParser
else:
    from configparser import ConfigParser

from scrapy.settings import BaseSettings
from scrapy.utils.deprecate import update_classpath
from scrapy.utils.python import without_none_values


def build_component_list(compdict, custom=None, convert=update_classpath):
    """Compose a component list from a { class: order } dictionary."""

    def _check_components(complist):
        if len({convert(c) for c in complist}) != len(complist):
            raise ValueError('Some paths in {!r} convert to the same object, '
                             'please update your settings'.format(complist))

    def _map_keys(compdict):
        if isinstance(compdict, BaseSettings):
            compbs = BaseSettings()
            for k, v in six.iteritems(compdict):
                prio = compdict.getpriority(k)
                if compbs.getpriority(convert(k)) == prio:
                    raise ValueError('Some paths in {!r} convert to the same '
                                     'object, please update your settings'
                                     ''.format(list(compdict.keys())))
                else:
                    compbs.set(convert(k), v, priority=prio)
            return compbs
        else:
            _check_components(compdict)
            return {convert(k): v for k, v in six.iteritems(compdict)}

    def _validate_values(compdict):
        """Fail if a value in the components dict is not a real number or None."""
        for name, value in six.iteritems(compdict):
            if value is not None and not isinstance(value, numbers.Real):
                raise ValueError('Invalid value {} for component {}, please provide ' \
                                 'a real number or None instead'.format(value, name))

    # BEGIN Backward compatibility for old (base, custom) call signature
    if isinstance(custom, (list, tuple)):
        _check_components(custom)
        return type(custom)(convert(c) for c in custom)

    if custom is not None:
        compdict.update(custom)
    # END Backward compatibility

    _validate_values(compdict)
    compdict = without_none_values(_map_keys(compdict))
    return [k for k, v in sorted(six.iteritems(compdict), key=itemgetter(1))]


def arglist_to_dict(arglist):
    """Convert a list of arguments like ['arg1=val1', 'arg2=val2', ...] to a
    dict
    """
    return dict(x.split('=', 1) for x in arglist)


def closest_scrapy_cfg(path='.', prevpath=None):
    # 利用递归函数，返回当前目录最近的一个 scrapy.cfg件所在路径
    # 即从当前目录开始往顶层目录查找，找到最顶层目录，找到便返回路径，找不到则返回 '' 字符串
    """Return the path to the closest scrapy.cfg file by traversing the current
    directory and its parents
    """
    # 此种情况下，是找到最顶层目录仍未找到 'scrapy.cfg' 文件
    if path == prevpath:
        return ''
    # 返回最近的scrapy.cfg path 变量的目录绝对路径
    path = os.path.abspath(path)
    # 将  path 变量的目录绝对路径 与 'scrapy.cfg' 组成一个路径
    cfgfile = os.path.join(path, 'scrapy.cfg')
    # 如果有存在，则返回这个路径
    if os.path.exists(cfgfile):
        return cfgfile
    # 否则继续往上一层路径找, os.path.dirname(path) 表示当前目录的上一层目录
    return closest_scrapy_cfg(os.path.dirname(path), path)


def init_env(project='default', set_syspath=True):
    """Initialize environment to use command-line tool from inside a project
    dir. This sets the Scrapy settings module and modifies the Python path to
    be able to locate the project module.
    """
    # 将 scrapy 配置文件以 ConfigParser 类的形式返回，即实例化 ConfigParser
    cfg = get_config()
    # 检查 scrapy 的 scrapy.cfg 文件中，[settings]下是否声明了 {{project}} 属性
    if cfg.has_option('settings', project):
        # 如果有，将其值赋值给系统环境变量 SCRAPY_SETTINGS_MODULE
        os.environ['SCRAPY_SETTINGS_MODULE'] = cfg.get('settings', project)
    # closest_scrapy_cfg() 返回当前目录最近的一个 scrapy.cfg件所在路径
    closest = closest_scrapy_cfg()
    if closest:
        # 如果存在该路径，则将该路径所在目录赋值给 projdir 变量
        projdir = os.path.dirname(closest)
        if set_syspath and projdir not in sys.path:
            # 将该目录添加到系统环境变量中
            # 对于模块和自己写的程序不在同一个目录下，可以把模块的路径通过sys.path.append(路径)添加到程序中
            sys.path.append(projdir)


def get_config(use_closest=True):
    """Get Scrapy config file as a ConfigParser"""
    # 将 scrapy 配置文件以 ConfigParser 类的形式返回
    sources = get_sources(use_closest)
    cfg = ConfigParser()
    cfg.read(sources)
    return cfg


def get_sources(use_closest=True):
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or \
        os.path.expanduser('~/.config')
    sources = ['/etc/scrapy.cfg', r'c:\scrapy\scrapy.cfg',
               xdg_config_home + '/scrapy.cfg',
               os.path.expanduser('~/.scrapy.cfg')]
    if use_closest:
        # closest_scrapy_cfg() 返回当前目录最近的一个 scrapy.cfg件所在路径，sources 列表添加该值为一个新的元素
        sources.append(closest_scrapy_cfg())
    return sources
