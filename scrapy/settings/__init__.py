import six
import json
import copy
import collections
from importlib import import_module
from pprint import pformat

from scrapy.settings import default_settings

if six.PY2:
    MutableMapping = collections.MutableMapping
else:
    MutableMapping = collections.abc.MutableMapping

# Scrapy设置的启用和填充可以由不同的机制来执行，并且每种机制都有不一样的优先级。值越低表示优先级越低
SETTINGS_PRIORITIES = {
    'default': 0,  # 默认的全局Settings（最低优先级），即 scrapy 自身的 default_settings.py文件
    'command': 10,  # 每个命令的默认Settings
    'project': 20,  # 项目的Settings，即创建 scrapy 项目时创建的 settings.py文件
    'spider': 30,  # 每个Spider的Settings，即在Spider中设置的类属性：custom_settings
    'cmdline': 40,  # 命令行选项（最高优先级）
}


def get_settings_priority(priority):
    """
    Small helper function that looks up a given string priority in the
    :attr:`~scrapy.settings.SETTINGS_PRIORITIES` dictionary and returns its
    numerical value, or directly returns a given numerical priority.
    """
    if isinstance(priority, six.string_types):
        return SETTINGS_PRIORITIES[priority]
    else:
        return priority


class SettingsAttribute(object):
    """Class for storing data related to settings attributes.

    This class is intended for internal usage, you should try Settings class
    for settings configuration, not this one.
    """

    def __init__(self, value, priority):
        self.value = value
        if isinstance(self.value, BaseSettings):
            self.priority = max(self.value.maxpriority(), priority)
        else:
            self.priority = priority

    def set(self, value, priority):
        """Sets vaule if priority is higher or equal than current priority."""
        if priority >= self.priority:
            if isinstance(self.value, BaseSettings):
                value = BaseSettings(value, priority=priority)
            self.value = value
            self.priority = priority

    def __str__(self):
        return "<SettingsAttribute value={self.value!r} " \
               "priority={self.priority}>".format(self=self)

    __repr__ = __str__


