"""CSC111 Project 1: Text Adventure Game - Simulator

Instructions (READ THIS FIRST!)
===============================

This Python module contains code for Project 1 that allows a user to simulate
an entire playthrough of the game. Please consult the project handout for
instructions and details.

You can copy/paste your code from Assignment 1 into this file, and modify it as
needed to work with your game.

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
from event_logger import Event, EventList
from adventure import AdventureGame
from game_entities import Location


class AdventureGameSimulation:
    """A simulation of an adventure game playthrough.
    """
    # Private Instance Attributes:
    #   - _game: The AdventureGame instance that this simulation uses.
    #   - _events: A collection of the events to process during the simulation.
    _game: AdventureGame
    _events: EventList

    def __init__(self, game_data_file: str, initial_location_id: int, commands: list[str]) -> None:
        """
        Initialize a new game simulation based on the given game data, that runs through the given commands.

        Preconditions:
        - len(commands) > 0
        - all commands in the given list are valid commands when starting from the location at initial_location_id
        """
        self._events = EventList()
        self._game = AdventureGame(game_data_file, initial_location_id)
        initial_location = self._game.get_location()
        self._events.add_event(Event(initial_location.id_num, initial_location.description['brief_description']))
        self.generate_events(commands, self._game.get_location())

    def generate_events(self, commands: list[str], current_location: Location) -> None:
        """
        Generate events in this simulation, based on current_location and commands, a valid list of commands.

        Preconditions:
        - len(commands) > 0
        - all commands in the given list are valid commands when starting from current_location
          OR are non-movement commands (e.g., "inventory", "score"), which keep the player
          in the same location for simulation logging purposes.
        """
        curr_location = current_location

        for command in commands:
            normalized = command.strip().lower()
            next_location = curr_location

            if normalized in curr_location.available_commands:
                next_location_id = curr_location.available_commands[normalized]
                can_enter, _ = self._game.can_enter_location(next_location_id)
                if can_enter:
                    self._game.current_location_id = next_location_id
                    next_location = self._game.get_location(next_location_id)
            else:
                self._process_non_movement_command(normalized)
                next_location = self._game.get_location()

            new_event = Event(next_location.id_num, next_location.description['brief_description'])
            self._events.add_event(new_event)
            curr_location = next_location

        self._game.current_location_id = curr_location.id_num

    def _process_non_movement_command(self, command: str) -> None:
        """Apply non-movement commands to simulation game state."""
        parts = command.split(maxsplit=1)
        if len(parts) != 2:
            return

        verb, item_name = parts
        if verb == "take":
            self._game.pick_up(item_name)
        elif verb == "drop" and self._game.drop(item_name):
            self._game.check_quest(item_name)
            self._game.apply_location_rewards(item_name)

    def get_id_log(self) -> list[int]:
        """
        Get back a list of all location IDs in the order that they are visited within a game simulation
        that follows the given commands.

        >>> sim = AdventureGameSimulation('game_data.json', 2, ["go west"])
        >>> sim.get_id_log()
        [2, 3]

        >>> sim = AdventureGameSimulation('game_data.json', 2, ["go west", "go west", "inventory"])
        >>> sim.get_id_log()
        [2, 3, 4, 4]
        """

        return self._events.get_id_log()

    def run(self) -> None:
        """
        Run the game simulation and print location descriptions.
        """

        current_event = self._events.first  # Start from the first event in the list

        while current_event:
            print(current_event.description)
            if current_event is not self._events.last:
                print("You choose:", current_event.next_command)

            # Move to the next event in the linked list
            current_event = current_event.next


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })

    win_walkthrough = [
        "take tcard",
        "go west", "take signed extension request", "go west", "take dorm key", "go west", "take lucky mug",
        "go east", "go east", "go east", "go east",
        "go south", "go east", "go east", "go east", "take usb drive",
        "go west", "go north", "go north", "go east", "go east", "go south", "go east", "take toonie",
        "go west", "go north", "go west", "go west", "go south", "go south", "go south", "go south",
        "go west", "go west", "go west", "drop toonie",
        "go east", "go east", "go east", "go north", "go north", "go north", "go north", "go east", "go east",
        "go south", "go east", "go south", "go south", "drop coffee",
        "go north", "go east", "take laptop charger",
        "go west", "go north", "go west", "go north", "go west", "go west", "go south", "go south", "go west",
        "go west", "go north",
        "drop lucky mug", "drop usb drive", "drop laptop charger", "submit early"
    ]
    expected_log = [
        2, 2, 3, 3, 4, 4, 5, 5, 4, 3, 2, 1, 9, 10, 11, 12, 12, 11, 13, 14, 16, 17, 18, 19, 19, 18,
        17, 16, 14, 13, 11, 31, 29, 30, 28, 27, 27, 28, 30, 29, 31, 11, 13, 14, 16, 17, 18, 19, 20, 33,
        33, 20, 21, 21, 20, 19, 18, 17, 16, 14, 13, 11, 10, 9, 1, 1, 1, 1, 1
    ]
    sim = AdventureGameSimulation('game_data.json', 2, win_walkthrough)
    assert expected_log == sim.get_id_log()

    lose_demo = ["go west", "go east"] * 33 + ["go west"]  # 67 movement commands
    expected_log = [2] + [3 if i % 2 == 1 else 2 for i in range(1, 67)] + [3]
    sim = AdventureGameSimulation('game_data.json', 2, lose_demo)
    assert expected_log == sim.get_id_log()

    inventory_demo = ["take tcard", "inventory", "go west",
                      "take signed extension request", "inventory", "go east"]
    expected_log = [2, 2, 2, 3, 3, 3, 2]
    sim = AdventureGameSimulation('game_data.json', 2, inventory_demo)
    assert expected_log == sim.get_id_log()

    scores_demo = [
        "take tcard",
        "go west", "go west", "take dorm key", "go east", "go east", "go east",
        "go south", "go east", "go east", "go east", "take usb drive",
        "go west", "go west", "go west", "go north", "drop usb drive", "score"
    ]
    expected_log = [2, 2, 3, 4, 4, 3, 2, 1, 9, 10, 11, 12, 12, 11, 10, 9, 1, 1, 1]
    sim = AdventureGameSimulation('game_data.json', 2, scores_demo)
    assert expected_log == sim.get_id_log()

    enhancement1_demo = [
        "take tcard", "go west", "take signed extension request", "go west", "take dorm key",
        "go east", "go east", "go east", "go south", "go east", "go east",
        "go north", "go north", "go north", "drop signed extension request"
    ]
    expected_log = [2, 2, 3, 3, 4, 4, 3, 2, 1, 9, 10, 11, 13, 14, 32, 32]
    sim = AdventureGameSimulation('game_data.json', 2, enhancement1_demo)
    assert expected_log == sim.get_id_log()
