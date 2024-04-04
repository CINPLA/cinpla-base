from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import intan
import spikesorters as ss
from . import utils
from distutils.version import StrictVersion

if StrictVersion(yaml.__version__) >= StrictVersion('5.0.0'):
    use_loader = True
else:
    use_loader = False

def attach_to_register(cli):
    @cli.command('intan',
                 short_help='Register an Intan recording-action to database.')
    @click.argument('intan-path', type=click.Path(exists=True))
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the recording.',
                  )
    @click.option('-d', '--depth',
                  multiple=True,
                  callback=utils.validate_depth,
                  help=(
                    'Alternative "find" to find from surgery or adjustment' +
                    ' or given as <key num depth unit> e.g. ' +
                    '<mecl 0 10 um> (omit <>).'),
                  )
    @click.option('-l', '--location',
                  type=click.STRING,
                  callback=utils.optional_choice,
                  envvar=project.config.get('possible_locations') or [],
                  help='The location of the recording, i.e. "room-1-ibv".'
                  )
    @click.option('--session',
                  type=click.STRING,
                  help='Session number, assumed to be 1 if not specified',
                  )
    @click.option('--action-id',
                  type=click.STRING,
                  help=('Desired action id for this action, if none' +
                        ', it is generated from open-ephys-path.'),
                  )
    @click.option('--entity-id',
                  type=click.STRING,
                  help='The id number of the entity.',
                  )
    @click.option('-m', '--message',
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('-t', '--tag',
                  multiple=True,
                  type=click.STRING,
                  callback=utils.optional_choice,
                  envvar=project.config.get('possible_tags') or [],
                  help='Add tags to action.',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite files and expipe action.',
                  )
    @click.option('--register-depth',
                  is_flag=True,
                  help='Overwrite files and expipe action.',
                  )
    @click.option('--templates',
                  multiple=True,
                  type=click.STRING,
                  help='Which templates to add',
                  )
    def _register_openephys_recording(action_id, intan_path, depth, overwrite, templates,
                                      entity_id, user, session, location, message, tag, register_depth):
        intan.register_intan_recording(
            project=project,
            action_id=action_id,
            intan_path=intan_path,
            depth=depth,
            overwrite=overwrite,
            templates=templates,
            entity_id=entity_id,
            user=user,
            session=session,
            location=location,
            message=message,
            tag=tag,
            delete_raw_data=None,
            correct_depth_answer=None,
            register_depth=register_depth)


def attach_to_process(cli):
    @cli.command('intan',
                 short_help='Process intan recordings.')
    @click.argument('action-id', type=click.STRING)
    @click.option('--probe-path',
                  type=click.STRING,
                  help='Path to probefile, assumed to be in expipe config directory by default.',
                  )
    @click.option('--sorter',
                  default='klusta',
                  type=click.Choice([s.sorter_name for s in ss.sorter_full_list]),
                  help='Spike sorter software to be used.',
                  )
    @click.option('--acquisition',
                  default=None,
                  type=click.STRING,
                  help='(optional) Intan acquisition folder.',
                  )
    @click.option('--exdir-path',
                  default=None,
                  type=click.STRING,
                  help='(optional) Exdir file path.',
                  )
    @click.option('--no-sorting',
                  is_flag=True,
                  help='if True spikesorting is not performed.',
                  )
    @click.option('--no-lfp',
                  is_flag=True,
                  help='if True LFP are not extracted.',
                  )
    @click.option('--no-mua',
                  is_flag=True,
                  help='if True MUA are not extracted.',
                  )
    @click.option('--spike-params',
                  type=click.STRING,
                  default=None,
                  help='Path to spike sorting params yml file.',
                  )
    @click.option('--no-par',
                  is_flag=True,
                  help='if True groups are not sorted in parallel.',
                  )
    @click.option('--sort-by',
                  type=click.STRING,
                  default=None,
                  help='sort by property (group).',
                  )
    @click.option('--server',
                  type=click.STRING,
                  default=None,
                  help="'local' or name of expipe server.",
                  )
    @click.option('--bad-channels', '-bc',
                  type=click.STRING,
                  multiple=True,
                  default=None,
                  help="bad channels to ground.",
                  )
    @click.option('--bad-threshold', '-bt',
                  type=click.FLOAT,
                  default=None,
                  help="bad channels to ground.",
                  )
    @click.option('--min-fr', '-mfr',
                  type=click.FLOAT,
                  default=None,
                  help="Minimum firing rate per unit to retain.",
                  )
    @click.option('--min-isi', '-mi',
                  type=click.FLOAT,
                  default=None,
                  help="Maximum isi violation rate (if > 0).",
                  )
    @click.option('--ref',
                  default='cmr',
                  type=click.Choice(['cmr', 'car', 'none']),
                  help='Reference to be used.',
                  )
    @click.option('--split-channels',
                  default='all',
                  type=click.STRING,
                  help="It can be 'all', 'half', or list of channels used for custom split e.g. [[0,1,2,3,4], [5,6,7,8,9]]"
                  )
    @click.option('--rm-art-channel',
                  default=-1,
                  type=click.INT,
                  help="Digital input trigger to remove artifacts"
                  )
    @click.option('--ms-before-wf',
                  default=1,
                  type=click.FLOAT,
                  help="ms to clip before waveform peak"
                  )
    @click.option('--ms-after-wf',
                  default=2,
                  type=click.FLOAT,
                  help="ms to clip after waveform peak"
                  )
    @click.option('--ms-before-stim',
                  default=2,
                  type=click.FLOAT,
                  help="ms to clip before stimulation trigger"
                  )
    @click.option('--ms-after-stim',
                  default=3,
                  type=click.FLOAT,
                  help="ms to clip before stimulation trigger"
                  )
    def _process_intan(action_id, probe_path, sorter, no_sorting, no_mua, no_lfp, rm_art_channel,
                       ms_before_wf, ms_after_wf, ms_before_stim, ms_after_stim,
                       spike_params, server, acquisition, exdir_path, bad_channels, ref, split_channels,
                       no_par, sort_by, bad_threshold, min_fr, min_isi):
        if 'auto' in bad_channels:
            bad_channels = ['auto']
        else:
            bad_channels = [int(bc) for bc in bad_channels]
        if no_sorting:
            spikesort = False
        else:
            spikesort = True
        if no_lfp:
            compute_lfp = False
        else:
            compute_lfp = True
        if no_mua:
            compute_mua = False
        else:
            compute_mua = True
        if spike_params is not None:
            spike_params = pathlib.Path(spike_params)
            if spike_params.is_file():
                with spike_params.open() as f:
                    if use_loader:
                        params = yaml.load(f, Loader=yaml.FullLoader)
                    else:
                        params = yaml.load(f)
            else:
                params = None
        else:
            params = None
        if no_par:
            parallel = False
        else:
            parallel = True

        if split_channels == 'custom':
            import ast
            split_channels = ast.literal_eval(split_channels)
            assert isinstance(split_channels, list), 'With custom reference the list of channels has to be provided ' \
                                                     'with the --split-channels argument'
        intan.process_intan(project=project, action_id=action_id, probe_path=probe_path, sorter=sorter,
                            spikesort=spikesort, compute_lfp=compute_lfp, compute_mua=compute_mua,
                            spikesorter_params=params, server=server, acquisition_folder=acquisition,
                            exdir_file_path=exdir_path, bad_channels=bad_channels, ref=ref, split=split_channels,
                            remove_artifact_channel=rm_art_channel, ms_before_wf=ms_before_wf, ms_after_wf=ms_after_wf,
                            ms_before_stim=ms_before_stim, ms_after_stim=ms_after_stim, parallel=parallel,
                            sort_by=sort_by, bad_threshold=bad_threshold, firing_rate_threshold=min_fr,
                            isi_viol_threshold=min_isi)
