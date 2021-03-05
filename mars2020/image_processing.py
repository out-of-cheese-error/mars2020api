import numpy as np
from PIL import Image
from scipy.ndimage.filters import convolve
from mars2020 import mars2020api as mapi
import typing as ty


def demosaic_image(pil_image: Image, pattern="RGGB"):
    """
    Returns the demosaiced *RGB* colourspace array from given *Bayer* CFA using
    bilinear interpolation.
    Parameters
    ----------
    CFA : array_like
        *Bayer* CFA.
    pattern : unicode, optional
        **{'RGGB', 'BGGR', 'GRBG', 'GBRG'}**,
        Arrangement of the colour filters on the pixel array.
    Returns
    -------
    ndarray
        *RGB* colourspace array.
    """
    image: np.ndarray = np.array(pil_image, dtype=np.float64).mean(axis=2)
    image /= 255.0

    channels = dict((channel, np.zeros(image.shape)) for channel in "RGB")
    for channel, (y, x) in zip(pattern.upper(), [(0, 0), (0, 1), (1, 0), (1, 1)]):
        channels[channel][y::2, x::2] = 1

    R_m, G_m, B_m = tuple(channels[c].astype(bool) for c in "RGB")

    H_G = (
            np.array([[0, 1, 0], [1, 4, 1], [0, 1, 0]], dtype=np.float64) / 4
    )  # yapf: disable

    H_RB = (
            np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float64) / 4
    )  # yapf: disable

    R = convolve(image * R_m, H_RB)
    G = convolve(image * G_m, H_G)
    B = convolve(image * B_m, H_RB)

    output = np.concatenate(
        [x[..., np.newaxis] for x in np.array([R, G, B], dtype=np.float64)], axis=-1
    )
    return Image.fromarray((output * 255).astype(np.uint8), "RGB")


def get_image_clusters(image_collection: ty.Union[mapi.ImageDataCollection, ty.List[mapi.ImageData]],
                       cluster_length: int = 16) -> ty.List[ty.List[mapi.ImageData]]:
    if type(image_collection) == mapi.ImageDataCollection:
        images: ty.List[mapi.ImageData] = image_collection.images
    else:
        images = image_collection
    clusters: ty.Dict[str, ty.List[mapi.ImageData]] = {}
    for image in images:
        if len(image.image_id.split("_")[-1]) == 4:
            common_id: str = "_".join(image.image_id.split("_")[:-3])
            if common_id not in clusters:
                clusters[common_id] = [image]
            else:
                clusters[common_id].append(image)
    return [list(v) for k, v in clusters.items() if len(v) == cluster_length]


def grid_from_4x4_imageset(images: ty.List[mapi.ImageData]) -> Image:
    assert len(images) == 16
    for im in images:
        im.order = int(im.image_id.split("_")[-2])
    images = sorted(images, key=lambda x: x.order)
    image_frames = [np.array(x.image_data) for x in images]
    d1 = min(x.shape[0] for x in image_frames)
    d2 = min(x.shape[1] for x in image_frames)
    grid_image = np.zeros((d1 * 4, d2 * 4, 4), dtype="uint8")
    for i in range(4):
        for j in range(4):
            current = image_frames[i * 4 + j]
            grid_image[d1 * i: d1 * (i + 1), d2 * j: d2 * (j + 1), :3] = current[:d1, :d2]
            grid_image[d1 * i: d1 * (i + 1), d2 * j: d2 * (j + 1), -1] = 255
    return Image.fromarray(grid_image)


def grid_from_4x4_imageset_with_layers(images: ty.List[mapi.ImageData]):
    assert len(images) == 16
    for im in images:
        im.order = int(im.image_id.split("_")[-2])
    images = sorted(images, key=lambda x: x.order)
    image_frames = [np.array(x.image_data) for x in images]
    d1 = min(x.shape[0] for x in image_frames)
    d2 = min(x.shape[1] for x in image_frames)
    layers = []
    for i in range(4):
        for j in range(4):
            grid_image = np.zeros((d1 * 4, d2 * 4, 4), dtype="uint8")
            current = image_frames[i * 4 + j]
            grid_image[d1 * i: d1 * (i + 1), d2 * j: d2 * (j + 1), :3] = current[:d1, :d2]
            grid_image[d1 * i: d1 * (i + 1), d2 * j: d2 * (j + 1), -1] = 255
            layers.append(Image.fromarray(grid_image))
    return layers
