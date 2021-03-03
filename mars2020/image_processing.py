import numpy as np
from PIL import Image
import typing as ty
from scipy.ndimage import morphology


def red_mosaic_idx(d1: int, d2: int) -> ty.Tuple[np.ndarray, np.ndarray]:
    red_d1: ty.List[int] = list()
    red_d2: ty.List[int] = list()
    for i in range(d1):
        red_d2 += [j for j in range(0, d2, 2)]
        red_d1 += [i] * (d2 // 2)
    return np.array(red_d1), np.array(red_d2)


def green_mosaic_idx(d1: int, d2: int) -> ty.Tuple[np.ndarray, np.ndarray]:
    green_d1: ty.List[int] = list()
    green_d2: ty.List[int] = list()
    for i in range(d1):
        if (i % 2) == 0:
            green_d1 += [i] * (d2 // 2)
            green_d2 += [j for j in range(1, d2, 2)]
        else:
            continue
    return np.array(green_d1), np.array(green_d2)


def blue_mosaic_idx(d1: int, d2: int) -> ty.Tuple[np.ndarray, np.ndarray]:
    blue_d1: ty.List[int] = list()
    blue_d2: ty.List[int] = list()
    for i in range(d1):
        if (i % 2) != 0:
            blue_d1 += [i] * (d2//2)
            blue_d2 += [j for j in range(1, d2, 2)]
        else:
            continue
    return np.array(blue_d1), np.array(blue_d2)


def demosaic_image(pil_image: Image) -> Image:
    image: np.ndarray = np.array(pil_image)
    if len(image.shape) == 3:
        image: np.ndarray = image.astype(float).mean(axis=2).astype("uint8")
    d1, d2 = image.shape[:2]
    red_d1, red_d2 = red_mosaic_idx(d1, d2)
    green_d1, green_d2 = green_mosaic_idx(d1, d2)
    blue_d1, blue_d2 = blue_mosaic_idx(d1, d2)
    new_image = np.zeros((d1, d2, 3), dtype="uint8")
    new_image[red_d1, red_d2, 0] = image[red_d1, red_d2]
    new_image[green_d1, green_d2, 1] = image[green_d1, green_d2]
    new_image[blue_d1, blue_d2, 2] = image[blue_d1, blue_d2]
    new_image[:, :, 0] = morphology.grey_dilation(new_image[:, :, 0], size=3)
    new_image[:, :, 1] = morphology.grey_dilation(new_image[:, :, 1], size=3)
    new_image[:, :, 2] = morphology.grey_dilation(new_image[:, :, 2], size=3)
    return Image.fromarray(new_image)
