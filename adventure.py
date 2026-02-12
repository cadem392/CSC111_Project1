"""CSC111 Project 1: Text Adventure Game - Game Manager

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from event_logger import Event, EventList
from game_entities import Item, Location


# Note: You may add helper functions, classes, etc. below as needed

DEFAULT_MIN_SCORE = 60
DEFAULT_MAX_TURNS = 67
REQUIRED_ITEMS = {"lucky mug", "usb drive", "laptop charger"}
MENU_COMMANDS = {"look", "inventory", "score", "log", "submit early", "quit"}
ITEM_COMMAND_PREFIXES = ("take ", "drop ", "inspect ")


@dataclass
class PlayerState:
    """Mutable player progress grouped into one structure.

    This keeps AdventureGame's instance-attribute count low while preserving
    the expected public AdventureGame API.
    """
    inventory: list[Item] = field(default_factory=list)
    score: int = 0
    turn: int = 0
    returned: set[str] = field(default_factory=set)


class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - current_location_id: the id number of the player's current location
        - ongoing: whether the current game session is still active

    Representation Invariants:
        - self.current_location_id in self._locations
    """

    # Private Instance Attributes (do NOT remove these two attributes):
    #   - _locations: a mapping from location id to Location object.
    #                 This represents all the locations in the game.
    #   - _items: a list of Item objects, representing all items in the game.

    _locations: dict[int, Location]
    _items: list[Item]
    _valid_items: set[str]
    _state: PlayerState
    current_location_id: int
    ongoing: bool

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """Initialize a game from a data file and starting location id.

        Preconditions:
            - game_data_file is the filename of a valid game data JSON file
        """
        self._locations, self._items, self._valid_items = self._load_game_data(game_data_file)
        self.current_location_id = initial_location_id
        self.ongoing = True
        self._state = PlayerState()

    def __getattr__(self, name: str) -> int:
        """Provide backwards-compatible access for legacy constant attribute names."""
        if name == "MIN_SCORE":
            return DEFAULT_MIN_SCORE
        if name == "MAX_TURNS":
            return DEFAULT_MAX_TURNS
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item], set[str]]:
        """Load locations/items from a JSON file and return game data objects."""
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)

        locations = {}
        for loc_data in data['locations']:
            location_obj = Location(
                loc_data['id'],
                loc_data['name'],
                loc_data['brief_description'],
                loc_data['long_description'],
                loc_data['available_commands'],
                loc_data['items'],
                loc_data['restrictions'] if 'restrictions' in loc_data else {},
                loc_data['rewards'] if 'rewards' in loc_data else {}
            )
            locations[loc_data['id']] = location_obj

        items = []
        valid_items = set()
        for item_data in data['items']:
            item_obj = Item(
                item_data['name'],
                item_data['description'],
                item_data['hint'],
                item_data['completion_text'],
                item_data['start_position'],
                item_data['target_position'],
                item_data['target_points']
            )
            items.append(item_obj)
            valid_items.add(item_data['name'])

        return locations, items, valid_items

    def location_dict(self) -> dict[int, Location]:
        """Return a dictionary of all available location IDs."""
        return self._locations.copy()

    @property
    def inventory(self) -> list[Item]:
        """Return the player's current inventory."""
        return self._state.inventory

    @inventory.setter
    def inventory(self, value: list[Item]) -> None:
        """Replace the player's inventory."""
        self._state.inventory = value

    @property
    def score(self) -> int:
        """Return the player's current score."""
        return self._state.score

    @score.setter
    def score(self, value: int) -> None:
        """Set the player's score."""
        self._state.score = value

    @property
    def turn(self) -> int:
        """Return the player's current move count."""
        return self._state.turn

    @turn.setter
    def turn(self, value: int) -> None:
        """Set the player's current move count."""
        self._state.turn = value

    @property
    def returned(self) -> set[str]:
        """Return names of items that have been successfully returned."""
        return self._state.returned

    @returned.setter
    def returned(self, value: set[str]) -> None:
        """Replace returned item names."""
        self._state.returned = value

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return location object for loc_id, or current location when loc_id is None."""
        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]

    def get_item(self, item_name: str) -> Optional[Item]:
        """Return the item object with the given name, or None if not found."""
        for item in self._items:
            if item.name == item_name:
                return item
        return None

    def pick_up(self, item_name: str) -> bool:
        """Pick up item_name from the current location."""
        if item_name not in self._valid_items:
            return False

        curr_item = self.get_item(item_name)
        if curr_item is None:
            return False

        curr_location = self.get_location()
        if item_name not in curr_location.items:
            return False

        self.inventory.append(curr_item)
        curr_location.items.remove(item_name)
        return True

    def drop(self, item_name: str) -> bool:
        """Drop item_name into the current location."""
        if item_name not in self._valid_items:
            return False

        curr_item = self.get_item(item_name)
        if curr_item is None or curr_item not in self.inventory:
            return False

        curr_location = self.get_location()
        self.inventory.remove(curr_item)
        curr_location.items.append(item_name)
        return True

    def inspect(self, item_name: str) -> None:
        """Print a hint for item_name if it is in the player's inventory."""
        if item_name not in self._valid_items:
            return

        curr_item = self.get_item(item_name)
        if curr_item is not None and curr_item in self.inventory:
            print(curr_item.hint)
            target_location = self.get_location(curr_item.target_position).name
            print(f"..... It needs to go to {target_location}")

    def check_quest(self, item_name: str) -> bool:
        """Check whether dropped item_name has reached its target location."""
        curr_item = self.get_item(item_name)
        curr_location = self.get_location()

        if curr_item is None:
            return False

        if curr_item.target_position != curr_location.id_num or item_name not in curr_location.items:
            return False

        print(curr_item.completion_text)
        self.returned.add(item_name)
        self.score += curr_item.target_points
        print("Your score is now " + str(self.score))
        curr_location.items.remove(item_name)
        return True

    def submit_early(self) -> None:
        """End the current game session early."""
        self.ongoing = False

    def reset(self) -> None:
        """Reset all items and player progress to a fresh game state."""
        self._locations, self._items, self._valid_items = self._load_game_data("game_data.json")
        self.current_location_id = 1
        self.ongoing = True
        self._state = PlayerState()


