from dataclasses import dataclass

from pde_calculations.environment import Environment
from pde_calculations.medium import Medium
from pde_calculations.vessel import Vessel


@dataclass
class HeatTransferEquation:
    fluid: Medium
    vessel: Vessel
    env: Environment

    def discretised_diffusion_term(
        self, above_temp: float, below_temp: float, current_temp: float
    ) -> float:
        diffusion_term = self.fluid.alpha * (
            (below_temp - 2 * current_temp + above_temp)
            / self.vessel.layer_thickness**2
        )
        return diffusion_term

    def direct_charge_term(
        self, mass_flow: float, inflow_temp: float, current_temp: float
    ) -> float:
        direct_term = (mass_flow * (inflow_temp - current_temp)) / (
            self.vessel.cross_sec_area
            * self.vessel.layer_thickness
            * self.fluid.density
        )
        return direct_term

    def environment_term(self, current_temp: float) -> float:
        env_term = (
            (self.vessel.perimeter_layer * self.vessel.thermal_conductance_iso)
            / (self.fluid.density * self.fluid.c_p * self.vessel.cross_sec_area)
            * (self.env.env_temp - current_temp)
        )
        return env_term

    def get_next_layer_temp(
        self,
        current_temp: float,
        above_temp: float,
        below_temp: float,
        mass_flow: float,
        inflow_temp: float,
        delta_t: int,  # [s]
    ) -> float:
        next_temp = (
            current_temp
            + (
                self.discretised_diffusion_term(above_temp, below_temp, current_temp)
                + self.environment_term(current_temp)
                + self.direct_charge_term(mass_flow, inflow_temp, current_temp)
            )
            * delta_t
        )
        return next_temp
