
import importlib

class PluginManager:

    PLUGINS = {}

    def __init__(self):
        self.PLUGINS = {}

    def load(self, name, module, plugin):
        print('Importing')
        mod = importlib.import_module(module)
        print('Loading plugin')
        plug = getattr(mod, plugin)
        print('Initializing')
        self.PLUGINS[name] = plug()

    def call_function(self, function, interface, *args, **kwargs):
        for k, v in self.PLUGINS.items():
            fnc = getattr(v, function, None)
            if callable(fnc):
                fnc(*args, **kwargs, interface=interface)


P = PluginManager()

def call_plugin_function(function, interface, *args, **kwargs):
    P.call_function(function, interface, *args, **kwargs)

def register_plugin(name, module, plugin):
    P.load(name, module, plugin)



