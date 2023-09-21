from typing import Tuple

import numpy as np
import numpy.typing as npt
from pde_calculations.flow import Flow
from pde_calculations.heat_pde import HeatTransferEquation
from pde_calculations.sim_enums import SimType


def copy_extreme_temps(
    current_vessel_state: npt.NDArray[np.float64],
    next_vessel_state: npt.NDArray[np.float64],
    state: SimType,
) -> npt.NDArray[np.float64]:
    """
    This function compares each layer temperature with the current inflow temperature.
    Depending on charging or discharging of the vessel it makes sure that no layer
    temperature is higher or lower than the inflow repesctively.
    """

    if state == SimType.SOURCE:
        j = 1
        while (
            current_vessel_state[j] >= current_vessel_state[0]
            and j <= len(current_vessel_state) - 2
        ):
            next_vessel_state[j] = current_vessel_state[j]
            j += 1
    else:
        j = len(current_vessel_state) - 1
        while current_vessel_state[j] <= current_vessel_state[-1] and j >= 1:
            next_vessel_state[j] = current_vessel_state[j]
            j -= 1
    return next_vessel_state


def get_next_vessel_state(
    current_vessel_state: npt.NDArray[np.float64],
    mass_flow: float,
    state_type: SimType,
    hte: HeatTransferEquation,
    delta_t: int,
) -> npt.NDArray[np.float64]:
    """
    Calculates the vessel state of the next time step. The returned state is
    based on one flow.

    Parameters
    ----------
    current_vessel_state: npt.NDArray[np.float64]
        1D array representing the current vessel state (every temperature for each layer)
    mass_flow: float
        Indicates the massflow of the current time step and the current mass flow. This
        flow corresponds to the temperature in the first or last entry of the vessel
        state array. (charging/ discharging repsectively)
    state_type: SimType
        SimType to distinguish between the different simulations of charging/ discharging
    hte: HeatTransferEquation
        The heat transfer equation for the current vessel, Medium and Environment.
    delta_t: int
        Time discretization delta between each time step.

    Returns
    -------
    npt.NDArray[np.float64]
        Array discribing the next vessel state of the next time step (every temperature
        of every layer)
    """

    next_vessel_state = np.copy(current_vessel_state)
    if state_type == SimType.SOURCE:
        for i, layer_temp in enumerate(current_vessel_state[1:-1], 1):
            next_vessel_state[i] = hte.get_next_layer_temp(
                current_temp=layer_temp,
                above_temp=current_vessel_state[i - 1],
                below_temp=current_vessel_state[i + 1],
                mass_flow=mass_flow,
                inflow_temp=current_vessel_state[i - 1],
                delta_t=delta_t,
            )
        next_vessel_state = copy_extreme_temps(
            current_vessel_state, next_vessel_state, state_type
        )
    else:
        for i, layer_temp in enumerate(current_vessel_state[1:-1], 1):
            next_vessel_state[i] = hte.get_next_layer_temp(
                current_temp=layer_temp,
                above_temp=current_vessel_state[i - 1],
                below_temp=current_vessel_state[i + 1],
                mass_flow=mass_flow,
                inflow_temp=current_vessel_state[i + 1],
                delta_t=delta_t,
            )
        next_vessel_state = copy_extreme_temps(
            current_vessel_state, next_vessel_state, state_type
        )
    return next_vessel_state


def base_simulation(
    hte: HeatTransferEquation, flows: list[Flow], delta_t: int
) -> npt.NDArray[np.float64]:
    """
    Simulates the pure heat equation based on the input flows. Each time step the
    function models the vessel state based on every flow in the list one after the
    other before progressing to the next time step.

    Parameters
    ----------
    hte: HeatTransferEquation
        The heat transfer equation for the current vessel, Medium and Environment.
    flows: list[Flow]
        List of all the flows that shall be simulated.
    delta_t: int
        Time discretization delta between each time step.

    Returns
    -------
    npt.NDArray[np.float64]
        2D Array with the shape (segmentation + 2 rows, number_of_timesteps columns) representing
        the vessel state at each timestep.
    """

    vessel_state = hte.vessel.init_state
    for timestep, _ in enumerate(flows[0].flow_temp):
        current_vessel_state = vessel_state[:, timestep].reshape(
            hte.vessel.init_state.shape
        )
        for flow in flows:
            if flow.input_type == SimType.SOURCE:
                current_vessel_state[0] = flow.flow_temp[timestep]
                current_vessel_state[-1] = current_vessel_state[-2]
            else:
                current_vessel_state[0] = current_vessel_state[1]
                current_vessel_state[-1] = flow.flow_temp[timestep]
            current_vessel_state = get_next_vessel_state(
                current_vessel_state=current_vessel_state,
                mass_flow=flow.mass_flow_kg_s[timestep],
                state_type=flow.input_type,
                hte=hte,
                delta_t=delta_t,
            )
        vessel_state = np.hstack((vessel_state, current_vessel_state))
    return vessel_state


