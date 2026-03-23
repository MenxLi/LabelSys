#include <algorithm>
#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace {

constexpr char BASE64_TABLE[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

int decodeBase64Char(char value) {
    const std::string table(BASE64_TABLE);
    const auto pos = table.find(value);
    if (pos == std::string::npos) {
        throw std::invalid_argument("invalid base64 character");
    }
    return static_cast<int>(pos);
}

class ContourRasterizer {
public:
    bool isInside(int32_t x, int32_t y, const int32_t* contour, uint32_t contourLen) {
        int intersectionCounter = 0;

        prevVert0_[0] = contour[contourLen - 2];
        prevVert0_[1] = contour[contourLen - 1];

        for (uint32_t index = 0; index < contourLen - 3; index += 2) {
            const auto x0 = contour[index];
            const auto y0 = contour[index + 1];
            const auto x1 = contour[index + 2];
            const auto y1 = contour[index + 3];

            if (checkLineRelation(x, y, x0, y0, x1, y1, intersectionCounter)) {
                return true;
            }

            prevVert0_[0] = x0;
            prevVert0_[1] = y0;
        }

        return checkLineRelation(
                   x,
                   y,
                   contour[contourLen - 2],
                   contour[contourLen - 1],
                   contour[0],
                   contour[1],
                   intersectionCounter)
            || (intersectionCounter % 2 != 0);
    }

private:
    bool checkLineRelation(
        int32_t x,
        int32_t y,
        int32_t x0,
        int32_t y0,
        int32_t x1,
        int32_t y1,
        int& counter) {
        if (x0 < x && x1 < x) {
            return false;
        }

        if ((y0 < y && y1 < y) || (y0 > y && y1 > y)) {
            return false;
        }

        if ((x0 == x && y0 == y) || (x1 == x && y1 == y)) {
            return true;
        }

        if (y0 == y1) {
            return !(x0 > x && x1 > x);
        }

        if (x1 == x0) {
            if (!(y == y0 || y == y1)) {
                ++counter;
            }
            return false;
        }

        const auto previousY = prevVert0_[1];
        if (y == y0) {
            if (x < x0 && (y - previousY) * (y - y1) <= 0) {
                ++counter;
            }
            return false;
        }

        if (y == y1) {
            return false;
        }

        const auto intersectionX = static_cast<long long>(
            static_cast<double>(x0)
            + (static_cast<double>(y) - static_cast<double>(y0))
                / (static_cast<double>(y1) - static_cast<double>(y0))
                * (static_cast<double>(x1) - static_cast<double>(x0)));

        if (intersectionX == x) {
            return true;
        }
        if (intersectionX > x) {
            ++counter;
        }
        return false;
    }

    std::array<int32_t, 2> prevVert0_{};
};

std::vector<std::array<uint8_t, 3>> parseColors(const py::sequence& colors, py::ssize_t expectedSize) {
    if (colors.size() != expectedSize) {
        throw std::invalid_argument("colors length must match masks length");
    }

    std::vector<std::array<uint8_t, 3>> parsedColors;
    parsedColors.reserve(static_cast<size_t>(expectedSize));
    for (const auto& colorObj : colors) {
        const auto color = py::cast<py::sequence>(colorObj);
        if (color.size() != 3) {
            throw std::invalid_argument("each color must contain exactly 3 values");
        }
        parsedColors.push_back({
            static_cast<uint8_t>(py::cast<int>(color[0])),
            static_cast<uint8_t>(py::cast<int>(color[1])),
            static_cast<uint8_t>(py::cast<int>(color[2]))
        });
    }
    return parsedColors;
}

}  // namespace

