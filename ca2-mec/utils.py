import numpy as np
import numpy.ma as ma
import scipy
import neo
import expipe
import dataloader as dl
import spatial_maps as sp


def ratemap_fn2(x,y,t,spike_train,bins=32,fill_value='extrapolate'):
    """
    Calculate ratemap from tracking and spikes.
    Essentially: 
        1. calculate occupancy map (2d histogram of x,y-positions)
        2. calculate spike_map (2d histogram of x,y spike positions)
        3. calculate ratemap as spike_map / occupancy_map
        4. (optional) smooth
    
    ---
    OBS! Note that matplotlib.imshow shows matrices as images, where
    the "logically" the origin of the image is in the top left, which can
    be "inverted" by the origin='lower' option. However, also the x,y coordinates
    are logically swapped, such that 'x' in X[x,y] moves in the cardinal downward
    y-direction. To counter this, x,y are swapped in this function.
    ---
    
    params:
        x: (n,) np.ndarray of cardinal x-positions
        y: (n,) np.ndarray of cardinal y-positions
        t: (n,) np.ndarray of position times
        spike_train: neo.SpikeTrain of spike times
    """
    occupancy_map = scipy.stats.binned_statistic_2d(y,x, None, statistic='count', bins=bins).statistic
    occupancy_map[occupancy_map == 0] = np.nan
    f = scipy.interpolate.interp1d(t, np.stack([x,y]), kind='linear', bounds_error=False, fill_value=fill_value)
    xs,ys = f(np.array(spike_train.times))
    spike_map = scipy.stats.binned_statistic_2d(ys,xs, None, statistic='count', bins=bins).statistic
    return spike_map/occupancy_map, occupancy_map, spike_map


def ratemap_fn(
    x,
    y,
    t,
    spike_train,
    box_size=[1.0, 1.0],
    bin_size=0.02,
    smoothing=0.05,
    mask_zero_occupancy=True,
):
    smap = sp.SpatialMap(y, x, t, np.array(spike_train.times), box_size, bin_size)
    return smap.rate_map(smoothing, mask_zero_occupancy)


def data_scope(
    tracking_data: list,
    t: np.ndarray,
    spike_times: neo.core.spiketrain.SpikeTrain = None,
    scope: np.ndarray = np.array([0.0, 0.5]),
    t_start: float = 0,
    t_stop: float = None,
) -> (np.ndarray, np.ndarray, np.ndarray, neo.core.spiketrain.SpikeTrain):
    """
    Remove leading and trailing portion of data. Subsequently, limit scope of
    data manually.

    Parameters
    ----------
    tracking_data : list
        List of 1d-tracking data. e.g. [x,y,a], i.e. spatial, and angular
        1D arrays.
    t : np.ndarray
        1D array. Tracking data times.
    spike_times : neo.core.spiketrain.SpikeTrain
        (Optional) spike time data
    scope : np.ndarray
        1D, 2 elements, array. Elements are start and stop of data scope.
    t_start : float
        When to start including data (wrt. t). Previous data are removed.
    t_stop : float
        When to stop including data (wrt. t). Subsequent data are removed.

    Returns
    -------
    (t, tracking_data, spike_times) : (np.ndarray, list
    neo.core.spiketrain.SpikeTrain)
        the inputs limited to the selected scope.

    Example
    -------
    >>> import numpy as np
    >>> tracking_data, t = [np.arange(4), np.arange(4)], np.linspace(-0.5,1,4)
    >>> data_scope(tracking_data, t)
    ([array([0, 1]), array([0, 1])], array([-0.5,  0. ]), None)
    """
    if t_start is not None and t_stop is not None:
        # limit recording scope (i.e. remove leading and trailing 'extra' recording times)
        track_mask = (t < t_stop) & (t > t_start)
        t = t[track_mask]
        tracking_data = [track_data_i[track_mask] for track_data_i in tracking_data]
        if spike_times is not None:
            spike_mask = (spike_times < t_stop) & (spike_times > t_start)
            spike_times = spike_times[spike_mask]

    scope_idxs = np.ceil((scope * (len(t) - 1))).astype(int)
    # scope tracking
    t = t[slice(*scope_idxs)]
    tracking_data = [
        tracking_data_i[slice(*scope_idxs)] for tracking_data_i in tracking_data
    ]

    if spike_times is not None:
        # get scope edges in realtime
        scope_realtime = t[[0, -1]]
        # scope spike times
        spike_times_mask = (spike_times > scope_realtime[0]) & (
            spike_times < scope_realtime[1]
        )
        spike_times = spike_times[spike_times_mask]
    return tracking_data, t, spike_times


def nancorrcoef(X, Y):
    """
    Correlate X, Y (2D arrays) while ignoring nans
    """
    X = ma.masked_array(X, mask=np.isnan(X))
    Y = ma.masked_array(Y, mask=np.isnan(Y))
    return ma.corrcoef(X.flatten(), Y.flatten())[0, 1]


def action_is_recording(action_id):
    return ("type" in project.require_action(action_id).attributes) and (
        project.require_action(action_id).attributes["type"] == "Recording"
    )


def get_entity_actions(entity):
    return [action_id for action_id in actions if action_id[:3] == entity]