def _ask_play_again() -> bool:
    """Prompt for replay and return whether the player selected yes."""
    again = ""
    while again not in {"y", "n"}:
        again = input("Would you like to play again? (y/n) ").strip().lower()
    return again == "y"


def win() -> bool:
    """Display win messaging and return whether the player wants replay."""
    print("YOU WIN!!!!")
    print("You submitted your assignment on time!")
    return _ask_play_again()


def lose() -> bool:
    """Display lose messaging and return whether the player wants replay."""
    print("YOU LOSE!!!!")
    print("You submitted your assignment late!")
    return _ask_play_again()


def _did_player_win(game: AdventureGame) -> bool:
    """Return whether the player has met all win requirements."""
    return game.score >= game.MIN_SCORE and REQUIRED_ITEMS.issubset(game.returned)


def _show_location(location: Location) -> None:
    """Print either the long or brief location description."""
    if location.visited:
        print(location.brief_description)
    else:
        location.visited = True
        print(location.long_description)


def _show_available_actions(location: Location, turns_left: int) -> None:
    """Print base commands, movement commands, and remaining turns."""
    print("What to do? Choose from: look, inventory, score, log, quit, take <item>, drop <item>, inspect <item>")
    print("At this location, you can also:")
    for action in location.available_commands:
        print("-", action)
    print(f"You have {turns_left} turns left....")


def _is_item_command(choice: str) -> bool:
    """Return whether choice is an item command with a non-empty item name."""
    return any(choice.startswith(prefix) and len(choice) > len(prefix) for prefix in ITEM_COMMAND_PREFIXES)


def _is_valid_choice(choice: str, location: Location) -> bool:
    """Return whether choice can be processed at this location."""
    if choice in location.available_commands or choice in MENU_COMMANDS:
        return True
    return _is_item_command(choice)


