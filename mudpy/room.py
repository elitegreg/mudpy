from .object import Object

from mudpy.database import ObjectCache
from mudpy.gameproperty import add_gameproperty

import yaml


class Room(Object, yaml.YAMLObject):
    __slots__ = tuple()

    yaml_loader = yaml.SafeLoader
    yaml_tag = '!Room'

    def __setstate__(self, newstate):
        super().__setstate__(newstate)
        self.cached_exits = dict()
        if not self.exits:
            self.exits = dict()

    def get_exit(self, direction):
        # TODO we can get rid of lower() here if we enforce
        # the exit to be stored in lowercase elsewhere
        direction = direction.lower()

        try:
            return self.cached_exits[direction]
        except KeyError:
            pass

        exit = ObjectCache().get(self.exits[direction])
        self.cached_exits[direction] = exit.weakref()
        return exit


add_gameproperty(Room, 'short_description', readonly=True)
add_gameproperty(Room, 'long_description', readonly=True)
add_gameproperty(Room, 'exits')
add_gameproperty(Room, 'cached_exits', tmp=True)
