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

DEFAULT_MIN_SCORE = 60
DEFAULT_MAX_SCORE = 100
DEFAULT_MAX_TURNS = 67
UNLIMITED_TURNS = 10 ** 9
DEFAULT_START_LOCATION = 2
EXTENSION_BONUS_TURNS = 30
USB_EQUIVALENT_ITEMS = {"usb drive", "spare usb cable"}
REQUIRED_RETURN_ITEMS = {"lucky mug", "laptop charger"}
MENU_COMMANDS = {"look", "inventory", "score", "log", "submit early", "quit"}
ITEM_COMMAND_PREFIXES = ("take ", "drop ", "inspect ")


@dataclass
class SessionFlags:
    """Boolean gameplay flags grouped into one object."""
    unlimited_moves: bool = False
    score_locked: bool = False
    submitted_once: bool = False
    quit_requested: bool = False
    extension_granted: bool = False


@dataclass
class PlayerState:
    """Mutable player progress grouped into one structure."""
    inventory: list[Item] = field(default_factory=list)
    score: int = 0
    turn: int = 0
    max_turns: int = DEFAULT_MAX_TURNS
    flags: SessionFlags = field(default_factory=SessionFlags)
    rewards_claimed: set[str] = field(default_factory=set)
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
    #   - _state: structure containing all the player progress

    _locations: dict[int, Location]
    _items: list[Item]
    _state: PlayerState
    current_location_id: int
    ongoing: bool

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """Initialize a game from a data file and starting location id.

        Preconditions:
            - game_data_file is the filename of a valid game data JSON file
        """
        self._locations, self._items = self._load_game_data(game_data_file)
        self.current_location_id = initial_location_id
        self.ongoing = True
        self._state = PlayerState()

    def __getattr__(self, name: str) -> int:
        """Provide access for constant attribute names."""
        if name == "MIN_SCORE":
            return DEFAULT_MIN_SCORE
        if name == "MAX_SCORE":
            return DEFAULT_MAX_SCORE
        if name == "MAX_TURNS":
            return self._state.max_turns
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item]]:
        """Load locations/items from a JSON file and return game data objects."""
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)

        locations = {}
        for loc_data in data['locations']:
            location_obj = Location(
                loc_data['id'],
                {
                    'name': loc_data['name'],
                    'brief_description': loc_data['brief_description'],
                    'long_description': loc_data['long_description']
                },
                loc_data['available_commands'],
                loc_data['items'],
                loc_data['restrictions'] if 'restrictions' in loc_data else {},
                loc_data['rewards'] if 'rewards' in loc_data else {}
            )
            locations[loc_data['id']] = location_obj

        items = []
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
        return locations, items

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

    def _inventory_names(self) -> set[str]:
        """Return lowercase names of all items currently in inventory."""
        return {item.name.lower() for item in self.inventory}

    def _required_items(self, restrictions: str) -> set[str]:
        """Extract required item names from a location restriction payload."""
        if restrictions in ({}, None, ""):
            return set()

        if isinstance(restrictions, str):
            required = restrictions.strip().lower()
            return {required} if required else set()

        return set()

    def can_enter_location(self, location_id: int) -> tuple[bool, Optional[str]]:
        """Return whether the player can enter a location, with a failure message if blocked."""
        destination = self.get_location(location_id)
        required_items = self._required_items(destination.restrictions)
        if not required_items:
            return True, None

        missing = sorted(item for item in required_items if item not in self._inventory_names())
        if not missing:
            return True, None

        if len(missing) == 1:
            return False, f"You need {missing[0]} to enter {destination.description['name']}."
        return False, f"You need {', '.join(missing)} to enter {destination.description['name']}."

    def _merge_string_mapping(self, target: dict[str, str], source: dict[str, str] | None) -> None:
        """Merge string-to-string pairs from source into target, lower-casing keys/values."""
        if source is None:
            return

        for key, value in source.items():
            target[key.lower()] = value.lower()

    def _extract_item_rewards(self, rewards_data: dict[str, object] | None) -> dict[str, str]:
        """Extract item-trade rewards from a location reward payload."""
        rewards: dict[str, str] = {}
        if not isinstance(rewards_data, dict):
            return rewards

        self._merge_string_mapping(rewards, rewards_data.get("items"))
        nested = rewards_data.get("rewards")
        if isinstance(nested, dict):
            self._merge_string_mapping(rewards, nested.get("items"))

        return rewards

    def _extract_attribute_rewards(self, rewards_data: dict[str, object] | None) -> dict[str, str]:
        """Extract attribute-trigger rewards from a location reward payload."""
        rewards: dict[str, str] = {}
        if not isinstance(rewards_data, dict):
            return rewards

        self._merge_string_mapping(rewards, rewards_data.get("attributes"))
        nested = rewards_data.get("rewards")
        if isinstance(nested, dict):
            self._merge_string_mapping(rewards, nested.get("attributes"))

        return rewards

    def apply_location_rewards(self, trigger_item_name: str) -> list[str]:
        """Apply location-specific rewards from dropping an item.

        Return user-facing messages describing any reward that was applied.
        """
        location = self.get_location()
        trigger = trigger_item_name.lower()
        messages = []

        self._apply_item_reward(location.id_num, trigger, location.rewards, messages)

        attribute_rewards = self._extract_attribute_rewards(location.rewards)
        if trigger in attribute_rewards:
            reward_effect = attribute_rewards[trigger]
            candidate_trigger = trigger
            marker = f"attribute:{location.id_num}:{candidate_trigger}->{reward_effect}"
            if marker in self._state.rewards_claimed:
                return messages

            if reward_effect == "extra time granted":
                if not self._state.flags.extension_granted:
                    self._state.max_turns += EXTENSION_BONUS_TURNS
                    self._state.flags.extension_granted = True
                    messages.append(f"Extension approved: +{EXTENSION_BONUS_TURNS} moves.")
                else:
                    messages.append("Extension already approved.")
            else:
                messages.append(reward_effect)

            self._state.rewards_claimed.add(marker)

        return messages

    def _apply_item_reward(
        self,
        location_id: int,
        trigger: str,
        rewards_data: dict[str, object] | None,
        messages: list[str]
    ) -> None:
        """Apply one item-based reward for a trigger at a location, if configured."""
        item_rewards = self._extract_item_rewards(rewards_data)
        if trigger not in item_rewards:
            return

        granted_name = item_rewards[trigger]
        marker = f"item:{location_id}:{trigger}->{granted_name}"
        if marker in self._state.rewards_claimed:
            return

        granted_item = self.get_item(granted_name)
        if granted_item is not None:
            if granted_item not in self.inventory:
                self.inventory.append(granted_item)
                messages.append(f"You received {granted_name}.")
            else:
                messages.append(f"You already have {granted_name}.")

        self._state.rewards_claimed.add(marker)

    def pick_up(self, item_name: str) -> bool:
        """Pick up item_name from the current location."""
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
        curr_item = self.get_item(item_name)
        if curr_item is None or curr_item not in self.inventory:
            return False

        curr_location = self.get_location()
        self.inventory.remove(curr_item)
        curr_location.items.append(item_name)
        return True

    def inspect(self, item_name: str) -> None:
        """Print a hint for item_name if it is in the player's inventory."""
        curr_item = self.get_item(item_name)
        if curr_item is not None and curr_item in self.inventory:
            print(curr_item.hint)
            target_location = self.get_location(curr_item.target_position).description['name']
            print(f"..... It needs to go to {target_location}")

    def check_quest(self, item_name: str) -> bool:
        """Check whether dropped item_name has reached its target location."""
        curr_item = self.get_item(item_name)
        curr_location = self.get_location()

        if curr_item is None:
            return False

        if curr_item.target_position != curr_location.id_num or item_name not in curr_location.items:
            return False

        if item_name in self.returned:
            return False

        print(curr_item.completion_text)
        self.returned.add(item_name)

        if self._state.flags.score_locked:
            print("Score is locked after submission.")
            return True

        points_earned = curr_item.target_points

        # Allow spare USB cable to substitute for the USB drive scoring objective.
        if item_name == "spare usb cable" and "usb drive" not in self.returned:
            usb_drive = self.get_item("usb drive")
            if usb_drive is not None and usb_drive.target_points > curr_item.target_points:
                points_earned = usb_drive.target_points

        self.score += points_earned
        print("Your score is now " + str(self.score))
        return True

    def has_storage_solution(self) -> bool:
        """Return whether at least one USB-equivalent item has been returned."""
        return any(item_name in self.returned for item_name in USB_EQUIVALENT_ITEMS)

    def has_required_returns(self) -> bool:
        """Return whether all mandatory return-item win conditions are met."""
        return REQUIRED_RETURN_ITEMS.issubset(self.returned) and self.has_storage_solution()

    def missing_win_items(self) -> list[str]:
        """Return human-readable missing item conditions for win-state messaging."""
        missing = []
        for item_name in sorted(REQUIRED_RETURN_ITEMS):
            if item_name not in self.returned:
                missing.append(item_name)
        if not self.has_storage_solution():
            missing.append("usb drive or spare usb cable")
        return missing

    def submit_early(self) -> bool:
        """End the current game session early.

        Return whether submission was newly accepted.
        """
        if self._state.flags.submitted_once:
            return False
        self._state.flags.submitted_once = True
        self.ongoing = False
        return True

    def enable_unlimited_moves(self) -> None:
        """Enable effectively unlimited moves for post-win free exploration."""
        self._state.flags.unlimited_moves = True
        self._state.max_turns = UNLIMITED_TURNS
        if self.turn < 0:
            self.turn = 0

    def is_unlimited_moves(self) -> bool:
        """Return whether move usage is currently unlimited."""
        return self._state.flags.unlimited_moves

    def lock_score(self) -> None:
        """Prevent any future score changes."""
        self._state.flags.score_locked = True

    def can_submit_early(self) -> bool:
        """Return whether the player can still use submit-early."""
        return not self._state.flags.submitted_once

    def request_quit(self) -> None:
        """Mark the current session as an explicit quit action."""
        self._state.flags.quit_requested = True
        self.ongoing = False

    def is_quit_requested(self) -> bool:
        """Return whether the current session ended by explicit quit."""
        return self._state.flags.quit_requested

    def reset(self) -> None:
        """Reset all items and player progress to a fresh game state."""
        self._locations, self._items = self._load_game_data("game_data.json")
        self.current_location_id = DEFAULT_START_LOCATION
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
    if not game.is_unlimited_moves() and game.turn >= game.MAX_TURNS:
        return False
    return game.score >= game.MIN_SCORE and game.has_required_returns()


