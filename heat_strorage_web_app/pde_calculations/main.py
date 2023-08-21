import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from pde_calculations.data_loader import RawDataLoader
from pde_calculations.data_plot import RawDataPlot, TimeEvolutionPlot
from pde_calculations.environment import Environment
from pde_calculations.flow import Flow
from pde_calculations.heat_pde import HeatTransferEquation
from pde_calculations.medium import Medium
from pde_calculations.sim_enums import SimType
from pde_calculations.simulations import base_simulation, heater_simulation
from pde_calculations.vessel import InitialStateType, Vessel


def main() -> None:
    test_vessel = Vessel(
        height=5,
        radius=1,
        segmentation=4,
        initial_state=InitialStateType.EVEN_DISTRIBUTION,
    )
    water = Medium(density=1000, alpha=1.43e-7, c_p=4184)
    ambient = Environment(env_temp=20)

    source_data = RawDataLoader(
        path="/Users/erikweilandt/Documents/emv/heat_storage_sim/src/main/resources/test_data_input.xlsx",
        sheet_name="Wärmequellen",
        sim_type=SimType.SOURCE,
    )
    sink_data = RawDataLoader(
        path="/Users/erikweilandt/Documents/emv/heat_storage_sim/src/main/resources/test_data_input.xlsx",
        sheet_name="Wärmesenken",
        sim_type=SimType.SINK,
    )
    # ____________________________________________________________________________________
    # some data modifications
    # ____________________________________________________________________________________
    source_data.combine_inputs(index=[0, 1])
    source_data.masses[0] = source_data.masses[0] * 1
    sink_data.masses[0] = sink_data.masses[0] * 3.8
    sink_data.temperatures[0] *= 0.3
    source_data.temperatures[0] = source_data.temperatures[0] * 1
    # ____________________________________________________________________________________

    flows = [
        Flow(
            flow_temp=source_data.temperatures[i],
            volume_flow=source_data.masses[i],
            input_type=SimType.SOURCE,
            medium=water,
        )
        for i in range(source_data.number_of_inputs)
    ]
    flows.extend(
        [
            Flow(
                flow_temp=sink_data.temperatures[i],
                volume_flow=sink_data.masses[i],
                input_type=SimType.SINK,
                medium=water,
            )
            for i in range(sink_data.number_of_inputs)
        ]
    )
    pde = HeatTransferEquation(water, test_vessel, ambient)
    base_result = base_simulation(pde, flows, delta_t=300)
    heater_result = heater_simulation(
        hte=pde,
        flows=flows,
        delta_t=300,
        vessel_section=0.2,
        critical_temp=50,
        turn_off_temp=65,
    )
    plot = TimeEvolutionPlot(time_evolution_results=base_result)
    plot_heater = TimeEvolutionPlot(time_evolution_results=heater_result[0])
    plot.plot()
    plot_heater.plot()
    raw_data_plot = RawDataPlot(source_data=source_data, sink_data=sink_data)
    raw_data_plot.plot_all()


if __name__ == "__main__":
    main()
