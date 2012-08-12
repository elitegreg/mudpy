from .object import Object

from mudpy.database import ObjectCache

import yaml


class Room(Object, yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Room'

    def __setstate__(self, newstate):
        super().__setstate__(newstate)
        self.tmp.cached_exits = dict()

    @property
    def short_description(self):
        return self.__short_description

    @property
    def long_description(self):
        return self.__long_description

    @property
    def exits(self):
        return self.__exits

    def get_exit(self, direction):
        # TODO we can get rid of lower() here if we enforce
        # the exit to be stored in lowercase elsewhere
        direction = direction.lower()

        try:
            return self.tmp.cached_exits[direction]
        except KeyError:
            pass

        exit = ObjectCache().get(self.__exits[direction])
        self.tmp.cached_exits[direction] = exit.weakref()
        return exit

