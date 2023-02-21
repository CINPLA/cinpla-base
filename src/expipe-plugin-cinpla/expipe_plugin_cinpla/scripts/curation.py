from expipe_plugin_cinpla.imports import *
from .utils import _get_data_path, read_python, write_python
from pathlib import Path
import shutil
import time
from pathlib import Path, PureWindowsPath
import shlex
from subprocess import Popen, PIPE
import spikeextractors as se
import spiketoolkit as st
import spikecomparison as sc
import numpy as np
import os


def process_phy(project, action_id, sorter, restore=False):
    action = project.actions[action_id]
    # if exdir_path is None:
    exdir_path = _get_data_path(action)
    exdir_file = exdir.File(exdir_path, plugins=exdir.plugins.quantities)

    phy_dir = exdir_file['processing']['electrophysiology']['spikesorting'][sorter]['phy'].directory
    phy_params = exdir_file['processing']['electrophysiology']['spikesorting'][sorter]['phy'].directory / 'params.py'

    if restore:
        groups_file = [p for p in phy_dir.iterdir() if 'cluster_group' in p.name]
        if len(groups_file) == 1:
            print('Removing cluster file')
            os.remove(str(groups_file[0]))
    sorting_phy = se.PhySortingExtractor(phy_dir)

    if len(sorting_phy.get_unit_ids()) > 1:
        print('Running phy')
        cmd = 'phy template-gui ' + str(phy_params)
        _run_command_and_print_output(cmd)
    else:
        print('Only one unit found. Phy needs more than one unit.')


def process_consensus(project, action_id, sorters, min_agreement=None):
    action = project.actions[action_id]
    # if exdir_path is None:
    exdir_path = _get_data_path(action)
    exdir_file = exdir.File(exdir_path, plugins=[exdir.plugins.quantities])

    sorting_list = []
    sorter_names = []
    for sorter in sorters:
        phy_dir = str(exdir_file['processing']['electrophysiology']['spikesorting'][sorter]['phy'].directory)
        phy_params = str(
            exdir_file['processing']['electrophysiology']['spikesorting'][sorter]['phy'].directory / 'params.py')

        sorting_phy = se.PhySortingExtractor(phy_dir)
        sorting_list.append(sorting_phy)
        sorter_names.append(sorter)
        recording = se.PhyRecordingExtractor(phy_dir)

    mcmp = sc.compare_multiple_sorters(sorting_list=sorting_list, name_list=sorter_names, verbose=True)
    if min_agreement is None:
        min_agreement = len(sorter_names) - 1

    agr = mcmp.get_agreement_sorting(minimum_agreement_count=min_agreement)
    print(agr.get_unit_ids())
    for u in agr.get_unit_ids():
        print(agr.get_unit_property(u, 'sorter_unit_ids'))
        agr.get_unit_property_names(u)

    consensus_dir = exdir_file['processing']['electrophysiology']['spikesorting'].require_group('consensus').require_raw('phy').directory
    st.postprocessing.export_to_phy(recording, agr, output_folder=consensus_dir,
                                    ms_before=0.5, ms_after=2, verbose=True,
                                    grouping_property='group')

def process_save_phy(project, action_id, sorter, save_waveforms=True, check_exists=False):
    action = project.actions[action_id]
    exdir_path = _get_data_path(action)
    if exdir_path is None:
        print('No "main" in data for action {}'.format(action.id))
        return
    exdir_file = exdir.File(exdir_path, plugins=exdir.plugins.quantities)
    elphys = exdir_file['processing']['electrophysiology']
    phy_folder = elphys['spikesorting'][sorter]['phy'].directory

    if check_exists:
        unit_ids = set([int(b) for a in elphys.values() if 'UnitTimes' in a for b in a['UnitTimes']])
        sorting_ = se.PhySortingExtractor(phy_folder, exclude_groups=['noise'])
        if set(sorting_.get_unit_ids()) == unit_ids:
            print('Unit ids are the same in phy and exdir.')
            return
    sorting = se.PhySortingExtractor(phy_folder, exclude_cluster_groups=['noise'])
    if save_waveforms:
        recording = se.PhyRecordingExtractor(phy_folder)

        # workaround to avoid grouping in windows
        waveforms = st.postprocessing.get_unit_waveforms(recording, sorting, max_spikes_per_unit=None, memmap=False,
                                                         save_property_or_features=False, n_jobs=8, verbose=True)

        if ("group" in sorting.get_shared_unit_property_names()) or ("ch_group" in sorting.get_shared_unit_property_names()):
            channel_groups = recording.get_channel_groups()
            for (wf, unit) in zip(waveforms, sorting.get_unit_ids()):
                if "ch_group" in sorting.get_shared_unit_property_names():
                    # sometimes 'group' is named 'ch_group'. Also add 'group' as a property then, duplicating
                    # the info stored in 'ch_group' to 'group'. IOW, they are synonomous.
                    sorting.set_unit_property(unit, "group", sorting.get_unit_property(unit, "ch_group"))
                unit_group = sorting.get_unit_property(unit, "group")
                channel_unit_group = np.where(channel_groups == int(unit_group))[0]

                waveform_group = wf[:, channel_unit_group]
                sorting.set_unit_spike_features(unit, "waveforms", waveform_group)
        else:
            for (wf, unit) in zip(waveforms, sorting.get_unit_ids()):
                #template = np.mean(wf,axis=0)
                #waveform_group = np.unravel_index(np.argmin(template),template.shape)[0]
                #orting.set_unit_property(unit, "channel", waveform_group)
                #sorting.set_unit_property(unit, "group", waveform_group//4)
                sorting.set_unit_spike_features(unit, "waveforms", wf)

    se.ExdirSortingExtractor.write_sorting(sorting, exdir_path, sampling_frequency=sorting.params['sample_rate'],
                                           save_waveforms=True, verbose=True)


def _run_command_and_print_output(command):
    command_list = shlex.split(command, posix="win" not in sys.platform)
    with Popen(command_list, stdout=PIPE, stderr=PIPE) as process:
        while True:
            output_stdout = process.stdout.readline()
            output_stderr = process.stderr.readline()
            if (not output_stdout) and (not output_stderr) and (process.poll() is not None):
                break
            if output_stdout:
                print(output_stdout.decode())
            if output_stderr:
                print(output_stderr.decode())
        rc = process.poll()
        return rc
