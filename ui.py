"""
Pygame UI for the CSC111 text adventure.

What this version adds/fixes:
- Output panel has its own independent scroll (mouse wheel over Output).
- Actions panel has its own independent scroll (mouse wheel over Actions list).
  This scroll does NOT move the rest of the UI.
- Anything that scrolls is properly clipped so it disappears behind the card,
  like a web app sidebar (no drawing over other content).

Controls:
- Scroll Output: hover Output box, use mouse wheel.
- Scroll Actions: hover Actions list area, use mouse wheel.
- ESC closes modal / quits.
"""

from __future__ import annotations

import pygame
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

# --- CHANGE THIS IMPORT IF NEEDED ---
from adventure import AdventureGame
from event_logger import EventList, Event


# =====================================================
# Theme (ACORN-inspired, light dashboard style)
# =====================================================

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


# =====================================================
# Drawing helpers
# =====================================================

def vertical_gradient(size: tuple[int, int],
                      top: tuple[int, int, int],
                      bottom: tuple[int, int, int]) -> pygame.Surface:
    """Return a surface filled with a vertical gradient."""
    w, h = size
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
    return surf


def draw_card(surface: pygame.Surface, rect: pygame.Rect,
              fill: tuple[int, int, int] = CARD,
              border: tuple[int, int, int] = BORDER,
              radius: int = 14,
              border_w: int = 2) -> None:
    """Draw a rounded card with a subtle drop shadow and border."""
    shadow = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
    pygame.draw.rect(shadow, SHADOW, shadow.get_rect(), border_radius=radius + 2)
    surface.blit(shadow, (rect.x + 2, rect.y + 3))
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width=border_w, border_radius=radius)


