import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from matplotlib import gridspec
import matplotlib.pyplot as plt


def get_unit_id(unit):
    try:
        uid = int(unit.annotations['name'].split('#')[-1])
    except AttributeError:
        uid = int(unit['name'].split('#')[-1])
    return uid


def dissimilarity(template_0, template_1):
    """
    Returns a value of dissimilarity of the mean between two or more
    spike templates.
    Parameters
    ----------
    templates : list object (see Notes)
        List containing the mean waveform over each electrode of spike sorted
        spiketrains from at least one electrode. All elements in the list must
        be of equal size, that is, the number of electrodes must be equal, and
        the number of points on the waveform must be equal.
    Returns
    -------
    diss : numpy array-like
        Returns a matrix containing the computed dissimilarity between the mean
        of the spiketrain, for the same channel.
    """
    max_val = np.max([np.max(np.abs(template_0)), np.max(np.abs(template_1))])

    t_i_lin = template_0.ravel()
    t_j_lin = template_1.ravel()


    return np.mean(np.abs(t_i_lin / max_val - t_j_lin / max_val))
    # return np.mean(np.abs(t_i_lin - t_j_lin))


def dissimilarity_weighted(waveforms_0, waveforms_1):
    """
    Returns a value of dissimilarity of the mean between two or more
    spike templates.
    Parameters
    ----------
    templates : list object (see Notes)
        List containing the mean waveform over each electrode of spike sorted
        spiketrains from at least one electrode. All elements in the list must
        be of equal size, that is, the number of electrodes must be equal, and
        the number of points on the waveform must be equal.
    Returns
    -------
    diss : numpy array-like
        Returns a matrix containing the computed dissimilarity between the mean
        of the spiketrain, for the same channel.
    """
    template1 = np.mean(waveforms_0, axis=0)

    template2 = np.mean(waveforms_1, axis=0)

    max_val = np.max([np.max(np.abs(template1)), np.max(np.abs(template2))])

    template1 /= max_val
    template2 /= max_val

    return np.sqrt(np.sum([(template1[i] - template2[i])**2 for i in range(template1.shape[0])], axis=0)).mean()


def compute_template(waveforms):
    return np.mean(waveforms, axis=0)


def get_waveform(spike_train):
    try:
        return spike_train.waveforms
    except AttributeError:
        return spike_train


def compute_templates(spike_trains):
    templates = [compute_template(get_waveform(st)) for st in spike_trains]
    return np.array(templates)


# def make_dissimilary_matrix(comp_object, channel_group):
#     templates_0 = comp_object.templates[channel_group][0]
#     templates_1 = comp_object.templates[channel_group][1]
#     diss_matrix = np.zeros((len(templates_0), len(templates_1)))
#
#     for i, t0 in enumerate(templates_0):
#         for j, t1 in enumerate(templates_1):
#             diss_matrix[i, j] = dissimilarity(t0, t1)
#
#     diss_matrix = pd.DataFrame(
#         diss_matrix,
#         index=comp_object.unit_ids[channel_group][0],
#         columns=comp_object.unit_ids[channel_group][1])
#
#     return diss_matrix


def make_dissimilary_matrix(comp_object, channel_group):
    waveforms_0 = comp_object.waveforms_0(channel_group)
    waveforms_1 = comp_object.waveforms_1(channel_group)
    diss_matrix = np.zeros((len(waveforms_0), len(waveforms_1)))

    for i, w0 in enumerate(waveforms_0):
        for j, w1 in enumerate(waveforms_1):
            diss_matrix[i, j] = dissimilarity_weighted(w0, w1)

    diss_matrix = pd.DataFrame(
        diss_matrix,
        index=comp_object.unit_ids[channel_group][0],
        columns=comp_object.unit_ids[channel_group][1])

    return diss_matrix


def make_possible_match(dissimilarity_scores, max_dissimilarity):
    """
    Given an agreement matrix and a max_dissimilarity threhold.
    Return as a dict all possible match for each spiketrain in each side.

    Note : this is symmetric.


    Parameters
    ----------
    dissimilarity_scores: pd.DataFrame

    max_dissimilarity: float


    Returns
    -----------
    best_match_12: pd.Series

    best_match_21: pd.Series

    """
    unit1_ids = np.array(dissimilarity_scores.index)
    unit2_ids = np.array(dissimilarity_scores.columns)

    # threhold the matrix
    scores = dissimilarity_scores.values.copy()
    scores[scores > max_dissimilarity] = np.inf

    possible_match_12 = {}
    for i1, u1 in enumerate(unit1_ids):
        inds_match = np.isfinite(scores[i1, :])
        possible_match_12[u1] = unit2_ids[inds_match]

    possible_match_21 = {}
    for i2, u2 in enumerate(unit2_ids):
        inds_match = np.isfinite(scores[:, i2])
        possible_match_21[u2] = unit1_ids[inds_match]

    return possible_match_12, possible_match_21


