import numpy as np
from PIL import Image
from scipy.ndimage.filters import convolve

def demosaic_image(pil_image: Image, pattern='RGGB'):
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
    image /= np.max(image)
    
    pattern = pattern.upper()

    channels = dict((channel, np.zeros(image.shape)) for channel in 'RGB')
    for channel, (y, x) in zip(pattern, [(0, 0), (0, 1), (1, 0), (1, 1)]):
        channels[channel][y::2, x::2] = 1

    R_m, G_m, B_m = tuple(channels[c].astype(bool) for c in 'RGB')

    H_G = np.array(
        [[0, 1, 0],
         [1, 4, 1],
         [0, 1, 0]], dtype=np.float64) / 4  # yapf: disable

    H_RB = np.array(
        [[1, 2, 1],
         [2, 4, 2],
         [1, 2, 1]], dtype=np.float64) / 4  # yapf: disable

    R = convolve(image * R_m, H_RB)
    G = convolve(image * G_m, H_G)
    B = convolve(image * B_m, H_RB)
    
    output = np.concatenate([x[..., np.newaxis] for x in np.array([R, G, B], dtype=np.float64)], axis=-1)
    return Image.fromarray((output * 255).astype(np.uint8), "RGB")