class BaseSettings(MutableMapping):
    """
    Instances of this class behave like dictionaries, but store priorities
    along with their ``(key, value)`` pairs, and can be frozen (i.e. marked
    immutable).

    Key-value entries can be passed on initialization with the ``values``
    argument, and they would take the ``priority`` level (unless ``values`` is
    already an instance of :class:`~scrapy.settings.BaseSettings`, in which
    case the existing priority levels will be kept).  If the ``priority``
    argument is a string, the priority name will be looked up in
    :attr:`~scrapy.settings.SETTINGS_PRIORITIES`. Otherwise, a specific integer
    should be provided.

    Once the object is created, new settings can be loaded or updated with the
    :meth:`~scrapy.settings.BaseSettings.set` method, and can be accessed with
    the square bracket notation of dictionaries, or with the
    :meth:`~scrapy.settings.BaseSettings.get` method of the instance and its
    value conversion variants. When requesting a stored key, the value with the
    highest priority will be retrieved.
    """

    def __init__(self, values=None, priority='project'):
        self.frozen = False
        self.attributes = {}
        self.update(values, priority)

    # 使用类似字典方式访问成员必须实现该方法
    def __getitem__(self, opt_name):
        # 默认转化为 self.__contains__(opt_name)的方法调用
        if opt_name not in self:
            return None
        return self.attributes[opt_name].value

    # 使用 in 可以判断元素是否在序列中时，如果是对象则调用对象中的 __contains__方法
    def __contains__(self, name):
        return name in self.attributes

    def get(self, name, default=None):
        # 获取一个设置中的常量值
        """
        Get a setting value without affecting its original type.

        :param name: the setting name
        :type name: string

        :param default: the value to return if no setting is found
        :type default: any
        """
        # 类似字典方式访问成员时，需要实现 __getitem__ 方法， self[name]会默认转化为 self.__getitem__(name)的方法调用
        return self[name] if self[name] is not None else default

    def getbool(self, name, default=False):
        # 将某项配置的值以布尔值形式返回。比如，1 和 '1'，True 都返回``True``， 而 0，'0'，False 和 None 返回 False。
        """
        Get a setting value as a boolean.

        ``1``, ``'1'``, `True`` and ``'True'`` return ``True``,
        while ``0``, ``'0'``, ``False``, ``'False'`` and ``None`` return ``False``.

        For example, settings populated through environment variables set to
        ``'0'`` will return ``False`` when using this method.

        :param name: the setting name
        :type name: string

        :param default: the value to return if no setting is found
        :type default: any
        """
        got = self.get(name, default)
        try:
            return bool(int(got))
        except ValueError:
            if got in ("True", "true"):
                return True
            if got in ("False", "false"):
                return False
            raise ValueError("Supported values for boolean settings "
                             "are 0/1, True/False, '0'/'1', "
                             "'True'/'False' and 'true'/'false'")

    def getint(self, name, default=0):
        # 将某项配置的值以整数形式返回
        """
        Get a setting value as an int.

        :param name: the setting name
        :type name: string

        :param default: the value to return if no setting is found
        :type default: any
        """
        return int(self.get(name, default))

    def getfloat(self, name, default=0.0):
        # 将某项配置的值以浮点数形式返回
        """
        Get a setting value as a float.

        :param name: the setting name
        :type name: string

        :param default: the value to return if no setting is found
        :type default: any
        """
        return float(self.get(name, default))

    def getlist(self, name, default=None):
        # 将某项配置的值以列表形式返回。如果配置值本来就是list则原样返回。 如果是字符串，则返回被 ”,” 分割后的列表。
        """
        Get a setting value as a list. If the setting original type is a list, a
        copy of it will be returned. If it's a string it will be split by ",".

        For example, settings populated through environment variables set to
        ``'one,two'`` will return a list ['one', 'two'] when using this method.

        :param name: the setting name
        :type name: string

        :param default: the value to return if no setting is found
        :type default: any
        """
        value = self.get(name, default or [])
        if isinstance(value, six.string_types):
            value = value.split(',')
        return list(value)

    def getdict(self, name, default=None):
        # 获取一个设置值作为字典。如果设置原始类型为字典，则返回其副本。如果它是一个字符串，
        # 它将作为JSON字典进行计算。如果它是一个 BaseSettings 实例本身，它将被转换为一个字典，
        # 其中包含所有当前设置值，这些值将由返回 get() 以及丢失有关优先级和可变性的所有信息。
        """
        Get a setting value as a dictionary. If the setting original type is a
        dictionary, a copy of it will be returned. If it is a string it will be
        evaluated as a JSON dictionary. In the case that it is a
        :class:`~scrapy.settings.BaseSettings` instance itself, it will be
        converted to a dictionary, containing all its current settings values
        as they would be returned by :meth:`~scrapy.settings.BaseSettings.get`,
        and losing all information about priority and mutability.

        :param name: the setting name
        :type name: string

        :param default: the value to return if no setting is found
        :type default: any
        """
        value = self.get(name, default or {})
        if isinstance(value, six.string_types):
            value = json.loads(value)
        return dict(value)

    def getwithbase(self, name):
        # 获取类似字典的设置及其 _BASE 对应的。
        """Get a composition of a dictionary-like setting and its `_BASE`
        counterpart.

        :param name: name of the dictionary-like setting
        :type name: string
        """
        compbs = BaseSettings()
        compbs.update(self[name + '_BASE'])
        compbs.update(self[name])
        return compbs

    def getpriority(self, name):
        # 返回设置的当前数字优先级值，或 None 如果给定 name 不存在。
        """
        Return the current numerical priority value of a setting, or ``None`` if
        the given ``name`` does not exist.

        :param name: the setting name
        :type name: string
        """
        if name not in self:
            return None
        return self.attributes[name].priority

    def maxpriority(self):
        # 返回所有设置中存在的最高优先级的数值，或返回 default 从 SETTINGS_PRIORITIES 如果没有存储设置。
        """
        Return the numerical value of the highest priority present throughout
        all settings, or the numerical value for ``default`` from
        :attr:`~scrapy.settings.SETTINGS_PRIORITIES` if there are no settings
        stored.
        """
        if len(self) > 0:
            return max(self.getpriority(name) for name in self)
        else:
            return get_settings_priority('default')

    def __setitem__(self, name, value):
        self.set(name, value)

    def set(self, name, value, priority='project'):
        """
        Store a key/value attribute with a given priority.

        Settings should be populated *before* configuring the Crawler object
        (through the :meth:`~scrapy.crawler.Crawler.configure` method),
        otherwise they won't have any effect.

        :param name: the setting name
        :type name: string

        :param value: the value to associate with the setting
        :type value: any

        :param priority: the priority of the setting. Should be a key of
            :attr:`~scrapy.settings.SETTINGS_PRIORITIES` or an integer
        :type priority: string or int
        """
        self._assert_mutability()
        priority = get_settings_priority(priority)
        if name not in self:
            if isinstance(value, SettingsAttribute):
                self.attributes[name] = value
            else:
                self.attributes[name] = SettingsAttribute(value, priority)
        else:
            self.attributes[name].set(value, priority)

    def setdict(self, values, priority='project'):
        self.update(values, priority)

    def setmodule(self, module, priority='project'):
        """
        Store settings from a module with a given priority.

        This is a helper function that calls
        :meth:`~scrapy.settings.BaseSettings.set` for every globally declared
        uppercase variable of ``module`` with the provided ``priority``.

        :param module: the module or the path of the module
        :type module: module object or string

        :param priority: the priority of the settings. Should be a key of
            :attr:`~scrapy.settings.SETTINGS_PRIORITIES` or an integer
        :type priority: string or int
        """
        self._assert_mutability()
        if isinstance(module, six.string_types):
            module = import_module(module)
        for key in dir(module):
            if key.isupper():
                self.set(key, getattr(module, key), priority)

    def update(self, values, priority='project'):
        """
        Store key/value pairs with a given priority.

        This is a helper function that calls
        :meth:`~scrapy.settings.BaseSettings.set` for every item of ``values``
        with the provided ``priority``.

        If ``values`` is a string, it is assumed to be JSON-encoded and parsed
        into a dict with ``json.loads()`` first. If it is a
        :class:`~scrapy.settings.BaseSettings` instance, the per-key priorities
        will be used and the ``priority`` parameter ignored. This allows
        inserting/updating settings with different priorities with a single
        command.

        :param values: the settings names and values
        :type values: dict or string or :class:`~scrapy.settings.BaseSettings`

        :param priority: the priority of the settings. Should be a key of
            :attr:`~scrapy.settings.SETTINGS_PRIORITIES` or an integer
        :type priority: string or int
        """
        self._assert_mutability()
        if isinstance(values, six.string_types):
            values = json.loads(values)
        if values is not None:
            if isinstance(values, BaseSettings):
                for name, value in six.iteritems(values):
                    self.set(name, value, values.getpriority(name))
            else:
                for name, value in six.iteritems(values):
                    self.set(name, value, priority)

    def delete(self, name, priority='project'):
        self._assert_mutability()
        priority = get_settings_priority(priority)
        if priority >= self.getpriority(name):
            del self.attributes[name]

    def __delitem__(self, name):
        self._assert_mutability()
        del self.attributes[name]

    def _assert_mutability(self):
        if self.frozen:
            raise TypeError("Trying to modify an immutable Settings object")

    def copy(self):
        """
        Make a deep copy of current settings.

        This method returns a new instance of the :class:`Settings` class,
        populated with the same values and their priorities.

        Modifications to the new object won't be reflected on the original
        settings.
        """
        # 对于当前设置做一次深拷贝
        return copy.deepcopy(self)

    def freeze(self):
        # 禁用对当前设置的进一步更改。
        # 调用此方法后，设置的当前状态将变为不可变。尝试通过 set() 方法及其变体是不可能的，将被警告。
        """
        Disable further changes to the current settings.

        After calling this method, the present state of the settings will become
        immutable. Trying to change values through the :meth:`~set` method and
        its variants won't be possible and will be alerted.
        """
        # 设置一个标识，当 self.frozen 为 True 时，不允许改变设置属性
        self.frozen = True

    def frozencopy(self):
        """
        Return an immutable copy of the current settings.

        Alias for a :meth:`~freeze` call in the object returned by :meth:`copy`.
        """
        copy = self.copy()
        copy.freeze()
        return copy

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def _to_dict(self):
        return {k: (v._to_dict() if isinstance(v, BaseSettings) else v)
                for k, v in six.iteritems(self)}

    def copy_to_dict(self):
        """
        Make a copy of current settings and convert to a dict.

        This method returns a new dict populated with the same values
        and their priorities as the current settings.

        Modifications to the returned dict won't be reflected on the original
        settings.

        This method can be useful for example for printing settings
        in Scrapy shell.
        """
        # 复制当前设置并转换为dict。
        settings = self.copy()
        return settings._to_dict()

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(repr(self))
        else:
            p.text(pformat(self.copy_to_dict()))


