import unittest

import numpy as np

from labelSys.clib.wrapper import Contour2Mask


class Contour2MaskTests(unittest.TestCase):
    def test_fills_expected_regions(self):
        contours = [
            [[(1, 1), (4, 1), (4, 4), (1, 4)]],
            [[(6, 2), (8, 2), (7, 5)]],
        ]

        mask = Contour2Mask.contours2Mask(contours, [3, 7], 8, 10)

        self.assertEqual(mask.shape, (8, 10))
        self.assertEqual(int(mask[2, 2]), 3)
        self.assertEqual(int(mask[3, 3]), 3)
        self.assertEqual(int(mask[3, 7]), 7)
        self.assertEqual(int(mask[0, 0]), 0)
        self.assertEqual(int(mask[7, 9]), 0)


if __name__ == "__main__":
    unittest.main()