def _prompt_choice(location: Location, game: AdventureGame) -> str:
    """Prompt user until a valid command is entered."""
    _show_available_actions(location, game.MAX_TURNS - game.turn)
    choice = input("\nEnter action: ").lower().strip()
    while not _is_valid_choice(choice, location):
        print("That was an invalid option; try again.")
        choice = input("\nEnter action: ").lower().strip()
    return choice


def _parse_item_command(choice: str) -> Optional[tuple[str, str]]:
    """Return (verb, item_name) from a take/drop/inspect command, if valid."""
    parts = choice.split(maxsplit=1)
    if len(parts) != 2:
        return None

    verb, item_name = parts[0], parts[1].strip()
    if verb not in {"take", "drop", "inspect"} or item_name == "":
        return None

    return verb, item_name


def _show_location_items(game: AdventureGame, location: Location) -> None:
    """Print all items currently available in location."""
    if location.items:
        print("Items In " + location.name)
        for item_name in location.items:
            item = game.get_item(item_name)
            print(item if item is not None else item_name)
    else:
        print("No Items In " + location.name)


def _show_inventory(game: AdventureGame) -> None:
    """Print all items currently held by the player."""
    if game.inventory:
        for item in game.inventory:
            print(item)
    else:
        print("No Items In Your Inventory")


def _handle_item_command(game: AdventureGame, choice: str) -> None:
    """Process take/drop/inspect commands."""
    parsed = _parse_item_command(choice)
    if parsed is None:
        print("That was an invalid option; try again.")
        return

    verb, item_name = parsed
    if verb == "take":
        if game.pick_up(item_name):
            print("You picked up " + item_name)
        else:
            print("No such item " + item_name + " here.")
    elif verb == "drop":
        if game.drop(item_name):
            print("You dropped " + item_name)
            game.check_quest(item_name)
        else:
            print("No such item " + item_name + " in inventory.")
    else:
        game.inspect(item_name)


def _handle_non_movement_command(
    game: AdventureGame,
    game_log: EventList,
    location: Location,
    choice: str
) -> None:
    """Process a command that does not move the player."""
    if choice == "log":
        game_log.display_events()
    elif choice == "look":
        print(location.long_description)
        _show_location_items(game, location)
    elif choice == "inventory":
        _show_inventory(game)
    elif choice == "score":
        print(game.score)
    elif choice == "quit":
        game.ongoing = False
    elif choice == "submit early":
        game.submit_early()
    else:
        _handle_item_command(game, choice)


def _apply_movement(game: AdventureGame, location: Location, choice: str) -> None:
    """Apply a movement command and update turn count."""
    game.current_location_id = location.available_commands[choice]
    game.turn += 1
    if game.turn >= game.MAX_TURNS:
        game.ongoing = False


def _resolve_turn(
    game: AdventureGame,
    game_log: EventList,
    location: Location
) -> tuple[Optional[str], bool]:
    """Process commands until move/submit/quit and return (move_command, quit_requested)."""
    choice = _prompt_choice(location, game)

    while game.ongoing:
        print("========")
        print("You decided to:", choice)

        if choice in location.available_commands:
            _apply_movement(game, location, choice)
            return choice, False

        _handle_non_movement_command(game, game_log, location, choice)
        if not game.ongoing:
            return None, choice == "quit"

        choice = _prompt_choice(location, game)

    return None, False


def _run_single_game() -> bool:
    """Run one game session and return whether the player wants replay."""
    game_log = EventList()  # Required baseline feature
    game = AdventureGame('game_data.json', 1)
    previous_choice = None

    while game.ongoing:
        location = game.get_location()
        game_log.add_event(Event(location.id_num, location.brief_description), previous_choice)

        _show_location(location)
        previous_choice, quit_requested = _resolve_turn(game, game_log, location)
        if quit_requested:
            return False

    if _did_player_win(game):
        return win()
    return lose()


def run() -> None:
    """Run the game and support replay loops."""
    play_again = True
    while play_again:
        play_again = _run_single_game()


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    import python_ta

    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })

    run()
