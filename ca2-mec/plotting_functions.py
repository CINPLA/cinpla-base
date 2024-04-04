from scipy.interpolate import interp1d
import numpy as np


#def plot_decision_regions_v2(X, y, clf, feature_index=[0, 1], mean_shift=True, **kwargs):
def plot_decision_regions_v2(X, y, clf, feature_index=[0, 1], **kwargs):
    """
    Improved default setting for the plot_decision_regions from mlxtend.plotting.
    Makes it easier to plot decision boundary for a classifcator
    with more than 2 feature vectors, by default.

    Concretely, provide default scope to include all data points for every
    non-included feature.
    """
    from mlxtend.plotting import plot_decision_regions

    X_2d = X[feature_index]  # subselect two features
    feature_means = np.mean(X, axis=0)
    farthest_points = np.max(np.abs(X - feature_means), axis=0)
    #farthest_points *= farthest_points*1.1
    #print(farthest_points, farthest_points.shape)
    not_included_feature_idxs = list(set(range(X.shape[-1])) - set(feature_index))
    #filler_feature_values = {i: feature_means[i] if mean_shift else 0 for i in not_included_feature_idxs}
    filler_feature_values = {i: feature_means[i] for i in not_included_feature_idxs}
    filler_feature_ranges = {i: farthest_points[i] for i in not_included_feature_idxs}
    #print(filler_feature_values, filler_feature_ranges)
    return plot_decision_regions(
        X,
        y,
        clf,
        feature_index=feature_index,
        filler_feature_values=filler_feature_values,
        filler_feature_ranges=filler_feature_ranges,
        **kwargs
    )


def spike_track(x, y, t, spike_train, ax, spines=True):
    ax.plot(x, y, color="grey", alpha=0.5, zorder=0)
    spike_pos_f = interp1d(
        t, np.stack([x, y], axis=0), kind="linear", fill_value="extrapolate"
    )
    spike_pos = spike_pos_f(spike_train.times)
    ax.scatter(*spike_pos, color=(0.7, 0.2, 0.2), zorder=1)
    axis_off_labels_on(ax)
    # re-add spines
    if spines:
        for spine in ax.spines.values():
            spine.set_visible(True)
    # set x and y limits (boundary)
    ax.axis([0, 1, 0, 1])
    return ax


def set_size(width=345.0, fraction=1, mode="wide"):
    """Set figure dimensions to avoid scaling in LaTeX.

    Taken from:
    https://jwalton.info/Embed-Publication-Matplotlib-Latex/

    To get the width of a latex document, print it with:
    \the\textwidth
    (https://tex.stackexchange.com/questions/39383/determine-text-width)

    Parameters
    ----------
    width: float
            Document textwidth or columnwidth in pts
    fraction: float, optional
            Fraction of the width which you wish the figure to occupy
    mode: str
            Whether figure should be scaled by the golden ratio in height
            or width

    Returns
    -------
    fig_dim: tuple
            Dimensions of figure in inches
    """
    # Width of figure (in pts)
    fig_width_pt = width * fraction

    # Convert from pt to inches
    inches_per_pt = 1 / 72.27

    # Golden ratio to set aesthetic figure height
    # https://disq.us/p/2940ij3
    golden_ratio = (5 ** 0.5 - 1) / 2

    # Figure width in inches
    fig_width_in = fig_width_pt * inches_per_pt
    # Figure height in inches
    if mode == "wide":
        fig_height_in = fig_width_in * golden_ratio
    elif mode == "tall":
        fig_height_in = fig_width_in / golden_ratio
    elif mode == "square":
        fig_height_in = fig_width_in

    fig_dim = (fig_width_in, fig_height_in)

    return fig_dim


def axis_off_labels_on(ax):
    """Turn of ticks etc, but leaving labels which .axis('off') doesnt"""
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])
