# This is work in progress,
import neo
import numpy as np
import exdir
import exdir.plugins.quantities
import exdir.plugins.git_lfs
import pathlib
import os
import quantities as pq
import spikeextractors as se
import expipe
import spatial_maps as sp
import warnings


def project_path():
    path = os.environ.get("CA2MEC_PATH")
    if path is None:
        raise Exception("Need to set `CA2MEC_PATH` as environment variable first.")
    else:
        path = pathlib.Path(path)
    return path


def view_active_channels(action, sorter):
    path = get_data_path(action)
    elphys_path = path / "processing" / "electrophysiology"
    sorter_path = elphys_path / "spikesorting" / sorter / "phy"
    return np.load(sorter_path / "channel_map_si.npy")


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


def _cut_to_same_len(*args):
    out = []
    lens = []
    for arg in args:
        lens.append(len(arg))
    minlen = min(lens)
    for arg in args:
        out.append(arg[:minlen])
    return out


def _read_epoch(exdir_file, path, lazy=False):
    group = exdir_file[path]
    if lazy:
        times = []
    else:
        times = pq.Quantity(group["timestamps"].data, group["timestamps"].attrs["unit"])

    if "durations" in group and not lazy:
        durations = pq.Quantity(
            group["durations"].data, group["durations"].attrs["unit"]
        )
    elif "durations" in group and lazy:
        durations = []
    else:
        durations = None

    if "data" in group and not lazy:
        if "unit" not in group["data"].attrs:
            labels = group["data"].data
        else:
            labels = pq.Quantity(group["data"].data, group["data"].attrs["unit"])
    elif "data" in group and lazy:
        labels = []
    else:
        labels = None
    annotations = {"exdir_path": path}
    annotations.update(group.attrs.to_dict())

    if lazy:
        lazy_shape = (group.attrs["num_samples"],)
    else:
        lazy_shape = None
    epo = neo.Epoch(
        times=times,
        durations=durations,
        labels=labels,
        lazy_shape=lazy_shape,
        **annotations
    )

    return epo


def velocity_filter(x, y, t, threshold):
    """
    Removes values above threshold
    Parameters
    ----------
    x : quantities.Quantity array in m
        1d vector of x positions
    y : quantities.Quantity array in m
        1d vector of y positions
    t : quantities.Quantity array in s
        1d vector of times at x, y positions
    threshold : float
    """
    assert len(x) == len(y) == len(t), "x, y, t must have same length"
    vel = np.gradient([x, y], axis=1) / np.gradient(t)
    speed = np.linalg.norm(vel, axis=0)
    speed_mask = speed < threshold
    speed_mask = np.append(speed_mask, 0)
    x = x[np.where(speed_mask)]
    y = y[np.where(speed_mask)]
    t = t[np.where(speed_mask)]
    return x, y, t


def interp_filt_position(x, y, tm, fs=100, f_cut=10):
    """
    rapid head movements will contribute to velocity artifacts,
    these can be removed by low-pass filtering
    see http://www.ncbi.nlm.nih.gov/pmc/articles/PMC1876586/
    code addapted from Espen Hagen
    Parameters
    ----------
    x : quantities.Quantity array in m
        1d vector of x positions
    y : quantities.Quantity array in m
        1d vector of y positions
    tm : quantities.Quantity array in s
        1d vector of times at x, y positions
    fs : quantities scalar in Hz
        return radians
    Returns
    -------
    out : angles, resized t
    """
    import scipy.signal as ss

    assert len(x) == len(y) == len(tm), "x, y, t must have same length"
    t = np.arange(tm.min(), tm.max() + 1.0 / fs, 1.0 / fs)
    x = np.interp(t, tm, x)
    y = np.interp(t, tm, y)
    # rapid head movements will contribute to velocity artifacts,
    # these can be removed by low-pass filteringpar
    # see http://www.ncbi.nlm.nih.gov/pmc/articles/PMC1876586/
    # code addapted from Espen Hagen
    b, a = ss.butter(N=1, Wn=f_cut * 2 / fs)
    # zero phase shift filter
    x = ss.filtfilt(b, a, x)
    y = ss.filtfilt(b, a, y)
    # we tolerate small interpolation errors
    x[(x > -1e-3) & (x < 0.0)] = 0.0
    y[(y > -1e-3) & (y < 0.0)] = 0.0

    return x, y, t


