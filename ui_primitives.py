"""Shared UI primitives for the CSC111 Pygame interface.

This module stores theme constants, drawing helpers, and reusable tools.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

import pygame

from adventure import AdventureGame
from game_entities import Location

FLAG_SRCALPHA = getattr(pygame, "SRCALPHA", 0)

# Theme colours
UOFT_BLUE = (9, 48, 102)
UOFT_LIGHT_BLUE = (0, 101, 179)
UOFT_GOLD = (255, 205, 0)

BG_TOP = (245, 248, 253)
BG_BOTTOM = (234, 240, 250)

TOPBAR = (9, 48, 102)
PANEL = (238, 244, 253)
CARD = (255, 255, 255)
CARD_2 = (244, 249, 255)

BORDER = (188, 204, 228)
BORDER_SOFT = (211, 223, 241)

TEXT = (20, 36, 61)
TEXT_DIM = (53, 83, 126)
MUTED = (110, 129, 158)
WHITE = (255, 255, 255)

SHADOW = (30, 56, 95, 28)
HOVER_SHADOW = (30, 56, 95, 42)

LOGO_FILE = Path(__file__).resolve().parent / "assets" / "uoft_coa.png"


@dataclass()
class CardStyle:
    """Style settings for rounded card drawing."""
    fill: tuple[int, int, int] = CARD
    border: tuple[int, int, int] = BORDER
    radius: int = 14
    border_width: int = 2


@dataclass()
class ChipStyle:
    """Style settings for pill chips."""
    fill: tuple[int, int, int]
    text_color: tuple[int, int, int]


DEFAULT_CARD_STYLE = CardStyle()


def vertical_gradient(
    size: tuple[int, int],
    top: tuple[int, int, int],
    bottom: tuple[int, int, int]
) -> pygame.Surface:
    """Return a surface filled with a vertical gradient."""
    width, height = size
    surface = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / max(1, height - 1)
        red = int(top[0] + (bottom[0] - top[0]) * ratio)
        green = int(top[1] + (bottom[1] - top[1]) * ratio)
        blue = int(top[2] + (bottom[2] - top[2]) * ratio)
        pygame.draw.line(surface, (red, green, blue), (0, y), (width, y))
    return surface


def draw_card(surface: pygame.Surface, rect: pygame.Rect, style: CardStyle = DEFAULT_CARD_STYLE) -> None:
    """Draw a rounded card with a subtle drop shadow and border."""
    shadow = pygame.Surface((rect.width + 8, rect.height + 8), FLAG_SRCALPHA)
    pygame.draw.rect(shadow, SHADOW, shadow.get_rect(), border_radius=style.radius + 2)
    surface.blit(shadow, (rect.x + 2, rect.y + 3))
    pygame.draw.rect(surface, style.fill, rect, border_radius=style.radius)
    pygame.draw.rect(
        surface,
        style.border,
        rect,
        width=style.border_width,
        border_radius=style.radius
    )


def draw_chip(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    style: ChipStyle
) -> None:
    """Draw a pill-style status chip."""
    border_radius = rect.height // 2
    pygame.draw.rect(surface, style.fill, rect, border_radius=border_radius)
    pygame.draw.rect(surface, BORDER, rect, width=1, border_radius=border_radius)
    label = font.render(text, True, style.text_color)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_uoft_logo(
    surface: pygame.Surface,
    center: tuple[int, int],
    ring_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
    glyph_font: pygame.font.Font
) -> None:
    """Draw a simple UofT-style seal mark for the top bar."""
    cx, cy = center
    pygame.draw.circle(surface, ring_color, (cx, cy), 24, 2)
    pygame.draw.circle(surface, accent_color, (cx, cy), 20, 1)
    pygame.draw.line(surface, accent_color, (cx - 10, cy + 11), (cx + 10, cy + 11), 1)

    pygame.draw.rect(surface, ring_color, pygame.Rect(cx - 2, cy - 9, 4, 14))
    pygame.draw.polygon(surface, ring_color, [(cx - 5, cy - 9), (cx + 5, cy - 9), (cx, cy - 14)])
    pygame.draw.rect(surface, ring_color, pygame.Rect(cx - 7, cy - 3, 3, 8))
    pygame.draw.rect(surface, ring_color, pygame.Rect(cx + 4, cy - 3, 3, 8))
    glyph = glyph_font.render("U", True, ring_color)
    surface.blit(glyph, glyph.get_rect(center=(cx, cy + 6)))


def wrap_text(text: str, font: pygame.font.Font, width: int) -> list[str]:
    """Wrap text into lines that fit within a given pixel width."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def end_clip(surface: pygame.Surface, previous_clip: pygame.Rect) -> None:
    """Restore previous clip."""
    surface.set_clip(previous_clip)


