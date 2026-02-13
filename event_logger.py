"""CSC111 Project 1: Text Adventure Game - Event Logger

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

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
from dataclasses import dataclass
from typing import Optional


# Note: We have completed the Event class for you. Do NOT modify it here for A1.
@dataclass
class Event:
    """
    A node representing one event in an adventure game.

    Instance Attributes:
    - id_num: Integer id of this event's location
    - description: Long description of this event's location
    - next_command: String command which leads this event to the next event, None if this is the last game event
    - next: Event object representing the next event in the game, or None if this is the last game event
    - prev: Event object representing the previous event in the game, None if this is the first game event
    """
    id_num: int
    description: str
    next_command: Optional[str] = None
    next: Optional[Event] = None
    prev: Optional[Event] = None


class EventList:
    """
    A linked list of game events.

    Instance Attributes:
        - first: Event object representing the first game event, None if there are no game events
        - last: Event object representing the last game event, None if there are no game events

    Representation Invariants:
    """
    first: Optional[Event]
    last: Optional[Event]

    def __init__(self) -> None:
        """Initialize a new empty event list."""

        self.first = None
        self.last = None

    def display_events(self) -> None:
        """Display all events in chronological order."""
        curr = self.first
        while curr:
            print(f"Location: {curr.id_num}, Command: {curr.next_command}")
            curr = curr.next

    def get_events_str(self) -> str:
        """Get a string representation of the current event."""
        curr = self.first
        string = ""
        while curr:
            string += str(f"Location: {curr.id_num}, Command: {curr.next_command} \n")
            curr = curr.next
        return string

    def is_empty(self) -> bool:
        """Return whether this event list is empty.

        >>> evnt_lst = EventList()
        >>> evnt_lst.is_empty()
        True
        >>> evnt_lst.add_event(Event(1, "blah"))
        >>> evnt_lst.is_empty()
        False
        """
        return self.first is None

    def add_event(self, event: Event, command: str = None) -> None:
        """
        Add the given new event to the end of this event list.
        The given command is the command which was used to reach this new event, or None if this is the first
        event in the game.

        >>> evnt_lst = EventList()
        >>> evnt1 = Event(1, "blah")
        >>> evnt2 = Event(2, "blah")
        >>> evnt3 = Event(3, "blah")
        >>> evnt_lst.add_event(evnt1)
        >>> evnt_lst.add_event(evnt2, "added 2")
        >>> evnt_lst.add_event(evnt3, "added 3")
        >>> evnt_lst.first == evnt1
        True

        >>> evnt_lst.first.next_command == "added 2"
        True

        >>> evnt_lst.last == evnt3
        True

        >>> evnt_lst.is_empty()
        False

        >>> evnt_lst.last.prev == evnt2
        True
        """

        last = self.last

        if last is None:
            self.first = event
            self.last = event
        else:
            last.next_command = command
            last.next = event
            event.prev = last
            self.last = event

    def remove_last_event(self) -> None:
        """
        Remove the last event from this event list.
        If the list is empty, do nothing.

        >>> evnt_lst = EventList()
        >>> evnt1 = Event(1, "blah")
        >>> evnt2 = Event(2, "blah")
        >>> evnt3 = Event(3, "blah")
        >>> evnt_lst.add_event(evnt1)
        >>> evnt_lst.add_event(evnt2, "added 2")
        >>> evnt_lst.add_event(evnt3, "added 3")
        >>> evnt_lst.remove_last_event()
        >>> evnt_lst.last == evnt2
        True
        >>> evnt_lst.remove_last_event()
        >>> evnt_lst.last == evnt1
        True
        >>> evnt_lst.remove_last_event()
        >>> evnt_lst.is_empty()
        True
        """

        if self.last is None:
            return
        elif self.last.prev is None:
            self.first = None
            self.last = None
        else:
            self.last = self.last.prev
            self.last.next_command = None
            self.last.next = None

    def get_id_log(self) -> list[int]:
        """Return a list of all location IDs visited for each event in this list, in sequence.

        >>> evnt_lst = EventList()
        >>> evnt1 = Event(1, "blah")
        >>> evnt2 = Event(2, "blah")
        >>> evnt3 = Event(3, "blah")
        >>> evnt_lst.add_event(evnt1)
        >>> evnt_lst.add_event(evnt2, "added 2")
        >>> evnt_lst.add_event(evnt3, "added 3")
        >>> evnt_lst.get_id_log()
        [1, 2, 3]
        """

        curr = self.first
        ids_so_far = []

        while curr is not None:
            ids_so_far.append(curr.id_num)
            curr = curr.next

        return ids_so_far


if __name__ == '__main__':
    # pass
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'allowed-io': ['EventList.display_events'],
        'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    })
