import numpy as np
from utils import *
from scipy.interpolate import interp1d
import tqdm


def Xy_trial(
    spikes, tracking, categories_to_include, input_dim, window_size=0.1, res=10
):
    """
    Creates design matrix X, and label vector y from spikes, tracking and labels (meta data).
    X and y may later be used in statistical and machine learning models.

    Concretely, this methods creates X and y based on trials.

    # CATEGORIES
    # 0,1,2,3,4,(5) FIVE (or SIX) in total
    # MEANING:
    # 0: action1 (according to SORT of 'include_actions')
    # 1: action2 (according to SORT of 'include_actions')
    # 2: action3 (according to SORT of 'include_actions')
    # 3: action4 (according to SORT of 'include_actions')
    # 4: action5 (according to SORT of 'include_actions')
    # 5: action6 (according to SORT of 'include_actions')

    Parameters:
        spikes (list of neo.SpikeTrains): persistent neurons across trials
        tracking (dict of trial_ids:ndarrays): tracking information for each trial
        categories_to_include (list of ints): which trials to consider
        input_dim (int): number of persistent units (across trials)
        window_size (float): size of time window to compute spike rates, and infer collectively label over
        res (int): resolution (number of non-random uniform) samples to draw from linear interpolation across
                   time window. More samples refines choice of collectively label.

    Returns:
        X (nsamples, input_dim): number of samples and number of persistent cells (units)
        y (nsamples): vector of categories (e.g. [1,2,3,4,4,2,2,2,1] etc)
    """
    X = []
    y_true = []

    for k, action_id in enumerate(tracking):
        if k not in categories_to_include:
            continue

        _, _, t, _ = tracking[action_id].T
        trial_duration = t[-1] - t[0]
        num_samples = int(trial_duration / window_size) - 1
        X_tmp = np.zeros((input_dim, num_samples))
        y_tmp = np.zeros((num_samples))

        # set trial label - all labels for an action has the same label
        y_tmp += include_actions.index(action_id)

        for i in tqdm.trange(num_samples):
            time_window = (i * window_size, (i + 1) * window_size)
            # loop units for current action_id
            action_spikes = [
                spike_train
                for spike_train in spikes
                if spike_train.annotations["action_id"] == action_id
            ]
            for j, spike_train in enumerate(action_spikes):
                X_tmp[j, i] = np.sum(
                    (time_window[0] <= spike_train) & (spike_train <= time_window[1])
                )

        X.append(X_tmp)
        y_true.append(y_tmp)

    X = np.concatenate(X, axis=1).T
    y_true = np.concatenate(y_true)
    return X, y_true


def Xy_spatial(
    spikes, tracking, categories_to_include, input_dim, window_size=0.1, res=10
):
    """
    Creates design matrix X, and label vector y from spikes, tracking and labels (meta data).
    X and y may later be used in statistical and machine learning models.

    Concretely, this methods creates X and y based on spatial positions given by corner_masks(*).

    # CATEGORIES
    # 0,1,2,3,4 -> FIVE in total
    # MEANING:
    # 0: Rat in bottom left (BL) corner
    # 1: Rat in top left (TL) corner
    # 2: Rat in top right (TR) corner
    # 3: Rat in bottom right (BR) corner
    # 4: Rat in "center" (not in any corners) of the box

    Parameters:
        spikes (list of neo.SpikeTrains): persistent neurons across trials
        tracking (dict of trial_ids:ndarrays): tracking information for each trial
        categories_to_include (list of ints): which spatial corners to consider
        input_dim (int): number of persistent units (across trials)
        window_size (float): size of time window to compute spike rates, and infer collectively label over
        res (int): resolution (number of non-random uniform) samples to draw from linear interpolation across
                   time window. More samples refines choice of collectively label.

    Returns:
        X (nsamples, input_dim): number of samples and number of persistent cells (units)
        y (nsamples): vector of categories (e.g. [1,2,3,4,4,2,2,2,1] etc)
    """
    X = []
    y_true = []

    for action_id in tracking:
        x, y, t, _ = tracking[action_id].T
        cms = corner_masks(x, y)
        f_labels = interp1d(t, cms.T, kind="nearest", fill_value="extrapolate")

        trial_duration = t[-1] - t[0]
        num_samples = int(trial_duration / window_size) - 1
        X_tmp = np.zeros((input_dim, num_samples))
        y_tmp = np.zeros((num_samples))
        include_mask = np.ones(num_samples, dtype=bool)

        for i in tqdm.trange(num_samples):
            time_window = (i * window_size, (i + 1) * window_size)
            # interpolate and round social-label for current time window
            rat_pos = f_labels(np.linspace(*time_window, res))
            spatial_label = np.argmax(np.sum(rat_pos, axis=-1))
            if not (spatial_label in categories_to_include):
                include_mask[i] = False
                continue
            y_tmp[i] = spatial_label

            # loop units for current action_id
            action_spikes = [
                spike_train
                for spike_train in spikes
                if spike_train.annotations["action_id"] == action_id
            ]
            for j, spike_train in enumerate(action_spikes):
                X_tmp[j, i] = np.sum(
                    (time_window[0] <= spike_train) & (spike_train <= time_window[1])
                )

        X.append(X_tmp[:, include_mask])
        y_true.append(y_tmp[include_mask])

    X = np.concatenate(X, axis=1).T
    y_true = np.concatenate(y_true)
    return X, y_true


