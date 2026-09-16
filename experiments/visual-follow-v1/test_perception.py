import inspect
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import perception
from perception import Camera, Detection, Follower, detect


def image(u=160, v=120, radius=12, color=(230, 15, 20)):
    frame = np.full((240, 320, 3), (20, 35, 45), np.uint8)
    yy, xx = np.indices(frame.shape[:2])
    frame[(xx-u)**2+(yy-v)**2 <= radius**2] = color
    return frame


class PixelPerceptionTests(unittest.TestCase):
    def test_geometry_and_left_right_sign(self):
        for u in (80, 160, 240):
            d = detect(image(u=u))
            self.assertTrue(d.valid)
            self.assertAlmostEqual(d.range_m, Camera().focal_px * .035/12, delta=.03)
            self.assertEqual(np.sign(d.bearing_rad), np.sign(159.5-u))

    def test_no_target_and_malformed(self):
        self.assertEqual(detect(np.zeros((240, 320, 3), np.uint8)).reason, "no_target")
        for frame in (np.zeros((2, 2, 3), np.uint8), np.zeros((240, 320, 3), float)):
            self.assertFalse(detect(frame).valid)

    def test_ambiguity_partial_occlusion_and_border(self):
        first = image(u=100)
        second = image(u=230)
        frame = np.maximum(first, second)
        self.assertEqual(detect(frame).reason, "ambiguous_targets")
        partial = image()
        partial[:, :160] = 0
        self.assertFalse(detect(partial).valid)
        self.assertEqual(detect(image(u=4)).reason, "clipped_target")

    def test_low_light_quantization_and_false_positive_negatives(self):
        for intensity in (25, 31, 45, 100, 230):
            self.assertTrue(detect(image(color=(intensity, 2, 3))).valid)
        for color in ((19, 2, 2), (30, 22, 22), (30, 20, 1), (15, 3, 2)):
            self.assertFalse(detect(image(color=color)).valid)
        rng = np.random.default_rng(26091502)
        for _ in range(20):
            noise = np.clip(rng.normal(12, 3, (240, 320, 3)), 0, 255).astype(np.uint8)
            self.assertFalse(detect(noise).valid)
        rectangle = image()
        rectangle[80:150, 100:140] = [45, 2, 3]
        self.assertFalse(detect(rectangle).valid)

    def test_disconnected_and_large_partial_occlusion(self):
        split = image()
        split[:, 157:164] = 0
        self.assertFalse(detect(split).valid)
        partly_hidden = image()
        partly_hidden[:, :158] = 0
        self.assertFalse(detect(partly_hidden).valid)

    def test_retained_reflection_ambiguity_and_known_limit(self):
        frames = np.load(Path(__file__).parent/"fixtures/v2-reflections.npz")
        ambiguous = detect(frames["direct_and_reflection"])
        self.assertEqual(ambiguous.reason, "ambiguous_targets")
        follower = Follower()
        for i in range(2):
            follower.ingest(ambiguous, i*.1, i, i*.1)
        np.testing.assert_array_equal(follower.command(.1), 0)
        # This deliberately records a limitation. One reflection has the same
        # visual signature, so reflective floors are outside the V3 envelope.
        self.assertTrue(detect(frames["reflection_only"]).valid)

    def test_lighting_and_noise_exposed_factor_grid(self):
        rng = np.random.default_rng(26091501)
        for gain in (.6, .8, 1., 1.15):
            for sigma in (0., 3.):
                pixels = np.clip(image().astype(float)*gain+rng.normal(0, sigma, (240, 320, 3)), 0, 255).astype(np.uint8)
                self.assertTrue(detect(pixels).valid, (gain, sigma))

    def test_input_boundary_has_no_simulator_or_pose_argument(self):
        self.assertEqual(list(inspect.signature(detect).parameters), ["rgb", "camera"])
        self.assertFalse(hasattr(perception, "mujoco"))
        self.assertEqual(list(inspect.signature(Follower.ingest).parameters),
                         ["self", "detection", "capture_s", "sequence", "now_s"])


class CommandSafetyTests(unittest.TestCase):
    def setUp(self):
        self.d = Detection(True, "detected", .1, .9)
        self.f = Follower()

    def acquire(self):
        self.f.ingest(self.d, 0., 0, 0.)
        np.testing.assert_array_equal(self.f.command(0.), 0)
        self.f.ingest(self.d, .1, 1, .1)
        self.assertGreater(self.f.command(.1)[0], 0)

    def test_loss_stale_and_reacquisition(self):
        self.acquire()
        self.f.ingest(Detection(False, "no_target"), .2, 2, .2)
        np.testing.assert_array_equal(self.f.command(.2), 0)
        self.f.ingest(self.d, .3, 3, .3)
        np.testing.assert_array_equal(self.f.command(.3), 0)
        self.f.ingest(self.d, .4, 4, .4)
        self.assertGreater(self.f.command(.4)[0], 0)
        np.testing.assert_array_equal(self.f.command(.54), 0)
        self.assertEqual(self.f.reason, "stale_frame")
        self.f.ingest(self.d, .6, 5, .6)
        np.testing.assert_array_equal(self.f.command(.6), 0)

    def test_replayed_frames_cannot_extend_motion(self):
        self.acquire()
        self.f.ingest(self.d, .1, 1, .2)
        np.testing.assert_array_equal(self.f.command(.24), 0)
        self.assertEqual(self.f.reason, "stale_frame")

    def test_clock_invalid_detection_and_limits(self):
        self.f.ingest(self.d, 1., 0, 0.)
        np.testing.assert_array_equal(self.f.command(0.), 0)
        for distance in (.61, .9, 1.7):
            for bearing in (-.5, 0., .5):
                f = Follower()
                for i in range(2):
                    f.ingest(Detection(True, "detected", bearing, distance), i*.1, i, i*.1)
                c = f.command(.1)
                self.assertEqual(c.dtype, np.float32)
                self.assertTrue(0 <= c[0] <= .12)
                self.assertTrue(abs(c[2]) <= .65)
        self.acquire()
        np.testing.assert_array_equal(self.f.command(.09), 0)

    def test_close_or_large_bearing_stops(self):
        for d in (Detection(True, "detected", 0., .5), Detection(True, "detected", .8, .9),
                  Detection(True, "detected", float("nan"), .9)):
            f = Follower()
            f.ingest(d, 0., 0, 0.)
            f.ingest(d, .1, 1, .1)
            np.testing.assert_array_equal(f.command(.1), 0)


if __name__ == "__main__":
    unittest.main()
