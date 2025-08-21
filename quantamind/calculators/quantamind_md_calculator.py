from typing import Dict, List, Union
from schnetpack.md import System
from schnetpack.md.calculators.base_calculator import MDCalculator
import torch
from schnetpack.md.neighborlist_md import NeighborListMD

from quantamind.model.quantamind_model import get_gnn_model

class QuantaMindCalculator(MDCalculator):
    def __init__(self,  model_cfg_yaml: str,
        force_key: str,
        energy_unit: Union[str, float],
        position_unit: Union[str, float],
        neighbor_list: NeighborListMD,
        energy_key: str = None,
        stress_key: str = None,
        required_properties: List = [],
        property_conversion: Dict[str, Union[str, float]] = {},
        script_model: bool = False,
        total_charge: float = 0.,
        md_config = None):
        super().__init__(required_properties, force_key, energy_unit, position_unit, energy_key, stress_key, property_conversion)
        self.gnn_model = get_gnn_model(model_cfg_yaml)
        self.total_charge = total_charge
        self.neighbor_list = neighbor_list
        self.md_config = md_config
    
    def calculate(self, system: System):
        """
        Main routine, generates a properly formatted input for the schnetpack model from the system, performs the
        computation and uses the results to update the system state.

        Args:
            system (schnetpack.md.System): System object containing current state of the simulation.
        """
        inputs = self._generate_input(system)
        Z = inputs["_atomic_numbers"]
        R = inputs["_positions"]
        Q = torch.as_tensor([self.total_charge]).to(R.device)
        S = torch.as_tensor([0.]).to(R.device)
        idx_i = inputs["_idx_i"]
        idx_j = inputs["_idx_j"]
        cell_offsets_direct = inputs["_offsets"]
        R.requires_grad = True
        energy, forces, f, ea, qa, ea_rep, ea_ele, ea_vdw, pa, c6 = \
            self.gnn_model.energy_and_forces(Z, Q, S, R, idx_i, idx_j, 
                    num_batch=1, 
                    batch_seg=None,
                    create_graph=False,
                    cell_offsets_direct=cell_offsets_direct)
        self.results = {"energy": energy}

        self.results["forces"] = forces
        self._update_system(system)

    def _generate_input(self, system: System) -> Dict[str, torch.Tensor]:
        """
        Function to extracts neighbor lists, atom_types, positions e.t.c. from the system and generate a properly
        formatted input for the schnetpack model.

        Args:
            system (schnetpack.md.System): System object containing current state of the simulation.

        Returns:
            dict(torch.Tensor): Schnetpack inputs in dictionary format.
        """
        inputs = self._get_system_molecules(system)
        neighbors = self.neighbor_list.get_neighbors(inputs)
        inputs.update(neighbors)
        return inputs
    