def Xy_social(
    spikes, tracking, categories_to_include, input_dim, window_size=0.1, res=10
):
    """
    Creates design matrix X, and label vector y from spikes, tracking and labels (meta data).
    X and y may later be used in statistical and machine learning models.

    Concretely, this methods creates X and y based on socialization given by corner_masks(*) and
    social_label(*) functions.

    # VALID CATEGORIES
    # -1,0,1,2 -> FOUR in total
    # MEANING:
    # -1: Rat NOT within margin of a transparent box
    # 0: Rat near EMPTY TRANSPARENT BOX
    # 1: Rat near FAMILIAR
    # 2: Rat near NOVEL

    Parameters:
        spikes (list of neo.SpikeTrains): persistent neurons across trials
        tracking (dict of trial_ids:ndarrays): tracking information for each trial
        categories_to_include (list of ints): considers which social_label(*)s to include
        input_dim (int): number of persistent units (across trials)
        window_size (float): size of time window to compute spike rates, and infer collectively label over
        res (int): resolution (number of non-random uniform) samples to draw from linear interpolation across
                   time window. More samples refines choice of collectively label.

    Returns:
        X (nsamples, input_dim): number of samples and number of persistent cells (units)
        y (nsamples): vector of categories (e.g. [1,2,3,4,4,2,2,2,1] etc)
    """
    X = []
    y_true = []

    for action_id in tracking:
        labels = social_label(action_id)
        labels = np.append(
            labels, -1
        )  # add "nobox" social label to centers of box, i.e. -1
        x, y, t, _ = tracking[action_id].T
        cms = corner_masks(x, y)
        f_labels = interp1d(t, cms.T, kind="nearest", fill_value="extrapolate")

        trial_duration = t[-1] - t[0]
        num_samples = int(trial_duration / window_size) - 1
        X_tmp = np.zeros((input_dim, num_samples))
        y_tmp = np.zeros((num_samples))
        include_mask = np.ones(num_samples, dtype=bool)

        for i in tqdm.trange(num_samples):
            time_window = (i * window_size, (i + 1) * window_size)
            # interpolate and round social-label for current time window
            rat_pos = f_labels(np.linspace(*time_window, res))
            idx = np.argmax(np.sum(rat_pos, axis=-1))
            if not (labels[idx] in categories_to_include):
                include_mask[i] = False
                continue
            y_tmp[i] = labels[idx]

            # loop units for current action_id
            action_spikes = [
                spike_train
                for spike_train in spikes
                if spike_train.annotations["action_id"] == action_id
            ]
            for j, spike_train in enumerate(action_spikes):
                X_tmp[j, i] = np.sum(
                    (time_window[0] <= spike_train) & (spike_train <= time_window[1])
                )

        X.append(X_tmp[:, include_mask])
        y_true.append(y_tmp[include_mask])

    X = np.concatenate(X, axis=1).T
    y_true = np.concatenate(y_true)
    return X, y_true


def distance_to_boundary(data, clf, labels=None, class_i=0):
    """
    parameters:
        data (nsamples,ndims): data points
        labels (nsamples,): integers indicating labelled classes
        class_i (int): indicating to which class hyperplane we are measuring distance to

    from clf we fetch:
        w (ndims,): hyper-plane normal
        b (float): scalar moving the hyper-plane from the origin (in the normal-direction)
    """
    w, b = clf.coef_[class_i], clf.intercept_[class_i]
    # distance along (+) or opposite (-) to normal
    dists = (data @ w + b) / np.linalg.norm(w)
    # remove normal induced sign()
    dists = abs(dists)
    if labels is not None:
        # add sign to distances depending on whether classification was correct
        preds = clf.predict(data)
        negative_sign_mask = preds != labels
        dists[negative_sign_mask] *= -1
    return dists


def relative_feature_importance(w):
    """
    Being parallel to the normal is the same as being
    orthogonal to the hyper-plane, and vice versa. 
    (wrt. hyperplane) Orthogonality => important, parallel => unimportant. 
    Hence, high values of w => parallel => orthogonal hyperplane => important.
    And, therefore, low values => unimportant.

    Normalise wrt. L1-norm to make distribution (sum to 1 and positive).
    """
    return abs(w) / np.sum(abs(w))

def relative_feature_importance_DEPRECATED(w):
    """
    -- SILLY LOGIC --
    Relative importance is trivial with an SVM, because
    the normal vector (w) already gives this (unscaled).


    Relative feature importance based on the normal vector.
    The intuition is that a feature is solely responsible for
    classfication if the hyper-plane defined by the normal w is
    orthogonal to that feature. Conversely, if it is paralell to a
    feature axis, that feature is completely redundant.

    We can calculate the angle between the normal and every feature
    basis vector with the cosine similiarty. Moreover, we don't care
    whether the hyper-plane is right or left angled to the basis vectors,
    hence we use the abs().

    Because we use basis vectors along the cardinal axis (e_1, ..., e_n) = I,
    we have that norm(e_i) = 1, and w @ e_i = w_i we can make the (vectorized)
    cosine similarity very simple, i.e. just using the normalized normal
    (vector -> giving in this case vectorization directly) directly in the
    arccos.

    Then we scale by np.pi/2 to get a percentage of orthogonality.

    Lastly, paralell normal directions means orthogonal decision
    boundary to feature. Hence large w_i (small angles) means important features,
    and low w_i (large angles) means unimportant features. We want
    the opposite, that large numbers indicate large importance, hence we
    "invert" the (relative) angles.
    """
    #angle = np.arccos(abs(w) / np.linalg.norm(w))
    angle = np.arccos(w / np.linalg.norm(w))
    relative = angle / (np.pi / 2)
    return 1 - relative
