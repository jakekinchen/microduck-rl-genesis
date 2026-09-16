"""Retain complete trusted native/controller history without advancing physics."""
import copy
from pathlib import Path
from microduck.native_standing_env_v42 import snapshot, restore
from experiments.walking.snapshots_v43 import save_state


def retain_state(world, output, session_id, step):
    state = snapshot(world)
    state['command_ramp'] = copy.deepcopy(world.command_ramp)
    state['heading_servo'] = copy.deepcopy(world.heading_servo)
    state['heading_sensor_history'] = copy.deepcopy(world.heading_sensor_history)
    state['fell'] = world.fell
    path = Path(output) / 'states' / f'{session_id}-step-{step}.json'
    save_state(state, path, Path(output) / 'snapshot-blobs')


def restore_state(world, state):
    restore(world, state)
    world.command_ramp = copy.deepcopy(state['command_ramp'])
    world.heading_servo = copy.deepcopy(state['heading_servo'])
    world.heading_sensor_history = copy.deepcopy(state['heading_sensor_history'])
    world.fell = state['fell']
