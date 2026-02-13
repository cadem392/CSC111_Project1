"""CSC111 Project 1: Text Adventure Game - Game Entities

Instructions (READ THIS FIRST!)
===============================

This Python module contains the entity classes for Project 1, to be imported and used by
 the `adventure` module.
 Please consult the project handout for instructions and details.

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class Location:
    """A location in our text adventure game world.

    Instance Attributes:
        - id_num: the numeric id used to identify this location.
        - description: text metadata for this location. Expected keys are
          ``name``, ``brief_description``, and ``long_description``.
        - available_commands: mapping of valid movement commands at this location
          to destination location ids.
        - items: names of items currently present at this location.
        - restrictions: optional restriction payload describing required items
          to enter this location.
        - rewards: optional reward payload describing item trades or attribute
          rewards available at this location.
        - visited: whether this location has been visited by the player in the
          current run.

    Representation Invariants:
        - self.id_num >= 0
        - all(key in self.description for key in {'name', 'brief_description', 'long_description'})
        - all(isinstance(obj, str) and obj != '' for obj in self.description)
        - all(isinstance(obj, str) for obj in self.description.values())
        - all(isinstance(item, str) and item != '' for item in self.items)
    """

    id_num: int
    description: dict[str, str]
    available_commands: dict[str, int]
    items: list[str]
    restrictions: str
    rewards: Any
    visited: bool = False


@dataclass
class Item:
    """An item in our text adventure game world.

    Instance Attributes:
        - name: the canonical item name used in commands.
        - description: short description shown to the player.
        - hint: hint text shown when the item is inspected.
        - completion_text: message shown when the item is returned correctly.
        - start_position: id of the starting location containing this item.
        - target_position: id of the location where this item should be returned.
        - target_points: points awarded for returning this item to target_position.

    Representation Invariants:
        - self.name != ''
        - self.description != ''
        - self.hint != ''
        - self.completion_text != ''
        - self.start_position >= 0
        - self.target_position >= 0
        - self.target_points >= 0
    """

    name: str
    description: str
    hint: str
    completion_text: str
    start_position: int
    target_position: int
    target_points: int

    def __str__(self) -> str:
        """Return a user-friendly item label."""
        return self.name.capitalize() + " - " + self.description


if __name__ == "__main__":
    # pass
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })
