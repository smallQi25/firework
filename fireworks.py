from __future__ import annotations

import colorsys
import math
import random
from dataclasses import dataclass

import pygame

WIDTH = 1280
HEIGHT = 720
FPS = 60
GRAVITY = 145.0
AIR_DRAG = 0.992

Color = tuple[int, int, int]


def hsv(h: float, s: float = 1.0, v: float = 1.0) -> Color:
    r, g, b = colorsys.hsv_to_rgb((h % 1.0), s, v)
    return int(r * 255), int(g * 255), int(b * 255)


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

        self.vel.x *= self.drag ** (dt * FPS)
        self.vel.y *= self.drag ** (dt * FPS)
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        return self.pos.y < HEIGHT + 80

    def draw(self, canvas: pygame.Surface, glow: pygame.Surface) -> None:
        ratio = clamp(self.life / self.max_life, 0.0, 1.0)
        flicker = 0.55 + 0.45 * math.sin(self.life * 42.0 + self.pos.x)
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
        alpha = int(34 * ratio)
        shade = int(60 + 70 * ratio)
        pygame.draw.circle(
            canvas,
            (shade, shade, shade + 8, alpha),
            (int(self.pos.x), int(self.pos.y)),
            max(2, int(self.size)),
        )


class Rocket:
    def __init__(self, x: float, target_y: float, hue: float, pattern: str):
        self.pos = pygame.Vector2(x, HEIGHT + 8)
        self.prev = self.pos.copy()
        self.vel = pygame.Vector2(random.uniform(-24, 24), random.uniform(-610, -520))
        self.target_y = target_y
        self.hue = hue
        self.color = hsv(hue, 0.5, 1.0)
        self.pattern = pattern
        self.timer = 0.0

    def update(self, dt: float, trail: list[Spark], smoke: list[Smoke]) -> bool:
        self.prev = self.pos.copy()
        self.timer += dt
        self.vel.y += 92.0 * dt
        self.pos += self.vel * dt

        for _ in range(2):
            trail.append(
                Spark(
                    pos=self.pos + pygame.Vector2(random.uniform(-2, 2), random.uniform(-2, 2)),
                    vel=pygame.Vector2(random.uniform(-28, 28), random.uniform(70, 130)),
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

        if random.random() < 0.16:
            smoke.append(
                Smoke(
                    self.pos.copy(),
                    pygame.Vector2(random.uniform(-7, 7), random.uniform(12, 25)),
                    1.0,
                    1.0,
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
        p = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(canvas, (255, 244, 205, 255), p, 3)
        pygame.draw.circle(glow, (*self.color, 40), p, 18)


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
        self.stars = self._build_stars(150)
        self.elapsed = 0.0
        self.next_launch = 0.25
        self.show_speed = 1.0
        self.autoplay = True
        self.fullscreen = False
        self.shake = 0.0
        self.caption_alpha = 255.0

    def _build_stars(self, count: int) -> list[tuple[float, float, float, float]]:
        return [
            (
                random.uniform(0, self.size[0]),
                random.uniform(0, self.size[1] * 0.73),
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
        self.stars = self._build_stars(150)

    def launch(
        self,
        x: float | None = None,
        target_y: float | None = None,
        pattern: str | None = None,
        hue: float | None = None,
    ) -> None:
        width, height = self.size
        x = x if x is not None else random.uniform(width * 0.16, width * 0.84)
        target_y = target_y if target_y is not None else random.uniform(height * 0.16, height * 0.53)
        pattern = pattern or random.choice(self.PATTERNS)
        hue = hue if hue is not None else random.random()
        rocket = Rocket(x, target_y, hue, pattern)
        rocket.pos.y = height + 8
        self.rockets.append(rocket)

    def finale(self) -> None:
        width, height = self.size
        palette = random.random()
        for i in range(9):
            x = width * (0.10 + 0.10 * i) + random.uniform(-20, 20)
            y = random.uniform(height * 0.12, height * 0.46)
            self.launch(
                x=x,
                target_y=y,
                pattern=self.PATTERNS[i % len(self.PATTERNS)],
                hue=palette + i * 0.075,
            )
        self.shake = max(self.shake, 7.0)

    def burst(self, rocket: Rocket) -> None:
        center = rocket.pos.copy()
        hue = rocket.hue
        pattern = rocket.pattern

        if pattern == "ring":
            self._radial(center, hue, count=120, speed=(190, 245), ring=True)
        elif pattern == "willow":
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
        elif pattern == "palm":
            self._palm(center, hue)
        elif pattern == "heart":
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

        for _ in range(22):
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

        for _ in range(9):
            self.smoke.append(
                Smoke(
                    center + pygame.Vector2(random.uniform(-5, 5), random.uniform(-5, 5)),
                    pygame.Vector2(random.uniform(-18, 18), random.uniform(-12, 12)),
                    random.uniform(1.0, 1.8),
                    1.8,
                    random.uniform(5, 12),
                )
            )
        self.shake = max(self.shake, 3.6)

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
        arms = random.randint(9, 13)
        for i in range(arms):
            angle = (i / arms) * math.tau + random.uniform(-0.08, 0.08)
            speed = random.uniform(210, 285)
            base = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            for step in range(8):
                velocity = (
                    base * random.uniform(0.66, 1.0)
                    + pygame.Vector2(random.uniform(-20, 20), random.uniform(-20, 20))
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
        for i in range(150):
            t = math.tau * i / 150
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
            speed = random.uniform(155, 235)
            spark_life = random.uniform(1.4, 2.1)
            self.sparks.append(
                Spark(
                    center.copy(),
                    direction * speed
                    + pygame.Vector2(random.uniform(-8, 8), random.uniform(-8, 8)),
                    hsv(hue + random.uniform(-0.025, 0.025), 0.66, 1.0),
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
        self.caption_alpha = max(0.0, self.caption_alpha - 24.0 * dt)

        if self.autoplay and self.elapsed >= self.next_launch:
            self.launch()
            delay = random.uniform(0.34, 0.92) / self.show_speed
            if random.random() < 0.18:
                delay *= 0.45
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
        self.shake *= 0.86 ** (dt * FPS)

    def _draw_background(self) -> None:
        width, height = self.size
        self.screen.fill((2, 3, 14))

        bands = 24
        for i in range(bands):
            y0 = int(height * i / bands)
            y1 = int(height * (i + 1) / bands)
            t = i / max(1, bands - 1)
            color = (
                int(2 + 6 * t),
                int(3 + 5 * t),
                int(14 + 15 * t),
            )
            pygame.draw.rect(self.screen, color, (0, y0, width, y1 - y0 + 1))

        for x, y, size, phase in self.stars:
            twinkle = 0.45 + 0.55 * (
                0.5 + 0.5 * math.sin(self.elapsed * (1.2 + size) + phase)
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
            w = skyline_rng.randint(22, 58)
            h = skyline_rng.randint(18, 78)
            pygame.draw.rect(
                self.screen,
                (4, 5, 10),
                (x, horizon - h, w, h),
            )
            for wy in range(horizon - h + 9, horizon - 4, 13):
                if skyline_rng.random() < 0.30:
                    pygame.draw.rect(
                        self.screen,
                        (35, 30, 18),
                        (x + skyline_rng.randint(4, max(5, w - 7)), wy, 2, 4),
                    )
            x += w + skyline_rng.randint(2, 8)

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

        if self.caption_alpha > 2:
            font = pygame.font.Font(None, 28)
            small = pygame.font.Font(None, 22)
            title = font.render(
                "PYTHON FIREWORKS",
                True,
                (235, 240, 255),
            )
            hint = small.render(
                "Click: launch  •  Space: finale  •  A: autoplay  •  F11: fullscreen  •  Esc: quit",
                True,
                (158, 168, 196),
            )
            title.set_alpha(int(self.caption_alpha))
            hint.set_alpha(int(self.caption_alpha))
            self.screen.blit(title, (28, 24))
            self.screen.blit(hint, (28, 56))

        if self.shake > 0.25:
            dx = random.randint(-int(self.shake), int(self.shake))
            dy = random.randint(-int(self.shake), int(self.shake))
            snapshot = self.screen.copy()
            self.screen.fill((2, 3, 14))
            self.screen.blit(snapshot, (dx, dy))

    def click_launch(self, pos: tuple[int, int]) -> None:
        x, y = pos
        target_y = clamp(
            y,
            self.size[1] * 0.10,
            self.size[1] * 0.62,
        )
        self.launch(x=x, target_y=target_y)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Python Fireworks — Advanced Particle Show")
    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT),
        pygame.RESIZABLE | pygame.DOUBLEBUF,
    )
    clock = pygame.time.Clock()
    show = FireworkShow(screen)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.033)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                show.click_launch(event.pos)
            elif event.type == pygame.VIDEORESIZE and not show.fullscreen:
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
                elif event.key == pygame.K_F11:
                    show.fullscreen = not show.fullscreen
                    flags = (
                        pygame.FULLSCREEN | pygame.DOUBLEBUF
                        if show.fullscreen
                        else pygame.RESIZABLE | pygame.DOUBLEBUF
                    )
                    screen = pygame.display.set_mode(
                        (0, 0) if show.fullscreen else (WIDTH, HEIGHT),
                        flags,
                    )
                    show.reset_surface(screen)

        show.update(dt)
        show.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
