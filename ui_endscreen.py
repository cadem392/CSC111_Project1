"""End screen rendering and interaction for the CSC111 Pygame UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pygame

from adventure import AdventureGame
from ui_primitives import (
    BG_BOTTOM,
    BG_TOP,
    PANEL,
    TEXT,
    TEXT_DIM,
    Button,
    CardStyle,
    draw_card,
    vertical_gradient,
    wrap_text,
)

EVENT_QUIT = getattr(pygame, "QUIT", 0)
EVENT_KEYDOWN = getattr(pygame, "KEYDOWN", 0)
EVENT_MOUSEBUTTONDOWN = getattr(pygame, "MOUSEBUTTONDOWN", 0)
KEY_ESCAPE = getattr(pygame, "K_ESCAPE", 27)
KEY_Q = getattr(pygame, "K_q", ord("q"))


@dataclass()
class EndScreenSpec:
    """Configuration payload used to render an end screen."""
    title: str
    subtitle: str
    body_lines: list[str]
    accent: tuple[int, int, int]
    allow_keep_playing: bool = False


class EndScreenView:
    """Display and manage end-screen interactions."""
    game: AdventureGame
    _screen: pygame.Surface
    _fonts: dict[str, pygame.font.Font]
    _spec: Optional[EndScreenSpec]
    _lines: list[str]
    _mouse_pos: tuple[int, int]

    def __init__(self, game: AdventureGame) -> None:
        self.game = game
        self._screen = self._ensure_screen()
        self._fonts = self._create_fonts()
        self._spec = None
        self._lines = []
        self._mouse_pos = (0, 0)

    def _ensure_screen(self) -> pygame.Surface:
        """Return active display surface, creating one if needed."""
        screen = pygame.display.get_surface()
        if screen is not None:
            return screen
        return pygame.display.set_mode((1280, 720))

    def _create_fonts(self) -> dict[str, pygame.font.Font]:
        """Create font set used on end screens."""
        pygame.font.init()
        return {
            "title": pygame.font.SysFont("segoeui", 40, bold=True),
            "subtitle": pygame.font.SysFont("segoeui", 18, bold=True),
            "body": pygame.font.SysFont("segoeui", 18),
            "hint": pygame.font.SysFont("segoeui", 14),
        }

    def _summary_lines(self, spec: EndScreenSpec) -> list[str]:
        """Build score/turn summary lines for an end screen."""
        turns_used = getattr(self.game, "turn", 0)
        turns_max = self.game.MAX_TURNS
        score = getattr(self.game, "score", 0)
        min_score = self.game.MIN_SCORE
        returned = sorted(list(getattr(self.game, "returned", set())))
        returned_str = ", ".join(returned) if returned else "(none)"
        score_percent = (min(score, self.game.MAX_SCORE) / self.game.MAX_SCORE) * 100

        lines = list(spec.body_lines)
        lines.extend(
            [
                "",
                f"Score: {score} / {self.game.MAX_SCORE}",
                f"Project Grade: {score_percent:.1f}%",
                f"Win Threshold: {min_score} / {self.game.MAX_SCORE}",
            ]
        )
        if turns_max:
            lines.append(f"Turns used: {turns_used} / {turns_max}")
        lines.append(f"Returned: {returned_str}")
        return lines

    def _draw_centered_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        x_and_top: tuple[int, int],
    ) -> int:
        """Draw centered text and return the text bottom y-coordinate."""
        image = font.render(text, True, color)
        rect = image.get_rect(midtop=x_and_top)
        self._screen.blit(image, rect)
        return rect.bottom

    def _draw_body(self, card: pygame.Rect, center_x: int, start_y: int) -> int:
        """Draw wrapped body paragraphs and return the bottom y-coordinate."""
        body_font = self._fonts["body"]
        max_width = card.width - 90
        y = start_y
        for paragraph in self._lines:
            if paragraph == "":
                y += 10
                continue
            for line in wrap_text(paragraph, body_font, max_width):
                image = body_font.render(line, True, TEXT)
                rect = image.get_rect(midtop=(center_x, y))
                self._screen.blit(image, rect)
                y += 24
            y += 6
        return y

    def _draw_buttons(self, card: pygame.Rect, body_bottom: int) -> tuple[pygame.Rect, Optional[pygame.Rect]]:
        """Draw restart and optional keep buttons and return their rectangles."""
        assert self._spec is not None

        button_w = 220
        button_h = 46
        restart_top = max(card.bottom - 110, body_bottom + 24)

        restart_rect = pygame.Rect(0, 0, button_w, button_h)
        restart_rect.midtop = (card.centerx, restart_top)
        Button(restart_rect, "Restart Game", lambda: None, kind="primary").draw(
            self._screen,
            self._fonts["body"],
            self._mouse_pos,
        )

        keep_rect: Optional[pygame.Rect] = None
        if self._spec.allow_keep_playing:
            keep_rect = pygame.Rect(0, 0, button_w, button_h)
            keep_rect.midtop = (card.centerx, restart_rect.top - (button_h + 10))
            Button(keep_rect, "Keep Game", lambda: None, kind="primary").draw(
                self._screen,
                self._fonts["body"],
                self._mouse_pos,
            )

        return restart_rect, keep_rect

    def _draw_frame(self) -> tuple[pygame.Rect, Optional[pygame.Rect]]:
        """Draw one end-screen frame and return clickable button areas."""
        assert self._spec is not None

        self._screen.blit(vertical_gradient(self._screen.get_size(), BG_TOP, BG_BOTTOM), (0, 0))
        card = pygame.Rect(0, 0, 860, 620)
        card.center = (self._screen.get_width() // 2, self._screen.get_height() // 2)
        draw_card(self._screen, card, CardStyle(fill=PANEL, radius=18))

        accent_bar = pygame.Rect(card.x + 14, card.y + 14, 10, card.height - 28)
        pygame.draw.rect(self._screen, self._spec.accent, accent_bar, border_radius=8)

        center_x = card.centerx
        y = card.y + 44
        y = self._draw_centered_text(self._spec.title, self._fonts["title"], TEXT, (center_x, y)) + 10
        y = self._draw_centered_text(
            self._spec.subtitle,
            self._fonts["subtitle"],
            TEXT_DIM,
            (center_x, y),
        ) + 26

        body_bottom = self._draw_body(card, center_x, y)
        restart_rect, keep_rect = self._draw_buttons(card, body_bottom)

        hint = self._fonts["hint"].render("ESC / Q to quit", True, TEXT_DIM)
        self._screen.blit(hint, hint.get_rect(midbottom=(card.centerx, card.bottom - 18)))
        return restart_rect, keep_rect

    def _click_action(
        self,
        pos: tuple[int, int],
        restart_rect: pygame.Rect,
        keep_rect: Optional[pygame.Rect],
    ) -> Optional[str]:
        """Return action selected by click, if any."""
        if restart_rect.collidepoint(pos):
            return "restart"
        if keep_rect is not None and keep_rect.collidepoint(pos):
            return "keep"
        return None

    def _process_events(self, restart_rect: pygame.Rect, keep_rect: Optional[pygame.Rect]) -> Optional[str]:
        """Process events and return end-screen action when chosen."""
        for event in pygame.event.get():
            if event.type == EVENT_QUIT:
                return "quit"
            if event.type == EVENT_KEYDOWN and event.key in {KEY_ESCAPE, KEY_Q}:
                return "quit"
            if event.type == EVENT_MOUSEBUTTONDOWN and event.button == 1:
                action = self._click_action(event.pos, restart_rect, keep_rect)
                if action is not None:
                    return action
        return None

    def show(self, spec: EndScreenSpec) -> Optional[str]:
        """Display an end screen and return restart/keep/quit action."""
        self._spec = spec
        self._lines = self._summary_lines(spec)
        clock = pygame.time.Clock()

        while True:
            clock.tick(60)
            self._mouse_pos = pygame.mouse.get_pos()
            restart_rect, keep_rect = self._draw_frame()
            action = self._process_events(restart_rect, keep_rect)
            pygame.display.flip()
            if action is not None:
                return action

        return None


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
