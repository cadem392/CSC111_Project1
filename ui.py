"""Pygame UI for the CSC111 text adventure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, TypedDict

import pygame

from game_entities import Location
from adventure import AdventureGame, DEFAULT_START_LOCATION
from event_logger import Event, EventList
from ui_endscreen import EndScreenSpec, EndScreenView
from ui_primitives import (
    BG_BOTTOM,
    BG_TOP,
    BORDER_SOFT,
    CARD,
    CARD_2,
    LOGO_FILE,
    PANEL,
    TEXT,
    TEXT_DIM,
    TOPBAR,
    UOFT_GOLD,
    UOFT_LIGHT_BLUE,
    WHITE,
    Button,
    CardStyle,
    ChipStyle,
    MiniMap,
    ModalPicker,
    ScrollArea,
    draw_card,
    draw_chip,
    draw_uoft_logo,
    end_clip,
    vertical_gradient,
    wrap_text,
)

PYGAME_INIT = getattr(pygame, "init")
PYGAME_QUIT = getattr(pygame, "quit")
EVENT_QUIT = getattr(pygame, "QUIT", 0)
EVENT_KEYDOWN = getattr(pygame, "KEYDOWN", 0)
EVENT_MOUSEBUTTONDOWN = getattr(pygame, "MOUSEBUTTONDOWN", 0)
EVENT_MOUSEWHEEL = getattr(pygame, "MOUSEWHEEL", 0)
KEY_ESCAPE = getattr(pygame, "K_ESCAPE", 27)
KEY_Q = getattr(pygame, "K_q", ord("q"))


@dataclass(frozen=True)
class ActionArea:
    """Geometry for the actions scroll area."""
    x: int
    y: int
    width: int


class UIFonts(TypedDict):
    """Strongly-typed font dictionary for the main UI."""
    title: pygame.font.Font
    label: pygame.font.Font
    body: pygame.font.Font
    cmd: pygame.font.Font
    chip: pygame.font.Font
    topbar_title: pygame.font.Font
    topbar_sub: pygame.font.Font
    logo: pygame.font.Font


class UILayout(TypedDict):
    """Strongly-typed layout dictionary for card geometry."""
    pad: int
    topbar_height: int
    left_panel: pygame.Rect
    right_panel: pygame.Rect
    header_rect: pygame.Rect
    desc_rect: pygame.Rect
    items_rect: pygame.Rect
    output_rect: pygame.Rect
    map_rect: pygame.Rect
    actions_card: pygame.Rect
    actions_inner: pygame.Rect


class UIFrame(TypedDict):
    """Strongly-typed draw-frame context."""
    surface: pygame.Surface
    layout: UILayout
    fonts: UIFonts
    logo_image: Optional[pygame.Surface]
    buttons: list[Button]
    mouse_pos: tuple[int, int]


class GameUI:
    """Main Pygame UI loop and rendering."""
    game: AdventureGame
    log: EventList
    modal: Optional[ModalPicker]
    minimap: MiniMap
    output_lines: list[str]
    output_scroll: Optional[ScrollArea]
    actions_scroll: Optional[ScrollArea]

    def __init__(self, game: AdventureGame, log: EventList) -> None:
        self.game = game
        self.log = log

        self.game.inventory = list(getattr(self.game, "inventory", []))
        self.game.score = int(getattr(self.game, "score", 0))

        self.modal = None
        self.minimap = MiniMap(game)
        self.output_lines = []
        self.output_scroll = None
        self.actions_scroll = None

    def begin_turn(self, label: str) -> None:
        """Clear output and begin a new action."""
        self.output_lines = [f"You chose: {label}"]
        if self.output_scroll is not None:
            self.output_scroll.offset = 0

    def out(self, text: str) -> None:
        """Append text to the current turn output."""
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                self.output_lines.append(stripped)

    def location_description(self) -> str:
        """Return the correct location description and update visited."""
        location = self.game.get_location()
        if getattr(location, "visited", False):
            return location.description['brief_description']
        location.visited = True
        return location.description['long_description']

    def _compute_output_content_height(self, body_font: pygame.font.Font, inner_width: int) -> int:
        """Compute the pixel height of output content (wrapped)."""
        line_height = body_font.get_height() + 4
        wrapped: list[str] = []
        for raw in self.output_lines:
            wrapped.extend(wrap_text(raw, body_font, inner_width))
        return max(1, len(wrapped) * line_height)

    def draw_output(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label_font: pygame.font.Font,
        body_font: pygame.font.Font
    ) -> None:
        """Draw a scrollable output card with proper clipping."""
        draw_card(surface, rect, CardStyle(fill=CARD, radius=16))
        label = label_font.render("OUTPUT", True, TEXT_DIM)
        surface.blit(label, (rect.x + 18, rect.y + 10))

        header_height = 34
        inner = pygame.Rect(rect.x + 18, rect.y + header_height, rect.width - 36, rect.height - header_height - 16)
        pygame.draw.rect(surface, CARD_2, inner, border_radius=10)
        pygame.draw.rect(surface, BORDER_SOFT, inner, width=1, border_radius=10)

        if self.output_scroll is None:
            self.output_scroll = ScrollArea(inner)
        else:
            self.output_scroll.set_rect(inner)

        content_height = self._compute_output_content_height(body_font, inner.width - 10)
        self.output_scroll.set_content_height(content_height)

        previous_clip = self.output_scroll.begin_clip(surface)
        y = inner.y - self.output_scroll.offset
        line_height = body_font.get_height() + 4

        for raw in self.output_lines:
            for line in wrap_text(raw, body_font, inner.width - 10):
                if y + body_font.get_height() >= inner.y - line_height and y <= inner.bottom + line_height:
                    surface.blit(body_font.render(line, True, TEXT), (inner.x, y))
                y += line_height

        end_clip(surface, previous_clip)
        self.output_scroll.draw_scrollbar(surface)

    def open_take_modal(self) -> None:
        """Show a modal list of items in the current location."""
        location = self.game.get_location()
        options = list(location.items)
        if not options:
            self.begin_turn("Take")
            self.out("There is nothing to take here.")
            return

        def pick(item_name: str) -> None:
            self.begin_turn(f"Take {item_name}")
            if self.game.pick_up(item_name):
                self.out(f"Picked up: {item_name}")
            else:
                self.out(f"Could not take: {item_name}")

        self.modal = ModalPicker("Take which item?", options, pick)

    def open_drop_modal(self) -> None:
        """Show a modal list of items in inventory to drop."""
        options = [item.name for item in self.game.inventory]
        if not options:
            self.begin_turn("Drop")
            self.out("Your inventory is empty.")
            return

        def pick(item_name: str) -> None:
            self.begin_turn(f"Drop {item_name}")
            if not self.game.drop(item_name):
                self.out(f"Could not drop: {item_name}")
                return

            completed = self.game.check_quest(item_name)
            reward_messages = self.game.apply_location_rewards(item_name)

            if completed:
                dropped_item = self.game.get_item(item_name)
                completion_text = dropped_item.completion_text if dropped_item is not None else ""
                self.out(completion_text)
                self.out(f"Your score is now {self.game.score}")

            if reward_messages:
                for reward_message in reward_messages:
                    self.out(reward_message)
            elif not completed:
                self.out(f"Dropped: {item_name}")

        self.modal = ModalPicker("Drop which item?", options, pick)

    def open_inspect_modal(self) -> None:
        """Show a modal list of items in inventory to inspect."""
        options = [item.name for item in self.game.inventory]
        if not options:
            self.begin_turn("Inspect")
            self.out("Your inventory is empty.")
            return

        def pick(item_name: str) -> None:
            self.begin_turn(f"Inspect {item_name}")
            item = self.game.get_item(item_name)
            if item is None:
                self.out("That item could not be inspected.")
                return
            self.out(item.hint)
            target_location = self.game.get_location(item.target_position).description['name']
            self.out(f"..... It needs to go to {target_location}")

        self.modal = ModalPicker("Inspect which item?", options, pick)

    def do_look(self) -> None:
        """Show long description and items."""
        self.begin_turn("Look")
        location = self.game.get_location()
        self.out(location.description['long_description'])
        self.out("Items here: " + (", ".join(location.items) if location.items else "(none)"))

    def do_inventory(self) -> None:
        """Show inventory contents."""
        self.begin_turn("Inventory")
        if self.game.inventory:
            self.out("You are carrying:")
            for item in self.game.inventory:
                self.out(f"- {item.name}")
            return
        self.out("Your inventory is empty.")

    def do_score(self) -> None:
        """Show score."""
        self.begin_turn("Score")
        grade_percent = (min(self.game.score, self.game.MAX_SCORE) / self.game.MAX_SCORE) * 100
        self.out(f"Score: {self.game.score}/{self.game.MAX_SCORE} ({grade_percent:.1f}%)")

    def do_log(self) -> None:
        """Print log to console and note it in UI."""
        self.begin_turn("Log")
        self.out(self.log.get_events_str())
        self.log.display_events()

    def do_quit(self) -> None:
        """Quit the game."""
        self.begin_turn("Quit")
        self.out("Quitting...")
        self.modal = None
        self.game.request_quit()
        self.game.ongoing = False

    def do_submit(self) -> None:
        """Attempt early submission."""
        self.begin_turn("Submit Early")
        if self.game.submit_early():
            self.out("Submission sent. Ending run...")
        else:
            self.out("Submission already finalized. Keep exploring.")

    def do_move(self, command_key: str) -> None:
        """Perform a location command (moves location)."""
        current_location = self.game.get_location()
        if command_key not in current_location.available_commands:
            self.begin_turn(command_key)
            self.out("That action isn't available here.")
            return

        next_location_id = current_location.available_commands[command_key]
        can_enter, reason = self.game.can_enter_location(next_location_id)
        if not can_enter:
            self.begin_turn(command_key)
            if reason is not None:
                self.out(reason)
            return

        self.begin_turn(command_key)
        self.game.current_location_id = next_location_id
        event = Event(current_location.id_num, current_location.description['brief_description'])
        self.log.add_event(event, command_key)

        if not self.game.is_unlimited_moves():
            self.game.turn += 1
            if self.game.MAX_TURNS <= self.game.turn:
                self.game.ongoing = False
                return

        new_location = self.game.get_location()
        self.out(self.location_description())
        if new_location.items:
            self.out("Items here: " + ", ".join(new_location.items))

    def _reset_ui_after_restart(self) -> None:
        """Reset transient UI state after a game restart."""
        self.actions_scroll = None
        self.output_scroll = None
        self.modal = None

    def _apply_end_action(self, action: str, can_keep: bool) -> None:
        """Apply selected end-screen action to game/UI state."""
        if action == "restart":
            self.game.reset()
            self._reset_ui_after_restart()
            self.begin_turn("Start")
            self.out(self.location_description())
            self.game.ongoing = True
            return

        if action == "keep" and can_keep:
            self.game.enable_unlimited_moves()
            self.game.lock_score()
            self.begin_turn("Explore Mode")
            self.out("Explore mode enabled. Moves are now unlimited and your score is locked.")
            self.game.ongoing = True
            return

        self.game.request_quit()
        self.game.ongoing = False

    def win(self) -> None:
        """Show win screen and apply player action."""
        spec = EndScreenSpec(
            title="You made it.",
            subtitle="Submission secured. Disaster avoided.",
            body_lines=[
                "You return to your room with the essentials in hand.",
                "The USB clicks in. The charger light turns on. The lucky mug sits by the keyboard.",
                "For once, your code is the quietest thing in the room.",
            ],
            accent=UOFT_LIGHT_BLUE,
            allow_keep_playing=True,
        )
        action = EndScreenView(self.game).show(spec)
        self._apply_end_action(action, can_keep=True)

    def lose(self) -> None:
        """Show lose screen and apply player action."""
        missing = self.game.missing_win_items()
        if self.game.score < self.game.MIN_SCORE:
            reason = f"Score too low: {self.game.score}/{self.game.MIN_SCORE}."
        elif missing:
            reason = "Missing: " + ", ".join(missing) + "."
        else:
            reason = "Something went wrong."

        spec = EndScreenSpec(
            title="Not this time.",
            subtitle=reason,
            body_lines=[
                "The clock wins. The campus keeps moving anyway.",
                "You stare at the screen like it might forgive you.",
                "It doesn't.",
            ],
            accent=(180, 60, 60),
            allow_keep_playing=False,
        )
        action = EndScreenView(self.game).show(spec)
        self._apply_end_action(action, can_keep=False)

    def _create_fonts(self) -> UIFonts:
        """Create all fonts used in the main UI."""
        return {
            "title": pygame.font.SysFont("segoeui", 26, bold=True),
            "label": pygame.font.SysFont("segoeui", 15, bold=True),
            "body": pygame.font.SysFont("segoeui", 18),
            "cmd": pygame.font.SysFont("segoeui", 16),
            "chip": pygame.font.SysFont("segoeui", 14, bold=True),
            "topbar_title": pygame.font.SysFont("segoeui", 21, bold=True),
            "topbar_sub": pygame.font.SysFont("segoeui", 13),
            "logo": pygame.font.SysFont("segoeui", 11, bold=True),
        }

    def _load_logo(self) -> Optional[pygame.Surface]:
        """Load and scale logo image if available."""
        if not LOGO_FILE.exists():
            return None
        raw_logo = pygame.image.load(str(LOGO_FILE)).convert_alpha()
        return pygame.transform.smoothscale(raw_logo, (62, 62))

    def _build_panels(
        self,
        screen: pygame.Surface,
        pad: int,
        gap: int,
        topbar_height: int,
    ) -> tuple[pygame.Rect, pygame.Rect]:
        """Build outer left/right panel rectangles."""
        left_width = 820
        right_width = screen.get_width() - (pad * 2) - left_width - gap
        panel_y = pad + topbar_height + 10
        panel_height = screen.get_height() - panel_y - pad
        left_panel = pygame.Rect(pad, panel_y, left_width, panel_height)
        right_panel = pygame.Rect(left_panel.right + gap, panel_y, right_width, panel_height)
        return left_panel, right_panel

    def _build_left_cards(
        self,
        left_panel: pygame.Rect,
        gap: int,
    ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect]:
        """Build left panel card rectangles."""
        header_rect = pygame.Rect(left_panel.x, left_panel.y, left_panel.width, 78)
        desc_rect = pygame.Rect(left_panel.x, header_rect.bottom + gap, left_panel.width, 70)
        items_rect = pygame.Rect(left_panel.x, desc_rect.bottom + gap, left_panel.width, 64)
        output_top = items_rect.bottom + gap + 6
        output_rect = pygame.Rect(left_panel.x, output_top, left_panel.width, left_panel.bottom - output_top)
        return header_rect, desc_rect, items_rect, output_rect

    def _build_right_cards(self, right_panel: pygame.Rect, gap: int) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        """Build right panel card rectangles."""
        map_rect = pygame.Rect(right_panel.x, right_panel.y, right_panel.width, 260)
        actions_height = right_panel.height - 260 - gap
        actions_card = pygame.Rect(right_panel.x, map_rect.bottom + gap, right_panel.width, actions_height)
        actions_inner = pygame.Rect(
            actions_card.x + 16,
            actions_card.y + 36,
            actions_card.width - 32,
            actions_card.height - 52,
        )
        return map_rect, actions_card, actions_inner

    def _build_layout(self, screen: pygame.Surface) -> UILayout:
        """Compute card geometry for the current window size."""
        pad = 20
        gap = 16
        topbar_height = 96
        left_panel, right_panel = self._build_panels(screen, pad, gap, topbar_height)
        header_rect, desc_rect, items_rect, output_rect = self._build_left_cards(left_panel, gap)
        map_rect, actions_card, actions_inner = self._build_right_cards(right_panel, gap)

        return {
            "pad": pad,
            "topbar_height": topbar_height,
            "left_panel": left_panel,
            "right_panel": right_panel,
            "header_rect": header_rect,
            "desc_rect": desc_rect,
            "items_rect": items_rect,
            "output_rect": output_rect,
            "map_rect": map_rect,
            "actions_card": actions_card,
            "actions_inner": actions_inner,
        }

    def _ensure_actions_scroll(self, actions_inner: pygame.Rect) -> None:
        """Initialize or update independent scroll state for actions panel."""
        if self.actions_scroll is None:
            self.actions_scroll = ScrollArea(actions_inner)
        else:
            self.actions_scroll.set_rect(actions_inner)

    def _append_ghost_button(
        self,
        buttons: list[Button],
        rect: pygame.Rect,
        label: str,
        callback: Callable[[], None],
    ) -> None:
        """Append one ghost-style full-width action row."""
        buttons.append(Button(rect, label, callback, kind="ghost"))

    def _add_inventory_buttons(self, buttons: list[Button], area: ActionArea, y: int) -> int:
        """Add Take/Drop/Inspect section buttons."""
        buttons.append(Button(pygame.Rect(area.x, y, area.width, 34), "Take", self.open_take_modal, kind="primary"))
        y += 43
        buttons.append(Button(pygame.Rect(area.x, y, area.width, 34), "Drop", self.open_drop_modal, kind="secondary"))
        y += 43
        buttons.append(
            Button(pygame.Rect(area.x, y, area.width, 34), "Inspect", self.open_inspect_modal, kind="secondary")
        )
        y += 43
        return y + 5

    def _add_menu_buttons(self, buttons: list[Button], area: ActionArea, y: int) -> int:
        """Add Look/Inventory/Score/Log/Submit/Quit section buttons."""
        self._append_ghost_button(buttons, pygame.Rect(area.x, y, area.width, 34), "Look", self.do_look)
        y += 43
        self._append_ghost_button(buttons, pygame.Rect(area.x, y, area.width, 34), "Inventory", self.do_inventory)
        y += 43
        self._append_ghost_button(buttons, pygame.Rect(area.x, y, area.width, 34), "Score", self.do_score)
        y += 43
        self._append_ghost_button(buttons, pygame.Rect(area.x, y, area.width, 34), "Log", self.do_log)
        y += 43

        submit_enabled = self.game.can_submit_early()
        submit_label = "Submit Early" if submit_enabled else "Already Submitted"
        buttons.append(
            Button(
                pygame.Rect(area.x, y, area.width, 34),
                submit_label,
                self.do_submit,
                kind="ghost",
                enabled=submit_enabled,
            )
        )
        y += 43
        self._append_ghost_button(buttons, pygame.Rect(area.x, y, area.width, 34), "Quit", self.do_quit)
        y += 43
        return y + 7

    def _fixed_direction_positions(self) -> dict[str, tuple[int, int]]:
        """Return fixed grid positions for cardinal direction buttons."""
        return {
            "go east": (0, 1),
            "go west": (0, 0),
            "go south": (1, 0),
            "go north": (1, 1),
        }

    def _move_callback(self, command_name: str) -> Callable[[], None]:
        """Return a callback that executes a movement command."""
        def callback() -> None:
            self.do_move(command_name)

        return callback

    def _add_direction_buttons(
        self,
        buttons: list[Button],
        start_y: int,
        area: ActionArea,
        command_keys: list[str],
    ) -> int:
        """Add fixed-direction movement buttons then extra movement commands."""
        col_width = (area.width - 10) // 2

        fixed_positions = self._fixed_direction_positions()
        for command_name, (row, col) in fixed_positions.items():
            if command_name not in command_keys:
                continue
            buttons.append(
                Button(
                    pygame.Rect(area.x + col * (col_width + 10), start_y + row * 38, col_width, 30),
                    command_name.title(),
                    self._move_callback(command_name),
                    kind="secondary",
                )
            )

        y = start_y + 78 + 10
        remaining_commands = [cmd for cmd in command_keys if cmd not in fixed_positions]
        for index, command_name in enumerate(remaining_commands):
            col = index % 2
            row = index // 2
            buttons.append(
                Button(
                    pygame.Rect(area.x + col * (col_width + 10), y + row * 38, col_width, 30),
                    command_name.title(),
                    self._move_callback(command_name),
                    kind="secondary",
                )
            )

        rows = (len(remaining_commands) + 1) // 2
        y += rows * 38
        if rows > 0:
            y -= 8
        return y

    def _build_action_buttons(self, actions_inner: pygame.Rect) -> list[Button]:
        """Build all action buttons and update actions content height."""
        location = self.game.get_location()
        commands = list(location.available_commands.keys())
        area = ActionArea(actions_inner.x, actions_inner.y, actions_inner.width - 12)

        buttons: list[Button] = []
        y = area.y
        y = self._add_inventory_buttons(buttons, area, y)
        y = self._add_menu_buttons(buttons, area, y)
        y = self._add_direction_buttons(buttons, y, area, commands)

        if self.actions_scroll is not None:
            content_height = max(1, (y - actions_inner.y) + 8)
            self.actions_scroll.set_content_height(content_height)
        return buttons

    def _handle_click(self, click_pos: tuple[int, int], buttons: list[Button]) -> None:
        """Handle left-click events in either modal or actions panel."""
        if self.modal is not None:
            self.modal.handle_click(click_pos)
            return

        if self.actions_scroll is None:
            return
        y_offset = -self.actions_scroll.offset
        for button in buttons:
            button.handle_click(click_pos, y_offset=y_offset)

    def _handle_wheel(self, mouse_pos: tuple[int, int], wheel_y: int) -> None:
        """Handle wheel events for whichever scroll region is hovered."""
        if self.modal is not None:
            self.modal.handle_wheel(mouse_pos, wheel_y)
            return
        if self.output_scroll is not None:
            self.output_scroll.handle_wheel(mouse_pos, wheel_y, speed=36)
        if self.actions_scroll is not None:
            self.actions_scroll.handle_wheel(mouse_pos, wheel_y, speed=36)

    def _process_events(self, buttons: list[Button], mouse_pos: tuple[int, int]) -> bool:
        """Process frame events and return whether the loop should continue."""
        running = True
        for event in pygame.event.get():
            if event.type == EVENT_QUIT:
                running = False
            elif event.type == EVENT_KEYDOWN:
                running = self._handle_keydown(event.key, running)
            elif event.type == EVENT_MOUSEWHEEL:
                self._handle_wheel(mouse_pos, event.y)
            elif event.type == EVENT_MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos, buttons)
            if self.game.is_quit_requested():
                return False
        return running

    def _handle_keydown(self, key: int, running: bool) -> bool:
        """Handle keydown and return updated running state."""
        if key != KEY_ESCAPE:
            return running

        if self.modal is not None:
            self.modal.close()
            return running

        self.do_quit()
        return running

    def _draw_topbar(self, frame: UIFrame) -> None:
        """Draw top branding bar."""
        surface = frame["surface"]
        fonts = frame["fonts"]
        layout = frame["layout"]
        logo_image = frame["logo_image"]
        topbar_height = layout["topbar_height"]
        pad = layout["pad"]

        topbar = pygame.Rect(0, 0, surface.get_width(), topbar_height + 8)
        pygame.draw.rect(surface, TOPBAR, topbar)
        pygame.draw.line(surface, UOFT_GOLD, (0, topbar.bottom - 2), (surface.get_width(), topbar.bottom - 2), 2)

        logo_x = layout["pad"] + 4
        logo_y = topbar.centery - 31
        if logo_image is not None:
            surface.blit(logo_image, (logo_x, logo_y))
        else:
            draw_uoft_logo(surface, (layout["pad"] + 34, topbar.centery), WHITE, UOFT_GOLD, fonts["logo"])

        brand = fonts["topbar_title"].render("University of Toronto", True, WHITE)
        subtitle = fonts["topbar_sub"].render("CSC111 Adventure Portal", True, (226, 236, 250))
        surface.blit(brand, (pad + 84, 28))
        surface.blit(subtitle, (pad + 84, 58))

    def _draw_header(self, frame: UIFrame, location: Location) -> None:
        """Draw location header card with status chips."""
        surface = frame["surface"]
        fonts = frame["fonts"]
        layout = frame["layout"]
        rect = layout["header_rect"]

        draw_card(surface, rect, CardStyle(fill=CARD, radius=16))
        accent = pygame.Rect(rect.x + 2, rect.y + 2, 8, rect.height - 4)
        pygame.draw.rect(surface, UOFT_LIGHT_BLUE, accent, border_radius=6)

        title = fonts["title"].render(location.description['name'], True, TEXT)
        surface.blit(title, (rect.x + 20, rect.y + 12))

        turns_left = self.game.MAX_TURNS - self.game.turn
        move_chip_text = "Moves Unlimited" if self.game.is_unlimited_moves() else f"Moves left {turns_left}"
        chips_y = rect.y + 44

        draw_chip(
            surface,
            pygame.Rect(rect.x + 20, chips_y, 114, 24),
            f"Location {location.id_num}",
            fonts["chip"],
            ChipStyle(fill=(235, 244, 255), text_color=TEXT_DIM),
        )
        draw_chip(
            surface,
            pygame.Rect(rect.x + 142, chips_y, 102, 24),
            f"Score {self.game.score}",
            fonts["chip"],
            ChipStyle(fill=(238, 252, 244), text_color=(27, 100, 75)),
        )
        draw_chip(
            surface,
            pygame.Rect(rect.x + 252, chips_y, 156, 24),
            move_chip_text,
            fonts["chip"],
            ChipStyle(fill=(255, 247, 233), text_color=(128, 78, 17)),
        )

    def _description_text(self, location: Location) -> str:
        """Return long or brief description based on visited flag."""
        if getattr(location, "visited", False):
            return location.description['brief_description']
        return location.description['long_description']

    def _draw_description_card(self, frame: UIFrame, location: Location) -> None:
        """Draw location description card."""
        surface = frame["surface"]
        fonts = frame["fonts"]
        layout = frame["layout"]
        rect = layout["desc_rect"]
        label_font = fonts["label"]
        body_font = fonts["body"]

        draw_card(surface, rect, CardStyle(fill=CARD, radius=16))
        surface.blit(label_font.render("DESCRIPTION", True, TEXT_DIM), (rect.x + 18, rect.y + 10))

        lines = wrap_text(self._description_text(location), body_font, rect.width - 36)
        y = rect.y + 36
        for line in lines:
            if y > rect.bottom - 22:
                break
            surface.blit(body_font.render(line, True, TEXT), (rect.x + 18, y))
            y += 22

    def _draw_items_card(self, frame: UIFrame, location: Location) -> None:
        """Draw current-location item summary card."""
        surface = frame["surface"]
        fonts = frame["fonts"]
        layout = frame["layout"]
        rect = layout["items_rect"]
        label_font = fonts["label"]
        body_font = fonts["body"]

        draw_card(surface, rect, CardStyle(fill=CARD, radius=16))
        surface.blit(label_font.render("ITEMS HERE", True, TEXT_DIM), (rect.x + 18, rect.y + 10))

        if not location.items:
            items_text = "(None)"
        else:
            shown = location.items[:3]
            items_text = ", ".join(shown).capitalize()
            if len(location.items) > 3:
                items_text += ", ..."
        surface.blit(body_font.render(items_text, True, TEXT), (rect.x + 18, rect.y + 32))

    def _draw_left_panel(self, frame: UIFrame, location: Location) -> None:
        """Draw left-side cards."""
        surface = frame["surface"]
        layout = frame["layout"]
        fonts = frame["fonts"]

        left_panel = layout["left_panel"]
        output_rect = layout["output_rect"]

        draw_card(surface, left_panel, CardStyle(fill=PANEL, radius=16))
        self._draw_header(frame, location)
        self._draw_description_card(frame, location)
        self._draw_items_card(frame, location)
        self.draw_output(surface, output_rect, fonts["label"], fonts["body"])

    def _draw_actions(self, frame: UIFrame) -> None:
        """Draw actions card with independent scrolling."""
        surface = frame["surface"]
        layout = frame["layout"]
        fonts = frame["fonts"]
        buttons = frame["buttons"]
        mouse_pos = frame["mouse_pos"]
        actions_card = layout["actions_card"]
        actions_inner = layout["actions_inner"]

        draw_card(surface, actions_card, CardStyle(fill=CARD, radius=16))
        surface.blit(fonts["label"].render("ACTIONS", True, TEXT_DIM), (actions_card.x + 18, actions_card.y + 10))

        if self.actions_scroll is None:
            return

        pygame.draw.rect(surface, BORDER_SOFT, actions_inner, width=2, border_radius=12)
        previous_clip = self.actions_scroll.begin_clip(surface)
        y_offset = -self.actions_scroll.offset

        for button in buttons:
            shifted = button.rect.move(0, y_offset)
            if shifted.bottom < actions_inner.top or shifted.top > actions_inner.bottom:
                continue
            font = fonts["cmd"] if shifted.height <= 30 else fonts["body"]
            button.draw(surface, font, mouse_pos, y_offset=y_offset)

        end_clip(surface, previous_clip)
        self.actions_scroll.draw_scrollbar(surface)

    def _draw_right_panel(self, frame: UIFrame, location: Location) -> None:
        """Draw right-side minimap and actions."""
        surface = frame["surface"]
        layout = frame["layout"]
        fonts = frame["fonts"]

        right_panel = layout["right_panel"]
        map_rect = layout["map_rect"]

        draw_card(surface, right_panel, CardStyle(fill=PANEL, radius=16))

        draw_card(surface, map_rect, CardStyle(fill=CARD, radius=16))
        surface.blit(fonts["label"].render("MINIMAP", True, TEXT_DIM), (map_rect.x + 18, map_rect.y + 10))
        map_inner = pygame.Rect(map_rect.x + 14, map_rect.y + 36, map_rect.width - 28, map_rect.height - 50)
        self.minimap.draw(surface, map_inner, location.id_num)

        self._draw_actions(frame)

    def _draw_frame(self, frame: UIFrame) -> None:
        """Draw one main-loop frame."""
        surface = frame["surface"]
        fonts = frame["fonts"]
        mouse_pos = frame["mouse_pos"]

        location = self.game.get_location()
        surface.blit(vertical_gradient(surface.get_size(), BG_TOP, BG_BOTTOM), (0, 0))
        self._draw_topbar(frame)
        self._draw_left_panel(frame, location)
        self._draw_right_panel(frame, location)

        if self.modal is not None:
            self.modal.layout(surface.get_rect())
            self.modal.draw(surface, fonts["title"], fonts["body"], mouse_pos)

    def _cleanup_modal(self) -> None:
        """Drop modal object after it is closed."""
        if self.modal is not None and not self.modal.is_open:
            self.modal = None

    def _resolve_end_state(self, running: bool) -> bool:
        """Handle win/lose/quit transitions and return updated running state."""
        if self.game.ongoing:
            return running

        if self.game.is_quit_requested():
            return False

        reached_turn_cap = not self.game.is_unlimited_moves() and self.game.turn >= self.game.MAX_TURNS
        if reached_turn_cap:
            self.lose()
        elif self.game.score >= self.game.MIN_SCORE and self.game.has_required_returns():
            self.win()
        else:
            self.lose()

        if self.game.is_quit_requested():
            return False
        return running

    def run(self) -> None:
        """Run the UI main loop."""
        PYGAME_INIT()
        screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("CSC111 Adventure - ACORN UI")

        fonts = self._create_fonts()
        logo_image = self._load_logo()
        clock = pygame.time.Clock()

        self.begin_turn("Start")
        self.out(self.location_description())

        running = True
        while running:
            clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            layout = self._build_layout(screen)
            actions_inner = layout["actions_inner"]
            self._ensure_actions_scroll(actions_inner)
            buttons = self._build_action_buttons(actions_inner)
            frame: UIFrame = {
                "surface": screen,
                "layout": layout,
                "fonts": fonts,
                "logo_image": logo_image,
                "buttons": buttons,
                "mouse_pos": mouse_pos,
            }

            running = self._process_events(buttons, mouse_pos)
            if not running or self.game.is_quit_requested():
                break
            self._cleanup_modal()
            self._draw_frame(frame)
            pygame.display.flip()

            running = self._resolve_end_state(running)
            if not running:
                break

        PYGAME_QUIT()


def run_pygame_ui(game_data_json: str = "game_data.json", initial_location_id: int = DEFAULT_START_LOCATION) -> None:
    """Create the game + UI and start the window."""
    game_log = EventList()
    game = AdventureGame(game_data_json, initial_location_id)
    ui = GameUI(game, game_log)
    ui.run()


if __name__ == "__main__":
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
    run_pygame_ui()
