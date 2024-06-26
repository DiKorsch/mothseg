import cv2
import typing as T
import numpy as np
import scipy as sp

from mothseg import utils
from mothseg.binarization import binarize


def segment(im, *, method: str = "grabcut+otsu",
            rescale: T.Optional[float] = None,
            channel: str = "saturation",
            ksize: T.Optional[int] = None,
            fill_holes: bool = True):

    if rescale is not None and 0 < rescale < 1.0:
        im = utils.rescale(im, rescale, channel_axis=2)
    else:
        rescale = 1.0

    hsv_im = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
    height, width, *_ = hsv_im.shape
    H, S, V = hsv_im.transpose(2, 0, 1)

    chan = {
        "hue": H,
        "saturation": S,
        "intensity": V,
        "value": V,
        "gray": V,
        "grey": V,
    }.get(channel)

    assert chan is not None, \
        f"Could not select desired channel: {channel}"

    if ksize is not None:
        chan = cv2.GaussianBlur(chan, (ksize, ksize), 0)

    bin_im = binarize(im, chan, method=method)

    contours, _ = cv2.findContours(bin_im, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    largest_contour = (contours[0] / rescale).astype(np.int32)

    stats = {

        'median-intensity': float(np.median(V)),
        'mean-intensity': float(np.mean(V)),
        'stddev-intensity': float(np.std(V)),
        'median-saturation': float(np.median(S)),
        'mean-saturation': float(np.mean(S)),
        'stddev-saturation': float(np.std(S)),
        'median-hue': float(np.median(H)),
        'mean-hue': float(np.mean(H)),
        'stddev-hue': float(np.std(H)),
        'image-width': int(width / rescale),
        'image-height': int(height / rescale),
        # these two do not make sense to me
        # 'seg-absolute-size': len(V),
        # 'seg-relative-size': len(V) / float( hsv_im.shape[0] * hsv_im.shape[1] ),

        'contour-length': len(largest_contour),
        'contour-area': cv2.contourArea(largest_contour),

        # compute bounding box
        'contour-xmin': int(np.amin( largest_contour[:, 0, 0] )),
        'contour-xmax': int(np.amax( largest_contour[:, 0, 0] )),
        'contour-ymin': int(np.amin( largest_contour[:, 0, 1] )),
        'contour-ymax': int(np.amax( largest_contour[:, 0, 1] )),

    }

    if fill_holes:
        bin_im = sp.ndimage.binary_fill_holes(bin_im).astype(bin_im.dtype)

    if rescale is not None and 0 < rescale < 1.0:
        chan = utils.rescale(chan, 1 / rescale)
        bin_im = utils.rescale(bin_im, 1 / rescale)

    return chan, stats, largest_contour[:, 0], bin_im