def _show_location(location: Location) -> None:
    """Print either the long or brief location description."""
    if location.visited:
        print(location.description['brief_description'])
    else:
        location.visited = True
        print(location.description['long_description'])


def _show_available_actions(location: Location, turns_left: int, menu_commands: set[str]) -> None:
    """Print base commands, movement commands, and remaining turns."""
    base_menu = sorted(menu_commands)
    print(f"What to do? Choose from: {', '.join(base_menu)}, take <item>, drop <item>, inspect <item>")
    print("At this location, you can also:")
    for action in location.available_commands:
        print("-", action)
    if turns_left >= UNLIMITED_TURNS:
        print("You have Unlimited turns left....")
    else:
        print(f"You have {turns_left} turns left....")


def _is_item_command(choice: str) -> bool:
    """Return whether choice is an item command with a non-empty item name."""
    return any(choice.startswith(prefix) and len(choice) > len(prefix) for prefix in ITEM_COMMAND_PREFIXES)


def _is_valid_choice(choice: str, location: Location, menu_commands: set[str]) -> bool:
    """Return whether choice can be processed at this location."""
    if choice in location.available_commands or choice in menu_commands:
        return True
    return _is_item_command(choice)


def _available_menu_commands(game: AdventureGame) -> set[str]:
    """Return currently valid non-movement menu commands."""
    if game.can_submit_early():
        return set(MENU_COMMANDS)
    return {command for command in MENU_COMMANDS if command != "submit early"}


