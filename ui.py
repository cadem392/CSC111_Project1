"""
CSC111 Project 1: Text Adventure Game - Professional Pygame UI (UofT Theme)

Features added vs the basic UI:
- UofT color theme (blue/white + clean neutrals)
- Better typography, spacing, and “card” UI with shadows
- Hover/press animations for buttons
- Smooth fade transitions when changing locations
- Dedicated item action buttons:
    - Take -> opens a modal list of items at the location
    - Drop -> opens a modal list of inventory items
    - Inspect -> opens a modal list of inventory items
- Optional images (auto-load if present; otherwise graceful fallback):
    assets/
      bg.png              (optional background)
      logo.png            (optional UofT-ish icon/logo you provide)
      locations/<id>.png  (optional per-location image, like locations/1.png)

How to use:
1) Put this in `game_pygame_ui.py`
2) Update the import path for AdventureGame (below) to match your file name.
3) Run: python game_pygame_ui.py

NOTE:
- This UI does NOT require you to change your JSON format.
- It assumes your Location has: id_num, name, brief_description, long_description, visited, available_commands, items
- It assumes your Item has: name, hint (and __str__ prints nicely)
"""

from __future__ import annotations

import os
import math
import pygame
from dataclasses import dataclass
from typing import Optional, Callable, Sequence

# ---- CHANGE THIS IMPORT TO YOUR PROJECT FILE NAME ----
from adventure import AdventureGame  # e.g. if your class is in "game_manager.py"
from event_logger import Event, EventList


# =====================================================
# Theme (UofT-inspired)
# =====================================================

UOFT_BLUE = (0, 46, 93)        # UofT navy-ish
UOFT_LIGHT_BLUE = (0, 88, 163) # accent
UOFT_GOLD = (255, 205, 0)      # gold accent
INK = (12, 14, 18)             # near-black
PANEL = (18, 21, 28)           # dark panel
CARD = (24, 28, 36)            # card background
CARD_2 = (28, 33, 43)
BORDER = (70, 80, 100)
TEXT = (240, 244, 250)
TEXT_DIM = (190, 198, 212)
MUTED = (140, 150, 170)
SHADOW = (0, 0, 0, 110)


# =====================================================
# Utility drawing helpers
# =====================================================

def clamp(x: float, a: float, b: float) -> float:
    return a if x < a else b if x > b else x

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3

def draw_rounded_rect(surf: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int], radius: int) -> None:
    pygame.draw.rect(surf, color, rect, border_radius=radius)

def draw_shadow(surf: pygame.Surface, rect: pygame.Rect, radius: int = 16, spread: int = 8, alpha: int = 110) -> None:
    shadow_surf = pygame.Surface((rect.width + spread * 2, rect.height + spread * 2), pygame.SRCALPHA)
    r = pygame.Rect(spread, spread, rect.width, rect.height)
    pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), r, border_radius=radius)
    surf.blit(shadow_surf, (rect.x - spread, rect.y - spread))

def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        c = (
            int(lerp(top[0], bottom[0], t)),
            int(lerp(top[1], bottom[1], t)),
            int(lerp(top[2], bottom[2], t)),
        )
        pygame.draw.line(s, c, (0, y), (w, y))
    return s

