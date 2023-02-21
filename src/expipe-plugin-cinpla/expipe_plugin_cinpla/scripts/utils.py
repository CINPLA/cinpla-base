from expipe_plugin_cinpla.imports import *
import re
import sys
from pathlib import Path

nwb_main_groups = ['acquisition', 'analysis', 'processing', 'epochs',
                   'general']
tmp_phy_folders = ['.klustakwik2', '.phy', '.spikedetect']


def query_yes_no(question, default="yes", answer=None):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    if answer is not None:
        assert isinstance(answer, bool)
        return answer
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [[Y]/n] "
    elif default == "no":
        prompt = " [y/[N]] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def deltadate(adjustdate, regdate):
    delta = regdate - adjustdate if regdate > adjustdate else datetime.timedelta.max
    return delta


def position_to_dict(depth):
    position = {d[0]: dict() for d in depth}
    for key, num, val, unit in depth:
        probe_key = 'probe_{}'.format(num)
        position[key][probe_key] = pq.Quantity(val, unit)
    return position


def read_python(path):
    from six import exec_
    path = Path(path).absolute()
    assert path.is_file()
    with path.open('r') as f:
        contents = f.read()
    metadata = {}
    exec_(contents, {}, metadata)
    metadata = {k.lower(): v for (k, v) in metadata.items()}
    return metadata


def write_python(path, dict):
    with Path(path).open('w') as f:
        for k, v in dict.items():
            if isinstance(v ,str) and not v.startswith("'"):
                if 'path' in k and 'win' in sys.platform:
                    f.write(str(k) + " = r'" + str(v) + "'\n")
                else:
                    f.write(str(k) + " = '" + str(v) + "'\n")
            else:
                f.write(str(k) + " = " + str(v) + "\n")


def get_depth_from_surgery(project, entity_id):
    index = 0
    surgery = project.actions[entity_id + '-surgery-implantation']
    position = {}
    for key, module in surgery.modules.items():
        for probe_key, probe in module.items():
            if probe_key.startswith('probe_') and probe_key.split('_')[-1].isnumeric():
                if key not in position:
                    position[key] = {}
                position[key][probe_key] = probe['position']
    for key, groups in position.items():
        for group, pos in groups.items():
            if not isinstance(pos, pq.Quantity):
                raise ValueError('Depth of implant ' +
                                 '"{} {} = {}"'.format(key, group, pos) +
                                 ' not recognized')
            position[key][group] = pos.astype(float)[2]  # index 2 = z
    return position


def get_depth_from_adjustment(project, action, entity_id):
    DTIME_FORMAT = expipe.core.datetime_format
    try:
        adjustments = project.actions[entity_id + '-adjustment']
    except KeyError as e:
        return None, None
    adjusts = {}
    for adjust in adjustments.modules.values():
        values = adjust.contents
        adjusts[datetime.datetime.strptime(values['date'], DTIME_FORMAT)] = adjust

    regdate = action.datetime
    adjustdates = adjusts.keys()
    adjustdate = min(adjustdates, key=lambda x: deltadate(x, regdate))
    return adjusts[adjustdate]['depth'].contents, adjustdate


def register_depth(project, action, depth=None, answer=None, overwrite=False):
    if len(action.entities) != 1:
        print('Exactly 1 entity is required to register depth.')
        return False
    depth = depth or []
    curr_depth = None
    if len(depth) > 0:
        curr_depth = position_to_dict(depth)
        adjustdate = None
    else:
        curr_depth, adjustdate = get_depth_from_adjustment(
            project, action, action.entities[0])
        print('Adjust date time: {}\n'.format(adjustdate))
    if curr_depth is None:
        print('Cannot find current depth from adjustments.')
        return False

    def last_num(x):
        return '{:03d}'.format(int(x.split('_')[-1]))
    print(''.join('Depth: {} {} = {}\n'.format(key, probe_key, val[probe_key])
            for key, val in curr_depth.items()
            for probe_key in sorted(val, key=lambda x: last_num(x))))
    correct = query_yes_no(
        'Are the values correct?',
        answer=answer)
    if not correct:
        return False
    if 'depth' in action.modules and overwrite:
        action.delete_module('depth')
    action.create_module(name='depth', contents=curr_depth)
    return True


def _make_data_path(action, overwrite):
    action_path = action._backend.path
    project_path = action_path.parent.parent
    data_path = action_path / 'data'
    data_path.mkdir(exist_ok=True)
    exdir_path = data_path / 'main.exdir'
    if exdir_path.exists():
        if overwrite:
            shutil.rmtree(str(exdir_path))
        else:
            raise FileExistsError(
                'The exdir path to this action "' + str(exdir_path) +
                '" exists, optionally use "--overwrite"')
    relpath = exdir_path.relative_to(project_path)
    action.data['main'] = str(relpath)
    return exdir_path


def _get_data_path(action):
    if 'main' not in action.data:
        return
    try:
        data_path = action.data_path('main')
    except:
        data_path = pathlib.Path('None')
        pass
    if not data_path.is_dir():
        action_path = action._backend.path
        project_path = action_path.parent.parent
        # data_path = action.data['main']
        data_path = project_path / str(pathlib.Path(pathlib.PureWindowsPath(action.data['main'])))
    return data_path


def register_templates(action, templates, overwrite=False):
    '''
    Parameters
    ----------
    action : expipe.Action
    templates : list
    '''
    for template in templates:
        try:
            action.create_module(template=template)
            print('Adding module ' + template)
        except KeyError as e:
            if overwrite:
                action.delete_module(template)
                action.create_module(template=template)
                print('Adding module ' + template)
            else:
                raise KeyError(str(e) + '. Optionally use "overwrite"')
        except Exception as e:
            print(template)
            raise e