def get_average_section_temp(
    current_vessel_state: npt.NDArray[np.float64],
    vessel_section: float,
) -> float:
    """
    Function returns the average temperature of the upper section of the vessel.
    The upper section is given as percentage of the whole vessel, where the percentage
    increases from top to bottom.

    Parameters
    ----------
    current_vessel_state: npt.NDArray[np.float64]
        1D array describing the curent vessel state based on which the average is calculated.
    vessel_section: float
        Value between 0 and 1 determining in percent the size of the layer section on which
        the average temperature is calculated. Percentages start at the top of the vessel.

    Returns
    -------
    float
        average temperature of the specified layer section.
    """

    number_of_segments = int((len(current_vessel_state) - 2) * vessel_section) + 2
    average_temp_section = float(np.average(current_vessel_state[1:number_of_segments]))
    return average_temp_section


def temp_hysteresis(
    critical_temp: float,
    high_temp: float,
    average_section_temp: float,
    heater_on_currently: bool,
) -> bool:
    """
    Hysteresis function based on temperature. Initialised as False and returns True
    once the average temperature is lower than the critical tempreture. Once True it
    returns true until average temperature is higher than the high temperature.

    Parameters
    ----------
    critical_temp: float

    high_temp: float,
    average_section_temp: float,
    heater_on_currently: bool,
    """

    if average_section_temp <= critical_temp:
        return True
    if average_section_temp >= high_temp:
        return False
    if critical_temp <= average_section_temp <= high_temp and heater_on_currently:
        return True
    return False


def calc_mix_power(
    mass_flow: float, c_p_fluid: float, high_temp: float, low_temp: float
) -> float:
    """
    input: [°C, kg/s]
    output: [kJ/s=kW]
    """
    thermal_power = mass_flow * c_p_fluid * (high_temp - low_temp)  # [J/s]
    if thermal_power < 0:
        return 0
    return thermal_power / 1000  # [kJ/s=kW]


def power_to_energy(power: float, delta_t: float) -> float:
    """
    input: [kJ/s=kW]
    output: [kWh=kJ*2.778e-4]
    """

    thermal_energy = power * delta_t * 2.778e-4
    return thermal_energy  # [kWh=kJ*2.778e-4]


def heater_simulation(
    hte: HeatTransferEquation,
    flows: list[Flow],
    delta_t: int,
    vessel_section: float,
    critical_temp: float,
    turn_off_temp: float,
    heating_temp: float,
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    vessel_state = hte.vessel.init_state
    heater_power_consumption = np.zeros((flows[0].number_of_steps, 1))
    heater_state_on = False
    for timestep, _ in enumerate(flows[0].flow_temp):
        current_vessel_state = vessel_state[:, timestep].reshape(
            hte.vessel.init_state.shape
        )
        average_section_temp = get_average_section_temp(
            current_vessel_state, vessel_section
        )
        heater_state_on = temp_hysteresis(
            critical_temp, turn_off_temp, average_section_temp, heater_state_on
        )
        for flow in flows:
            if flow.input_type == SimType.SOURCE:
                if heater_state_on:
                    heater_power_consumption[timestep] = calc_mix_power(
                        mass_flow=flow.mass_flow_kg_s[timestep],
                        c_p_fluid=hte.fluid.c_p,
                        high_temp=heating_temp,
                        low_temp=flow.flow_temp[timestep],
                    )
                    flow.flow_temp[timestep] = heating_temp
                current_vessel_state[0] = flow.flow_temp[timestep]
                current_vessel_state[-1] = current_vessel_state[-2]
            else:
                current_vessel_state[0] = current_vessel_state[1]
                current_vessel_state[-1] = flow.flow_temp[timestep]
            current_vessel_state = get_next_vessel_state(
                current_vessel_state=current_vessel_state,
                mass_flow=flow.mass_flow_kg_s[timestep],
                state_type=flow.input_type,
                hte=hte,
                delta_t=delta_t,
            )
        vessel_state = np.hstack((vessel_state, current_vessel_state))
    return vessel_state, heater_power_consumption


def cooler_simulation(
    layer: npt.NDArray[np.float64],
    desired_temp: float,
    flows: list[Flow],
    c_p_fluid: float,
) -> npt.NDArray[np.float64]:
    cooler_power_consumption = np.zeros(len(layer))
    for i, temp in enumerate(layer):
        if (
            temp > desired_temp
        ):  # TODO: this "if" might be unnecessary now since calc mix power returns 0
            for flow in flows:
                cooler_power_consumption[i] += calc_mix_power(
                    flow.mass_flow_kg_s[i], c_p_fluid, temp, desired_temp
                )
    return cooler_power_consumption.reshape((len(cooler_power_consumption), 1))


SIMULATIONS = {
    "base": base_simulation,
    "heater": heater_simulation,
    "cooler": cooler_simulation,
}
