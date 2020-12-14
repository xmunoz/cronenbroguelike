import copy
import logging
import random

from engine import dice
from engine.event import Event as _Event
from engine.globals import G
from engine.room import Room as _Room
from engine import say


# TODO: Devise a way to load rooms (and maybe events?) from a config file.
# TODO: Create "locations" within each room to find items in, for enemies to
# hang out in, etc.
# TODO: Allow multiple themes.
cathedral_pews = _Room.create(
    "You are in the pews of a maddening cathedral. The benches stretch on "
    "all sides and seem to creep up the walls. A murmuring sound suggests "
    "either wind or the prayers of an unseen petitioner.",
    theme="cathedral",
)
cathedral_catacombs = _Room.create(
    "You descend slick stairs into catacombs. Time-smooth placards adorn "
    "niches. The thick air smells of stone and moisture.",
    theme="cathedral",
)
cathedral_library = _Room.create(
    "A crumbling library. Tomes of thick vellum stand open on tables. The "
    "chairs are askew. Distant laughter can be heard.",
    theme="cathedral",
)
cathedral_office = _Room.create(
    "A desk is strewn with sheaves of paper. Little of sense is written there.",
    theme="cathedral",
)


class _BoilerHeatEvent(_Event):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._counter = 1

    def execute(self):
        if self._counter % 3 == 0:
            say.insayne("The heat is too much for you.")
            G.player.health.heal_or_harm(-1 * dice.roll("1d2"))
        self._counter += 1


class _BoilerRoom(_Room):
    def on_enter(self):
        super().on_enter()
        self._event = _BoilerHeatEvent()
        G.add_event(self._event, "post")

    def on_exit(self):
        super().on_exit()
        self._event.kill()


cathedral_boiler = _BoilerRoom.create(
    "A boiler sits in the center of this room. Its grate glows red. The air is "
    "intolerably hot.",
    theme="cathedral",
)


class _SongInHeadEvent(_Event):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._counter = 2

    def execute(self):
        say.insayne("🎵 MMMMMMMMBOP ba duba dop ba du dop DING DONG 🎵")
        self._counter -= 1
        if self._counter <= 0:
            self.kill()


class _BelfryEvent(_Event):

    _TURNS_TO_CHIME = 24

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._counter = -1

    def execute(self):
        self._counter += 1
        if self.room is not G.player.current_room:
            return
        if self._counter % self._TURNS_TO_CHIME == 0:
            say.insayne(
                "Suddenly, the bells begin to chime in simultaneity, if not "
                "exactly unison. From the chaos can be discerned a discordant "
                "melody. It is a blasphemous all-bells rendition of Hanson's "
                "'MMMBop.' As the final incomprehensible peal subsides, you "
                "realize the song is stuck in your head, threatening the "
                "sinews of your very sanity."
            )
            G.player.insanity.modify(15)
            G.add_event(_SongInHeadEvent(), "pre")


class _BelfryRoom(_Room):
    def on_enter(self):
        super().on_enter()
        self._event = _BelfryEvent()
        self._event.room = self
        G.add_event(self._event, "post")

    def on_exit(self):
        super().on_exit()


cathedral_belfry = _BelfryRoom.create(
    "A disquieting array of bells hangs from the ceiling here. The clappers "
    "swing low, nearly grazing the top of your head. An unseen motive force "
    "sweeps through the bells at random, causing them to chime.",
    theme="cathedral",
)


blank = _Room.create(
    "A featureless room. The air tastes stale here. The walls and floor are sallow."
)
sitting_room = _Room.create(
    "A gloomy expanse filled with furniture. You feel you are perhaps "
    "outdoors, though you see no sky or stars."
)


iron_womb = _Room.create(
    "You are squatting in a humid, low-ceilinged room made of rusted iron.",
    theme="biopunk",
)


class _AcidDropEvent(_Event):
    def execute(self):
        if dice.roll("1d100") > 90:
            say.insayne("A drop of acid falls on your head.")
            G.player.health.heal_or_harm(-1 * dice.roll("1d2"))


class _AcidRoom(_Room):
    def on_enter(self):
        super().on_enter()
        self._event = _AcidDropEvent()
        G.add_event(self._event, "post")

    def on_exit(self):
        super().on_exit()
        logging.debug(f"Killing event {self._event}.")
        self._event.kill()


acid_room = _AcidRoom.create(
    "You are in a large chamber. Its center is dominated by a reeking, acidic "
    "sump. The walls around are like gristle. On the ceiling, an aperture "
    "occasionally drips pale liquid into the fetid pool.",
    theme="behemoth",
)


# TODO: Attach events to the global queue, rather than to individual rooms.
# TODO: Poll for events after each command.
# TODO: Many behemoth rooms should induce insanity ...
# TODO: How to tie events to a specific room, though?
class _IntestineRoomEvent(_Event):
    def execute(self):
        # TODO: This kind of thing could be handled with a description generator.
        say.insayne(
            "You are in a dark tube. The walls and floor quiver at your touch, "
            "and you realize this is the intestine of a vast behemoth."
        )
        G.player.insanity.modify(10)
        # TODO: change to self.room.description
        G.player.current_room.description = (
            "The walls and floor of the intestine room shudder at your step."
        )
        self._will_execute = False


class _IntestineRoom(_Room):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entered = False

    def on_enter(self):
        super().on_enter()
        if not self._entered:
            G.add_event(_IntestineRoomEvent(), "post")
            self._entered = True


intestine_room = _IntestineRoom.create("", theme="behemoth")
rib_room = _Room.create(
    "You are standing on a slick, wet floor. The walls are a ribcage palisade. "
    "The room expands and contracts rhythmically.",
    theme="behemoth",
)


def _rooms_for_theme(theme=None):
    if theme is None:
        return _Room.ALL_ROOMS
    return _Room.THEME_TO_ROOMS[theme] + _Room.THEME_TO_ROOMS[_Room.DEFAULT_THEME]


def all_rooms(theme=None):
    # TODO: Don't do this via copies. Maybe use getter functions. Maybe just
    # use inheritance.
    return copy.deepcopy(_rooms_for_theme(theme))


def get_room(theme=None):
    return random.choice(all_rooms(theme))