def make_best_match(dissimilarity_scores, max_dissimilarity):
    """
    Given an agreement matrix and a max_dissimilarity threhold.
    return a dict a best match for each units independently of others.

    Note : this is symmetric.

    Parameters
    ----------
    dissimilarity_scores: pd.DataFrame

    max_dissimilarity: float


    Returns
    -----------
    best_match_12: pd.Series

    best_match_21: pd.Series


    """
    unit1_ids = np.array(dissimilarity_scores.index)
    unit2_ids = np.array(dissimilarity_scores.columns)

    scores = dissimilarity_scores.values.copy()

    best_match_12 = pd.Series(index=unit1_ids, dtype='int64')
    for i1, u1 in enumerate(unit1_ids):
        ind_min = np.argmin(scores[i1, :])
        if scores[i1, ind_min] <= max_dissimilarity:
            best_match_12[u1] = unit2_ids[ind_min]
        else:
            best_match_12[u1] = -1

    best_match_21 = pd.Series(index=unit2_ids, dtype='int64')
    for i2, u2 in enumerate(unit2_ids):
        ind_min = np.argmin(scores[:, i2])
        if scores[ind_min, i2] <= max_dissimilarity:
            best_match_21[u2] = unit1_ids[ind_min]
        else:
            best_match_21[u2] = -1

    return best_match_12, best_match_21


def make_hungarian_match(dissimilarity_scores, max_dissimilarity):
    """
    Given an agreement matrix and a max_dissimilarity threhold.
    return the "optimal" match with the "hungarian" algo.
    This use internally the scipy.optimze.linear_sum_assignment implementation.

    Parameters
    ----------
    dissimilarity_scores: pd.DataFrame

    max_dissimilarity: float


    Returns
    -----------
    hungarian_match_12: pd.Series

    hungarian_match_21: pd.Series

    """
    unit1_ids = np.array(dissimilarity_scores.index)
    unit2_ids = np.array(dissimilarity_scores.columns)

    # threhold the matrix
    scores = dissimilarity_scores.values.copy()

    [inds1, inds2] = linear_sum_assignment(scores)

    hungarian_match_12 = pd.Series(index=unit1_ids, dtype='int64')
    hungarian_match_12[:] = -1
    hungarian_match_21 = pd.Series(index=unit2_ids, dtype='int64')
    hungarian_match_21[:] = -1

    for i1, i2 in zip(inds1, inds2):
        u1 = unit1_ids[i1]
        u2 = unit2_ids[i2]
        if dissimilarity_scores.at[u1, u2] < max_dissimilarity:
            hungarian_match_12[u1] = u2
            hungarian_match_21[u2] = u1

    return hungarian_match_12, hungarian_match_21


def plot_waveform(wf, fig, gs, axs=None, **kwargs):

    nrc = wf.shape[1]
    if axs is None:
        gs0 = gridspec.GridSpecFromSubplotSpec(1, nrc, subplot_spec=gs)
        axs = [fig.add_subplot(gs0[0])]
        axs.extend([fig.add_subplot(gs0[i], sharey=axs[0], sharex=axs[0]) for i in range(1, nrc)])
    for c in range(nrc):
        wf_ch = wf[:, c, :]
        m = np.mean(wf_ch, axis=0)
        sd = np.std(wf_ch, axis=0)
        samples = np.arange(wf.shape[2])
        axs[c].plot(samples, m, **kwargs)
        axs[c].fill_between(samples, m-sd, m+sd, alpha=.1, color=kwargs.get('color'))
        if c > 0:
            plt.setp(axs[c].get_yticklabels(), visible=False)
    return axs


def plot_template(template, fig, gs, axs=None, **kwargs):
    # template = np.squeeze(template).T
    nrc = template.shape[0]
    if axs is None:
        gs0 = gridspec.GridSpecFromSubplotSpec(1, nrc, subplot_spec=gs)
        axs = [fig.add_subplot(gs0[0])]
        axs.extend([fig.add_subplot(gs0[i], sharey=axs[0], sharex=axs[0]) for i in range(1, nrc)])
    for c in range(nrc):
        axs[c].plot(template[c, :], **kwargs)
        if c > 0:
            plt.setp(axs[c].get_yticklabels(), visible=False)
    return axs