def blur_fallback_glow_circle(surf: pygame.Surface, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> None:
    # cheap glow: multiple circles
    for i in range(6):
        r = int(radius * (1 + i * 0.25))
        a = int(alpha * (1 - i / 6))
        g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(g, (*color, a), (r, r), r)
        surf.blit(g, (center[0] - r, center[1] - r), special_flags=pygame.BLEND_PREMULTIPLIED)


# =====================================================
# UI Components
# =====================================================

@dataclass
class UIButton:
    rect: pygame.Rect
    label: str
    on_click: Callable[[], None]
    kind: str = "primary"  # primary/secondary/ghost
    enabled: bool = True

    # internal animation state
    hover_t: float = 0.0
    press_t: float = 0.0

    def update(self, dt: float, mouse_pos: tuple[int, int], mouse_down: bool) -> None:
        hovered = self.enabled and self.rect.collidepoint(mouse_pos)
        target_hover = 1.0 if hovered else 0.0
        self.hover_t = lerp(self.hover_t, target_hover, clamp(dt * 10, 0, 1))

        target_press = 1.0 if (hovered and mouse_down) else 0.0
        self.press_t = lerp(self.press_t, target_press, clamp(dt * 18, 0, 1))

    def handle_click(self, mouse_pos: tuple[int, int]) -> None:
        if self.enabled and self.rect.collidepoint(mouse_pos):
            self.on_click()

    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        r = self.rect.copy()
        # slight press "sink"
        r.y += int(self.press_t * 2)

        # style
        if self.kind == "primary":
            base = UOFT_BLUE
            accent = UOFT_LIGHT_BLUE
            text_color = (250, 250, 255)
        elif self.kind == "secondary":
            base = CARD_2
            accent = (40, 48, 64)
            text_color = TEXT
        else:  # ghost
            base = (0, 0, 0)
            accent = (0, 0, 0)
            text_color = TEXT

        if not self.enabled:
            base = (32, 36, 46)
            accent = (32, 36, 46)
            text_color = (150, 155, 165)

        # hover brighten
        t = self.hover_t
        bg = (
            int(lerp(base[0], accent[0], t)),
            int(lerp(base[1], accent[1], t)),
            int(lerp(base[2], accent[2], t)),
        )

        # shadow + border
        draw_shadow(surf, r, radius=14, spread=6, alpha=90 if self.enabled else 40)
        draw_rounded_rect(surf, r, bg, radius=14)

        if self.kind != "ghost":
            pygame.draw.rect(surf, (90, 105, 135), r, width=2, border_radius=14)
        else:
            # ghost hover outline
            if self.hover_t > 0.05:
                pygame.draw.rect(surf, (90, 105, 135), r, width=2, border_radius=14)

        # label
        txt = font.render(self.label, True, text_color)
        surf.blit(txt, txt.get_rect(center=r.center))


class ModalPicker:
    """A modal overlay that shows a list of options and lets user click one."""
    def __init__(self, title: str, options: Sequence[str], on_pick: Callable[[str], None]) -> None:
        self.title = title
        self.options = list(options)
        self.on_pick = on_pick
        self.open_t = 0.0
        self.closing = False

        self.scroll = 0
        self.buttons: list[UIButton] = []

    def start_close(self) -> None:
        self.closing = True

    def is_done(self) -> bool:
        return self.closing and self.open_t <= 0.01

    def update(self, dt: float, mouse_pos: tuple[int, int], mouse_down: bool) -> None:
        target = 0.0 if self.closing else 1.0
        speed = 10 if not self.closing else 14
        self.open_t = lerp(self.open_t, target, clamp(dt * speed, 0, 1))

        for b in self.buttons:
            b.update(dt, mouse_pos, mouse_down)

    def handle_wheel(self, dy: int) -> None:
        # dy: +/-1 steps
        self.scroll += dy * 32
        self.scroll = int(clamp(self.scroll, -9999, 9999))

    def handle_click(self, mouse_pos: tuple[int, int]) -> None:
        # Clicking outside panel closes
        for b in self.buttons:
            b.handle_click(mouse_pos)

    def layout(self, screen_rect: pygame.Rect, font: pygame.font.Font, small: pygame.font.Font) -> None:
        # Center panel
        w = min(640, int(screen_rect.width * 0.72))
        h = min(520, int(screen_rect.height * 0.72))
        x = screen_rect.centerx - w // 2
        y = screen_rect.centery - h // 2
        self.panel_rect = pygame.Rect(x, y, w, h)

        # Create option buttons (recreated each frame; simple)
        self.buttons = []

        pad = 18
        title_h = 54
        list_rect = pygame.Rect(x + pad, y + title_h, w - pad * 2, h - title_h - 72)

        # Option rows
        row_h = 44
        visible_rows = max(1, list_rect.height // (row_h + 10))

        max_scroll = max(0, (len(self.options) - visible_rows) * (row_h + 10))
        self.scroll = int(clamp(self.scroll, 0, max_scroll))

        start_idx = int(self.scroll // (row_h + 10))
        y0 = list_rect.y - int(self.scroll % (row_h + 10))

        def make_pick(opt: str) -> Callable[[], None]:
            return lambda: (self.on_pick(opt), self.start_close())

        for i in range(start_idx, len(self.options)):
            yy = y0 + (i - start_idx) * (row_h + 10)
            if yy > list_rect.bottom:
                break
            r = pygame.Rect(list_rect.x, yy, list_rect.width, row_h)
            self.buttons.append(UIButton(r, self.options[i], make_pick(self.options[i]), kind="secondary"))

        # Cancel button
        cancel_rect = pygame.Rect(x + pad, y + h - 54, 120, 36)
        self.buttons.append(UIButton(cancel_rect, "Cancel", self.start_close, kind="ghost"))

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, small: pygame.font.Font) -> None:
        # overlay fade
        t = ease_out_cubic(self.open_t)
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(140 * t)))
        surf.blit(overlay, (0, 0))

        # panel pop animation
        pr = self.panel_rect.copy()
        scale = lerp(0.96, 1.0, t)
        pr.width = int(pr.width * scale)
        pr.height = int(pr.height * scale)
        pr.center = self.panel_rect.center

        draw_shadow(surf, pr, radius=18, spread=10, alpha=120)
        draw_rounded_rect(surf, pr, CARD, radius=18)
        pygame.draw.rect(surf, (90, 105, 135), pr, width=2, border_radius=18)

        # Title
        title = font.render(self.title, True, TEXT)
        surf.blit(title, (pr.x + 18, pr.y + 14))

        # Buttons
        clip = surf.get_clip()
        inner = pygame.Rect(pr.x + 16, pr.y + 58, pr.width - 32, pr.height - 58 - 64)
        surf.set_clip(inner)
        for b in self.buttons:
            if b.label == "Cancel":
                continue
            b.draw(surf, small)
        surf.set_clip(clip)

        # Cancel
        for b in self.buttons:
            if b.label == "Cancel":
                b.draw(surf, small)


