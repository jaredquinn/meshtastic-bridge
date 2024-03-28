
import importlib
import logging

logger = logging.getLogger(__name__)

class PluginManager:

    PLUGINS = {}

    def __init__(self):
        self.PLUGINS = {}

    def register_plugin(self, cls):
        (module, plugin) = cls.split('.')
        logger.info(f'Importing plugin.{module} and loading {plugin}')
        mod = importlib.import_module(f'plugin.{module}')
        plug = getattr(mod, plugin)
        self.PLUGINS[mod.__PLUGIN_NAME__] = plug()

    def call_function(self, function, interface, *args, **kwargs):
        for k, v in self.PLUGINS.items():
            fnc = getattr(v, function, None)
            if callable(fnc):
                fnc(*args, **kwargs, interface=interface)


__PLUGMGR__ = PluginManager()

def call_plugin_function(function, interface, *args, **kwargs):
    __PLUGMGR__.call_function(function, interface, *args, **kwargs)

def register_plugin(cls):
    __PLUGMGR__.register_plugin(cls)