py::array_t<uint8_t> cnts2msk(const py::sequence& contours, const py::sequence& destVals, int32_t imH, int32_t imW) {
    if (contours.size() != destVals.size()) {
        throw std::invalid_argument("contours and dest_vals length mismatch");
    }
    if (imH < 0 || imW < 0) {
        throw std::invalid_argument("image dimensions must be non-negative");
    }

    std::vector<int32_t> flattenedContours;
    std::vector<uint32_t> contourLens;
    std::vector<uint8_t> flattenedDestVals;

    for (py::ssize_t contourIndex = 0; contourIndex < contours.size(); ++contourIndex) {
        const auto contourGroup = py::cast<py::sequence>(contours[contourIndex]);
        const auto destVal = static_cast<uint8_t>(py::cast<int>(destVals[contourIndex]));

        for (const auto& contourObj : contourGroup) {
            const auto contour = py::cast<py::sequence>(contourObj);
            if (contour.size() == 0) {
                continue;
            }

            contourLens.push_back(static_cast<uint32_t>(contour.size() * 2));
            flattenedDestVals.push_back(destVal);

            for (const auto& pointObj : contour) {
                const auto point = py::cast<py::sequence>(pointObj);
                if (point.size() != 2) {
                    throw std::invalid_argument("each contour point must have 2 coordinates");
                }
                flattenedContours.push_back(py::cast<int32_t>(point[0]));
                flattenedContours.push_back(py::cast<int32_t>(point[1]));
            }
        }
    }

    py::array_t<uint8_t> mask(std::vector<py::ssize_t>{imH, imW});
    auto* maskPtr = static_cast<uint8_t*>(mask.mutable_data());
    std::fill_n(maskPtr, static_cast<size_t>(imH) * static_cast<size_t>(imW), static_cast<uint8_t>(0));

    if (contourLens.empty()) {
        return mask;
    }

    ContourRasterizer rasterizer;
    size_t contourOffset = 0;

    for (size_t contourIndex = 0; contourIndex < contourLens.size(); ++contourIndex) {
        const auto contourLen = contourLens[contourIndex];
        const auto* contourPtr = flattenedContours.data() + contourOffset;
        const auto destVal = flattenedDestVals[contourIndex];

        int32_t bboxXMax = 0;
        int32_t bboxYMax = 0;
        int32_t bboxXMin = 999999;
        int32_t bboxYMin = 999999;

        for (uint32_t index = 0; index < contourLen; index += 2) {
            bboxXMax = std::max(bboxXMax, contourPtr[index]);
            bboxXMin = std::min(bboxXMin, contourPtr[index]);
        }
        for (uint32_t index = 1; index < contourLen; index += 2) {
            bboxYMax = std::max(bboxYMax, contourPtr[index]);
            bboxYMin = std::min(bboxYMin, contourPtr[index]);
        }

        for (int32_t y = 0; y < imH; ++y) {
            for (int32_t x = 0; x < imW; ++x) {
                if (x < bboxXMin || x > bboxXMax || y < bboxYMin || y > bboxYMax) {
                    continue;
                }
                if (rasterizer.isInside(x, y, contourPtr, contourLen)) {
                    maskPtr[static_cast<size_t>(y) * static_cast<size_t>(imW) + static_cast<size_t>(x)] = destVal;
                }
            }
        }

        contourOffset += contourLen;
    }

    return mask;
}

py::array_t<uint8_t> mergeBool2Color2D(
    py::array_t<uint8_t, py::array::c_style | py::array::forcecast> masks,
    const py::sequence& colors) {
    const auto info = masks.request();
    if (info.ndim != 3) {
        throw std::invalid_argument("masks must have shape (n, H, W)");
    }

    const auto nMasks = info.shape[0];
    const auto imH = info.shape[1];
    const auto imW = info.shape[2];
    const auto parsedColors = parseColors(colors, nMasks);
    const auto* masksPtr = static_cast<const uint8_t*>(info.ptr);

    py::array_t<uint8_t> dest(std::vector<py::ssize_t>{imH, imW, 3});
    auto* destPtr = static_cast<uint8_t*>(dest.mutable_data());
    std::fill_n(destPtr, static_cast<size_t>(imH) * static_cast<size_t>(imW) * 3U, static_cast<uint8_t>(0));

    for (py::ssize_t row = 0; row < imH; ++row) {
        for (py::ssize_t col = 0; col < imW; ++col) {
            unsigned int selectedCount = 0;
            unsigned int channelSum[3] = {0U, 0U, 0U};

            for (py::ssize_t maskIndex = 0; maskIndex < nMasks; ++maskIndex) {
                const auto offset = static_cast<size_t>(maskIndex) * static_cast<size_t>(imH) * static_cast<size_t>(imW)
                    + static_cast<size_t>(row) * static_cast<size_t>(imW)
                    + static_cast<size_t>(col);
                if (masksPtr[offset] == 1U) {
                    const auto& color = parsedColors[static_cast<size_t>(maskIndex)];
                    channelSum[0] += color[0];
                    channelSum[1] += color[1];
                    channelSum[2] += color[2];
                    ++selectedCount;
                }
            }

            if (selectedCount == 0U) {
                continue;
            }

            const auto destOffset = (static_cast<size_t>(row) * static_cast<size_t>(imW) + static_cast<size_t>(col)) * 3U;
            destPtr[destOffset] = static_cast<uint8_t>(channelSum[0] / selectedCount);
            destPtr[destOffset + 1] = static_cast<uint8_t>(channelSum[1] / selectedCount);
            destPtr[destOffset + 2] = static_cast<uint8_t>(channelSum[2] / selectedCount);
        }
    }

    return dest;
}

