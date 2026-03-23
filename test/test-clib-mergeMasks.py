import unittest

import numpy as np

from labelSys.clib.wrapper import MergeMasks


class MergeMasksTests(unittest.TestCase):
    def test_averages_overlapping_mask_colors(self):
        masks = np.array(
            [
                [[1, 0, 0], [0, 1, 0]],
                [[1, 1, 0], [0, 0, 0]],
                [[0, 1, 1], [0, 0, 1]],
            ],
            dtype=np.uint8,
        )
        colors = [(90, 0, 0), (0, 60, 0), (0, 0, 30)]

        actual = MergeMasks.mergeBool2Color2D(masks, colors)
        expected = np.array(
            [
                [[45, 30, 0], [0, 30, 15], [0, 0, 30]],
                [[0, 0, 0], [90, 0, 0], [0, 0, 30]],
            ],
            dtype=np.uint8,
        )

        self.assertTrue(np.array_equal(actual, expected))


if __name__ == "__main__":
    unittest.main()
