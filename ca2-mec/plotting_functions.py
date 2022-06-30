

def set_size(width=345.0, fraction=1, mode='wide'):
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
    golden_ratio = (5**.5 - 1) / 2

    # Figure width in inches
    fig_width_in = fig_width_pt * inches_per_pt
    # Figure height in inches
    if mode == 'wide':
        fig_height_in = fig_width_in * golden_ratio
    elif mode == 'tall':
        fig_height_in = fig_width_in / golden_ratio
    elif mode == 'square':
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