def rm_nans(*args):
    """
    Removes nan from all corresponding arrays
    Parameters
    ----------
    args : arrays, lists or quantities which should have removed nans in
           all the same indices
    Returns
    -------
    out : args with removed nans
    """
    nan_indices = []
    for arg in args:
        nan_indices.extend(np.where(np.isnan(arg))[0].tolist())
    nan_indices = np.unique(nan_indices)
    out = []
    for arg in args:
        out.append(np.delete(arg, nan_indices))
    return out


def unit_path(channel_id, unit_id):
    return "/processing/electrophysiology/channel_group_{}/UnitTimes/{}".format(
        channel_id, unit_id
    )


def load_leds(data_path):
    root_group = exdir.File(
        data_path, "r", plugins=[exdir.plugins.quantities, exdir.plugins.git_lfs]
    )

    # tracking data
    position_group = root_group["processing"]["tracking"]["camera_0"]["Position"]
    stop_time = position_group.attrs["stop_time"]
    x1, y1 = position_group["led_0"]["data"].data.T
    t1 = position_group["led_0"]["timestamps"].data
    x2, y2 = position_group["led_1"]["data"].data.T
    t2 = position_group["led_1"]["timestamps"].data

    return x1, y1, t1, x2, y2, t2, stop_time


def filter_xy_zero(x, y, t):
    (idxs,) = np.where((x == 0) & (y == 0))
    return [np.delete(a, idxs) for a in [x, y, t]]


def filter_xy_box_size(x, y, t, box_size):
    (idxs,) = np.where((x > box_size[0]) | (x < 0) | (y > box_size[1]) | (y < 0))
    return [np.delete(a, idxs) for a in [x, y, t]]


def filter_t_zero_duration(x, y, t, duration):
    (idxs,) = np.where((t < 0) | (t > duration))
    return [np.delete(a, idxs) for a in [x, y, t]]


def load_head_direction(data_path, sampling_rate, low_pass_frequency, box_size):
    from head_direction.head import head_direction

    x1, y1, t1, x2, y2, t2, stop_time = load_leds(data_path)

    x1, y1, t1 = rm_nans(x1, y1, t1)
    x2, y2, t2 = rm_nans(x2, y2, t2)

    x1, y1, t1 = filter_t_zero_duration(x1, y1, t1, stop_time.magnitude)
    x2, y2, t2 = filter_t_zero_duration(x2, y2, t2, stop_time.magnitude)

    # OE saves 0.0 when signal is lost, these can be removed
    x1, y1, t1 = filter_xy_zero(x1, y1, t1)
    x2, y2, t2 = filter_xy_zero(x2, y2, t2)

    # x1, y1, t1 = filter_xy_box_size(x1, y1, t1, box_size)
    # x2, y2, t2 = filter_xy_box_size(x2, y2, t2, box_size)

    x1, y1, t1 = interp_filt_position(
        x1, y1, t1, fs=sampling_rate, f_cut=low_pass_frequency
    )
    x2, y2, t2 = interp_filt_position(
        x2, y2, t2, fs=sampling_rate, f_cut=low_pass_frequency
    )

    x1, y1, t1, x2, y2, t2 = _cut_to_same_len(x1, y1, t1, x2, y2, t2)

    check_valid_tracking(x1, y1, box_size)
    check_valid_tracking(x2, y2, box_size)

    angles, times = head_direction(x1, y1, x2, y2, t1)
    return angles, times


def check_valid_tracking(x, y, box_size):
    if np.isnan(x).any() and np.isnan(y).any():
        raise ValueError(
            "nans found in  position, "
            + "x nans = %i, y nans = %i" % (sum(np.isnan(x)), sum(np.isnan(y)))
        )

    if x.min() < 0 or x.max() > box_size[0] or y.min() < 0 or y.max() > box_size[1]:
        warnings.warn(
            "Invalid values found "
            + "outside box: min [x, y] = [{}, {}], ".format(x.min(), y.min())
            + "max [x, y] = [{}, {}]".format(x.max(), y.max())
        )


