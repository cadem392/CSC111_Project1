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
from typing import Optional

from game_entities import Location, Item
from event_logger import Event, EventList


# Note: You may add in other import statements here as needed

# Note: You may add helper functions, classes, etc. below as needed


class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - # TODO add descriptions of public instance attributes as needed

    Representation Invariants:
        - # TODO add any appropriate representation invariants as needed
    """

    # Private Instance Attributes (do NOT remove these two attributes):
    #   - _locations: a mapping from location id to Location object.
    #                       This represents all the locations in the game.
    #   - _items: a list of Item objects, representing all items in the game.

    _locations: dict[int, Location]
    _items: list[Item]
    _valid_items: set[Item]
    current_location_id: int  # Suggested attribute, can be removed
    ongoing: bool  # Suggested attribute, can be removed
    inventory: list[Item] = []
    score: int = 0
    turn: int = 0
    max_turns: int = 67
    min_score: int = 50
    returned: set[str] = set()



    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """
        Initialize a new text adventure game, based on the data in the given file, setting starting location of game
        at the given initial location ID.
        (note: you are allowed to modify the format of the file as you see fit)

        Preconditions:
        - game_data_file is the filename of a valid game data JSON file
        """

        # NOTES:
        # You may add parameters/attributes/methods to this class as you see fit.

        # Requirements:
        # 1. Make sure the Location class is used to represent each location.
        # 2. Make sure the Item class is used to represent each item.

        # Suggested helper method (you can remove and load these differently if you wish to do so):
        self._locations, self._items, self._valid_items = self._load_game_data(game_data_file)

        # Suggested attributes (you can remove and track these differently if you wish to do so):
        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True  # whether the game is ongoing

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item], set[str]]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a list of all Item objects."""

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(loc_data['id'], loc_data['name'], loc_data['brief_description'],
                                    loc_data['long_description'], loc_data['available_commands'], loc_data['items'])
            locations[loc_data['id']] = location_obj

        items = []
        valid_items = set()
        for item_data in data['items']:  # Go through each element associated with the 'locations' key in the file
            item_obj = Item(item_data['name'], item_data['description'], item_data['hint'],
                            item_data['completion_text'], item_data['start_position'], item_data['target_position'],
                            item_data['target_points'])
            items.append(item_obj)
            valid_items.add(item_data['name'])

        return locations, items, valid_items

    def location_dict(self) -> dict[int, Location]:
        """Return a dictionary of all available locations IDs."""
        return self._locations.copy()

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """

        if loc_id is None:
            return self._locations[self.current_location_id]
        else:
            return self._locations[loc_id]

    def get_item(self, item_name: str) -> Optional[Item]:
        """Return Item object associated with the provided item name."""
        return next(i for i in self._items if i.name == item_name)

    def pick_up(self, item_name: str) -> bool:
        """Pick up an item from the given item name from your current location."""
        if item_name not in self._valid_items:
            return False
        curr_item = self.get_item(item_name)
        curr_location = self.get_location()
        if item_name in curr_location.items:
            self.inventory.append(curr_item)
            curr_location.items.remove(item_name)
            return True
        else:
            return False

    def drop(self, item_name: str) -> bool:
        """Drop an item from the given item name from your current location."""
        if item_name not in self._valid_items:
            return False
        curr_item = self.get_item(item_name)
        curr_location = self.get_location()
        if curr_item in self.inventory:
            self.inventory.remove(curr_item)
            curr_location.items.append(item_name)
            return True
        else:
            return False

    def inspect(self, item_name: str) -> None:
        """Inspect an item from the given item name from your inventory."""
        if item_name not in self._valid_items:
            return
        curr_item = self.get_item(item_name)
        if curr_item in self.inventory:
            print(curr_item.hint)

    def check_quest(self, item_name: str) -> None:
        """Check if an item is in the target location."""
        curr_item = self.get_item(item_name)
        curr_location = self.get_location()
        if curr_item.target_position == curr_location.id_num:
            print(curr_item.completion_text)
            self.returned.add(item_name)
            self.score += curr_item.target_points
            print("Your score is now " + str(self.score))
            curr_location.items.remove(item_name)


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })

    game_log = EventList()  # This is REQUIRED as one of the baseline requirements
    game = AdventureGame('game_data.json', 1)  # load data, setting initial location ID to 1
    menu = ["look", "inventory", "score", "log", "quit"]  # Regular menu options available at each location
    choice = None

    # Note: You may modify the code below as needed; the following starter code is just a suggestion
    while game.ongoing:
        # Note: If the loop body is getting too long, you should split the body up into helper functions
        # for better organization. Part of your mark will be based on how well-organized your code is.

        location = game.get_location()

        game_log.add_event(Event(location.id_num, location.brief_description), choice)

        if location.visited:
            print(location.brief_description)
        else:
            location.visited = True
            print(location.long_description)

        # Display possible actions at this location
        print("What to do? Choose from: look, inventory, score, log, quit, take <item>, drop <item>, inspect <item>")
        print("At this location, you can also:")
        for action in location.available_commands:
            print("-", action)

        # Validate choice
        choice = input("\nEnter action: ").lower().strip()
        while (choice not in location.available_commands and choice not in menu and
               "take" not in choice and "drop" not in choice and "inspect" not in choice):
            print("That was an invalid option; try again.")
            choice = input("\nEnter action: ").lower().strip()

        print("========")
        print("You decided to:", choice)

        while choice not in location.available_commands:

            if choice == "log":
                game_log.display_events()

            elif choice == "look":
                print(location.long_description)
                if len(location.items) > 0:
                    print("Items In " + location.name)
                    for item in location.items:
                        print(game.get_item(item))
                else:
                    print("No Items In " + location.name)

            elif choice == "inventory":
                if len(game.inventory) > 0:
                    for item in game.inventory:
                        print(item)
                else:
                    print("No Items In Your Inventory")

            elif choice == "score":
                print(game.score)

            elif choice == "log":
                game_log.display_events()

            elif "take" in choice:
                item = choice.split(maxsplit=1)[1]

                if game.pick_up(item):
                    print("You picked up " + item)
                else:
                    print("No such item " + item + " here.")

            elif "drop" in choice:
                item = choice.split(maxsplit=1)[1]

                if game.drop(item):
                    print("You dropped " + item)
                    game.check_quest(item)
                else:
                    print("No such item " + item + " in inventory.")

            elif "inspect" in choice:
                item = choice.split(maxsplit=1)[1]
                game.inspect(item)

            choice = input("\nEnter action: ").lower().strip()
            while (choice not in location.available_commands and choice not in menu and
                   "take" not in choice and "drop" not in choice and "inspect" not in choice):
                print("That was an invalid option; try again.")
                choice = input("\nEnter action: ").lower().strip()

            print("========")
            print("You decided to:", choice)

        # ENTER YOUR CODE BELOW to handle other menu commands (remember to use helper functions as appropriate)
        # Handle non-menu actions
        result = location.available_commands[choice]
        game.current_location_id = result

        # TODO: Add in code to deal with actions which do not change the location (e.g. taking or using an item)
        # TODO: Add in code to deal with special locations (e.g. puzzles) as needed for your game


def run_minigame(minigame: str) -> None:
    """runs different minigames and puzzles."""
    pass