class _DictProxy(MutableMapping):

    def __init__(self, settings, priority):
        self.o = {}
        self.settings = settings
        self.priority = priority

    def __len__(self):
        return len(self.o)

    def __getitem__(self, k):
        return self.o[k]

    def __setitem__(self, k, v):
        self.settings.set(k, v, priority=self.priority)
        self.o[k] = v

    def __delitem__(self, k):
        del self.o[k]

    def __iter__(self, k, v):
        return iter(self.o)


class Settings(BaseSettings):
    """
    This object stores Scrapy settings for the configuration of internal
    components, and can be used for any further customization.

    It is a direct subclass and supports all methods of
    :class:`~scrapy.settings.BaseSettings`. Additionally, after instantiation
    of this class, the new object will have the global default settings
    described on :ref:`topics-settings-ref` already populated.
    """

    def __init__(self, values=None, priority='project'):
        # Do not pass kwarg values here. We don't want to promote user-defined
        # dicts, and we want to update, not replace, default dicts with the
        # values given by the user
        # 调用父类构造初始化
        super(Settings, self).__init__()
        # 把 default_settings.py 的所有配置 set 到 settings 实例中，优先级为 'default'
        self.setmodule(default_settings, 'default')
        # Promote default dictionaries to BaseSettings instances for per-key
        # priorities
        # 把 attributes 属性也 set 到 settings 实例中
        # 程序加载默认配置文件 default_settings.py 中的所有配置项设置到 Settings 中，且这个配置是有优先级的。
        for name, val in six.iteritems(self):
            if isinstance(val, dict):
                self.set(name, BaseSettings(val, 'default'), 'default')
        self.update(values, priority)


def iter_default_settings():
    # 将默认设置作为一组类型为元组 (name, value)的迭代器返回
    """Return the default settings as an iterator of (name, value) tuples"""
    # 遍历 default_settings 中所有的属性
    for name in dir(default_settings):
        # 如果属性变量全部为大写（如果在 settings 设置的属性变量，必须全部为大写，如果变量中有小写，则该属性设置无效）
        if name.isupper():
            # 返回属性名称及属性值
            yield name, getattr(default_settings, name)


def overridden_settings(settings):
    # 返回被覆盖的设置
    """Return a dict of the settings that have been overridden"""
    for name, defvalue in iter_default_settings():
        value = settings[name]
        # 如果默认的属性值不为字典类型，且覆盖的属性值不等于默认的属性值，则返回覆盖后的值，否则不做处理
        if not isinstance(defvalue, dict) and value != defvalue:
            yield name, value