def _prompt_choice(location: Location, game: AdventureGame) -> str:
    """Prompt user until a valid command is entered."""
    menu_commands = _available_menu_commands(game)
    if game.is_unlimited_moves():
        _show_available_actions(location, UNLIMITED_TURNS, menu_commands)
    else:
        _show_available_actions(location, game.MAX_TURNS - game.turn, menu_commands)
    choice = input("\nEnter action: ").lower().strip()
    while not _is_valid_choice(choice, location, menu_commands):
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
        print("Items In " + location.description['name'])
        for item_name in location.items:
            item = game.get_item(item_name)
            print(item if item is not None else item_name)
    else:
        print("No Items In " + location.description['name'])


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
            for reward_message in game.apply_location_rewards(item_name):
                print(reward_message)
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
        print(location.description['long_description'])
        _show_location_items(game, location)
    elif choice == "inventory":
        _show_inventory(game)
    elif choice == "score":
        print(f"{game.score} / {game.MAX_SCORE}")
    elif choice == "quit":
        game.request_quit()
    elif choice == "submit early":
        submitted = game.submit_early()
        if not submitted:
            print("Submission is already finalized.")
    else:
        _handle_item_command(game, choice)


def _apply_movement(game: AdventureGame, location: Location, choice: str) -> bool:
    """Apply a movement command and update turn count.

    Return whether movement succeeded (it can fail if entry restrictions are not met).
    """
    next_location_id = location.available_commands[choice]
    can_enter, reason = game.can_enter_location(next_location_id)
    if not can_enter:
        if reason is not None:
            print(reason)
        return False

    game.current_location_id = next_location_id
    if not game.is_unlimited_moves():
        game.turn += 1
        if game.turn >= game.MAX_TURNS:
            game.ongoing = False
    return True


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
            moved = _apply_movement(game, location, choice)
            if moved:
                return choice, False
            choice = _prompt_choice(location, game)
            continue

        _handle_non_movement_command(game, game_log, location, choice)
        if not game.ongoing:
            return None, choice == "quit"

        choice = _prompt_choice(location, game)

    return None, False


def _run_single_game() -> bool:
    """Run one game session and return whether the player wants replay."""
    game_log = EventList()  # Required baseline feature
    game = AdventureGame('game_data.json', DEFAULT_START_LOCATION)
    previous_choice = None

    while game.ongoing:
        location = game.get_location()
        game_log.add_event(Event(location.id_num, location.description['brief_description']), previous_choice)

        _show_location(location)
        previous_choice, quit_requested = _resolve_turn(game, game_log, location)
        if quit_requested:
            return False

    if game.is_quit_requested():
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
    # import python_ta
    #
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': [
    #         'R1705',
    #         'E9998',
    #         'E9999',
    #         'static_type_checker',
    #     ]
    # })

    run()