# =====================================================
# The Game UI
# =====================================================

class ProfessionalGameUI:
    def __init__(self, game: AdventureGame, game_log: EventList) -> None:
        self.game = game
        self.log = game_log

        # Fix common bug: class attributes used as instance state
        if not hasattr(self.game, "inventory") or self.game.inventory is AdventureGame.inventory:
            self.game.inventory = []
        if not hasattr(self.game, "score") or self.game.score is AdventureGame.score:
            self.game.score = 0

        self.menu = ["Look", "Inventory", "Score", "Log", "Quit"]
        self.messages: list[str] = []
        self.modal: Optional[ModalPicker] = None
        self.clear_output_each_choice = True
        self.max_history_lines = 12

        self.transition_t = 0.0
        self.transition_active = False
        self.prev_location_id: Optional[int] = None

        # Images (optional)
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.bg_img = self._load_image(os.path.join(self.assets_dir, "bg.png"))
        self.logo_img = self._load_image(os.path.join(self.assets_dir, "logo.png"))
        self.location_img_cache: dict[int, pygame.Surface] = {}

    def clear_output(self) -> None:
        self.messages.clear()

    def _load_image(self, path: str) -> Optional[pygame.Surface]:
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                return img
        except Exception:
            return None
        return None

    def _get_location_image(self, loc_id: int) -> Optional[pygame.Surface]:
        if loc_id in self.location_img_cache:
            return self.location_img_cache[loc_id]
        path = os.path.join(self.assets_dir, "locations", f"{loc_id}.png")
        img = self._load_image(path)
        if img is not None:
            self.location_img_cache[loc_id] = img
        return img

    def push(self, s: str) -> None:
        for line in s.split("\n"):
            if line.strip():
                self.messages.append(line.strip())
        self.messages = self.messages[-12:]

    def current_desc(self) -> str:
        loc = self.game.get_location()
        if getattr(loc, "visited", False):
            return loc.brief_description
        loc.visited = True
        return loc.long_description

    def start_transition(self) -> None:
        self.transition_active = True
        self.transition_t = 0.0

    def update_transition(self, dt: float) -> None:
        if not self.transition_active:
            return
        self.transition_t += dt * 3.0
        if self.transition_t >= 1.0:
            self.transition_t = 1.0
            self.transition_active = False

    def go_to_location(self, loc_id: int) -> None:
        self.prev_location_id = self.game.current_location_id
        self.game.current_location_id = loc_id
        self.start_transition()
        self.push(self.current_desc())
        new_loc = self.game.get_location()
        if getattr(new_loc, "items", None):
            if len(new_loc.items) > 0:
                self.push("Items here: " + ", ".join(new_loc.items))

    def begin_turn(self, choice_label: str) -> None:
        if self.clear_output_each_choice:
            self.clear_output()
        self.push(f"▶ You chose: {choice_label}")

    # ---------------- Commands ----------------

    def do_menu(self, label: str) -> None:
        self.begin_turn(label)  # <-- NEW (clears output each choice)
        label_lower = label.lower()
        loc = self.game.get_location()
        self.log.add_event(Event(loc.id_num, loc.brief_description), label_lower)

        if label_lower == "quit":
            self.game.ongoing = False
            self.push("Quitting...")
            return

        if label_lower == "look":
            self.push(loc.long_description)
            if len(loc.items) > 0:
                self.push("Items here: " + ", ".join(loc.items))
            else:
                self.push("No items here.")
            return

        if label_lower == "inventory":
            if self.game.inventory:
                inv = ", ".join([it.name for it in self.game.inventory])
                self.push("Inventory: " + inv)
            else:
                self.push("Inventory is empty.")
            return

        if label_lower == "score":
            self.push(f"Score: {self.game.score}")
            return

        if label_lower == "log":
            # Your EventList probably prints to console; here we show a friendly message.
            self.push("Opened log. (If EventList only prints, check console output.)")
            try:
                self.log.display_events()
            except Exception:
                pass
            return

    def open_take_modal(self) -> None:
        # NOTE: we don't clear output on opening the modal; only when an item is picked.
        loc = self.game.get_location()
        options = list(loc.items) if loc.items else []
        if not options:
            self.begin_turn("Take")
            self.push("Nothing to take here.")
            return

        def pick(item_name: str) -> None:
            self.begin_turn(f"Take {item_name}")  # <-- NEW (clears)
            if self.game.pick_up(item_name):
                self.push(f"Picked up: {item_name}")
            else:
                self.push(f"Couldn't take: {item_name}")

        self.modal = ModalPicker("Take which item?", options, pick)

    def open_drop_modal(self) -> None:
        options = [it.name for it in self.game.inventory]
        if not options:
            self.begin_turn("Drop")
            self.push("You have nothing to drop.")
            return

        def pick(item_name: str) -> None:
            self.begin_turn(f"Drop {item_name}")  # <-- NEW (clears)
            if self.game.drop(item_name):
                self.push(f"Dropped: {item_name}")
                try:
                    self.game.check_quest(item_name)
                except Exception:
                    pass
            else:
                self.push(f"Couldn't drop: {item_name}")

        self.modal = ModalPicker("Drop which item?", options, pick)

    def open_inspect_modal(self) -> None:
        options = [it.name for it in self.game.inventory]
        if not options:
            self.begin_turn("Inspect")
            self.push("You have nothing to inspect.")
            return

        def pick(item_name: str) -> None:
            self.begin_turn(f"Inspect {item_name}")  # <-- NEW (clears)
            try:
                it = self.game.get_item(item_name)
                self.push(f"{it.name}: {it.hint}")
            except Exception:
                self.push(f"Can't inspect: {item_name}")

        self.modal = ModalPicker("Inspect which item?", options, pick)

    def do_location_action(self, action: str) -> None:
        self.begin_turn(action)  # <-- NEW (clears output each choice)
        loc = self.game.get_location()
        if action not in loc.available_commands:
            self.push("Invalid action.")
            return
        nxt = loc.available_commands[action]
        self.go_to_location(nxt)

    # ---------------- Layout ----------------

    def build_buttons(self, screen_rect: pygame.Rect) -> tuple[list[UIButton], list[UIButton]]:
        w, h = screen_rect.size

        # Right panel
        panel_w = 380
        x = w - panel_w - 20
        y = 20
        right = pygame.Rect(x, y, panel_w, h - 40)

        # Top quick actions (Take/Drop/Inspect)
        qa_y = right.y + 72
        qa_h = 44
        qa_gap = 10
        qa_w = right.width - 36
        qa_x = right.x + 18

        quick: list[UIButton] = []
        quick.append(UIButton(pygame.Rect(qa_x, qa_y + 0 * (qa_h + qa_gap), qa_w, qa_h),
                              "Take", self.open_take_modal, kind="primary"))
        quick.append(UIButton(pygame.Rect(qa_x, qa_y + 1 * (qa_h + qa_gap), qa_w, qa_h),
                              "Drop", self.open_drop_modal, kind="secondary"))
        quick.append(UIButton(pygame.Rect(qa_x, qa_y + 2 * (qa_h + qa_gap), qa_w, qa_h),
                              "Inspect", self.open_inspect_modal, kind="secondary"))

        # Menu buttons
        menu_y = qa_y + 3 * (qa_h + qa_gap) + 18
        menu_h = 40
        menu_gap = 10

        menu_btns: list[UIButton] = []
        for i, lab in enumerate(self.menu):
            r = pygame.Rect(qa_x, menu_y + i * (menu_h + menu_gap), qa_w, menu_h)
            kind = "ghost" if lab in ("Log", "Inventory") else "secondary"
            if lab == "Quit":
                kind = "ghost"
            menu_btns.append(UIButton(r, lab, lambda l=lab: self.do_menu(l), kind=kind))

        # Location commands list below menu
        loc = self.game.get_location()
        cmds = list(loc.available_commands.keys())

        cmd_start = menu_btns[-1].rect.bottom + 18
        cmd_h = 38
        cmd_gap = 9
        for i, cmd in enumerate(cmds[:12]):  # clip to avoid overflow
            r = pygame.Rect(qa_x, cmd_start + i * (cmd_h + cmd_gap), qa_w, cmd_h)
            menu_btns.append(UIButton(r, cmd.title(), lambda c=cmd: self.do_location_action(c), kind="secondary"))

        return quick, menu_btns

    # ---------------- Rendering ----------------

    def draw_background(self, screen: pygame.Surface) -> None:
        w, h = screen.get_size()
        if self.bg_img is not None:
            img = pygame.transform.smoothscale(self.bg_img, (w, h))
            screen.blit(img, (0, 0))
            # add a dark overlay for readability
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
        else:
            # nice gradient
            g = vertical_gradient((w, h), (10, 12, 18), (6, 8, 12))
            screen.blit(g, (0, 0))
            # subtle glow accent
            blur_fallback_glow_circle(screen, (int(w * 0.25), int(h * 0.25)), 120, UOFT_LIGHT_BLUE, 80)
            blur_fallback_glow_circle(screen, (int(w * 0.70), int(h * 0.65)), 180, (40, 60, 110), 60)

    def draw_left_panel(self, screen: pygame.Surface, font: pygame.font.Font,
                        small: pygame.font.Font, tiny: pygame.font.Font) -> None:
        w, h = screen.get_size()
        right_panel_w = 420
        left = pygame.Rect(20, 20, w - right_panel_w - 60, h - 40)

        draw_shadow(screen, left, radius=18, spread=10, alpha=120)
        draw_rounded_rect(screen, left, PANEL, radius=18)
        pygame.draw.rect(screen, (60, 70, 95), left, width=2, border_radius=18)

        loc = self.game.get_location()

        # Header bar
        header = pygame.Rect(left.x + 16, left.y + 14, left.width - 32, 68)
        draw_rounded_rect(screen, header, CARD, radius=16)
        pygame.draw.rect(screen, (90, 105, 135), header, width=2, border_radius=16)

        # Optional logo
        if self.logo_img is not None:
            logo = pygame.transform.smoothscale(self.logo_img, (42, 42))
            screen.blit(logo, (header.x + 12, header.y + 13))
            title_x = header.x + 12 + 42 + 12
        else:
            # small gold dot accent
            pygame.draw.circle(screen, UOFT_GOLD, (header.x + 28, header.y + 34), 8)
            title_x = header.x + 48

        title = font.render(loc.name, True, TEXT)
        screen.blit(title, (title_x, header.y + 10))

        subtitle = tiny.render(f"Location ID: {loc.id_num}    •    Score: {self.game.score}", True, TEXT_DIM)
        screen.blit(subtitle, (title_x, header.y + 40))

        # Location image “card”
        img_card = pygame.Rect(left.x + 16, header.bottom + 14, min(360, left.width - 32), 200)
        draw_rounded_rect(screen, img_card, CARD, radius=16)
        pygame.draw.rect(screen, (90, 105, 135), img_card, width=2, border_radius=16)

        img = self._get_location_image(loc.id_num)
        if img is not None:
            # cover-fit
            iw, ih = img.get_size()
            scale = max(img_card.width / iw, img_card.height / ih)
            new_size = (int(iw * scale), int(ih * scale))
            scaled = pygame.transform.smoothscale(img, new_size)
            crop = scaled.subsurface(pygame.Rect(
                (scaled.get_width() - img_card.width) // 2,
                (scaled.get_height() - img_card.height) // 2,
                img_card.width,
                img_card.height
            ))
            # rounded clip
            mask = pygame.Surface(img_card.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=16)
            crop2 = crop.copy()
            crop2.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(crop2, (img_card.x, img_card.y))
        else:
            # placeholder art
            ph = tiny.render("Add assets/locations/<id>.png to show an image here", True, MUTED)
            screen.blit(ph, (img_card.x + 14, img_card.y + 14))
            # diagonal stripes
            stripe = pygame.Surface(img_card.size, pygame.SRCALPHA)
            for k in range(-img_card.height, img_card.width, 18):
                pygame.draw.line(stripe, (255, 255, 255, 18), (k, 0), (k + img_card.height, img_card.height), 6)
            screen.blit(stripe, img_card.topleft)

        # Description & items column next to image if wide
        text_area = pygame.Rect(img_card.right + 14, img_card.y, left.right - (img_card.right + 14) - 16, img_card.height)
        if text_area.width < 240:
            # stack below if too narrow
            text_area = pygame.Rect(left.x + 16, img_card.bottom + 14, left.width - 32, 170)

        draw_rounded_rect(screen, text_area, CARD, radius=16)
        pygame.draw.rect(screen, (90, 105, 135), text_area, width=2, border_radius=16)

        desc = loc.brief_description if getattr(loc, "visited", False) else loc.long_description
        self._draw_wrapped(screen, desc, small, TEXT, pygame.Rect(text_area.x + 14, text_area.y + 12,
                                                                  text_area.width - 28, text_area.height - 24))

        # Items pill row
        items_card = pygame.Rect(left.x + 16, max(img_card.bottom, text_area.bottom) + 14, left.width - 32, 58)
        draw_rounded_rect(screen, items_card, CARD, radius=16)
        pygame.draw.rect(screen, (90, 105, 135), items_card, width=2, border_radius=16)

        items_label = tiny.render("Items here", True, TEXT_DIM)
        screen.blit(items_label, (items_card.x + 14, items_card.y + 10))

        items_str = ", ".join(loc.items) if loc.items else "(none)"
        items_val = small.render(items_str, True, TEXT)
        screen.blit(items_val, (items_card.x + 14, items_card.y + 28))

        # Output card
        out_card = pygame.Rect(left.x + 16, items_card.bottom + 14, left.width - 32, left.bottom - (items_card.bottom + 14) - 16)
        draw_rounded_rect(screen, out_card, CARD, radius=16)
        pygame.draw.rect(screen, (90, 105, 135), out_card, width=2, border_radius=16)

        out_title = tiny.render("Output", True, TEXT_DIM)
        screen.blit(out_title, (out_card.x + 14, out_card.y + 10))

        # messages
        y = out_card.y + 32
        for line in self.messages[-11:]:
            t = small.render(line, True, TEXT)
            screen.blit(t, (out_card.x + 14, y))
            y += t.get_height() + 4

    def _draw_wrapped(self, surf: pygame.Surface, text: str, font: pygame.font.Font,
                      color: tuple[int, int, int], rect: pygame.Rect) -> None:
        words = text.split()
        lines: list[str] = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= rect.width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

        y = rect.y
        for line in lines:
            if y + font.get_height() > rect.bottom:
                break
            surf.blit(font.render(line, True, color), (rect.x, y))
            y += font.get_height() + 2

    def draw_right_panel(self, screen: pygame.Surface, font: pygame.font.Font,
                         small: pygame.font.Font, tiny: pygame.font.Font,
                         quick: list[UIButton], buttons: list[UIButton]) -> None:
        w, h = screen.get_size()
        right = pygame.Rect(w - 380 - 20, 20, 380, h - 40)

        draw_shadow(screen, right, radius=18, spread=10, alpha=120)
        draw_rounded_rect(screen, right, PANEL, radius=18)
        pygame.draw.rect(screen, (60, 70, 95), right, width=2, border_radius=18)

        header = font.render("Actions", True, TEXT)
        screen.blit(header, (right.x + 18, right.y + 16))
        sub = tiny.render("Movement + inventory tools", True, TEXT_DIM)
        screen.blit(sub, (right.x + 18, right.y + 46))

        # quick action card
        qa_card = pygame.Rect(right.x + 18, right.y + 64, right.width - 36, 200)
        draw_rounded_rect(screen, qa_card, CARD, radius=16)
        pygame.draw.rect(screen, (90, 105, 135), qa_card, width=2, border_radius=16)
        lab = tiny.render("Items", True, TEXT_DIM)
        screen.blit(lab, (qa_card.x + 14, qa_card.y + 12))

        # Draw quick buttons
        for b in quick:
            b.draw(screen, small)

        # divider
        pygame.draw.line(screen, (70, 80, 100), (right.x + 22, qa_card.bottom + 16), (right.right - 22, qa_card.bottom + 16), 2)

        # Buttons already laid out in build_buttons
        for b in buttons:
            b.draw(screen, small)

        # subtle gold accent at bottom
        pygame.draw.rect(screen, UOFT_GOLD, pygame.Rect(right.x + 18, right.bottom - 10, 90, 4), border_radius=2)

    def draw_transition(self, screen: pygame.Surface) -> None:
        if not self.transition_active and self.transition_t <= 0.0:
            return
        t = ease_out_cubic(self.transition_t)
        # fade overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(120 * (1 - t))))
        screen.blit(overlay, (0, 0))

    # ---------------- Main loop integration ----------------

    def update(self, dt: float, mouse_pos: tuple[int, int], mouse_down: bool,
               quick: list[UIButton], buttons: list[UIButton]) -> None:
        self.update_transition(dt)

        # modal updates
        if self.modal is not None:
            self.modal.update(dt, mouse_pos, mouse_down)
            if self.modal.is_done():
                self.modal = None
            return

        for b in quick:
            b.update(dt, mouse_pos, mouse_down)
        for b in buttons:
            b.update(dt, mouse_pos, mouse_down)

    def click(self, mouse_pos: tuple[int, int], quick: list[UIButton], buttons: list[UIButton]) -> None:
        if self.modal is not None:
            self.modal.handle_click(mouse_pos)
            return

        for b in quick:
            b.handle_click(mouse_pos)
        for b in buttons:
            b.handle_click(mouse_pos)

    def wheel(self, dy: int) -> None:
        if self.modal is not None:
            self.modal.handle_wheel(-dy)  # pygame dy: up is +1 typically depending on event

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, small: pygame.font.Font, tiny: pygame.font.Font,
             quick: list[UIButton], buttons: list[UIButton]) -> None:
        self.draw_background(screen)
        self.draw_left_panel(screen, font, small, tiny)
        self.draw_right_panel(screen, font, small, tiny, quick, buttons)

        # modal (if any)
        if self.modal is not None:
            self.modal.layout(screen.get_rect(), font, small)
            self.modal.draw(screen, font, small)

        self.draw_transition(screen)


