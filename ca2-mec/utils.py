import numpy as np


def trial_label(action):
    for tag in action.attributes['tags']:
        if 'trial_id' in tag:
            trial_num = int(tag.split('_')[-1][1])
            return trial_num

def social_label(action):
    """
    socializing can happen at either of the four corners of the box (space).
    there are four types of socializing: nobox (-1) empty (0), familiar (1) or novel (2).
    this gives a 4d-vector with four possible categories each.
    """
    
    def social_category(str1, str2):
        """ helper function """
        if str1 == 'nobox':
            return -1
        if str2 == 'e':
            return 0
        if str2 == 'f':
            return 1
        if str2 == 'n':
            return 2
    
    tags = action.attributes['tags']
    social_types = {'s': np.zeros(4), 'o': np.zeros(4)}
    for tag in tags:
        if not 'corner' in tag:
            continue
        stag = tag.split('_')[1:]
        # TR, TL, BL and BR, respectively
        if stag[1] == 'tr':
            social_types[stag[0]][0] = social_category(*stag[-2:])
        elif stag[1] == 'tl':
            social_types[stag[0]][1] = social_category(*stag[-2:])
        elif stag[1] == 'bl':
            social_types[stag[0]][2] = social_category(*stag[-2:])
        elif stag[1] == 'br':
            social_types[stag[0]][3] = social_category(*stag[-2:])
    
    return social_types


def transform_coordinates(x, y, theta=90, **kwargs):
    """
    Transform tracking coordinates to align with physical coordinates
    For this project (CA2 MEC): rotate recorded coordinates 90 degrees, 
    followed by a shift to make values positive afterwards.
    """
    # rotate x,y coordinates 90 degrees using a 2D rotation matrix transform
    theta = np.radians(theta)
    r = np.array(( (np.cos(theta), -np.sin(theta)),
                   (np.sin(theta),  np.cos(theta)) ))
    coords = r @ np.array([x,y])
    # shift new x-coordinates to be positive
    coords -= np.array([[-1],[0]])
    return coords


def corner_masks(x, y, margin=0.4, **kwargs):
    """
    Find corner and center of box masks.
    """
    assert margin < 0.5 and margin > 0, "OBS! Margin must be positive and max half the box size, i.e. 0.5 OBS!"
    
    # center x and y coordinates
    x = x - 0.5
    y = y - 0.5
    pos = np.array([x, y]).T
    
    # create cardinal basis vectors
    ex, ey = np.arange(2), np.arange(2)[::-1]
    
    # create corner vectors: TR, TL, BL and BR, respectively
    corners = np.array([ex+ey, -ex+ey, -ex-ey, ex-ey])
    
    corner_masks = np.zeros((len(x), 5),dtype=bool)
    for i, corner in enumerate(corners):
        # find which quadrant positions are in, and if they are within the
        # box margins. The intersection gives the grand mask.
        quadrant_mask = ((pos * corner) > 0).all(axis=-1)
        margin_mask = (np.abs(pos) > (np.ones(2) * (0.5 - margin))).all(axis=-1)
        corner_masks[:,i] = quadrant_mask & margin_mask
    
    # inverse of union over corner masks
    corner_masks[:,-1] = ~np.array(corner_masks).any(axis=-1)
    return corner_masks


def truncate_recording(arr, t, t_start=0.0, t_stop=None):
    """
    Truncate recording, in seconds.
    if t_start or t_stop is None, then don't truncate
    """
    if not isinstance(arr, np.ndarray):
        return arr
    mask = np.ones(len(arr),dtype=bool)
    mask = (t > t_start) if t_start is not None else mask
    mask = mask & (t < t_stop) if t_stop is not None else mask
    return arr[mask]

def persistent_units(spikes):
    """
    Find all units that persist across all trials for each animal (cumulative intersection over trials)
    """
    punits = []
    for trial in spikes:
        if not punits:
            # empty list
            punits = list(spikes[trial].keys())
            continue
        punits = list(spikes[trial].keys() & punits)
    return punits