def load_tracking(
    data_path, sampling_rate, low_pass_frequency, box_size, velocity_threshold=5
):
    x1, y1, t1, x2, y2, t2, stop_time = load_leds(data_path)
    x1, y1, t1 = rm_nans(x1, y1, t1)
    x2, y2, t2 = rm_nans(x2, y2, t2)

    x1, y1, t1 = filter_t_zero_duration(x1, y1, t1, stop_time.magnitude)
    x2, y2, t2 = filter_t_zero_duration(x2, y2, t2, stop_time.magnitude)

    # select data with least nan
    if len(x1) > len(x2):
        x, y, t = x1, y1, t1
    else:
        x, y, t = x2, y2, t2

    # OE saves 0.0 when signal is lost, these can be removed
    x, y, t = filter_xy_zero(x, y, t)

    # x, y, t = filter_xy_box_size(x, y, t, box_size)

    # remove velocity artifacts
    x, y, t = velocity_filter(x, y, t, velocity_threshold)

    x, y, t = interp_filt_position(x, y, t, fs=sampling_rate, f_cut=low_pass_frequency)

    check_valid_tracking(x, y, box_size)

    vel = np.gradient([x, y], axis=1) / np.gradient(t)
    speed = np.linalg.norm(vel, axis=0)

    return x, y, t, speed


def get_data_path(action):
    action_path = action._backend.path
    project_path = action_path.parent.parent
    # data_path = action.data['main']
    data_path = str(pathlib.Path(pathlib.PureWindowsPath(action.data["main"])))

    #    print("Project path: {}\nData path: {}".format(project_path, data_path))
    return project_path / data_path


def get_sample_rate(data_path, default_sample_rate=30000 * pq.Hz):
    f = exdir.File(str(data_path), "r", plugins=[exdir.plugins.quantities])
    sr = default_sample_rate
    if "processing" in f.keys():
        processing = f["processing"]
        if "electrophysiology" in processing.keys():
            ephys = processing["electrophysiology"]
            if "sample_rate" in ephys.attrs.keys():
                sr = ephys.attrs["sample_rate"]
    return sr


def get_duration(data_path):
    f = exdir.File(str(data_path), "r", plugins=[exdir.plugins.quantities])

    return f.attrs["session_duration"].rescale("s")


def load_lfp(data_path, channel_group, lim=None):
    f = exdir.File(str(data_path), "r", plugins=[exdir.plugins.quantities])
    # LFP
    _lfp = f["processing"]["electrophysiology"][
        "channel_group_{}".format(channel_group)
    ]["LFP"]
    keys = list(_lfp.keys())
    electrode_value = [_lfp[key]["data"].value.flatten() for key in keys]
    electrode_idx = [_lfp[key].attrs["electrode_idx"] for key in keys]
    sampling_rate = _lfp[keys[0]].attrs["sample_rate"]
    units = _lfp[keys[0]]["data"].attrs["unit"]
    LFP = np.r_[[_lfp[key]["data"].value.flatten() for key in keys]].T
    LFP = LFP[:, np.argsort(electrode_idx)]
    if lim is None:
        t_stop = f.attrs["session_duration"]
    else:
        assert len(lim) == 2
        times = np.arange(LFP.shape[0]) / sampling_rate.magnitude
        mask = (times >= lim[0]) & (times <= lim[1])
        LFP = LFP[mask, :]
        t_stop = lim[1]

    LFP = neo.AnalogSignal(
        LFP,
        units=units,
        t_stop=t_stop,
        sampling_rate=sampling_rate,
        **{"electrode_idx": electrode_idx}
    )
    LFP = LFP.rescale("mV")
    return LFP


def sort_by_cluster_id(spike_trains):
    if len(spike_trains) == 0:
        return spike_trains
    if "name" not in spike_trains[0].annotations:
        print("Unable to get cluster_id, save with phy to create")
    sorted_sptrs = sorted(
        spike_trains,
        key=lambda x: int(x.annotations["name"].lower().replace("unit #", "")),
    )
    return sorted_sptrs


def load_epochs(data_path):
    f = exdir.File(str(data_path), "r", plugins=[exdir.plugins.quantities])
    epochs_group = f["epochs"]
    epochs = []
    for group in epochs_group.values():
        if "timestamps" in group.keys():
            epo = _read_epoch(f, group.name)
            epochs.append(epo)
        else:
            for g in group.values():
                if "timestamps" in g.keys():
                    epo = _read_epoch(f, g.name)
                    epochs.append(epo)
    return epochs


def get_channel_groups(data_path):
    """
    Returns channeø groups of processing/electrophysiology
    Parameters
    ----------
    data_path: Path
        The action data path
    Returns
    -------
    channel groups: list
        The channel groups
    """
    f = exdir.File(str(data_path), "r", plugins=[exdir.plugins.quantities])
    channel_groups = []
    if "processing" in f.keys():
        processing = f["processing"]
        if "electrophysiology" in processing.keys():
            ephys = processing["electrophysiology"]
            for chname, ch in ephys.items():
                if "channel" in chname:
                    channel_groups.append(int(chname.split("_")[-1]))
    return channel_groups


