import json
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from mobile import MOBILE_PATTERNS, MobileShow, viewport_size


class MobileControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.show = MobileShow(pygame.display.set_mode((720, 540)))
        self.show.autoplay = False

    def test_buttons_launch_selected_shape_immediately(self):
        for pattern in MOBILE_PATTERNS:
            before = len(self.show.rockets)
            self.show.dispatch({"action": "pattern", "pattern": pattern})
            self.assertEqual(len(self.show.rockets), before + 1)
            self.assertEqual(self.show.rockets[-1].pattern, pattern)
            self.assertEqual(self.show.selected_pattern, pattern)

    def test_sky_tap_uses_selected_shape(self):
        self.show.dispatch({"action": "pattern", "pattern": "heart"})
        self.show.dispatch({"action": "launch", "x": 0.25, "y": 0.30})
        rocket = self.show.rockets[-1]
        self.assertEqual(rocket.pattern, "heart")
        self.assertAlmostEqual(rocket.pos.x, 180)
        self.assertAlmostEqual(rocket.target_y, 162)

    def test_auto_toggle_and_state(self):
        self.show.dispatch({"action": "toggle-auto"})
        self.assertTrue(json.loads(self.show.state_json())["autoplay"])
        self.assertEqual(len(self.show.rockets), 0)
        self.show.dispatch({"action": "toggle-auto"})
        self.show.update(0.5)
        self.assertFalse(self.show.autoplay)
        self.assertEqual(len(self.show.rockets), 0)

    def test_autoplay_follows_selection(self):
        self.show.dispatch({"action": "pattern", "pattern": "ring"})
        self.show.rockets.clear()
        self.show.autoplay = True
        self.show.next_launch = 0
        self.show.update(0.01)
        self.assertEqual(self.show.rockets[-1].pattern, "ring")

    def test_heart_is_not_normalized_to_a_circle(self):
        self.show._heart(pygame.Vector2(300, 200), 0.96)
        velocities = [spark.vel for spark in self.show.sparks]
        radii = [v.length() for v in velocities]
        self.assertGreater(max(radii) - min(radii), 80)
        self.assertAlmostEqual(velocities[0].y, -57.5)
        self.assertAlmostEqual(velocities[60].y, 195.5)
        self.assertAlmostEqual(velocities[30].x, -velocities[90].x)

    def test_invalid_commands_are_ignored(self):
        for command in [None, [], {}, {"action":"pattern","pattern":"invalid"},
                        {"action":"launch","x":"nan","y":0.2},
                        {"action":"launch","x":None,"y":0.2}]:
            self.show.dispatch(command)
        self.assertEqual(len(self.show.rockets), 0)

    def test_rapid_taps_are_bounded(self):
        for _ in range(100):
            self.show.dispatch({"action":"pattern","pattern":"willow"})
        self.assertEqual(len(self.show.rockets), self.show.max_rockets)

    def test_resize_scales_scene(self):
        self.show.dispatch({"action":"launch","x":0.5,"y":0.4})
        rocket = self.show.rockets[-1]
        self.show.reset_surface(pygame.display.set_mode((360, 720)))
        self.assertEqual(self.show.size, (360, 720))
        self.assertAlmostEqual(rocket.pos.x, 180)
        self.assertAlmostEqual(rocket.target_y, 288)

    def test_animation_and_drawing(self):
        for pattern in MOBILE_PATTERNS:
            self.show.dispatch({"action":"pattern","pattern":pattern})
        for frame in range(180):
            self.show.update(1 / 60)
            if frame % 12 == 0:
                self.show.draw()
        self.assertGreater(len(self.show.sparks), 0)
        self.assertLessEqual(len(self.show.sparks), self.show.max_sparks)
        self.assertEqual(self.show.caption_alpha, 0)

    def test_viewport_is_bounded(self):
        self.assertEqual(viewport_size({"width":99999,"height":99999},(960,540)),(960,800))
        self.assertEqual(viewport_size({"width":0,"height":0},(960,540)),(160,160))
        self.assertEqual(viewport_size({},(960,540)),(960,540))


if __name__ == "__main__":
    unittest.main()
