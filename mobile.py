"""Reuse the Python particle engine with native Chinese browser controls."""
from __future__ import annotations

import asyncio
import json
import math
import random
import sys

import pygame

from fireworks import FireworkShow, Spark, WEB_SIZE, clamp, hsv
from mobile_ui import BROWSER_UI

MOBILE_PATTERNS = ("heart", "ring", "willow")


class MobileShow(FireworkShow):
    """HTML handles fonts and input; Python handles particles and authoritative state."""

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.selected_pattern: str | None = None
        self.max_sparks = 2200
        self.particle_scale = 0.72
        self.max_rockets = 24
        self.caption_alpha = 0.0

    def _draw_touch_controls(self) -> None:
        # The Chinese toolbar is outside the shaking canvas.
        pass

    def launch(self, x=None, target_y=None, pattern=None, hue=None) -> None:
        if len(self.rockets) >= self.max_rockets:
            return
        pattern = pattern or self.selected_pattern
        if hue is None and pattern in MOBILE_PATTERNS:
            hue = {"heart": 0.96, "ring": 0.56, "willow": 0.115}[pattern]
        super().launch(x=x, target_y=target_y, pattern=pattern, hue=hue)

    def _heart(self, center: pygame.Vector2, hue: float) -> None:
        # Preserve parametric radii: normalizing every vector erases the heart.
        count = 120
        for i in range(count):
            angle = math.tau * i / count
            x = 16 * math.sin(angle) ** 3
            y = -(13 * math.cos(angle) - 5 * math.cos(2 * angle)
                  - 2 * math.cos(3 * angle) - math.cos(4 * angle))
            life = random.uniform(1.75, 2.15)
            self.sparks.append(Spark(
                center.copy(), pygame.Vector2(x, y) * 11.5,
                hsv(hue + random.uniform(-0.012, 0.012), 0.64, 1.0),
                life, life, 2.0, gravity=35, drag=0.989, glitter=True,
            ))

    def burst(self, rocket) -> None:
        first = len(self.sparks)
        super().burst(rocket)
        scale = clamp(min(self.size) / 540.0, 0.35, 1.3)
        for spark in self.sparks[first:]:
            spark.vel *= scale
            spark.gravity *= scale

    def reset_surface(self, screen: pygame.Surface) -> None:
        old_width, old_height = self.size
        new_width, new_height = screen.get_size()
        sx, sy = new_width / old_width, new_height / old_height
        for item in [*self.rockets, *self.sparks, *self.smoke]:
            item.pos.x *= sx
            item.pos.y *= sy
            item.vel.x *= sx
            item.vel.y *= sy
        for rocket in self.rockets:
            rocket.prev.x *= sx
            rocket.prev.y *= sy
            rocket.target_y *= sy
        super().reset_surface(screen)

    def dispatch(self, command: dict) -> None:
        """Accept known commands only; never execute input from the UI as code."""
        if not isinstance(command, dict):
            return
        action = command.get("action")
        if action == "pattern":
            pattern = command.get("pattern")
            if pattern not in MOBILE_PATTERNS:
                return
            self.selected_pattern = pattern
            self.launch(pattern=pattern, x=self.size[0] * 0.5,
                        target_y=self.size[1] * 0.35)
        elif action == "toggle-auto":
            self.autoplay = not self.autoplay
        elif action == "finale":
            self.finale()
        elif action == "launch":
            try:
                x, y = float(command["x"]), float(command["y"])
            except (KeyError, TypeError, ValueError):
                return
            if not (math.isfinite(x) and math.isfinite(y)):
                return
            self.launch(x=clamp(x, 0.04, 0.96) * self.size[0],
                        target_y=clamp(y, 0.08, 0.66) * self.size[1])

    def state_json(self) -> str:
        return json.dumps({"autoplay": self.autoplay, "pattern": self.selected_pattern})


def viewport_size(packet: dict, fallback: tuple[int, int]) -> tuple[int, int]:
    """Bound externally supplied sizes before allocating display surfaces."""
    try:
        width, height = int(packet["width"]), int(packet["height"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return fallback
    return max(160, min(width, 960)), max(160, min(height, 800))


async def run() -> None:
    if sys.platform != "emscripten":
        from fireworks import run as desktop_run
        await desktop_run()
        return

    import platform  # Pygbag supplies its synchronous JavaScript bridge here.

    platform.window.eval(BROWSER_UI)
    bridge = platform.window.fireworkMobile
    packet = json.loads(str(bridge.poll()))
    pygame.init()
    screen = pygame.display.set_mode(viewport_size(packet, WEB_SIZE))
    show = MobileShow(screen)
    clock = pygame.time.Clock()
    previous_state = ""
    running = True

    while running:
        # Yield to the browser instead of busy-waiting in clock.tick(60).
        dt = min(clock.tick(0) / 1000.0, 0.033)
        packet = json.loads(str(bridge.poll()))
        size = viewport_size(packet, show.size)
        if size != show.size:
            screen = pygame.display.set_mode(size)
            show.reset_surface(screen)
        for command in packet.get("actions", [])[:24]:
            show.dispatch(command)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                show.rockets.clear()
                show.sparks.clear()
                show.smoke.clear()
            # HTML buttons/sky own activation events. Ignore SDL's synthesized
            # mouse events, which otherwise make one touch trigger twice.
        show.update(dt)
        show.draw()
        pygame.display.flip()
        state = show.state_json()
        if state != previous_state:
            bridge.setState(state)
            previous_state = state
        await asyncio.sleep(0)
    pygame.quit()
