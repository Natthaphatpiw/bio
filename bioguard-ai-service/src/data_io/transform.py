# -*- coding: utf-8 -*-
from __future__ import division

import math
import random
import numpy as np
import numbers
import types
from PIL import Image

from src.data_io import functional as F

__all__ = ["Compose", "ToTensor", "Normalize", "RandomHorizontalFlip", "Lambda"]


class Compose(object):
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, img):
        for t in self.transforms:
            img = t(img)
        return img


class ToTensor(object):
    def __call__(self, pic):
        return F.to_tensor(pic)


class Normalize(object):
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, tensor):
        return F.normalize(tensor, self.mean, self.std)


class Lambda(object):
    def __init__(self, lambd):
        assert isinstance(lambd, types.LambdaType)
        self.lambd = lambd

    def __call__(self, img):
        return self.lambd(img)


class RandomHorizontalFlip(object):
    def __call__(self, img):
        if random.random() < 0.5:
            return F.hflip(img)
        return img


