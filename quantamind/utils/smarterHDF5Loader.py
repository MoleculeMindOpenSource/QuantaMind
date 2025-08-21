import json
import logging
import h5py
import numpy as np
from ase import Atoms
from typing import Optional
from tqdm import trange

from schnetpack import properties, units
from schnetpack.md.data.hdf5_data import HDF5Loader, log

class HDF5LoaderSmart(HDF5Loader):
    def convert_to_atoms(self, mol_idx = 0, replica_idx = None, every = None, entries = None):
        if (every is None) and (entries is None):
            return super().convert_to_atoms(mol_idx, replica_idx)

        positions = self.get_positions(
            mol_idx=mol_idx, replica_idx=replica_idx
        ) / units.unit2internal("Angstrom")

        atomic_numbers = self.get_property(
            properties.Z, atomistic=True, mol_idx=mol_idx, replica_idx=replica_idx
        )

        cells = self.get_property(
            properties.cell, atomistic=False, mol_idx=mol_idx, replica_idx=replica_idx
        )

        if entries is None:
            entries = self.entries

        if cells is None:
            cells = [None] * entries
        else:
            cells = cells / units.unit2internal("Angstrom")

        all_atoms = []

        log.info("Extracting structures...")
        for idx in trange(0, entries, every):
            atoms = Atoms(
                atomic_numbers, positions[idx], cell=cells[idx], pbc=self.pbc[mol_idx]
            )
            atoms.wrap()
            all_atoms.append(atoms)

        return all_atoms