def draw_chip(surface: pygame.Surface, rect: pygame.Rect, text: str,
              font: pygame.font.Font, fill: tuple[int, int, int],
              fg: tuple[int, int, int]) -> None:
    """Draw a pill-style status chip."""
    pygame.draw.rect(surface, fill, rect, border_radius=rect.height // 2)
    pygame.draw.rect(surface, BORDER, rect, width=1, border_radius=rect.height // 2)
    label = font.render(text, True, fg)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_uoft_logo(surface: pygame.Surface, center: tuple[int, int],
                   ring_color: tuple[int, int, int], accent_color: tuple[int, int, int],
                   glyph_font: pygame.font.Font) -> None:
    """Draw a simple UofT-style seal mark for the top bar."""
    cx, cy = center
    pygame.draw.circle(surface, ring_color, (cx, cy), 24, 2)
    pygame.draw.circle(surface, accent_color, (cx, cy), 20, 1)
    pygame.draw.line(surface, accent_color, (cx - 10, cy + 11), (cx + 10, cy + 11), 1)

    # Minimal crest glyph.
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

    for w in words:
        test = (current + " " + w).strip()
        if font.size(test)[0] <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w

    if current:
        lines.append(current)

    return lines


# =====================================================
# UI primitives
# =====================================================

@dataclass
class Button:
    """Clickable UI button."""
    rect: pygame.Rect
    label: str
    callback: Callable[[], None]
    kind: str = "secondary"   # primary / secondary / ghost
    enabled: bool = True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font,
             mouse_pos: tuple[int, int], y_offset: int = 0) -> None:
        """Draw the button, shifted by y_offset (for scroll areas)."""
        r = self.rect.move(0, y_offset)
        hovered = self.enabled and r.collidepoint(mouse_pos)

        if self.kind == "primary":
            base = UOFT_BLUE
            hover = UOFT_LIGHT_BLUE
            txt_color = WHITE
        elif self.kind == "ghost":
            base = CARD
            hover = (238, 246, 255)
            txt_color = TEXT
        else:
            base = CARD_2
            hover = (232, 241, 253)
            txt_color = TEXT_DIM

        fill = hover if hovered else base
        if not self.enabled:
            fill = (235, 239, 246)
            txt_color = MUTED

        shadow = pygame.Surface((r.width + 6, r.height + 6), pygame.SRCALPHA)
        shadow_color = HOVER_SHADOW if hovered else SHADOW
        pygame.draw.rect(shadow, shadow_color, shadow.get_rect(), border_radius=13)
        surface.blit(shadow, (r.x + 1, r.y + 2))
        pygame.draw.rect(surface, fill, r, border_radius=12)
        pygame.draw.rect(surface, BORDER_SOFT, r, width=2, border_radius=12)

        text = font.render(self.label, True, txt_color)
        surface.blit(text, text.get_rect(center=r.center))

    def handle_click(self, pos: tuple[int, int], y_offset: int = 0) -> None:
        """Invoke callback if clicked (accounts for scroll offset)."""
        r = self.rect.move(0, y_offset)
        if self.enabled and r.collidepoint(pos):
            self.callback()


def end_clip(surface: pygame.Surface, prev: pygame.Rect) -> None:
    """Restore previous clip."""
    surface.set_clip(prev)


class ScrollArea:
    """A clipped region with an independent vertical scroll offset."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.offset = 0
        self.content_height = rect.height

    def set_rect(self, rect: pygame.Rect) -> None:
        """Update the rectangle and clamp the offset."""
        self.rect = rect
        self.set_content_height(self.content_height)

    def set_content_height(self, h: int) -> None:
        """Set content height and clamp the scroll offset."""
        self.content_height = max(h, self.rect.height)
        self.offset = max(0, min(self.offset, self.content_height - self.rect.height))

    def handle_wheel(self, mouse_pos: tuple[int, int], wheel_y: int, speed: int = 32) -> None:
        """Scroll when the mouse is over this area."""
        if self.rect.collidepoint(mouse_pos):
            # wheel_y: +1 up, -1 down
            self.offset = max(0, min(self.offset - wheel_y * speed,
                                     self.content_height - self.rect.height))

    def begin_clip(self, surface: pygame.Surface) -> pygame.Rect:
        """Apply clipping to this area and return previous clip."""
        prev = surface.get_clip()
        surface.set_clip(self.rect)
        return prev

    def draw_scrollbar(self, surface: pygame.Surface) -> None:
        """Draw a slim scrollbar thumb (only if scrolling is possible)."""
        if self.content_height <= self.rect.height:
            return

        track = pygame.Rect(self.rect.right - 8, self.rect.y + 6, 4, self.rect.height - 12)
        pygame.draw.rect(surface, BORDER_SOFT, track, border_radius=3)

        thumb_h = max(18, int(track.height * (self.rect.height / self.content_height)))
        max_off = self.content_height - self.rect.height
        t = 0 if max_off == 0 else self.offset / max_off
        thumb_y = track.y + int((track.height - thumb_h) * t)

        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_h)
        pygame.draw.rect(surface, UOFT_LIGHT_BLUE, thumb, border_radius=3)


# =====================================================
# Modal Picker
# =====================================================

class ModalPicker:
    """Centered modal that shows a scrollable list of options."""

    def __init__(self, title: str, options: Sequence[str], on_pick: Callable[[str], None]) -> None:
        self.title = title
        self.options = list(options)
        self.on_pick = on_pick

        self.panel = pygame.Rect(0, 0, 0, 0)
        self.scroll: Optional[ScrollArea] = None

        self.option_buttons: list[Button] = []
        self.cancel_button: Optional[Button] = None
        self.is_open = True

    def close(self) -> None:
        """Close the modal."""
        self.is_open = False

    def layout(self, screen_rect: pygame.Rect) -> None:
        """Compute modal geometry and option buttons."""
        w = min(560, screen_rect.width - 160)
        h = min(520, screen_rect.height - 160)
        x = screen_rect.centerx - w // 2
        y = screen_rect.centery - h // 2
        self.panel = pygame.Rect(x, y, w, h)

        pad = 18
        title_h = 54
        bottom_h = 56

        # Scrollable list area inside modal
        inner = pygame.Rect(
            x + pad,
            y + title_h,
            w - pad * 2,
            h - title_h - bottom_h
        )

        if self.scroll is None:
            self.scroll = ScrollArea(inner)
        else:
            self.scroll.set_rect(inner)

        # Build ALL option buttons in "content coordinates" (same pattern as Actions panel)
        self.option_buttons.clear()
        row_h = 40
        gap = 10
        content_y = inner.y
        content_w = inner.width - 12  # leave room for scrollbar

        for opt in self.options:
            r = pygame.Rect(inner.x, content_y, content_w, row_h)

            def pick(o: str = opt) -> None:
                """Pick a button"""
                self.on_pick(o)
                self.close()

            self.option_buttons.append(Button(r, opt, pick, kind="secondary"))
            content_y += row_h + gap

        content_h = max(1, (content_y - inner.y) - gap)
        self.scroll.set_content_height(content_h)

        # Cancel button (non-scroll)
        cancel_rect = pygame.Rect(x + pad, y + h - 44, 120, 32)
        self.cancel_button = Button(cancel_rect, "Cancel", self.close, kind="ghost")

    def draw(self, surface: pygame.Surface, title_font: pygame.font.Font,
             btn_font: pygame.font.Font, mouse_pos: tuple[int, int]) -> None:
        """Render the modal with a dark overlay + clipped scroll list."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((14, 40, 86, 88))
        surface.blit(overlay, (0, 0))

        draw_card(surface, self.panel, CARD, radius=16)

        title = title_font.render(self.title, True, TEXT)
        surface.blit(title, (self.panel.x + 18, self.panel.y + 16))

        if self.scroll is not None:
            # optional border to show list area
            pygame.draw.rect(surface, BORDER_SOFT, self.scroll.rect, width=2, border_radius=12)

            prev = self.scroll.begin_clip(surface)
            y_off = -self.scroll.offset

            for b in self.option_buttons:
                rr = b.rect.move(0, y_off)
                if rr.bottom < self.scroll.rect.top or rr.top > self.scroll.rect.bottom:
                    continue
                b.draw(surface, btn_font, mouse_pos, y_offset=y_off)

            end_clip(surface, prev)
            self.scroll.draw_scrollbar(surface)

        if self.cancel_button is not None:
            self.cancel_button.draw(surface, btn_font, mouse_pos)

    def handle_wheel(self, mouse_pos: tuple[int, int], wheel_y: int) -> None:
        """Scroll the modal list if mouse is over it."""
        if self.scroll is not None:
            self.scroll.handle_wheel(mouse_pos, wheel_y, speed=36)

    def handle_click(self, pos: tuple[int, int]) -> None:
        """Handle clicks on modal buttons (account for scroll)."""
        if self.scroll is not None:
            y_off = -self.scroll.offset
            for b in self.option_buttons:
                b.handle_click(pos, y_offset=y_off)

        if self.cancel_button is not None:
            self.cancel_button.handle_click(pos)


# =====================================================
# Minimap
# =====================================================

class MiniMap:
    """Cardinal-direction minimap derived from available_commands."""

    DIRS = {
        "north": (0, -1),
        "south": (0,  1),
        "east":  (1,  0),
        "west":  (-1, 0),
    }

    def __init__(self, game: AdventureGame) -> None:
        self.game = game
        self.pos: dict[int, tuple[int, int]] = {}
        self.edges: set[tuple[int, int]] = set()
        self._build_cardinal_layout()

    def _parse_dir(self, cmd: str) -> Optional[str]:
        c = cmd.lower().strip()
        # expects "go north" etc.
        for d in self.DIRS:
            if d in c:
                return d
        return None

    def _build_cardinal_layout(self) -> None:
        """Assign integer grid coordinates using BFS from the smallest id."""
        loc_ids = sorted(self.game.location_dict().keys())
        if not loc_ids:
            return

        start = loc_ids[0]
        self.pos[start] = (0, 0)

        from collections import deque
        q = deque([start])

        while q:
            u = q.popleft()
            ux, uy = self.pos[u]
            loc = self.game.location_dict()[u]

            for cmd, v in loc.available_commands.items():
                if v not in self.game.location_dict():
                    continue

                d = self._parse_dir(cmd)
                if d is None:
                    # ignore non-cardinal commands in minimap layout
                    continue

                dx, dy = self.DIRS[d]
                cand = (ux + dx, uy + dy)

                a, b = (u, v) if u < v else (v, u)
                self.edges.add((a, b))

                if v not in self.pos:
                    self.pos[v] = cand
                    q.append(v)
                else:
                    # If already placed but inconsistent, keep placement and still keep edge.
                    # (If you want, you can add conflict resolution here.)
                    pass

        # Any disconnected nodes: place them in a line to the far right
        used = set(self.pos.values())
        maxx = max(x for x, _ in used) if used else 0
        spill_x = maxx + 3
        spill_y = 0
        for lid in loc_ids:
            if lid not in self.pos:
                while (spill_x, spill_y) in used:
                    spill_y += 1
                self.pos[lid] = (spill_x, spill_y)
                used.add((spill_x, spill_y))
                spill_y += 1

    def draw(self, surface: pygame.Surface, rect: pygame.Rect, current_id: int) -> None:
        """Draw a cardinal map with orthogonal edges."""
        draw_card(surface, rect, CARD, radius=14)

        if not self.pos:
            return

        # Direction labels
        n_lbl = pygame.font.SysFont("arial", 14, bold=True).render("N", True, TEXT_DIM)
        e_lbl = pygame.font.SysFont("arial", 14, bold=True).render("E", True, TEXT_DIM)
        s_lbl = pygame.font.SysFont("arial", 14, bold=True).render("S", True, TEXT_DIM)
        w_lbl = pygame.font.SysFont("arial", 14, bold=True).render("W", True, TEXT_DIM)
        surface.blit(n_lbl, (rect.centerx - n_lbl.get_width() // 2, rect.y + 6))
        surface.blit(s_lbl, (rect.centerx - s_lbl.get_width() // 2, rect.bottom - 6 - s_lbl.get_height()))
        surface.blit(w_lbl, (rect.x + 6, rect.centery - w_lbl.get_height() // 2))
        surface.blit(e_lbl, (rect.right - 6 - e_lbl.get_width(), rect.centery - e_lbl.get_height() // 2))

        # Normalize integer grid coords to rect with padding
        xs = [p[0] for p in self.pos.values()]
        ys = [p[1] for p in self.pos.values()]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        dx = max(1, maxx - minx)
        dy = max(1, maxy - miny)

        pad = 18
        inner = pygame.Rect(rect.x + pad, rect.y + pad, rect.width - pad * 2, rect.height - pad * 2)

        def to_screen(lidp: int) -> tuple[int, int]:
            """Flip to Screen"""
            gx, gy = self.pos[lidp]
            tx = (gx - minx) / dx
            ty = (gy - miny) / dy
            sx = inner.x + int(tx * inner.width)
            sy = inner.y + int(ty * inner.height)
            return sx, sy

        # Draw edges as orthogonal segments (L-shape) to feel “map-like”
        for u, v in self.edges:
            if u not in self.pos or v not in self.pos:
                continue
            x1, y1 = to_screen(u)
            x2, y2 = to_screen(v)

            mid = (x2, y1)  # elbow
            pygame.draw.line(surface, BORDER, (x1, y1), mid, 2)
            pygame.draw.line(surface, BORDER, mid, (x2, y2), 2)

        # Draw nodes (current highlighted)
        for lid in sorted(self.pos.keys()):
            x, y = to_screen(lid)

            if lid == current_id:
                pygame.draw.circle(surface, UOFT_GOLD, (x, y), 8)
                pygame.draw.circle(surface, UOFT_BLUE, (x, y), 8, 2)
            else:
                pygame.draw.circle(surface, UOFT_LIGHT_BLUE, (x, y), 5)
                pygame.draw.circle(surface, WHITE, (x, y), 5, 2)


# =====================================================
# Main UI
# =====================================================

class GameUI:
    """Main Pygame UI loop and rendering."""

    def __init__(self, game: AdventureGame, log: EventList) -> None:
        self.game = game
        self.log = log

        self.game.inventory = list(getattr(self.game, "inventory", []))
        self.game.score = int(getattr(self.game, "score", 0))

        self.modal: Optional[ModalPicker] = None
        self.minimap = MiniMap(game)

        self.output_lines: list[str] = []
        self.output_scroll: Optional[ScrollArea] = None
        self.actions_scroll: Optional[ScrollArea] = None

    # ---------- Output helpers ----------

    def begin_turn(self, label: str) -> None:
        """Clear output and begin a new action."""
        self.output_lines = [f"You chose: {label}"]

        # Reset output scroll so new content starts at the top.
        if self.output_scroll is not None:
            self.output_scroll.offset = 0

    def out(self, text: str) -> None:
        """Append text to the current turn output."""
        for line in text.split("\n"):
            s = line.strip()
            if s:
                self.output_lines.append(s)

    def location_description(self) -> str:
        """Return the correct location description and update visited."""
        loc = self.game.get_location()
        if getattr(loc, "visited", False):
            return loc.brief_description
        loc.visited = True
        return loc.long_description

    def _compute_output_content_height(self, body_font: pygame.font.Font, inner_width: int) -> int:
        """Compute the pixel height of output content (wrapped)."""
        line_h = body_font.get_height() + 4
        wrapped: list[str] = []
        for raw in self.output_lines:
            wrapped.extend(wrap_text(raw, body_font, inner_width))
        return max(1, len(wrapped) * line_h)

    def draw_output(self, surface: pygame.Surface, rect: pygame.Rect,
                    label_font: pygame.font.Font, body_font: pygame.font.Font) -> None:
        """Draw a scrollable output card with proper clipping."""
        draw_card(surface, rect, CARD, radius=16)
        label = label_font.render("OUTPUT", True, TEXT_DIM)
        surface.blit(label, (rect.x + 18, rect.y + 10))

        header_h = 34
        inner = pygame.Rect(rect.x + 18, rect.y + header_h,
                            rect.width - 36, rect.height - header_h - 16)
        pygame.draw.rect(surface, CARD_2, inner, border_radius=10)
        pygame.draw.rect(surface, BORDER_SOFT, inner, width=1, border_radius=10)

        if self.output_scroll is None:
            self.output_scroll = ScrollArea(inner)
        else:
            self.output_scroll.set_rect(inner)

        content_h = self._compute_output_content_height(body_font, inner.width - 10)
        self.output_scroll.set_content_height(content_h)

        # Draw clipped scrolling text
        prev = self.output_scroll.begin_clip(surface)

        y = inner.y - self.output_scroll.offset
        line_h = body_font.get_height() + 4

        for raw in self.output_lines:
            for line in wrap_text(raw, body_font, inner.width - 10):
                if y + body_font.get_height() >= inner.y - line_h and y <= inner.bottom + line_h:
                    surface.blit(body_font.render(line, True, TEXT), (inner.x, y))
                y += line_h

        end_clip(surface, prev)
        self.output_scroll.draw_scrollbar(surface)

    # ---------- Actions ----------

    def open_take_modal(self) -> None:
        """Show a modal list of items in the current location."""
        loc = self.game.get_location()
        options = list(loc.items)
        if not options:
            self.begin_turn("Take")
            self.out("There is nothing to take here.")
            return

        def pick(item_name: str) -> None:
            """Pick a button"""
            self.begin_turn(f"Take {item_name}")
            if self.game.pick_up(item_name):
                self.out(f"Picked up: {item_name}")
            else:
                self.out(f"Could not take: {item_name}")

        self.modal = ModalPicker("Take which item?", options, pick)

    def open_drop_modal(self) -> None:
        """Show a modal list of items in inventory to drop."""
        options = [it.name for it in self.game.inventory]
        if not options:
            self.begin_turn("Drop")
            self.out("Your inventory is empty.")
            return

        def pick(item_name: str) -> None:
            """Pick a drop"""
            self.begin_turn(f"Drop {item_name}")
            if self.game.drop(item_name):
                self.out(f"Dropped: {item_name}")
                self.game.check_quest(item_name)

            else:
                self.out(f"Could not drop: {item_name}")

        self.modal = ModalPicker("Drop which item?", options, pick)

    def open_inspect_modal(self) -> None:
        """Show a modal list of items in inventory to inspect."""
        options = [it.name for it in self.game.inventory]
        if not options:
            self.begin_turn("Inspect")
            self.out("Your inventory is empty.")
            return

        def pick(item_name: str) -> None:
            """Pick an item"""
            self.begin_turn(f"Inspect {item_name}")
            it = self.game.get_item(item_name)
            self.out(it.hint)
            self.out("That item could not be inspected.")

        self.modal = ModalPicker("Inspect which item?", options, pick)

    def do_look(self) -> None:
        """Show long description and items."""
        self.begin_turn("Look")
        loc = self.game.get_location()
        self.out(loc.long_description)
        self.out("Items here: " + (", ".join(loc.items) if loc.items else "(none)"))

    def do_inventory(self) -> None:
        """Show inventory contents."""
        self.begin_turn("Inventory")
        if self.game.inventory:
            self.out("You are carrying:")
            for it in self.game.inventory:
                self.out(f"- {it.name}")
        else:
            self.out("Your inventory is empty.")

    def do_score(self) -> None:
        """Show score."""
        self.begin_turn("Score")
        self.out(f"Score: {self.game.score}")

    def do_log(self) -> None:
        """Print log to console and note it in UI."""
        self.begin_turn("Log")
        self.out(self.log.get_events_str())
        self.log.display_events()

    def do_quit(self) -> None:
        """Quit the game."""
        self.begin_turn("Quit")
        self.out("Quitting...")
        self.game.ongoing = False

    def do_move(self, command_key: str) -> None:
        """Perform a location command (moves location)."""
        loc = self.game.get_location()
        if command_key not in loc.available_commands:
            self.begin_turn(command_key)
            self.out("That action isn't available here.")
            return

        self.begin_turn(command_key)
        self.game.current_location_id = loc.available_commands[command_key]

        new_loc = self.game.get_location()
        self.log.add_event(Event(loc.id_num, loc.brief_description), command_key)
        self.game.turn += 1
        if self.game.max_turns == self.game.turn:
            if (self.game.score >= self.game.min_score and "lucky mug" in self.game.returned and
                    "usb drive" in self.game.returned and "laptop charger" in self.game.returned):
                self.win()
                return
            else:
                self.lose()
                return
        self.out(self.location_description())
        if new_loc.items:
            self.out("Items here: " + ", ".join(new_loc.items))

    def win(self) -> None:
        """Win the game."""
        self.out("Win")

    def lose(self) -> None:
        """Lose the game."""
        self.out("Lose")

    # ---------- Run loop ----------

    def run(self) -> None:
        """Run the UI main loop."""
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("CSC111 Adventure - ACORN UI")
        clock = pygame.time.Clock()

        title_font = pygame.font.SysFont("segoeui", 26, bold=True)
        label_font = pygame.font.SysFont("segoeui", 15, bold=True)
        body_font = pygame.font.SysFont("segoeui", 18)
        cmd_font = pygame.font.SysFont("segoeui", 16)
        chip_font = pygame.font.SysFont("segoeui", 14, bold=True)
        topbar_title_font = pygame.font.SysFont("segoeui", 21, bold=True)
        topbar_sub_font = pygame.font.SysFont("segoeui", 13)
        logo_font = pygame.font.SysFont("segoeui", 11, bold=True)

        logo_image: Optional[pygame.Surface] = None
        if LOGO_FILE.exists():
            raw_logo = pygame.image.load(str(LOGO_FILE)).convert_alpha()
            logo_image = pygame.transform.smoothscale(raw_logo, (62, 62))

        self.begin_turn("Start")
        self.out(self.location_description())

        running = True
        while running and self.game.ongoing:
            clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            pad = 20
            gap = 16
            topbar_h = 96

            left_w = 820
            right_w = screen.get_width() - (pad * 2) - left_w - gap

            panel_y = pad + topbar_h + 10
            panel_h = screen.get_height() - panel_y - pad
            left_panel = pygame.Rect(pad, panel_y, left_w, panel_h)
            right_panel = pygame.Rect(left_panel.right + gap, panel_y, right_w, left_panel.height)

            # LEFT cards
            header_h = 78
            desc_h = 210
            items_h = 64

            header_rect = pygame.Rect(left_panel.x, left_panel.y, left_panel.width, header_h)
            desc_rect = pygame.Rect(left_panel.x, header_rect.bottom + gap, left_panel.width, desc_h)
            items_rect = pygame.Rect(left_panel.x, desc_rect.bottom + gap, left_panel.width, items_h)

            output_top = items_rect.bottom + gap + 6
            out_rect = pygame.Rect(left_panel.x, output_top, left_panel.width, left_panel.bottom - output_top)

            # RIGHT cards
            map_h = 260
            map_rect = pygame.Rect(right_panel.x, right_panel.y, right_panel.width, map_h)
            actions_card = pygame.Rect(right_panel.x, map_rect.bottom + gap, right_panel.width,
                                       right_panel.height - map_h - gap)

            # Actions card inner scroll area (this is what scrolls independently)
            actions_header_h = 36
            actions_inner = pygame.Rect(actions_card.x + 16, actions_card.y + actions_header_h,
                                        actions_card.width - 32, actions_card.height - actions_header_h - 16)

            if self.actions_scroll is None:
                self.actions_scroll = ScrollArea(actions_inner)
            else:
                self.actions_scroll.set_rect(actions_inner)

            loc = self.game.get_location()
            cmd_keys = list(loc.available_commands.keys())

            # Build ALL action buttons in one scrollable "content space"
            # (So you can always scroll within Actions without anything overflowing.)
            btn_h = 34
            btn_gap = 9
            y = actions_inner.y  # content y starts at the scroll area's top in content-coordinates
            x = actions_inner.x
            w = actions_inner.width - 12  # leave room for scrollbar

            buttons: list[Button] = [Button(pygame.Rect(x, y, w, btn_h), "Take", self.open_take_modal, kind="primary")]

            # Section: Items
            y += btn_h + btn_gap
            buttons.append(Button(pygame.Rect(x, y, w, btn_h), "Drop", self.open_drop_modal, kind="secondary"))
            y += btn_h + btn_gap
            buttons.append(Button(pygame.Rect(x, y, w, btn_h), "Inspect", self.open_inspect_modal, kind="secondary"))
            y += btn_h + 14

            # Section: Menu
            buttons.append(Button(pygame.Rect(x, y, w, btn_h), "Look", self.do_look, kind="ghost"))
            y += btn_h + btn_gap
            buttons.append(Button(pygame.Rect(x, y, w, btn_h), "Inventory", self.do_inventory, kind="ghost"))
            y += btn_h + btn_gap
            buttons.append(Button(pygame.Rect(x, y, w, btn_h), "Score", self.do_score, kind="ghost"))
            y += btn_h + btn_gap
            buttons.append(Button(pygame.Rect(x, y, w, btn_h), "Log", self.do_log, kind="ghost"))
            y += btn_h + btn_gap
            buttons.append(Button(pygame.Rect(x, y, w, btn_h), "Quit", self.do_quit, kind="ghost"))
            y += btn_h + 16

            # Section: Move/Interact (two-column grid inside the scroll content)
            col_gap = 10
            col_w = (w - col_gap) // 2
            row_h = 30
            row_gap = 8

            start_y = y
            for i, cmd in enumerate(cmd_keys):
                col = i % 2
                row = i // 2
                bx = x + col * (col_w + col_gap)
                by = start_y + row * (row_h + row_gap)
                buttons.append(Button(pygame.Rect(bx, by, col_w, row_h),
                                      cmd.title(),
                                      lambda c=cmd: self.do_move(c),
                                      kind="secondary"))
            rows = (len(cmd_keys) + 1) // 2
            y = start_y + (rows * (row_h + row_gap) - (row_gap if rows > 0 else 0))

            # Update actions scroll content height
            content_h = max(1, (y - actions_inner.y) + 8)
            self.actions_scroll.set_content_height(content_h)

            # ---------------- Events ----------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.modal is not None:
                            self.modal.close()
                        else:
                            self.do_quit()

                elif event.type == pygame.MOUSEWHEEL:
                    if self.modal is not None:
                        self.modal.handle_wheel(mouse_pos, event.y)
                    else:
                        if self.output_scroll is not None:
                            self.output_scroll.handle_wheel(mouse_pos, event.y, speed=36)
                        if self.actions_scroll is not None:
                            self.actions_scroll.handle_wheel(mouse_pos, event.y, speed=36)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.modal is not None:
                        self.modal.handle_click(event.pos)
                    else:
                        # Click inside scrollable actions: shift by -offset
                        if self.actions_scroll is not None:
                            y_off = -self.actions_scroll.offset
                            for b in buttons:
                                b.handle_click(event.pos, y_offset=y_off)

            if self.modal is not None and not self.modal.is_open:
                self.modal = None

            # ---------------- Draw ----------------
            screen.blit(vertical_gradient(screen.get_size(), BG_TOP, BG_BOTTOM), (0, 0))

            topbar = pygame.Rect(0, 0, screen.get_width(), topbar_h + 8)
            pygame.draw.rect(screen, TOPBAR, topbar)
            pygame.draw.line(screen, UOFT_GOLD, (0, topbar.bottom - 2), (screen.get_width(), topbar.bottom - 2), 2)

            logo_x = pad + 4
            logo_y = topbar.centery - 31
            if logo_image is not None:
                screen.blit(logo_image, (logo_x, logo_y))
            else:
                draw_uoft_logo(screen, (pad + 34, topbar.centery), WHITE, UOFT_GOLD, logo_font)

            brand = topbar_title_font.render("University of Toronto", True, WHITE)
            subtitle = topbar_sub_font.render("CSC111 Adventure Portal", True, (226, 236, 250))
            screen.blit(brand, (pad + 84, 28))
            screen.blit(subtitle, (pad + 84, 58))

            draw_card(screen, left_panel, PANEL, radius=16)
            draw_card(screen, right_panel, PANEL, radius=16)

            # Header
            draw_card(screen, header_rect, CARD, radius=16)
            accent = pygame.Rect(header_rect.x + 2, header_rect.y + 2, 8, header_rect.height - 4)
            pygame.draw.rect(screen, UOFT_LIGHT_BLUE, accent, border_radius=6)

            header_title = title_font.render(loc.name, True, TEXT)
            screen.blit(header_title, (header_rect.x + 20, header_rect.y + 12))

            turns_left = self.game.max_turns - self.game.turn
            chips_y = header_rect.y + 44
            draw_chip(
                screen,
                pygame.Rect(header_rect.x + 20, chips_y, 114, 24),
                f"Location {loc.id_num}",
                chip_font,
                (235, 244, 255),
                TEXT_DIM
            )
            draw_chip(
                screen,
                pygame.Rect(header_rect.x + 142, chips_y, 102, 24),
                f"Score {self.game.score}",
                chip_font,
                (238, 252, 244),
                (27, 100, 75)
            )
            draw_chip(
                screen,
                pygame.Rect(header_rect.x + 252, chips_y, 118, 24),
                f"Moves left {turns_left}",
                chip_font,
                (255, 247, 233),
                (128, 78, 17)
            )

            # Description
            draw_card(screen, desc_rect, CARD, radius=16)
            screen.blit(label_font.render("DESCRIPTION", True, TEXT_DIM), (desc_rect.x + 18, desc_rect.y + 10))

            desc_text = loc.brief_description if getattr(loc, "visited", False) else loc.long_description
            lines = wrap_text(desc_text, body_font, desc_rect.width - 36)
            yy = desc_rect.y + 36
            for line in lines:
                if yy > desc_rect.bottom - 22:
                    break
                screen.blit(body_font.render(line, True, TEXT), (desc_rect.x + 18, yy))
                yy += 22

            # Items
            draw_card(screen, items_rect, CARD, radius=16)
            screen.blit(label_font.render("ITEMS HERE", True, TEXT_DIM), (items_rect.x + 18, items_rect.y + 10))
            if not loc.items:
                items_str = "(none)"
            else:
                shown = loc.items[:3]
                items_str = ", ".join(shown)
                if len(loc.items) > 3:
                    items_str += ", ..."
            screen.blit(body_font.render(items_str, True, TEXT), (items_rect.x + 18, items_rect.y + 32))

            # Output (scrollable)
            self.draw_output(screen, out_rect, label_font, body_font)

            # Minimap
            draw_card(screen, map_rect, CARD, radius=16)
            screen.blit(label_font.render("MINIMAP", True, TEXT_DIM), (map_rect.x + 18, map_rect.y + 10))
            map_inner = pygame.Rect(map_rect.x + 14, map_rect.y + 36, map_rect.width - 28, map_rect.height - 50)
            self.minimap.draw(screen, map_inner, loc.id_num)

            # Actions card + header
            draw_card(screen, actions_card, CARD, radius=16)
            screen.blit(label_font.render("ACTIONS", True, TEXT_DIM), (actions_card.x + 18, actions_card.y + 10))

            # Scrollable actions content, clipped so it stays "behind" the card
            if self.actions_scroll is not None:
                # Optional inner border to communicate it's a scroll area
                pygame.draw.rect(screen, BORDER_SOFT, actions_inner, width=2, border_radius=12)

                prev = self.actions_scroll.begin_clip(screen)
                y_off = -self.actions_scroll.offset

                for b in buttons:
                    rr = b.rect.move(0, y_off)
                    if rr.bottom < actions_inner.top or rr.top > actions_inner.bottom:
                        continue
                    # Choose font based on button type (grid uses smaller)
                    f = cmd_font if rr.height <= 30 else body_font
                    b.draw(screen, f, mouse_pos, y_offset=y_off)

                end_clip(screen, prev)
                self.actions_scroll.draw_scrollbar(screen)

            # Modal
            if self.modal is not None:
                self.modal.layout(screen.get_rect())
                self.modal.draw(screen, title_font, body_font, mouse_pos)

            pygame.display.flip()

        pygame.quit()


# =====================================================
# Entrypoint
# =====================================================

def run_pygame_ui(game_data_json: str = "game_data.json", initial_location_id: int = 1) -> None:
    """Create the game + UI and start the window."""
    game_log = EventList()
    game = AdventureGame(game_data_json, initial_location_id)
    ui = GameUI(game, game_log)
    ui.run()


if __name__ == "__main__":
    run_pygame_ui()
