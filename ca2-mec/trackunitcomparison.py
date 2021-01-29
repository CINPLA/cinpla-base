from track_units_tools import make_dissimilary_matrix, compute_templates, make_possible_match, make_best_match, \
    make_hungarian_match, get_unit_id, dissimilarity
from data_processing import get_data_path, load_spiketrains, get_channel_groups, load_unit_annotations
import matplotlib.pylab as plt
import numpy as np
from pathlib import Path


class TrackingSession:
    """
    Base class shared by SortingComparison and GroundTruthComparison
    """

    def __init__(self, action_id_0, action_id_1, actions, channel_group=None,
                 max_dissimilarity=10, dissimilarity_function=None, verbose=False):

        data_path_0 = get_data_path(actions[action_id_0])
        data_path_1 = get_data_path(actions[action_id_1])

        self._actions = actions
        self.action_id_0 = action_id_0
        self.action_id_1 = action_id_1
        self._channel_group = channel_group
        self.action_ids = [action_id_0, action_id_1]
        self.max_dissimilarity = max_dissimilarity
        self.dissimilarity_function = dissimilarity_function
        self._verbose = verbose

        if channel_group is None:
            channel_groups = get_channel_groups(data_path_0)
            self.matches = {}
            self.templates = {}
            self.unit_ids = {}
            for chan in channel_groups:
                self.matches[chan] = dict()
                self.templates[chan] = list()
                self.unit_ids[chan] = list()
        else:
            self.matches = {channel_group: dict()}
            self.templates = {channel_group: list()}
            self.unit_ids = {channel_group: list()}

        for channel_group in self.matches.keys():
            unit_annotations_0 = load_unit_annotations(
                data_path_0, channel_group=channel_group)
            unit_annotations_1 = load_unit_annotations(
                data_path_1, channel_group=channel_group)

            unit_ids_0 = []
            unit_ids_1 = []
            for st in unit_annotations_0:
                unit_ids_0.append(get_unit_id(st))
            for st in unit_annotations_1:
                unit_ids_1.append(get_unit_id(st))

            self.unit_ids[channel_group] = [
                np.array(unit_ids_0),
                np.array(unit_ids_1)
            ]
            self.templates[channel_group] = [
                compute_templates(self.waveforms_0(channel_group)),
                compute_templates(self.waveforms_1(channel_group))
            ]
            if len(unit_annotations_0) > 0 and len(unit_annotations_1) > 0:

                self._do_dissimilarity(channel_group)
                self._do_matching(channel_group)

    def save_dissimilarity_matrix(self, path=None):
        path = path or Path.cwd()
        for channel_group in self.matches:
            if 'dissimilarity_scores' not in self.matches[channel_group]:
                continue
            filename = f'{self.action_id_0}_{self.action_id_1}_{channel_group}'
            self.matches[channel_group]['dissimilarity_scores'].to_csv(
                path / (filename + '.csv'))

    def waveforms_0(self, channel_group):
        action_0 = self._actions[self.action_id_0]

        data_path_0 = get_data_path(action_0)

        spike_trains_0 = load_spiketrains(
            data_path_0, channel_group=channel_group, load_waveforms=True)

        return [np.array(sptr.waveforms) for sptr in spike_trains_0]

    def waveforms_1(self, channel_group):
        action_1 = self._actions[self.action_id_1]

        data_path_1 = get_data_path(action_1)

        spike_trains_1 = load_spiketrains(
            data_path_1, channel_group=channel_group, load_waveforms=True)

        return [np.array(sptr.waveforms) for sptr in spike_trains_1]

    @property
    def session_0_name(self):
        return self.name_list[0]

    @property
    def session_1_name(self):
        return self.name_list[1]

    def _do_dissimilarity(self, channel_group):
        if self._verbose:
            print('Agreement scores...')

        # agreement matrix score for each pair
        self.matches[channel_group]['dissimilarity_scores'] = make_dissimilary_matrix(
            self, channel_group)

    def _do_matching(self, channel_group):
        # must be implemented in subclass
        if self._verbose:
            print("Matching...")

        self.matches[channel_group]['possible_match_01'], self.matches[channel_group]['possible_match_10'] = \
            make_possible_match(self.matches[channel_group]['dissimilarity_scores'], self.max_dissimilarity)
        self.matches[channel_group]['best_match_01'], self.matches[channel_group]['best_match_10'] = \
            make_best_match(self.matches[channel_group]['dissimilarity_scores'], self.max_dissimilarity)
        self.matches[channel_group]['hungarian_match_01'], self.matches[channel_group]['hungarian_match_10'] = \
            make_hungarian_match(self.matches[channel_group]['dissimilarity_scores'], self.max_dissimilarity)

    def plot_matched_units(self, match_mode='hungarian', channel_group=None, ylim=[-200, 50], figsize=(15, 15)):
        '''

        Parameters
        ----------
        match_mode

        Returns
        -------

        '''
        if channel_group is None:
            ch_groups = self.matches.keys()
        else:
            ch_groups = [channel_group]

        for ch_group in ch_groups:
            if 'hungarian_match_01' not in self.matches[ch_group].keys():
                print('Not units for group', ch_group)
                continue

            if match_mode == 'hungarian':
                match12 = self.matches[ch_group]['hungarian_match_01']
            elif match_mode == 'best':
                match12 = self.matches[ch_group]['best_match_01']

            num_matches = len(np.where(match12 != -1)[0])

            if num_matches > 0:

                fig, ax_list = plt.subplots(nrows=2, ncols=num_matches, figsize=figsize)
                fig.suptitle('Channel group ' + str(ch_group))

                if num_matches == 1:
                    i = np.where(match12 != -1)[0][0]
                    j = match12.iloc[i]
                    i1 = np.where(self.matches[ch_group]['unit_ids_0'] == match12.index[i])
                    i2 = np.where(self.matches[ch_group]['unit_ids_1'] == j)
                    template1 = np.squeeze(
                        compute_templates(
                            self.matches[ch_group]['waveforms_0'][i1])).T
                    ax_list[0].plot(template1, color='C0')
                    ax_list[0].set_title('Unit ' + str(match12.index[i]))
                    template2 = np.squeeze(
                        compute_templates(
                            self.matches[ch_group]['waveforms_1'][i1])).T
                    ax_list[1].plot(template2, color='C0')
                    ax_list[1].set_title('Unit ' + str(j))
                    ax_list[0].set_ylabel(self.name_list[0])
                    ax_list[1].set_ylabel(self.name_list[1])
                    ax_list[0].set_ylim(ylim)
                    ax_list[1].set_ylim(ylim)
                else:
                    id_ax = 0
                    for i, j in enumerate(match12):
                        if j != -1:
                            i1 = np.where(self.matches[ch_group]['unit_ids_0'] == match12.index[i])
                            i2 = np.where(self.matches[ch_group]['unit_ids_1'] == j)

                            if id_ax == 0:
                                ax_list[0, id_ax].set_ylabel(self.name_list[0])
                                ax_list[1, id_ax].set_ylabel(self.name_list[1])
                            template1 = np.squeeze(
                                compute_templates(
                                    self.matches[ch_group]['waveforms_0'][i1])).T
                            ax_list[0, id_ax].plot(template1, color='C'+str(id_ax))
                            ax_list[0, id_ax].set_title('Unit ' + str(match12.index[i]))
                            template2 = np.squeeze(
                                compute_templates(
                                    self.matches[ch_group]['waveforms_1'][i1])).T
                            ax_list[1, id_ax].plot(template2, color='C'+str(id_ax))
                            ax_list[1, id_ax].set_title('Unit ' + str(j))
                            ax_list[0, id_ax].set_ylim(ylim)
                            ax_list[1, id_ax].set_ylim(ylim)
                            id_ax += 1
            else:
                print('No matched units for group', ch_group)
                continue