### PARAMIKO UTILS ###

class ShellHandler:
    def __init__(self, ssh):
        self.ssh = ssh
        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

    def __del__(self):
        self.ssh.close()

    def execute(self, cmd, print_lines=False):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """
        print(cmd)
        cmd = cmd.strip('\n')
        self.stdin.write(cmd + '\n')
        finish_proc = 'Finished processing'
        finish = 'end of stdout buffer. finished with exit status'
        echo_cmd = 'echo {}'.format(finish)
        self.stdin.write(echo_cmd + '\n')
        shin = self.stdin
        self.stdin.flush()

        shout = []
        sherr = []
        for line in self.stdout:
            if cmd in str(line) or echo_cmd in str(line):
                # up for now filled with shell junk from stdin
                shout = []
            elif finish in str(line) or finish_proc in str(line):
                # our finish command ends with the exit status
                if finish in str(line):
                    print(finish)
                    break
                if finish_proc in str(line):
                    print(finish_proc)
                    break
            else:
                if finish in str(line):
                    print(finish)
                    break
                if finish_proc in str(line):
                    print(finish_proc)
                    break
                if print_lines:
                    print(str(line))
                shout.append(str(line))

        # first and last lines of shout/sherr contain a prompt
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        if shout and cmd in shout[0]:
            shout.pop(0)
        if sherr and echo_cmd in sherr[-1]:
            sherr.pop()
        if sherr and cmd in sherr[0]:
            sherr.pop(0)

        return shin, shout, sherr


def ssh_execute(ssh, command, **kw):
    stdin, stdout, stderr = ssh.exec_command(command, **kw)
    exit_status = stdout.channel.recv_exit_status()          # Blocking call
    # print(stdout.readlines())
    # print(stderr)
    if exit_status == 0:
        pass
    else:
        raise IOError(''.join(stdout.readlines()) + '\n' + ''.join(stderr.readlines()))
    return ''.join(stdout.readlines()), ''.join(stderr.readlines())


def untar(fname, prefix):
    assert fname.endswith('.tar')

    def get_members(tar, prefix):
        if not prefix.endswith('/'):
            prefix += '/'
        if prefix.startswith('/'):
            prefix = prefix[1:]
        offset = len(prefix)
        for tarinfo in tar.getmembers():
            if tarinfo.name.startswith(prefix):
                tarinfo.name = tarinfo.name[offset:]
                yield tarinfo

    tar = tarfile.open(fname)
    dest = os.path.splitext(fname)[-0]
    tar.extractall(dest, get_members(tar, prefix))
    tar.close()


def get_login(port=22, username=None, password=None, hostname=None, server=None):
    if server is not None:
        hostname = server.get('hostname')
        username = server.get('username')
        password = server.get('password')

    username = username or ''
    if hostname is None:
        hostname = input('Hostname: ')
        if len(hostname) == 0:
            print('*** Hostname required.')
            sys.exit(1)

        if hostname.find(':') >= 0:
            hostname, portstr = hostname.split(':')
            port = int(portstr)

    # get username
    if username == '':
        default_username = getpass.getuser()
        username = input('Username [%s]: ' % default_username)
        if len(username) == 0:
            username = default_username
    if password is None:
        password = getpass.getpass('Password for %s@%s: ' % (username,
                                                             hostname))
    return hostname, username, password, port


def get_view_bar():
    fnames = [None]
    pbar = [None]
    try:
        from tqdm import tqdm
        last = [0]  # last known iteration, start at 0

        def view_bar(filename, size, sent):
            if filename != fnames[0]:
                try:
                    pbar[0].close()
                except Exception:
                    pass
                pbar[0] = tqdm(ascii=True, unit='B', unit_scale=True)
                pbar[0].set_description('Transferring: %s' % filename)
                pbar[0].refresh() # to show immediately the update
                last[0] = sent
                pbar[0].total = int(size)
            delta = int(sent - last[0])
            if delta >= 0:
                pbar[0].update(delta)  # update pbar with increment
            last[0] = sent  # update last known iteration
            fnames[0] = filename
    except Exception:
        def view_bar(filename, size, sent):
            if filename != fnames[0]:
                print('\nTransferring: %s' % filename)
            res = sent / size * 100
            sys.stdout.write('\rComplete precent: %.2f %%' % (res))
            sys.stdout.flush()
            fnames[0] = filename
    return view_bar, pbar


def login(hostname, username, password, port):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, port=port, username=username,
                password=password, timeout=4)
    sftp_client = ssh.open_sftp()
    view_bar, pbar = get_view_bar()
    scp_client = scp.SCPClient(ssh.get_transport(), progress=view_bar)
    return ssh, scp_client, sftp_client, pbar


def scp_put(scp_client, source, dest=None, serverpath=None):

    source = os.path.abspath(source)
    dest_name = source.split(os.sep)[-1]
    dest_path = os.path.join(serverpath, dest_name)

    print('Transferring', source, ' to ', dest_path)
    scp_client.put(source, dest_path, recursive=True)
    scp_client.close()


def scp_get(scp_client, source, dest=None, serverpath=None):
    if serverpath is None:
        serverpath = os.path.split(source)[0]
    else:
        source = os.path.join(serverpath, source)
    if dest is None:
        dest_name = os.path.split(source)[-1]
        dest_path = os.path.join(os.getcwd(), dest_name)

    print('Transferring', source, ' to ', dest_path)
    scp_client.get(source, dest_path, recursive=True)