@dataclass
class Button:
    """Clickable UI button."""
    rect: pygame.Rect
    label: str
    callback: Callable[[], None]
    kind: str = "secondary"
    enabled: bool = True

    def _palette(self, hovered: bool) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        """Return fill/text colours based on state."""
        if self.kind == "primary":
            fill = UOFT_LIGHT_BLUE if hovered else UOFT_BLUE
            text_color = WHITE
        elif self.kind == "ghost":
            fill = (238, 246, 255) if hovered else CARD
            text_color = TEXT
        else:
            fill = (232, 241, 253) if hovered else CARD_2
            text_color = TEXT_DIM

        if not self.enabled:
            fill = (235, 239, 246)
            text_color = MUTED
        return fill, text_color

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        mouse_pos: tuple[int, int],
        y_offset: int = 0
    ) -> None:
        """Draw the button, shifted by y_offset (for scroll areas)."""
        rect = self.rect.move(0, y_offset)
        hovered = self.enabled and rect.collidepoint(mouse_pos)
        fill, text_color = self._palette(hovered)

        shadow = pygame.Surface((rect.width + 6, rect.height + 6), FLAG_SRCALPHA)
        shadow_color = HOVER_SHADOW if hovered else SHADOW
        pygame.draw.rect(shadow, shadow_color, shadow.get_rect(), border_radius=13)
        surface.blit(shadow, (rect.x + 1, rect.y + 2))

        pygame.draw.rect(surface, fill, rect, border_radius=12)
        pygame.draw.rect(surface, BORDER_SOFT, rect, width=2, border_radius=12)

        text_image = font.render(self.label, True, text_color)
        surface.blit(text_image, text_image.get_rect(center=rect.center))

    def handle_click(self, pos: tuple[int, int], y_offset: int = 0) -> None:
        """Invoke callback if clicked (accounts for scroll offset)."""
        rect = self.rect.move(0, y_offset)
        if self.enabled and rect.collidepoint(pos):
            self.callback()


