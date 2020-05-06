# image-encoders — Copyright (c) 2020, Novelty Factory KG.  See LICENSE for details.

import collections

import torch

from . import io
from . import convert


class ModuleConfig:
    def __init__(self, f, b):
        self.filters = f
        self.blocks = b


class Encoder(torch.nn.Module):
    def __init__(
        self, block_type, pool_type, input_type, in_channels=3, pretrained=True
    ):
        super(Encoder, self).__init__()

        blocks = self.make_blocks(self.CONFIG, block_type, pool_type, in_channels)
        if input_type == "RGB":
            blocks = [("0_0", convert.NormalizeRGB())] + list(blocks)

        self.features = torch.nn.Sequential(collections.OrderedDict(blocks))

        if pretrained is True:
            self.load_pretrained(self.FILENAME, self.HEXDIGEST)

    def load_pretrained(self, model: str, hexdigest: str):
        fullpath = io.download_to_file(model, hexdigest)
        self.load_state_dict(torch.load(fullpath), strict=False)

    def make_blocks(self, config, block_type, pool_type, in_channels):
        previous = in_channels
        for octave, module in enumerate(config):
            for block in range(module.blocks):
                yield f"{octave+1}_{block+1}", block_type(previous, module.filters)
                if block == module.blocks - 1:
                    yield f"{octave+2}_0", pool_type(kernel_size=(2, 2))
                previous = module.filters

    def extract(self, image, layers: list, start="0_0"):
        if len(layers) == 0:
            raise ValueError("Expecting list of output layers, e.g. ['1_1', '2_1'].")

        names = list(self.features._modules.keys())
        indices = [names.index(l) for l in layers]

        for i in range(names.index(start), max(indices) + 1):
            image = self.features[i].forward(image)
            if i in indices:
                yield names[i], image