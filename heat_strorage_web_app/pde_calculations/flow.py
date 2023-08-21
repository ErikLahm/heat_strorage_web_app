from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from pde_calculations.medium import Medium
from pde_calculations.sim_enums import SimType


@dataclass
class Flow:
    flow_temp: npt.NDArray[np.float64]  # FIXME: initialise with fixed empty array?
    volume_flow: npt.NDArray[np.float64]
    input_type: SimType
    medium: Medium

    @property
    def mass_flow_kg_s(self) -> npt.NDArray[np.float64]:
        """input: [volume_flow]=[m^3/h]
        output: [kg/s]"""
        return self.volume_flow * self.medium.density / (60 * 60)  # [kg/s]

    @property
    def number_of_steps(self) -> int:
        return len(self.flow_temp)

    def create_constant_flow(
        self, constant_flow: float
    ) -> None:  # TODO: necessary if I have to initialise the array anyway?
        self.volume_flow = np.full(
            shape=(self.number_of_steps, 1), fill_value=constant_flow
        )
