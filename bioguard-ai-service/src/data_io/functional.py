# -*- coding: utf-8 -*-
from __future__ import division

import torch
from PIL import Image, ImageOps, ImageEnhance
import numpy as np
import numbers
import types
import collections
import warnings

try:
    import accimage
except ImportError:
    accimage = None


def _is_pil_image(img):
    if accimage is not None:
        return isinstance(img, (Image.Image, accimage.Image))
    return isinstance(img, Image.Image)


def _is_tensor_image(img):
    return torch.is_tensor(img) and img.ndimension() == 3


def _is_numpy_image(img):
    return isinstance(img, np.ndarray) and (img.ndim in {2, 3})


def to_tensor(pic):
    # Reference implementation returns float WITHOUT /255 (modified by zkx)
    if not (_is_pil_image(pic) or _is_numpy_image(pic)):
        raise TypeError("pic should be PIL Image or ndarray. Got {}".format(type(pic)))

    if isinstance(pic, np.ndarray):
        if pic.ndim == 2:
            pic = pic.reshape((pic.shape[0], pic.shape[1], 1))
        img = torch.from_numpy(pic.transpose((2, 0, 1)))
        return img.float()

    if accimage is not None and isinstance(pic, accimage.Image):
        nppic = np.zeros([pic.channels, pic.height, pic.width], dtype=np.float32)
        pic.copyto(nppic)
        return torch.from_numpy(nppic)

    if pic.mode == "I":
        img = torch.from_numpy(np.array(pic, np.int32, copy=False))
    elif pic.mode == "I;16":
        img = torch.from_numpy(np.array(pic, np.int16, copy=False))
    else:
        img = torch.ByteTensor(torch.ByteStorage.from_buffer(pic.tobytes()))

    if pic.mode == "YCbCr":
        nchannel = 3
    elif pic.mode == "I;16":
        nchannel = 1
    else:
        nchannel = len(pic.mode)

    img = img.view(pic.size[1], pic.size[0], nchannel)
    img = img.transpose(0, 1).transpose(0, 2).contiguous()

    if isinstance(img, torch.ByteTensor):
        return img.float()
    return img


def normalize(tensor, mean, std):
    if not _is_tensor_image(tensor):
        raise TypeError("tensor is not a torch image.")
    for t, m, s in zip(tensor, mean, std):
        t.sub_(m).div_(s)
    return tensor


def hflip(img):
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def vflip(img):
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    return img.transpose(Image.FLIP_TOP_BOTTOM)


def resize(img, size, interpolation=Image.BILINEAR):
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    if not (isinstance(size, int) or (isinstance(size, collections.abc.Iterable) and len(size) == 2)):
        raise TypeError("Got inappropriate size arg: {}".format(size))
    if isinstance(size, int):
        w, h = img.size
        if (w <= h and w == size) or (h <= w and h == size):
            return img
        if w < h:
            ow = size
            oh = int(size * h / w)
            return img.resize((ow, oh), interpolation)
        oh = size
        ow = int(size * w / h)
        return img.resize((ow, oh), interpolation)
    return img.resize(size[::-1], interpolation)


def scale(*args, **kwargs):
    warnings.warn("transforms.Scale is deprecated, please use transforms.Resize instead.")
    return resize(*args, **kwargs)


def pad(img, padding, fill=0):
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    if not isinstance(padding, (numbers.Number, tuple)):
        raise TypeError("Got inappropriate padding arg")
    if not isinstance(fill, (numbers.Number, str, tuple)):
        raise TypeError("Got inappropriate fill arg")
    if isinstance(padding, collections.abc.Sequence) and len(padding) not in [2, 4]:
        raise ValueError("Padding must be an int or a 2, or 4 element tuple")
    return ImageOps.expand(img, border=padding, fill=fill)


def adjust_brightness(img, brightness_factor):
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(brightness_factor)


def adjust_contrast(img, contrast_factor):
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(contrast_factor)


def adjust_saturation(img, saturation_factor):
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    enhancer = ImageEnhance.Color(img)
    return enhancer.enhance(saturation_factor)


def adjust_hue(img, hue_factor):
    if not (-0.5 <= hue_factor <= 0.5):
        raise ValueError("hue_factor is not in [-0.5, 0.5].")
    if not _is_pil_image(img):
        raise TypeError("img should be PIL Image. Got {}".format(type(img)))
    input_mode = img.mode
    if input_mode in {"L", "1", "I", "F"}:
        return img
    h, s, v = img.convert("HSV").split()
    np_h = np.array(h, dtype=np.uint8)
    with np.errstate(over="ignore"):
        np_h += np.uint8(hue_factor * 255)
    h = Image.fromarray(np_h, "L")
    return Image.merge("HSV", (h, s, v)).convert(input_mode)


