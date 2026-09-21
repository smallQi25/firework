from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass

import pygame

DESKTOP_SIZE = (1280, 720)
WEB_SIZE = (960, 540)
FPS = 60
GRAVITY = 145.0
AIR_DRAG = 0.992
IS_WEB = sys.platform in {"emscripten", "wasi"}

Color = tuple[int, int, int]


def hsv(h: float, s: float = 1.0, v: float = 1.0) -> Color:
    color = pygame.Color(0)
    color.hsva = ((h % 1.0) * 360.0, s * 100.0, v * 100.0, 100.0)
    return color.r, color.g, color.b


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass
class Spark:
    pos: pygame.Vector2
    vel: pygame.Vector2
    color: Color
    life: float
    max_life: float
    size: float = 2.0
    gravity: float = GRAVITY
    drag: float = AIR_DRAG
    glitter: bool = False
    ember: bool = False
    trail: bool = True

    def update(self, dt: float) -> bool:
        self.life -= dt
        if self.life <= 0:
            return False

        drag_factor = self.drag ** (dt * FPS)
        self.vel.x *= drag_factor
        self.vel.y *= drag_factor
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        return self.pos.y < 900

    def draw(self, canvas: pygame.Surface, glow: pygame.Surface) -> None:
        ratio = clamp(self.life / self.max_life, 0.0, 1.0)
        flicker = 0.58 + 0.42 * math.sin(self.life * 42.0 + self.pos.x * 0.08)
        alpha = int(255 * ratio * (flicker if self.glitter else 1.0))
        if alpha <= 3:
            return

        px, py = int(self.pos.x), int(self.pos.y)
        radius = max(1, int(self.size * (0.7 + 0.55 * ratio)))

        if self.trail and self.vel.length_squared() > 30:
            direction = self.vel.normalize() * (8 + self.size * 2.5)
            tail = self.pos - direction
            pygame.draw.line(
                canvas,
                (*self.color, max(18, alpha // 2)),
                (px, py),
                (int(tail.x), int(tail.y)),
                max(1, radius),
            )

        pygame.draw.circle(canvas, (*self.color, alpha), (px, py), radius)
        glow_radius = radius * (5 if self.ember else 3)
        pygame.draw.circle(
            glow,
            (*self.color, max(6, alpha // (5 if self.ember else 7))),
            (px, py),
            glow_radius,
        )


@dataclass
class Smoke:
    pos: pygame.Vector2
    vel: pygame.Vector2
    life: float
    max_life: float
    size: float

    def update(self, dt: float) -> bool:
        self.life -= dt
        if self.life <= 0:
            return False
        self.pos += self.vel * dt
        self.vel *= 0.985 ** (dt * FPS)
        self.size += 7.0 * dt
        return True

    def draw(self, canvas: pygame.Surface) -> None:
        ratio = clamp(self.life / self.max_life, 0.0, 1.0)
        alpha = int(32 * ratio)
        shade = int(58 + 68 * ratio)
        pygame.draw.circle(
            canvas,
            (shade, shade, shade + 8, alpha),
            (int(self.pos.x), int(self.pos.y)),
            max(2, int(self.size)),
        )


class Rocket:
    def __init__(
        self,
        x: float,
        start_y: float,
        target_y: float,
        hue: float,
        pattern: str,
    ):
        self.pos = pygame.Vector2(x, start_y)
        self.prev = self.pos.copy()
        self.vel = pygame.Vector2(random.uniform(-22, 22), random.uniform(-600, -515))
        self.target_y = target_y
        self.hue = hue
        self.color = hsv(hue, 0.5, 1.0)
        self.pattern = pattern

    def update(self, dt: float, trail: list[Spark], smoke: list[Smoke]) -> bool:
        self.prev = self.pos.copy()
        self.vel.y += 92.0 * dt
        self.pos += self.vel * dt

        for _ in range(2):
            trail.append(
                Spark(
                    pos=self.pos + pygame.Vector2(
                        random.uniform(-2, 2),
                        random.uniform(-2, 2),
                    ),
                    vel=pygame.Vector2(
                        random.uniform(-28, 28),
                        random.uniform(70, 130),
                    ),
                    color=(255, random.randint(165, 225), 80),
                    life=random.uniform(0.20, 0.38),
                    max_life=0.38,
                    size=random.uniform(1.2, 2.4),
                    gravity=35,
                    drag=0.965,
                    glitter=True,
                    ember=True,
                )
            )

        if random.random() < 0.11:
            smoke.append(
                Smoke(
                    self.pos.copy(),
                    pygame.Vector2(
                        random.uniform(-7, 7),
                        random.uniform(12, 25),
                    ),
                    0.9,
                    0.9,
                    random.uniform(2.0, 4.0),
                )
            )

        return self.pos.y <= self.target_y or self.vel.y >= -55

    def draw(self, canvas: pygame.Surface, glow: pygame.Surface) -> None:
        pygame.draw.line(
            canvas,
            (*self.color, 220),
            (int(self.prev.x), int(self.prev.y)),
            (int(self.pos.x), int(self.pos.y)),
            2,
        )
        point = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(canvas, (255, 244, 205, 255), point, 3)
        pygame.draw.circle(glow, (*self.color, 42), point, 18)


class FireworkShow:
    PATTERNS = ("chrysanthemum", "ring", "willow", "palm", "heart")

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.size = screen.get_size()
        self.canvas = pygame.Surface(self.size, pygame.SRCALPHA)
        self.glow = pygame.Surface(self.size, pygame.SRCALPHA)
        self.rockets: list[Rocket] = []
        self.sparks: list[Spark] = []
        self.smoke: list[Smoke] = []
        self.stars = self._build_stars(125 if IS_WEB else 165)
        self.elapsed = 0.0
        self.next_launch = 0.25
        self.autoplay = True
        self.shake = 0.0
        self.caption_alpha = 255.0
        self.max_sparks = 2200 if IS_WEB else 4200
        self.particle_scale = 0.72 if IS_WEB else 1.0

    def _build_stars(self, count: int) -> list[tuple[float, float, float, float]]:
        width, height = self.size
        return [
            (
                random.uniform(0, width),
                random.uniform(0, height * 0.73),
                random.uniform(0.55, 1.55),
                random.uniform(0, math.tau),
            )
            for _ in range(count)
        ]

    def reset_surface(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.size = screen.get_size()
        self.canvas = pygame.Surface(self.size, pygame.SRCALPHA)
        self.glow = pygame.Surface(self.size, pygame.SRCALPHA)
        self.stars = self._build_stars(125 if IS_WEB else 165)

    def launch(
        self,
        x: float | None = None,
        target_y: float | None = None,
        pattern: str | None = None,
        hue: float | None = None,
    ) -> None:
        width, height = self.size
        x = x if x is not None else random.uniform(width * 0.14, width * 0.86)
        target_y = (
            target_y
            if target_y is not None
            else random.uniform(height * 0.13, height * 0.54)
        )
        self.rockets.append(
            Rocket(
                x=x,
                start_y=height + 8,
                target_y=target_y,
                hue=random.random() if hue is None else hue,
                pattern=pattern or random.choice(self.PATTERNS),
            )
        )

    def finale(self) -> None:
        width, height = self.size
        count = 7 if IS_WEB else 9
        base_hue = random.random()
        for i in range(count):
            x = width * ((i + 1) / (count + 1)) + random.uniform(-18, 18)
            self.launch(
                x=x,
                target_y=random.uniform(height * 0.12, height * 0.46),
                pattern=self.PATTERNS[i % len(self.PATTERNS)],
                hue=base_hue + i * 0.075,
            )
        self.shake = max(self.shake, 6.0)

    def burst(self, rocket: Rocket) -> None:
        center = rocket.pos.copy()
        hue = rocket.hue

        if rocket.pattern == "ring":
            self._radial(center, hue, count=120, speed=(190, 245), ring=True)
        elif rocket.pattern == "willow":
            self._radial(
                center,
                hue,
                count=145,
                speed=(110, 225),
                life=(2.6, 4.0),
                gravity=82,
                drag=0.986,
                glitter=True,
            )
        elif rocket.pattern == "palm":
            self._palm(center, hue)
        elif rocket.pattern == "heart":
            self._heart(center, hue)
        else:
            self._radial(
                center,
                hue,
                count=155,
                speed=(105, 285),
                life=(1.3, 2.2),
                glitter=True,
            )

        for _ in range(16 if IS_WEB else 22):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(25, 95)
            self.sparks.append(
                Spark(
                    center.copy(),
                    pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                    (255, 235, 190),
                    random.uniform(0.28, 0.65),
                    0.65,
                    random.uniform(1.0, 2.0),
                    gravity=70,
                    drag=0.96,
                    glitter=True,
                    ember=True,
                )
            )

        for _ in range(6 if IS_WEB else 9):
            self.smoke.append(
                Smoke(
                    center
                    + pygame.Vector2(
                        random.uniform(-5, 5),
                        random.uniform(-5, 5),
                    ),
                    pygame.Vector2(
                        random.uniform(-18, 18),
                        random.uniform(-12, 12),
                    ),
                    random.uniform(1.0, 1.8),
                    1.8,
                    random.uniform(5, 12),
                )
            )

        self.shake = max(self.shake, 3.2)

    def _radial(
        self,
        center: pygame.Vector2,
        hue: float,
        *,
        count: int,
        speed: tuple[float, float],
        life: tuple[float, float] = (1.25, 2.0),
        gravity: float = GRAVITY,
        drag: float = AIR_DRAG,
        ring: bool = False,
        glitter: bool = False,
    ) -> None:
        count = max(24, int(count * self.particle_scale))
        for i in range(count):
            angle = (i / count) * math.tau + random.uniform(-0.018, 0.018)
            velocity = random.uniform(*speed)
            if not ring:
                velocity *= random.uniform(0.55, 1.0)

            tint = hsv(
                hue + random.uniform(-0.035, 0.035),
                random.uniform(0.58, 0.95),
                1.0,
            )
            spark_life = random.uniform(*life)
            self.sparks.append(
                Spark(
                    center.copy(),
                    pygame.Vector2(math.cos(angle), math.sin(angle)) * velocity,
                    tint,
                    spark_life,
                    spark_life,
                    random.uniform(1.3, 2.8),
                    gravity=gravity,
                    drag=drag,
                    glitter=glitter or random.random() < 0.18,
                    ember=random.random() < 0.23,
                )
            )

    def _palm(self, center: pygame.Vector2, hue: float) -> None:
        arms = 9 if IS_WEB else random.randint(9, 13)
        steps = 6 if IS_WEB else 8

        for i in range(arms):
            angle = (i / arms) * math.tau + random.uniform(-0.08, 0.08)
            speed = random.uniform(210, 285)
            base = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed

            for step in range(steps):
                velocity = (
                    base * random.uniform(0.66, 1.0)
                    + pygame.Vector2(
                        random.uniform(-20, 20),
                        random.uniform(-20, 20),
                    )
                )
                spark_life = random.uniform(1.4, 2.4)
                self.sparks.append(
                    Spark(
                        center.copy(),
                        velocity,
                        hsv(hue + step * 0.006, 0.72, 1.0),
                        spark_life,
                        spark_life,
                        random.uniform(1.7, 2.7),
                        gravity=155,
                        drag=0.987,
                        glitter=True,
                    )
                )

    def _heart(self, center: pygame.Vector2, hue: float) -> None:
        count = 105 if IS_WEB else 150

        for i in range(count):
            t = math.tau * i / count
            x = 16 * math.sin(t) ** 3
            y = -(
                13 * math.cos(t)
                - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t)
                - math.cos(4 * t)
            )
            direction = pygame.Vector2(x, y)
            if direction.length_squared() > 0:
                direction = direction.normalize()

            spark_life = random.uniform(1.4, 2.1)
            self.sparks.append(
                Spark(
                    center.copy(),
                    direction * random.uniform(155, 235)
                    + pygame.Vector2(
                        random.uniform(-8, 8),
                        random.uniform(-8, 8),
                    ),
                    hsv(
                        hue + random.uniform(-0.025, 0.025),
                        0.66,
                        1.0,
                    ),
                    spark_life,
                    spark_life,
                    random.uniform(1.4, 2.5),
                    gravity=118,
                    drag=0.989,
                    glitter=True,
                )
            )

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.caption_alpha = max(0.0, self.caption_alpha - 20.0 * dt)

        if self.autoplay and self.elapsed >= self.next_launch:
            self.launch()
            delay = random.uniform(0.40, 0.96)
            if random.random() < 0.16:
                delay *= 0.48
            self.next_launch = self.elapsed + delay

        alive_rockets: list[Rocket] = []
        for rocket in self.rockets:
            if rocket.update(dt, self.sparks, self.smoke):
                self.burst(rocket)
            else:
                alive_rockets.append(rocket)
        self.rockets = alive_rockets

        self.sparks = [spark for spark in self.sparks if spark.update(dt)]
        self.smoke = [cloud for cloud in self.smoke if cloud.update(dt)]

        if len(self.sparks) > self.max_sparks:
            self.sparks = self.sparks[-self.max_sparks :]
        if len(self.smoke) > 220:
            self.smoke = self.smoke[-220:]

        self.shake *= 0.86 ** (dt * FPS)

    def _draw_background(self) -> None:
        width, height = self.size
        self.screen.fill((2, 3, 14))

        bands = 20
        for i in range(bands):
            y0 = int(height * i / bands)
            y1 = int(height * (i + 1) / bands)
            t = i / max(1, bands - 1)
            color = (
                int(2 + 6 * t),
                int(3 + 5 * t),
                int(14 + 15 * t),
            )
            pygame.draw.rect(
                self.screen,
                color,
                (0, y0, width, y1 - y0 + 1),
            )

        for x, y, size, phase in self.stars:
            twinkle = 0.45 + 0.55 * (
                0.5
                + 0.5
                * math.sin(
                    self.elapsed * (1.2 + size) + phase,
                )
            )
            c = int(155 + 95 * twinkle)
            pygame.draw.circle(
                self.screen,
                (c, c, min(255, c + 14)),
                (int(x), int(y)),
                max(1, int(size)),
            )

        horizon = int(height * 0.90)
        pygame.draw.rect(
            self.screen,
            (3, 4, 8),
            (0, horizon, width, height - horizon),
        )

        skyline_rng = random.Random(12)
        x = 0
        while x < width:
            building_width = skyline_rng.randint(22, 58)
            building_height = skyline_rng.randint(18, 78)
            pygame.draw.rect(
                self.screen,
                (4, 5, 10),
                (
                    x,
                    horizon - building_height,
                    building_width,
                    building_height,
                ),
            )
            x += building_width + skyline_rng.randint(2, 8)

    def control_rects(self) -> dict[str, pygame.Rect]:
        width, height = self.size
        button_h = max(48, int(height * 0.09))
        button_w = max(96, int(width * 0.12))
        gap = max(10, int(width * 0.012))
        margin = max(14, int(width * 0.018))
        y = height - button_h - margin

        auto_rect = pygame.Rect(
            width - button_w - margin,
            y,
            button_w,
            button_h,
        )
        finale_rect = pygame.Rect(
            auto_rect.left - gap - button_w,
            y,
            button_w,
            button_h,
        )
        return {
            "finale": finale_rect,
            "auto": auto_rect,
        }

    def _draw_touch_controls(self) -> None:
        font_size = max(18, int(self.size[1] * 0.036))
        font = pygame.font.Font(None, font_size)
        rects = self.control_rects()

        for name, rect in rects.items():
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            active = name == "auto" and self.autoplay
            fill = (46, 62, 110, 195) if active else (15, 18, 36, 180)
            border = (166, 189, 255, 175)
            pygame.draw.rect(
                panel,
                fill,
                panel.get_rect(),
                border_radius=15,
            )
            pygame.draw.rect(
                panel,
                border,
                panel.get_rect(),
                width=2,
                border_radius=15,
            )

            label = (
                "AUTO ON"
                if name == "auto" and self.autoplay
                else "AUTO OFF"
                if name == "auto"
                else "FINALE"
            )
            text = font.render(label, True, (242, 246, 255))
            panel.blit(
                text,
                text.get_rect(center=panel.get_rect().center),
            )
            self.screen.blit(panel, rect.topleft)

    def draw(self) -> None:
        self._draw_background()
        self.canvas.fill((0, 0, 0, 0))
        self.glow.fill((0, 0, 0, 0))

        for cloud in self.smoke:
            cloud.draw(self.canvas)
        for rocket in self.rockets:
            rocket.draw(self.canvas, self.glow)
        for spark in self.sparks:
            spark.draw(self.canvas, self.glow)

        self.screen.blit(
            self.glow,
            (0, 0),
            special_flags=pygame.BLEND_RGBA_ADD,
        )
        self.screen.blit(self.canvas, (0, 0))
        self._draw_touch_controls()

        if self.caption_alpha > 2:
            title_font = pygame.font.Font(
                None,
                max(26, int(self.size[1] * 0.055)),
            )
            hint_font = pygame.font.Font(
                None,
                max(18, int(self.size[1] * 0.034)),
            )

            title = title_font.render(
                "PYTHON FIREWORKS",
                True,
                (235, 240, 255),
            )
            hint_text = (
                "Tap the sky to launch  •  FINALE for a big show  •  AUTO toggles autoplay"
                if IS_WEB
                else "Click: launch  •  Space: finale  •  A: autoplay  •  F11: fullscreen"
            )
            hint = hint_font.render(
                hint_text,
                True,
                (158, 168, 196),
            )
            title.set_alpha(int(self.caption_alpha))
            hint.set_alpha(int(self.caption_alpha))
            self.screen.blit(title, (24, 20))
            self.screen.blit(hint, (24, 58))

        if self.shake > 0.25:
            radius = max(1, int(self.shake))
            dx = random.randint(-radius, radius)
            dy = random.randint(-radius, radius)
            snapshot = self.screen.copy()
            self.screen.fill((2, 3, 14))
            self.screen.blit(snapshot, (dx, dy))

    def pointer_down(self, pos: tuple[int, int]) -> None:
        rects = self.control_rects()

        if rects["finale"].collidepoint(pos):
            self.finale()
            return

        if rects["auto"].collidepoint(pos):
            self.autoplay = not self.autoplay
            self.caption_alpha = 150.0
            return

        x, y = pos
        target_y = clamp(
            y,
            self.size[1] * 0.08,
            self.size[1] * 0.66,
        )
        self.launch(x=x, target_y=target_y)


def create_display() -> pygame.Surface:
    size = WEB_SIZE if IS_WEB else DESKTOP_SIZE
    flags = pygame.DOUBLEBUF
    if not IS_WEB:
        flags |= pygame.RESIZABLE
    return pygame.display.set_mode(size, flags)


async def run() -> None:
    pygame.init()
    pygame.display.set_caption("Python Fireworks — Mobile & Desktop")
    screen = create_display()
    clock = pygame.time.Clock()
    show = FireworkShow(screen)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.033)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.FINGERDOWN:
                width, height = show.size
                show.pointer_down(
                    (
                        int(event.x * width),
                        int(event.y * height),
                    )
                )

            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and not getattr(event, "touch", False)
            ):
                show.pointer_down(event.pos)

            elif (
                event.type == pygame.VIDEORESIZE
                and not IS_WEB
            ):
                screen = pygame.display.set_mode(
                    event.size,
                    pygame.RESIZABLE | pygame.DOUBLEBUF,
                )
                show.reset_surface(screen)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    show.finale()
                elif event.key == pygame.K_a:
                    show.autoplay = not show.autoplay
                elif event.key == pygame.K_r:
                    show.rockets.clear()
                    show.sparks.clear()
                    show.smoke.clear()
                elif event.key == pygame.K_F11 and not IS_WEB:
                    fullscreen = bool(
                        pygame.display.get_surface().get_flags()
                        & pygame.FULLSCREEN
                    )
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            DESKTOP_SIZE,
                            pygame.RESIZABLE | pygame.DOUBLEBUF,
                        )
                    else:
                        screen = pygame.display.set_mode(
                            (0, 0),
                            pygame.FULLSCREEN | pygame.DOUBLEBUF,
                        )
                    show.reset_surface(screen)

        show.update(dt)
        show.draw()
        pygame.display.flip()

        if IS_WEB:
            import asyncio
            await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
