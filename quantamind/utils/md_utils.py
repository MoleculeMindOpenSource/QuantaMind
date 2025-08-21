import argparse
from omegaconf import OmegaConf
from dataclasses import dataclass, field
import os.path as osp
from typing import List, Optional, Union
import torch

from omegaconf import MISSING
from schnetpack.md import System
from ase.io import read
from schnetpack.md import UniformInit
from schnetpack.md.integrators import VelocityVerlet, NPTVelocityVerlet
from schnetpack.md.simulation_hooks import NHCBarostatIsotropic
from schnetpack.md.neighborlist_md import NeighborListMD
from schnetpack.transform import ASENeighborList

from quantamind.calculators.quantamind_md_calculator import QuantaMindCalculator

def mdmin_cfg_from_yaml(cfg_yaml):
    schema: MDMinConfig = OmegaConf.structured(MDMinConfig)
    cfg = OmegaConf.load(cfg_yaml)
    cfg: MDMinConfig = OmegaConf.merge(schema, cfg)
    if cfg.mdmin_workdir == "AUTO":
        cfg.mdmin_workdir = f"{cfg.mdmin_workdir_root}/{osp.basename(cfg_yaml).split('.yaml')[0]}"
    return cfg

@dataclass
class MoleculeConfig:
    use_pbc: bool = True
    # re-center coordinates and calculate appropriate PBC boundary
    reset_pbc_boundaries: bool = True
    # only one file should be specified
    molecule_path: Optional[str] = None
    molecule_paths: Optional[List[str]] = None
    # atoms within inner shell will be optimized/simulated
    inner_shell_cutoff: Optional[float] = None
    # atoms bettwen inner shell and outer shell will be freezed
    # atoms outside of outer shell will be ignored
    outer_shell_cutoff: Optional[float] = None
    # atoms within inner_freeze_shell will be freezed
    inner_freeze_shell_cutoff: Optional[float] = None
    # the id of molecules in "molecule_paths" that we are interested in
    interested_molecule_id: Optional[int] = None
    frozen_molecule_id: Optional[int] = None
    # SDF files support multiple molecules in the same file
    multiple_mol_file: Optional[str] = None
    multiple_mol_id: Optional[Union[str, int]] = None
    # Only used when optimizing a single molecule
    out_molecule_path: Optional[str] = None
    # exclusive to DFT-binding free energy calculation
    lig_conf_sample_sdf: Optional[str] = None

@dataclass
class MDConfig:
    comment: str = MISSING
    md_workdir: str = "AUTO"
    molecule: MoleculeConfig = field(default_factory=MoleculeConfig)
    system_ckpt: Optional[str] = None
    debug_mode: bool = False
    time_step: float = 0.5 # fs
    # set cutoff and buffer region
    cutoff: float = 5.291772105638412  # Angstrom (units used in model)
    cutoff_shell: float = 2.0  # Angstrom
    # Set temperature and thermostat constant
    bath_temperature: float = 300  # K
    time_constant: float = 100  # fs
    pressure: Optional[float] = None # bar, None means NVT
    # Create the file logger
    log_every_n_steps: int = 1000
    n_steps: int = 200000
    sensecore_job_id: Optional[str] = None
    total_charge: int = 0
    global_force_max: Optional[float] = None

@dataclass
class MDMinConfig:
    comment: str = MISSING
    model_path: str = MISSING
    # hparams.yaml, loading it from model_cfg is more robust
    model_cfg_path: Optional[str] = None
    molecule: MoleculeConfig = field(default_factory=MoleculeConfig)
    mdmin_workdir: str = "AUTO"
    mdmin_workdir_root: str = "./md_minimization"
    # set cutoff and buffer region
    cutoff: float = 5.291772105638412  # Angstrom (units used in model)
    cutoff_shell: float = 2.0  # Angstrom
    maxstep: Optional[float] = None
    # only implemented in single mol optimization
    fmax: float = 0.05
    optim_class: str = "LBFGS"
    lbfgs_memory: int = 100
    # minimum distance to calculate force, used to optimize clashed structures.
    dij_min: Optional[float] = None
    total_charge: int = 0
    chain_id_ref_file: Optional[str] = None
    sensecore_job_id: Optional[str] = None
    save_traj: bool = True
    neighborlist: str = "TorchNeighborListNoPBC"
    calc_hessian: bool = False

def load_ase_atoms(cfg: MoleculeConfig):
    # Load atoms with ASE
    molecule = read(cfg.molecule_path)
    molecule.set_pbc(cfg.use_pbc)
    if cfg.reset_pbc_boundaries:
        molecule.set_positions(molecule.positions - molecule.positions.min(axis=0).reshape(1, -3) + 0.5)
        pbc = molecule.positions.max(axis=0) + 1.0
        molecule.set_cell([(pbc[0], 0, 0), (0, pbc[1], 0), (0, 0, pbc[2])])
    return molecule

def create_md_system(molecule):
    # Number of molecular replicas
    n_replicas = 1

    # Create system instance and load molecule
    md_system = System()
    md_system.load_molecules(
        molecule,
        n_replicas,
        position_unit_input="Angstrom"
    )
    return md_system

def create_md_initializer(md_system):
    system_temperature = 300 # Kelvin

    # Set up the initializer
    md_initializer = UniformInit(
        system_temperature,
        remove_center_of_mass=False,
        remove_translation=True,
        remove_rotation=True,
    )

    # Initialize the system momenta
    md_initializer.initialize_system(md_system)
    return md_initializer

def create_integrator(cfg: MDConfig):
    if cfg.pressure is None:
        # Set up the integrator
        md_integrator = VelocityVerlet(cfg.time_step)
        return md_integrator
    
    barostat = NHCBarostatIsotropic(cfg.pressure, cfg.bath_temperature, cfg.time_constant)
    md_integrator = NPTVelocityVerlet(cfg.time_step, barostat)
    return md_integrator

def create_md_neighborlist(cfg: MDConfig):
    # initialize neighbor list for MD using the ASENeighborlist as basis
    md_neighborlist = NeighborListMD(
        cfg.cutoff,
        cfg.cutoff_shell,
        ASENeighborList,
    )
    return md_neighborlist

def create_md_calculator(cfg: MDConfig, md_neighborlist):
    param_yaml_file = "./quantamind_hyper_params.yaml"
    model_param_file = "./quantamind_example_parameters.pth"
    if not (osp.exists(param_yaml_file) and osp.exists(model_param_file)):
        err_msg = f"Required files {param_yaml_file} and/or {model_param_file} not found, please make sure you have demo_data.zip unziped and move it to the QuantaMind folder."
        print(err_msg)
        raise RuntimeError(err_msg)

    required_properties = []
    md_calculator = QuantaMindCalculator(
        param_yaml_file,  # path to stored model
        "forces",  # force key
        "eV",  # energy units
        "Angstrom",  # length units
        md_neighborlist,  # neighbor list
        energy_key="energy",  # name of potential energies
        required_properties=required_properties,  # additional properties extracted from the model,
        total_charge=float(cfg.total_charge),
        md_config=cfg
    )
    state_dict = torch.load(model_param_file, map_location="cuda" if torch.cuda.is_available() else "cpu")
    md_calculator.load_state_dict(state_dict)
    return md_calculator