# =====================================================
# Entrypoint
# =====================================================

def run_pygame_ui(game_data_json: str = "game_data.json", initial_location_id: int = 1) -> None:
    pygame.init()
    pygame.display.set_caption("CSC111 Adventure — UofT UI")

    W, H = 1280, 720
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    # Fonts (system)
    font = pygame.font.SysFont("arial", 28, bold=True)
    small = pygame.font.SysFont("arial", 20)
    tiny = pygame.font.SysFont("arial", 16)

    # Game
    log = EventList()
    game = AdventureGame(game_data_json, initial_location_id)
    ui = ProfessionalGameUI(game, log)

    ui.push(ui.current_desc())
    loc = game.get_location()
    if getattr(loc, "items", None) and len(loc.items) > 0:
        ui.push("Items here: " + ", ".join(loc.items))

    running = True
    mouse_down = False

    while running and game.ongoing:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        quick, buttons = ui.build_buttons(screen.get_rect())

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_down = True
                ui.click(mouse_pos, quick, buttons)

            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                mouse_down = False

            elif e.type == pygame.MOUSEWHEEL:
                ui.wheel(e.y)

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if ui.modal is not None:
                        ui.modal.start_close()
                    else:
                        game.ongoing = False

        ui.update(dt, mouse_pos, mouse_down, quick, buttons)
        ui.draw(screen, font, small, tiny, quick, buttons)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run_pygame_ui("game_data.json", 1)
