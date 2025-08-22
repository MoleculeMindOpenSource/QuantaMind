import argparse
import os
import os.path as osp
import shutil
import torch
import numpy as np
import os
import matplotlib.pyplot as plt

from omegaconf import OmegaConf
from ase.io import write
from schnetpack.md import Simulator
from schnetpack import properties
from schnetpack.md.simulation_hooks import LangevinThermostat, callback_hooks
from schnetpack import units as spk_units
from quantamind.utils.md_utils import MDConfig, create_integrator, create_md_calculator, create_md_initializer, create_md_neighborlist, create_md_system, load_ase_atoms
from quantamind.utils.smarterHDF5Loader import HDF5LoaderSmart

if torch.cuda.is_available():
    md_device = "cuda"
else:
    md_device = "cpu"

parser = argparse.ArgumentParser()
parser.add_argument("config_file")
args, unknown = parser.parse_known_args()
config_file = args.config_file

schema: MDConfig = OmegaConf.structured(MDConfig)
cfg = OmegaConf.load(config_file)
cfg: MDConfig = OmegaConf.merge(schema, cfg)
if cfg.md_workdir == "AUTO":
    cfg.md_workdir = f"./md_simulations/{osp.basename(config_file).split('.yaml')[0]}"

cli_cfg = OmegaConf.from_cli(unknown)
cfg = OmegaConf.merge(cfg, cli_cfg)

if cfg.debug_mode: 
    cfg.n_steps = 100
    cfg.log_every_n_steps = 1
    cfg.md_workdir = osp.join(osp.dirname(cfg.md_workdir), "DEBUG." + osp.basename(cfg.md_workdir))


def create_folder():
    if osp.exists(cfg.md_workdir):
        shutil.rmtree(cfg.md_workdir)

    # Generate a directory if not present
    if not os.path.exists(cfg.md_workdir):
        os.makedirs(cfg.md_workdir)
    
    with open(osp.join(cfg.md_workdir, "runtime_cfg.yaml"), "w") as f:
        f.write(OmegaConf.to_yaml(cfg))

create_folder()

molecule = load_ase_atoms(cfg.molecule)

md_system = create_md_system(molecule)
if cfg.system_ckpt is not None:
    system_ckpt = torch.load(cfg.system_ckpt)["system"]
    md_system.load_system_state(system_ckpt)
md_system = md_system.to(md_device)

md_initializer = create_md_initializer(md_system)

md_integrator = create_integrator(cfg)

md_neighborlist = create_md_neighborlist(cfg)

md_calculator = create_md_calculator(cfg, md_neighborlist)

simulation_hooks = []

def add_thermostat():
    if cfg.pressure is not None:
        # temperature control is built in Barostats
        simulation_hooks.append(md_integrator.barostat)
        return
    # Initialize the thermostat
    langevin = LangevinThermostat(cfg.bath_temperature, cfg.time_constant)
    simulation_hooks.append(langevin)

add_thermostat()

def add_file_logger():
    # Path to database
    log_file = os.path.join(cfg.md_workdir, "simulation.hdf5")

    # Size of the buffer
    buffer_size = 100

    target_properties = [properties.energy]

    # Set up data streams to store positions, momenta and the energy
    data_streams = [
        callback_hooks.MoleculeStream(store_velocities=True),
        callback_hooks.PropertyStream(target_properties=target_properties),
    ]

    file_logger = callback_hooks.FileLogger(
        log_file,
        buffer_size,
        data_streams=data_streams,
        every_n_steps=cfg.log_every_n_steps,  # logging frequency
        precision=32,  # floating point precision used in hdf5 database
    )

    # Update the simulation hooks
    simulation_hooks.append(file_logger)

add_file_logger()

def add_checkpoint():
    #Set the path to the checkpoint file
    chk_file = os.path.join(cfg.md_workdir, 'simulation.chk')

    # Create the checkpoint logger
    checkpoint = callback_hooks.Checkpoint(chk_file, every_n_steps=100)

    # Update the simulation hooks
    simulation_hooks.append(checkpoint)

add_checkpoint()

def add_tensorboard_logger():
    # directory where tensorboard log will be stored to
    tensorboard_dir = os.path.join(cfg.md_workdir, 'logs')

    tensorboard_logger = callback_hooks.TensorBoardLogger(
        tensorboard_dir,
        ["energy", "temperature", "pressure", "volume"], # properties to log
    )

    # update simulation hooks
    simulation_hooks.append(tensorboard_logger)

add_tensorboard_logger()

def run_simulation():
    md_simulator = Simulator(
        md_system,
        md_integrator,
        md_calculator,
        simulator_hooks=simulation_hooks
    )

    # use single precision
    md_precision = torch.float32

    # set precision
    md_simulator = md_simulator.to(md_precision)
    # move everything to target device
    md_simulator = md_simulator.to(md_device)

    md_simulator.simulate(cfg.n_steps)

run_simulation()

def load_data():
    # Path to database
    log_file = os.path.join(cfg.md_workdir, "simulation.hdf5")
    data = HDF5LoaderSmart(log_file)
    return data

data = load_data()


def write_traj():
    # extract structure information from HDF5 data
    md_atoms = data.convert_to_atoms(every=1)

    # write list of Atoms to XYZ file
    write(
        os.path.join(cfg.md_workdir, "trajectory.nc"),
        md_atoms,
        format="netcdftrajectory"
    )
write_traj()


def plot_temperature(data):

    # Read the temperature
    temperature = data.get_temperature()

    # Compute the cumulative mean
    temperature_mean = np.cumsum(temperature) / (np.arange(data.entries)+1)

    # Get the time axis
    time_axis = np.arange(data.entries) * data.time_step / spk_units.fs  # in fs

    plt.figure(figsize=(8,4))
    plt.plot(time_axis, temperature, label='T')
    plt.plot(time_axis, temperature_mean, label='T (avg.)')
    plt.ylabel('T [K]')
    plt.xlabel('t [fs]')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(cfg.md_workdir, "temperature.png"))

plot_temperature(data)