def get_unit_id(unit):
    try:
        uid = int(unit.annotations["name"].split("#")[-1])
    except AttributeError:
        uid = int(unit["name"].split("#")[-1])
    return uid


def load_spiketrains(data_path, channel_group=None, load_waveforms=False, lim=None):
    """
    Parameters
    ----------
    data_path
    channel_group
    load_waveforms
    remove_label
    Returns
    -------
    """
    sample_rate = get_sample_rate(data_path)
    sorting = se.ExdirSortingExtractor(
        data_path,
        sampling_frequency=sample_rate,
        channel_group=channel_group,
        load_waveforms=load_waveforms,
    )
    sptr = []
    # build neo pbjects
    for u in sorting.get_unit_ids():
        times = sorting.get_unit_spike_train(u) / sample_rate
        if lim is None:
            t_stop = get_duration(data_path)
            t_start = 0 * pq.s
        else:
            t_start = pq.Quantity(lim[0], "s")
            t_stop = pq.Quantity(lim[1], "s")
        mask = (times >= t_start) & (times <= t_stop)
        times = times[mask]
        if load_waveforms and "waveforms" in sorting.get_unit_spike_feature_names(u):
            wf = sorting.get_unit_spike_features(u, "waveforms")
            wf = wf[mask] * pq.uV
        else:
            wf = None
        st = neo.SpikeTrain(
            times=times, t_stop=t_stop, waveforms=wf, sampling_rate=sample_rate
        )
        for p in sorting.get_unit_property_names(u):
            st.annotations.update({p: sorting.get_unit_property(u, p)})
        sptr.append(st)

    return sptr


def load_unit_annotations(data_path, channel_group):
    """
    Parameters
    ----------
    data_path
    channel_group
    Returns
    -------
    """
    sample_rate = get_sample_rate(data_path)
    sorting = se.ExdirSortingExtractor(
        data_path,
        sampling_frequency=sample_rate,
        channel_group=channel_group,
        load_waveforms=False,
    )
    units = []
    for u in sorting.get_unit_ids():
        annotations = {}
        for p in sorting.get_unit_property_names(u):
            annotations.update({p: sorting.get_unit_property(u, p)})
        units.append(annotations)
    return units


class Template:
    def __init__(self, sptr):
        self.data = np.array(sptr.waveforms.mean(0))
        self.sampling_rate = float(sptr.sampling_rate)


