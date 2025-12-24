from __future__ import annotations

from datetime import datetime
import os


def get_time() -> str:
    return (str(datetime.now())[:-10]).replace(" ", "-").replace(":", "-")


def get_kernel(height: int, width: int):
    # matches reference implementation
    return ((height + 15) // 16, (width + 15) // 16)


def parse_model_name(model_name: str):
    """
    Parses names like: 4_0_0_80x80_MiniFASNetV1SE.pth
    Returns: (h_input, w_input, model_type, scale)
    """
    info = model_name.split("_")[0:-1]
    h_input, w_input = info[-1].split("x")
    model_type = model_name.split(".pth")[0].split("_")[-1]
    if info[0] == "org":
        scale = None
    else:
        scale = float(info[0])
    return int(h_input), int(w_input), model_type, scale


def make_if_not_exist(folder_path: str):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


