import unittest

import numpy as np

from labelSys.clib import _native
from labelSys.clib.wrapper import Contour2Mask, MergeMasks
from labelSys.utils.base64ImageConverter import Base64_2DImageDecoder, Base64_2DImageEncoder


class NativeBindingsTests(unittest.TestCase):
    def test_contours2mask(self):
        mask = Contour2Mask.contours2Mask(
            [[[(1, 1), (3, 1), (3, 3), (1, 3)]]],
            [9],
            5,
            5,
        )

        self.assertEqual(mask.shape, (5, 5))
        self.assertEqual(mask.dtype, np.uint8)
        self.assertEqual(int(mask[2, 2]), 9)
        self.assertEqual(int(mask[0, 0]), 0)

    def test_merge_masks(self):
        merged = MergeMasks.mergeBool2Color2D(
            np.array(
                [
                    [[1, 0], [0, 0]],
                    [[1, 1], [0, 0]],
                ],
                dtype=np.uint8,
            ),
            [(100, 0, 0), (0, 50, 0)],
        )

        self.assertEqual(merged.shape, (2, 2, 3))
        self.assertTrue(np.array_equal(merged[0, 0], np.array([50, 25, 0], dtype=np.uint8)))
        self.assertTrue(np.array_equal(merged[0, 1], np.array([0, 50, 0], dtype=np.uint8)))

    def test_base64_accelerated_path_matches_python(self):
        image = np.array([[0, 1], [2, 3]], dtype=np.int32)

        encoded_fast = Base64_2DImageEncoder(image, bit_len=2)(accelerate=True)
        encoded_slow = Base64_2DImageEncoder(image, bit_len=2)(accelerate=False)
        self.assertEqual(encoded_fast, encoded_slow)

        decoded_fast = Base64_2DImageDecoder(encoded_fast)(accelerate=True)
        decoded_slow = Base64_2DImageDecoder(encoded_fast)(accelerate=False)
        self.assertTrue(np.array_equal(decoded_fast, image))
        self.assertTrue(np.array_equal(decoded_slow, image))

    def test_native_bit_helpers(self):
        bits = _native.intArray2Bool(np.array([0, 1, 2, 3], dtype=np.intc), 2)
        self.assertTrue(np.array_equal(bits, np.array([0, 0, 0, 1, 1, 0, 1, 1], dtype=np.intc)))

        encoded = _native.biArray2B64Str(np.array([0, 0, 0, 0, 0, 0], dtype=np.intc))
        self.assertEqual(encoded, "A")

        decoded = _native.str2intArray("A", 2)
        self.assertTrue(np.array_equal(decoded, np.array([0, 0, 0], dtype=np.intc)))


if __name__ == "__main__":
    unittest.main()