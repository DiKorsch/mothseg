import numpy as np
import matplotlib.pyplot as plt
import typing as T
import scalebar

from mothseg import PointsOfInterest

def plot(ims, contour, stats, pois: T.Optional[PointsOfInterest] = None, calib_result: T.Optional[scalebar.Result] = None):

    nrows = len(ims)
    ncols = 1
    if calib_result is not None:
        ncols += 1

    if calib_result.match is not None:
        ncols += 1

    fig = plt.figure(figsize=(16,9))
    spec = plt.GridSpec(nrows=nrows, ncols=ncols, figure=fig)
    #fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(16,9), squeeze=False)

    for _, _im in enumerate(ims):
        ax = plt.subplot(spec[_, 0]) #axs[np.unravel_index(_, axs.shape)]

        ax.imshow(_im)
        ax.plot(contour[:, 0], contour[:, 1], linewidth=2, alpha=0.6)
        x0, y0, x1, y1 = stats['contour_xmin'], stats['contour_ymin'], stats['contour_xmax'], stats['contour_ymax']

        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=None, edgecolor='m', linewidth=1))
        ax.annotate("", xy=(x0, y1), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='<->'))

        if 'calibration_length' not in stats:
            lengthx = '{:.0f} pixels'.format(x1 - x0)
        else:
            lengthx = '{:.2f} mm'.format(stats['width_calibrated'])

        ax.text(0.5 * (x1 + x0), y1 + 20,
                 lengthx,
                 horizontalalignment='center', verticalalignment='top', fontsize=18)

        if pois is not None:
            for name, poi in pois:
                ax.scatter(poi.col, poi.row, color='r')

            for key, p0, p1 in pois.named_distances:
                dist = stats[key]
                unit = "px" if 'calibration_length' not in stats else "mm"
                ax.annotate("", xy=(p0.col, p0.row), xytext=(p1.col, p1.row),
                            arrowprops=dict(arrowstyle='<->'))
                ax.text(x=(p0.col + p1.col)/2, y=(p0.row + p1.row)/2 + 15,
                        s=f"{dist:.2f} {unit}",
                        horizontalalignment='center',
                        verticalalignment='top',
                        fontsize=10,
                )

    if calib_result is not None:

        ax = plt.subplot(spec[:, 1])
        scalebar_crop = calib_result.scalebar
        ax.imshow(scalebar_crop, cmap=plt.cm.gray)
        ax.set_title(f"Detected scalebar: \n{calib_result.scale:.2f} px/mm")

        if calib_result.distances is not None:
            corners = calib_result.distances.corners
            mask = np.zeros(len(corners), dtype=bool)
            selected_corners, pairs = calib_result.best_corners()
            mask[selected_corners] = True

            ys, xs = corners[mask].transpose(1, 0)
            ax.scatter(xs, ys, marker="o", c="blue")

            ys, xs = corners[~mask].transpose(1, 0)
            ax.scatter(xs, ys, marker="o", c="red", alpha=0.5)

        if calib_result.match is not None:
            ax = plt.subplot(spec[0, 2])
            templ = calib_result.template
            ax.imshow(templ, cmap=plt.cm.gray)
            ax.set_title("Artifitial scalebar template")

            ax = plt.subplot(spec[1:, 2])
            match = calib_result.match
            ax.imshow(_im)
            ax.imshow(match, cmap=plt.cm.gray, alpha=0.5)
            ax.set_title("Template matches")

    plt.tight_layout()
    return fig


def imshow(ims):

    if len(ims) <= 3:
        nrows, ncols = 1, len(ims)
    else:
        nrows = int(np.ceil(np.sqrt(len(ims))))
        ncols = int(np.ceil( len(ims) / nrows))

    fig, axs = plt.subplots(ncols=ncols, nrows=nrows,
                            figsize=(16,9), squeeze=False)
    for i, (title, im, cmap) in enumerate(ims):
        ax = axs[np.unravel_index(i, axs.shape)]

        if isinstance(im, (list, tuple)):
            alpha = 1 / len([_im for _im in im if _im is not None])
            for _im, _cm in zip(im, cmap):
                if _im is not None:
                    ax.imshow(_im, cmap=_cm, alpha=alpha)
        else:
            ax.imshow(im, cmap=cmap)
        ax.set_title(title)

    for _ in range(i+1, nrows*ncols):
        ax = axs[np.unravel_index(_, axs.shape)]
        ax.axis("off")

    return fig, axs


def plot_interm(result: scalebar.Result):
    images = result.images
    im = result.images.original

    ROI = scalebar.utils.hide_non_roi(images.binary, result.roi_fraction, 127,
                                      location=result.scalebar_location)
    scalebar_crop = result.position.crop(images.equalized)
    match_crop = None
    if result.match is not None:
        match_crop = result.position.crop(result.match)
    px_per_mm = result.scale


    fig, axs = imshow([
        ("Input image", im, plt.cm.gray),
        ("B/W image", images.gray, plt.cm.gray),
        ("B/W image equalized", images.equalized, plt.cm.gray),

        ("Binarized", images.binary, plt.cm.gray),
        ("ROI to be masked", ROI, plt.cm.gray),
        ("Masked", images.masked, plt.cm.gray),

        # ("Template", , plt.cm.gray),
        ("Template Matches", (images.binary, result.match), (plt.cm.gray, plt.cm.viridis)),

        ("Cropped template matches", (scalebar_crop, match_crop), (plt.cm.gray, plt.cm.viridis)),
        (f"Scalebar | {px_per_mm} px/mm", scalebar_crop, plt.cm.gray),
    ])
    ax = axs[np.unravel_index(8, axs.shape)]
    ys, xs = result.distances.corners.transpose(1, 0)
    ax.scatter(xs, ys, marker=".", c="red", alpha=0.3)


    if px_per_mm is None:
        fig.suptitle("Estimation Failed!")

    else:
        W, H = result.image_size
        size = W / px_per_mm, H / px_per_mm
        fig.suptitle(" | ".join(
            [
                f"{px_per_mm:.2f} px/mm",
                f"Image size: {size[0]:.2f} x {size[1]:.2f}mm"
            ])
        )

    plt.tight_layout()
    return fig
