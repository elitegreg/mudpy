# Game properties should be registered at import time

class GameProperty:
    __slots__ = ('__propname', '__default', '__readonly')

    def __init__(self, propname, default=None, readonly=False, tmp=False):
        if not tmp:
            self.__propname = '_GameProperty_' + propname
        else:
            self.__propname = '_TempGameProperty_' + propname
        self.__default  = default
        self.__readonly = readonly

    def __get__(self, obj, type=None):
        return getattr(obj, self.__propname, self.__default)

    def __set__(self, obj, value):
        if self.__readonly:
            raise AttributeError("{} is readonly".format(self.__propname))
        obj._Object__propdict[self.__propname] = value

    def __delete__(self, obj):
        if self.__readonly:
            raise AttributeError("{} is readonly".format(self.__propname))
        delattr(obj, self.__propname)


def add_gameproperty(klass, propname, default=None, readonly=False, tmp=False):
    setattr(klass, propname, GameProperty(propname, default, readonly, tmp))