py::array_t<int> intArray2Bool(py::array_t<int, py::array::c_style | py::array::forcecast> arr, int bitLen) {
    if (bitLen <= 0) {
        throw std::invalid_argument("bit_len must be positive");
    }

    const auto info = arr.request();
    const auto* src = static_cast<const int*>(info.ptr);
    py::array_t<int> dest(info.size * bitLen);
    auto* destPtr = static_cast<int*>(dest.mutable_data());

    for (py::ssize_t index = 0; index < info.size; ++index) {
        int value = src[index];
        int* chunk = destPtr + index * bitLen;
        for (int bitIndex = bitLen - 1; bitIndex >= 0; --bitIndex) {
            chunk[bitIndex] = value & 1;
            value >>= 1;
        }
    }

    return dest;
}

std::string biArray2B64Str(py::array_t<int, py::array::c_style | py::array::forcecast> biArr) {
    const auto info = biArr.request();
    if (info.size % 6 != 0) {
        throw std::invalid_argument("bit array length must be a multiple of 6");
    }

    const auto* bits = static_cast<const int*>(info.ptr);
    std::string encoded(static_cast<size_t>(info.size) / 6U, '\0');
    for (py::ssize_t index = 0; index < info.size; index += 6) {
        int decimal = 0;
        for (int bitIndex = 0; bitIndex < 6; ++bitIndex) {
            decimal += bits[index + bitIndex] << (5 - bitIndex);
        }
        encoded[static_cast<size_t>(index / 6)] = BASE64_TABLE[decimal];
    }

    return encoded;
}

py::array_t<int> str2intArray(const std::string& encoded, int bitLen) {
    if (bitLen <= 0) {
        throw std::invalid_argument("bit_len must be positive");
    }

    const auto bitCount = static_cast<py::ssize_t>(encoded.size()) * 6;
    if (bitCount % bitLen != 0) {
        throw std::invalid_argument("string bit count must be divisible by bit_len");
    }

    py::array_t<int> decoded(bitCount / bitLen);
    auto* decodedPtr = static_cast<int*>(decoded.mutable_data());

    std::vector<int> bits(static_cast<size_t>(bitCount));
    for (size_t charIndex = 0; charIndex < encoded.size(); ++charIndex) {
        const auto decimal = decodeBase64Char(encoded[charIndex]);
        for (int bitIndex = 0; bitIndex < 6; ++bitIndex) {
            bits[charIndex * 6U + static_cast<size_t>(bitIndex)] = (decimal >> (5 - bitIndex)) & 1;
        }
    }

    for (py::ssize_t valueIndex = 0; valueIndex < bitCount / bitLen; ++valueIndex) {
        int value = 0;
        for (int bitIndex = 0; bitIndex < bitLen; ++bitIndex) {
            value += bits[static_cast<size_t>(valueIndex * bitLen + bitIndex)] << (bitLen - 1 - bitIndex);
        }
        decodedPtr[valueIndex] = value;
    }

    return decoded;
}

PYBIND11_MODULE(_native, module) {
    module.doc() = "Native pybind11 bindings for LabelSys";

    module.def("cnts2msk", &cnts2msk, py::arg("contours"), py::arg("dest_vals"), py::arg("im_h"), py::arg("im_w"));
    module.def("mergeBool2Color2D", &mergeBool2Color2D, py::arg("masks"), py::arg("colors"));
    module.def("intArray2Bool", &intArray2Bool, py::arg("arr"), py::arg("bit_len"));
    module.def("biArray2B64Str", &biArray2B64Str, py::arg("bi_arr"));
    module.def("str2intArray", &str2intArray, py::arg("encoded"), py::arg("bit_len"));
}