def trial_identity(action):
    if type(action) == str:
        project = expipe.get_project(dl.project_path())
        action = project.require_action(action)
    for tag in action.attributes["tags"]:
        if "trial_id" in tag:
            return tag.split("_")[-1]


def action_identity(trial, actions, project):
    """
    Return the action_id that matches the trial_ids.
    """
    for action in actions:
        if trial == trial_identity(project.require_action(action)):
            return action
    return None


def trial_label(action):
    """
    Returns the trial label (number) for the action.
    """
    return int(trial_id(action)[1])


def social_label(spike_train):
    """
    socializing can happen at either of the four corners of the box (space).
    there are four types of socializing: nobox (-1) empty (0), familiar (1) or novel (2).
    this gives a 4d-vector with four possible categories each.
    """

    def social_category(string):
        """helper function"""
        str1,str2 = string.split("_")[3:]
        if str1 == "nobox":
            return -1
        if str2 == "e":
            return 0
        if str2 == "f":
            return 1
        if str2 == "n":
            return 2

    def corner_idx(string):
        """helper function"""
        string = string.split("_")[2] # tl,tr,bl,br
        if string == "bl":
            return 0
        if string == "tl":
            return 1
        if string == "tr":
            return 2
        if string == "br":
            return 3

    tags = spike_train.annotations["tags"]
    social_types = np.zeros(4)
    for tag in tags:
        if not "corner" in tag:
            continue
        # BL, TL, TR and BR, respectively
        social_types[corner_idx(tag)] = social_category(tag)

    return social_types


def rotmat(theta):
    """
    Returns a 2D rotation matrix for theta degrees.
    """
    theta = np.radians(theta)
    r = np.array(((np.cos(theta), -np.sin(theta)), (np.sin(theta), np.cos(theta))))
    return r


def corner_masks(x, y, margin=0.4, **kwargs):
    """
    Find corner and center of box masks.
    """
    assert (
        margin < 0.5 and margin > 0
    ), "OBS! Margin must be positive and max half the box size, i.e. 0.5 OBS!"

    # center x and y coordinates
    x = x - 0.5
    y = y - 0.5
    pos = np.array([x, y]).T

    # create cardinal basis vectors
    ex, ey = np.arange(2), np.arange(2)[::-1]

    # create corner vectors: BL, TL, TR and BR, respectively
    corners = np.array([-ex - ey, -ex + ey, ex + ey, ex - ey])

    corner_masks = np.zeros((len(x), 5), dtype=bool)
    for i, corner in enumerate(corners):
        # find which quadrant positions are in, and if they are within the
        # box margins. The intersection gives the grand mask.
        quadrant_mask = ((pos * corner) > 0).all(axis=-1)
        margin_mask = (np.abs(pos) > (np.ones(2) * (0.5 - margin))).all(axis=-1)
        corner_masks[:, i] = quadrant_mask & margin_mask

    # inverse of union over corner masks
    corner_masks[:, -1] = ~np.array(corner_masks).any(axis=-1)
    return corner_masks


def truncate_recording(arr, t, t_start=0.0, t_stop=None):
    """
    Truncate recording, in seconds.
    if t_start or t_stop is None, then don't truncate
    """
    if not isinstance(arr, np.ndarray):
        return arr
    mask = np.ones(len(arr), dtype=bool)
    mask = (t > t_start) if t_start is not None else mask
    mask = mask & (t < t_stop) if t_stop is not None else mask
    return arr[mask]


def truncate_tracking_dict(tracking_dict, t_start=0.0, t_stop=None):
    """
    Truncate tracking dict, in seconds.
    if t_start or t_stop is None, then don't truncate
    """
    t = np.copy(tracking_dict["t"])
    for key in tracking_dict:
        tracking_dict[key] = truncate_recording(tracking_dict[key], t, t_start, t_stop)
    return tracking_dict


def truncate_spikes(spike_times, t):
    """
    Truncate spikes to the same length as the recording.
    """
    scope_realtime = t[[0, -1]]
    # scope spike times
    spike_times_mask = (spike_times > scope_realtime[0]) & (
        spike_times < scope_realtime[1]
    )
    spike_times = spike_times[spike_times_mask]
    return spike_times


def persistent_units(spikes, include_trials=None):
    """
    Find all units that persist across all trials for each animal (cumulative intersection over trials)
    """
    if include_trials is None:
        # include all trials
        include_trials = list(spikes.keys())

    punits = []
    for trial in spikes:
        if trial not in include_trials:
            continue
        if not punits:
            # empty list
            punits = list(spikes[trial].keys())
            continue
        punits = list(spikes[trial].keys() & punits)
    return punits


def transform_coordinates(x, y, theta=90, **kwargs):
    """
    Transform tracking coordinates to align with physical coordinates
    For this project (CA2 MEC): rotate recorded coordinates 90 degrees,
    followed by a shift to make values positive afterwards.
    """
    # rotate x,y coordinates 90 degrees using a 2D rotation matrix transform
    coords = rotmat(theta) @ np.array([x, y])
    # shift new x-coordinates to be positive
    coords -= np.array([[-1], [0]])
    return coords