class ScrollArea:
    """A clipped region with an independent vertical scroll offset."""
    rect: pygame.Rect
    offset: int
    content_height: int

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.offset = 0
        self.content_height = rect.height

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the rectangle and clamp the offset."""
        self.rect = rect
        self.set_content_height(self.content_height)

    def set_content_height(self, content_height: int) -> None:
        """Set content height and clamp the scroll offset."""
        self.content_height = max(content_height, self.rect.height)
        max_offset = self.content_height - self.rect.height
        self.offset = max(0, min(self.offset, max_offset))

    def handle_wheel(self, mouse_pos: tuple[int, int], wheel_y: int, speed: int = 32) -> None:
        """Scroll when the mouse is over this area."""
        if not self.rect.collidepoint(mouse_pos):
            return
        max_offset = self.content_height - self.rect.height
        self.offset = max(0, min(self.offset - wheel_y * speed, max_offset))

    def begin_clip(self, surface: pygame.Surface) -> pygame.Rect:
        """Apply clipping to this area and return previous clip."""
        previous_clip = surface.get_clip()
        surface.set_clip(self.rect)
        return previous_clip

    def draw_scrollbar(self, surface: pygame.Surface) -> None:
        """Draw a slim scrollbar thumb (only if scrolling is possible)."""
        if self.content_height <= self.rect.height:
            return

        track = pygame.Rect(self.rect.right - 8, self.rect.y + 6, 4, self.rect.height - 12)
        pygame.draw.rect(surface, BORDER_SOFT, track, border_radius=3)

        thumb_height = max(18, int(track.height * (self.rect.height / self.content_height)))
        max_offset = self.content_height - self.rect.height
        ratio = 0.0 if max_offset == 0 else self.offset / max_offset
        thumb_y = track.y + int((track.height - thumb_height) * ratio)
        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        pygame.draw.rect(surface, UOFT_LIGHT_BLUE, thumb, border_radius=3)


class ModalPicker:
    """Centered modal that shows a scrollable list of options."""
    title: str
    options: list[str]
    on_pick: Callable[[str], None]
    panel: pygame.Rect
    scroll: Optional[ScrollArea]
    option_buttons: list[Button]
    is_open: bool

    def __init__(self, title: str, options: Sequence[str], on_pick: Callable[[str], None]) -> None:
        self.title = title
        self.options = list(options)
        self.on_pick = on_pick
        self.panel = pygame.Rect(0, 0, 0, 0)
        self.scroll = None
        self.option_buttons = []
        self.is_open = True

    def close(self) -> None:
        """Close the modal."""
        self.is_open = False

    def _panel_rect(self, screen_rect: pygame.Rect) -> pygame.Rect:
        """Return the centered panel rectangle."""
        width = min(560, screen_rect.width - 160)
        height = min(520, screen_rect.height - 160)
        x = screen_rect.centerx - width // 2
        y = screen_rect.centery - height // 2
        return pygame.Rect(x, y, width, height)

    def _list_rect(self, panel: pygame.Rect) -> pygame.Rect:
        """Return the inner list rectangle for option rows."""
        padding = 18
        title_height = 54
        bottom_height = 56
        return pygame.Rect(
            panel.x + padding,
            panel.y + title_height,
            panel.width - padding * 2,
            panel.height - title_height - bottom_height
        )

    def _cancel_rect(self, panel: pygame.Rect) -> pygame.Rect:
        """Return the cancel button rectangle."""
        return pygame.Rect(panel.x + 18, panel.y + panel.height - 44, 120, 32)

    def _rebuild_option_buttons(self, inner: pygame.Rect) -> None:
        """Rebuild option buttons in content coordinates."""
        row_height = 40
        gap = 10
        content_width = inner.width - 12
        content_y = inner.y

        self.option_buttons.clear()
        for option in self.options:
            button_rect = pygame.Rect(inner.x, content_y, content_width, row_height)
            self.option_buttons.append(Button(button_rect, option, self._make_pick_callback(option)))
            content_y += row_height + gap

        content_height = max(1, (content_y - inner.y) - gap)
        if self.scroll is not None:
            self.scroll.set_content_height(content_height)

    def _make_pick_callback(self, option: str) -> Callable[[], None]:
        """Return callback used when an option button is clicked."""
        def pick() -> None:
            self.on_pick(option)
            self.close()

        return pick

    def layout(self, screen_rect: pygame.Rect) -> None:
        """Compute modal geometry and option buttons."""
        self.panel = self._panel_rect(screen_rect)
        inner = self._list_rect(self.panel)

        if self.scroll is None:
            self.scroll = ScrollArea(inner)
        else:
            self.scroll.set_rect(inner)

        self._rebuild_option_buttons(inner)

    def draw(
        self,
        surface: pygame.Surface,
        title_font: pygame.font.Font,
        button_font: pygame.font.Font,
        mouse_pos: tuple[int, int]
    ) -> None:
        """Render the modal with a dark overlay and clipped list."""
        overlay = pygame.Surface(surface.get_size(), FLAG_SRCALPHA)
        overlay.fill((14, 40, 86, 88))
        surface.blit(overlay, (0, 0))

        draw_card(surface, self.panel, CardStyle(fill=CARD, border=BORDER, radius=16, border_width=2))
        title = title_font.render(self.title, True, TEXT)
        surface.blit(title, (self.panel.x + 18, self.panel.y + 16))

        if self.scroll is not None:
            pygame.draw.rect(surface, BORDER_SOFT, self.scroll.rect, width=2, border_radius=12)
            previous_clip = self.scroll.begin_clip(surface)
            y_offset = -self.scroll.offset
            for button in self.option_buttons:
                shifted = button.rect.move(0, y_offset)
                if shifted.bottom < self.scroll.rect.top or shifted.top > self.scroll.rect.bottom:
                    continue
                button.draw(surface, button_font, mouse_pos, y_offset=y_offset)
            end_clip(surface, previous_clip)
            self.scroll.draw_scrollbar(surface)

        cancel_button = Button(self._cancel_rect(self.panel), "Cancel", self.close, kind="ghost")
        cancel_button.draw(surface, button_font, mouse_pos)

    def handle_wheel(self, mouse_pos: tuple[int, int], wheel_y: int) -> None:
        """Scroll the modal list if mouse is over it."""
        if self.scroll is not None:
            self.scroll.handle_wheel(mouse_pos, wheel_y, speed=36)

    def handle_click(self, pos: tuple[int, int]) -> None:
        """Handle clicks on modal buttons."""
        if self.scroll is not None:
            y_offset = -self.scroll.offset
            for button in self.option_buttons:
                button.handle_click(pos, y_offset=y_offset)
        cancel_button = Button(self._cancel_rect(self.panel), "Cancel", self.close, kind="ghost")
        cancel_button.handle_click(pos)


class MiniMap:
    """Cardinal-direction minimap derived from available commands."""
    dirs: dict[str, tuple[int, int]] = {
        "north": (0, -1),
        "south": (0, 1),
        "east": (1, 0),
        "west": (-1, 0),
    }

    game: AdventureGame
    pos: dict[int, tuple[int, int]]
    edges: set[tuple[int, int]]

    def __init__(self, game: AdventureGame) -> None:
        self.game = game
        self.pos = {}
        self.edges = set()
        self._build_cardinal_layout()

    def _parse_dir(self, command: str) -> Optional[str]:
        """Return cardinal direction from a command like 'go north'."""
        lowered = command.lower().strip()
        for direction in self.dirs:
            if direction in lowered:
                return direction
        return None

    def _starting_location(self) -> Optional[int]:
        """Return the smallest location id or None if empty."""
        location_ids = sorted(self.game.location_dict().keys())
        if not location_ids:
            return None
        return location_ids[0]

    def _add_edge(self, u: int, v: int) -> None:
        """Store an undirected edge in normalized order."""
        a, b = (u, v) if u < v else (v, u)
        self.edges.add((a, b))

    def _build_cardinal_layout(self) -> None:
        """Assign integer grid coordinates using BFS from the smallest id."""
        start = self._starting_location()
        if start is None:
            return
        self.pos[start] = (0, 0)
        self._bfs_place_nodes(start)
        self._place_disconnected_nodes()

    def _bfs_place_nodes(self, start: int) -> None:
        """Visit connected locations and assign coordinates."""
        queue = deque([start])
        locations = self.game.location_dict()
        while queue:
            current = queue.popleft()
            location = locations[current]
            neighbors = self._visit_neighbors(location, current, locations)
            queue.extend(neighbors)

    def _visit_neighbors(
        self,
        location: Location,
        current_id: int,
        locations: dict[int, Location],
    ) -> list[int]:
        """Inspect available commands for a location and place neighbours."""
        current_x, current_y = self.pos[current_id]
        discovered: list[int] = []
        for command, destination in location.available_commands.items():
            if destination not in locations:
                continue
            direction = self._parse_dir(command)
            if direction is None:
                continue
            dx, dy = self.dirs[direction]
            candidate = (current_x + dx, current_y + dy)
            self._add_edge(current_id, destination)
            if destination not in self.pos:
                self.pos[destination] = candidate
                discovered.append(destination)
        return discovered

    def _place_disconnected_nodes(self) -> None:
        """Place disconnected nodes in a vertical spill column."""
        used = set(self.pos.values())
        max_x = max((x for x, _ in used), default=0)
        spill_x = max_x + 3
        spill_y = 0
        for location_id in sorted(self.game.location_dict().keys()):
            if location_id in self.pos:
                continue
            while (spill_x, spill_y) in used:
                spill_y += 1
            self.pos[location_id] = (spill_x, spill_y)
            used.add((spill_x, spill_y))
            spill_y += 1

    def _draw_direction_labels(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Draw N/E/S/W guides around a minimap card."""
        label_font = pygame.font.SysFont("arial", 14, bold=True)
        north = label_font.render("N", True, TEXT_DIM)
        east = label_font.render("E", True, TEXT_DIM)
        south = label_font.render("S", True, TEXT_DIM)
        west = label_font.render("W", True, TEXT_DIM)
        surface.blit(north, (rect.centerx - north.get_width() // 2, rect.y + 6))
        surface.blit(south, (rect.centerx - south.get_width() // 2, rect.bottom - 6 - south.get_height()))
        surface.blit(west, (rect.x + 6, rect.centery - west.get_height() // 2))
        surface.blit(east, (rect.right - 6 - east.get_width(), rect.centery - east.get_height() // 2))

    def _normalization_bounds(self) -> tuple[int, int, int, int]:
        """Return (min_x, max_x, min_y, max_y) for node coordinates."""
        xs = [point[0] for point in self.pos.values()]
        ys = [point[1] for point in self.pos.values()]
        return min(xs), max(xs), min(ys), max(ys)

    def _to_screen_builder(self, inner: pygame.Rect) -> Callable[[int], tuple[int, int]]:
        """Return a function converting location ids to screen coordinates."""
        min_x, max_x, min_y, max_y = self._normalization_bounds()
        delta_x = max(1, max_x - min_x)
        delta_y = max(1, max_y - min_y)

        def to_screen(location_id: int) -> tuple[int, int]:
            gx, gy = self.pos[location_id]
            tx = (gx - min_x) / delta_x
            ty = (gy - min_y) / delta_y
            screen_x = inner.x + int(tx * inner.width)
            screen_y = inner.y + int(ty * inner.height)
            return screen_x, screen_y

        return to_screen

    def _draw_edges(self, surface: pygame.Surface, to_screen: Callable[[int], tuple[int, int]]) -> None:
        """Draw orthogonal edge segments for each map connection."""
        for u, v in self.edges:
            if u not in self.pos or v not in self.pos:
                continue
            x1, y1 = to_screen(u)
            x2, y2 = to_screen(v)
            elbow = (x2, y1)
            pygame.draw.line(surface, BORDER, (x1, y1), elbow, 2)
            pygame.draw.line(surface, BORDER, elbow, (x2, y2), 2)

    def _draw_nodes(
        self,
        surface: pygame.Surface,
        to_screen: Callable[[int], tuple[int, int]],
        current_id: int
    ) -> None:
        """Draw minimap nodes with a highlighted current location."""
        for location_id in sorted(self.pos):
            x, y = to_screen(location_id)
            if location_id == current_id:
                pygame.draw.circle(surface, UOFT_GOLD, (x, y), 8)
                pygame.draw.circle(surface, UOFT_BLUE, (x, y), 8, 2)
            else:
                pygame.draw.circle(surface, UOFT_LIGHT_BLUE, (x, y), 5)
                pygame.draw.circle(surface, WHITE, (x, y), 5, 2)

    def draw(self, surface: pygame.Surface, rect: pygame.Rect, current_id: int) -> None:
        """Draw a cardinal map with orthogonal edges."""
        draw_card(surface, rect, CardStyle(fill=CARD, border=BORDER, radius=14, border_width=2))
        if not self.pos:
            return

        self._draw_direction_labels(surface, rect)
        padding = 18
        inner = pygame.Rect(rect.x + padding, rect.y + padding, rect.width - padding * 2, rect.height - padding * 2)
        to_screen = self._to_screen_builder(inner)
        self._draw_edges(surface, to_screen)
        self._draw_nodes(surface, to_screen, current_id)


if __name__ == "__main__":
    import python_ta

    python_ta.check_all(config={
        'max-line-length': 120,
        'disable': [
            'R1705',
            'E9998',
            'E9999',
            'static_type_checker',
        ]
    })