class Data:
    def __init__(self, stim_mask=False, baseline_duration=None, **kwargs):
        self.project_path = project_path()
        self.params = kwargs
        self.project = expipe.get_project(self.project_path)
        self.actions = self.project.actions
        self._spike_trains = {}
        self._templates = {}
        self._stim_times = {}
        self._unit_names = {}
        self._tracking = {}
        self._head_direction = {}
        self._lfp = {}
        self._occupancy = {}
        self._rate_maps = {}
        self._rate_maps_split = {}
        self._prob_dist = {}
        self._spatial_bins = None
        self.stim_mask = stim_mask
        self.baseline_duration = baseline_duration

    def data_path(self, action_id):
        return (
            pathlib.Path(self.project_path)
            / "actions"
            / action_id
            / "data"
            / "main.exdir"
        )

    def get_lim(self, action_id):
        stim_times = self.stim_times(action_id)
        if stim_times is None:
            if self.baseline_duration is None:
                return [0, get_duration(self.data_path(action_id))]
            else:
                return [0, self.baseline_duration]
        stim_times = np.array(stim_times)
        return [stim_times.min(), stim_times.max()]

    def duration(self, action_id):
        return get_duration(self.data_path(action_id))

    def tracking(self, action_id):
        if action_id not in self._tracking:
            x, y, t, speed = load_tracking(
                self.data_path(action_id),
                sampling_rate=self.params["position_sampling_rate"],
                low_pass_frequency=self.params["position_low_pass_frequency"],
                box_size=self.params["box_size"],
            )
            if self.stim_mask:
                t1, t2 = self.get_lim(action_id)
                mask = (t >= t1) & (t <= t2)
                x = x[mask]
                y = y[mask]
                t = t[mask]
                speed = speed[mask]
            self._tracking[action_id] = {"x": x, "y": y, "t": t, "v": speed}
        return self._tracking[action_id]

    @property
    def spatial_bins(self):
        if self._spatial_bins is None:
            box_size_, bin_size_ = sp.maps._adjust_bin_size(
                box_size=self.params["box_size"], bin_size=self.params["bin_size"]
            )
            xbins, ybins = sp.maps._make_bins(box_size_, bin_size_)
            self._spatial_bins = (xbins, ybins)
            self.box_size_, self.bin_size_ = box_size_, bin_size_
        return self._spatial_bins

    def occupancy(self, action_id):
        if action_id not in self._occupancy:
            xbins, ybins = self.spatial_bins

            occupancy_map = sp.maps._occupancy_map(
                self.tracking(action_id)["x"],
                self.tracking(action_id)["y"],
                self.tracking(action_id)["t"],
                xbins,
                ybins,
            )
            threshold = self.params.get("occupancy_threshold")
            if threshold is not None:
                occupancy_map[occupancy_map <= threshold] = 0
            self._occupancy[action_id] = occupancy_map
        return self._occupancy[action_id]

    def prob_dist(self, action_id):
        if action_id not in self._prob_dist:
            xbins, ybins = xbins, ybins = self.spatial_bins
            prob_dist = sp.stats.prob_dist(
                self.tracking(action_id)["x"],
                self.tracking(action_id)["y"],
                bins=(xbins, ybins),
            )
            self._prob_dist[action_id] = prob_dist
        return self._prob_dist[action_id]

    def rate_map_split(self, action_id, channel_group, unit_name, smoothing):
        make_rate_map = False
        if action_id not in self._rate_maps_split:
            self._rate_maps_split[action_id] = {}
        if channel_group not in self._rate_maps_split[action_id]:
            self._rate_maps_split[action_id][channel_group] = {}
        if unit_name not in self._rate_maps_split[action_id][channel_group]:
            self._rate_maps_split[action_id][channel_group][unit_name] = {}
        if smoothing not in self._rate_maps_split[action_id][channel_group][unit_name]:
            make_rate_map = True

        if make_rate_map:
            xbins, ybins = self.spatial_bins
            x, y, t = map(self.tracking(action_id).get, ["x", "y", "t"])
            spikes = self.spike_train(action_id, channel_group, unit_name)
            t_split = t[-1] / 2
            mask_1 = t < t_split
            mask_2 = t >= t_split
            x_1, y_1, t_1 = x[mask_1], y[mask_1], t[mask_1]
            x_2, y_2, t_2 = x[mask_2], y[mask_2], t[mask_2]
            spikes_1 = spikes[spikes < t_split]
            spikes_2 = spikes[spikes >= t_split]
            occupancy_map_1 = sp.maps._occupancy_map(x_1, y_1, t_1, xbins, ybins)
            occupancy_map_2 = sp.maps._occupancy_map(x_2, y_2, t_2, xbins, ybins)

            spike_map_1 = sp.maps._spike_map(x_1, y_1, t_1, spikes_1, xbins, ybins)
            spike_map_2 = sp.maps._spike_map(x_2, y_2, t_2, spikes_2, xbins, ybins)

            smooth_spike_map_1 = sp.maps.smooth_map(
                spike_map_1, bin_size=self.bin_size_, smoothing=smoothing
            )
            smooth_spike_map_2 = sp.maps.smooth_map(
                spike_map_2, bin_size=self.bin_size_, smoothing=smoothing
            )
            smooth_occupancy_map_1 = sp.maps.smooth_map(
                occupancy_map_1, bin_size=self.bin_size_, smoothing=smoothing
            )
            smooth_occupancy_map_2 = sp.maps.smooth_map(
                occupancy_map_2, bin_size=self.bin_size_, smoothing=smoothing
            )

            rate_map_1 = smooth_spike_map_1 / smooth_occupancy_map_1
            rate_map_2 = smooth_spike_map_2 / smooth_occupancy_map_2
            self._rate_maps_split[action_id][channel_group][unit_name][smoothing] = [
                rate_map_1,
                rate_map_2,
            ]

        return self._rate_maps_split[action_id][channel_group][unit_name][smoothing]

    def rate_map(self, action_id, channel_group, unit_name, smoothing):
        make_rate_map = False
        if action_id not in self._rate_maps:
            self._rate_maps[action_id] = {}
        if channel_group not in self._rate_maps[action_id]:
            self._rate_maps[action_id][channel_group] = {}
        if unit_name not in self._rate_maps[action_id][channel_group]:
            self._rate_maps[action_id][channel_group][unit_name] = {}
        if smoothing not in self._rate_maps[action_id][channel_group][unit_name]:
            make_rate_map = True

        if make_rate_map:
            xbins, ybins = self.spatial_bins

            spike_map = sp.maps._spike_map(
                self.tracking(action_id)["x"],
                self.tracking(action_id)["y"],
                self.tracking(action_id)["t"],
                self.spike_train(action_id, channel_group, unit_name),
                xbins,
                ybins,
            )

            smooth_spike_map = sp.maps.smooth_map(
                spike_map, bin_size=self.bin_size_, smoothing=smoothing
            )
            smooth_occupancy_map = sp.maps.smooth_map(
                self.occupancy(action_id), bin_size=self.bin_size_, smoothing=smoothing
            )
            rate_map = smooth_spike_map / smooth_occupancy_map
            self._rate_maps[action_id][channel_group][unit_name][smoothing] = rate_map

        return self._rate_maps[action_id][channel_group][unit_name][smoothing]

    def head_direction(self, action_id):
        if action_id not in self._head_direction:
            a, t = load_head_direction(
                self.data_path(action_id),
                sampling_rate=self.params["position_sampling_rate"],
                low_pass_frequency=self.params["position_low_pass_frequency"],
                box_size=self.params["box_size"],
            )
            if self.stim_mask:
                t1, t2 = self.get_lim(action_id)
                mask = (t >= t1) & (t <= t2)
                a = a[mask]
                t = t[mask]
            self._head_direction[action_id] = {"a": a, "t": t}
        return self._head_direction[action_id]

    def lfp(self, action_id, channel_group, clean_memory=False):
        lim = self.get_lim(action_id) if self.stim_mask else None
        if clean_memory:
            return load_lfp(self.data_path(action_id), channel_group, lim)
        if action_id not in self._lfp:
            self._lfp[action_id] = {}
        if channel_group not in self._lfp[action_id]:
            self._lfp[action_id][channel_group] = load_lfp(
                self.data_path(action_id), channel_group, lim
            )
        return self._lfp[action_id][channel_group]

    def template(self, action_id, channel_group, unit_id):
        if action_id not in self._templates:
            self._templates[action_id] = {}
        if channel_group not in self._templates[action_id]:
            lim = self.get_lim(action_id) if self.stim_mask else None
            self._templates[action_id][channel_group] = {
                get_unit_id(st): Template(st)
                for st in load_spiketrains(
                    self.data_path(action_id),
                    channel_group,
                    load_waveforms=True,
                    lim=lim,
                )
            }
        return self._templates[action_id][channel_group][unit_id]

    def spike_train(self, action_id, channel_group, unit_id):
        self.spike_trains(action_id, channel_group)
        return self._spike_trains[action_id][channel_group][unit_id]

    def spike_trains(self, action_id, channel_group):
        if action_id not in self._spike_trains:
            self._spike_trains[action_id] = {}
        if channel_group not in self._spike_trains[action_id]:
            lim = self.get_lim(action_id) if self.stim_mask else None
            self._spike_trains[action_id][channel_group] = {
                get_unit_id(st): st
                for st in load_spiketrains(
                    self.data_path(action_id),
                    channel_group,
                    load_waveforms=False,
                    lim=lim,
                )
            }
        return self._spike_trains[action_id][channel_group]

    def unit_names(self, action_id, channel_group):
        if action_id not in self._unit_names:
            self._unit_names[action_id] = {}
        if channel_group not in self._unit_names[action_id]:
            self._unit_names[action_id][channel_group] = [
                get_unit_id(st)
                for st in load_unit_annotations(
                    self.data_path(action_id), channel_group
                )
            ]
        return self._unit_names[action_id][channel_group]

    def stim_times(self, action_id):
        if action_id not in self._stim_times:
            epochs = load_epochs(self.data_path(action_id))
            if len(epochs) == 0:
                self._stim_times[action_id] = None
            elif len(epochs) == 1:
                stim_times = epochs[0]
                stim_times = np.sort(np.abs(stim_times))
                # there are some 0 times and inf times, remove those
                stim_times = stim_times[
                    stim_times <= get_duration(self.data_path(action_id))
                ]
                # stim_times = stim_times[stim_times >= 1e-20]
                self._stim_times[action_id] = stim_times
            else:
                raise ValueError("Found multiple epochs")
        return self._stim_times[action_id]
