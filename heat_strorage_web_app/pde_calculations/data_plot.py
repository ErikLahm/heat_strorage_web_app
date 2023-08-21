from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from data_loader import RawDataLoader
from sim_enums import ControllerType

LINESTYLE_STD = [
    ("solid", "solid"),
    ("dotted", "dotted"),
    ("dashed", "dashed"),
    ("dashdot", "dashdot"),
]

LINESTYLE_TUPLE = [
    ("loosely dotted", (0, (1, 10))),
    ("dotted", (0, (1, 1))),
    ("densely dotted", (0, (1, 1))),
    ("long dash with offset", (5, (10, 3))),
    ("loosely dashed", (0, (5, 10))),
    ("dashed", (0, (5, 5))),
    ("densely dashed", (0, (5, 1))),
    ("loosely dashdotted", (0, (3, 10, 1, 10))),
    ("dashdotted", (0, (3, 5, 1, 5))),
    ("densely dashdotted", (0, (3, 1, 1, 1))),
    ("dashdotdotted", (0, (3, 5, 1, 5, 1, 5))),
    ("loosely dashdotdotted", (0, (3, 10, 1, 10, 1, 10))),
    ("densely dashdotdotted", (0, (3, 1, 1, 1, 1, 1))),
]


@dataclass
class TimeEvolutionPlot:
    time_evolution_results: npt.NDArray[np.float64]

    def plot(self):
        fig, ax = plt.subplots()  # type: ignore
        for i, result in enumerate(self.time_evolution_results):
            if i == 0 or i == 6:
                # ax.plot(np.arange(0, len(result), 1), result)
                continue
            else:
                ax.plot(  # type: ignore
                    np.arange(0, len(result), 1),  # type: ignore
                    result,
                    "-+",
                    label="Schicht " + str(i),
                )
        # ax.plot(
        #     np.arange(0, len(result), 1),
        #     self.mass_flow_source - self.mass_flow_user,
        #     label="Massflow Differenz",
        # )
        # ax.plot(np.arange(0, len(result), 1), self.top_inflow_temp, label="top inflow")
        # ax.plot(
        #     np.arange(0, len(result), 1), self.bottom_inflow_temp, label="bottom inflow"
        # )
        # ax.plot(np.linspace(0, 100, len(self.bottom_inflow_temp)), self.bottom_inflow_temp,
        # 		label='Rücklauftemp Verbraucher')
        ax.grid(True)  # type: ignore
        ax.legend()  # type: ignore
        ax.set_title("Temperaturentwicklung der Speicherschichten")  # type: ignore
        ax.set_ylabel("$\degree C$")  # type: ignore
        ax.set_xlabel("Zeit")  # type: ignore
        # plt.show()  # type: ignore
        return fig, ax


@dataclass
class RawDataPlot:
    source_data: RawDataLoader
    sink_data: RawDataLoader

    def plot_all(self):
        fig, ax = plt.subplots(2, 1)  # type: ignore
        for i, temp in enumerate(self.source_data.temperatures):
            ax[0].plot(  # type: ignore
                np.arange(0, len(temp), 1),  # type: ignore
                temp,
                label=f"Temperatur Quelle {i+1}",
                color="yellowgreen",
                linestyle=LINESTYLE_STD[i % 4][0],
            )
        for i, temp in enumerate(self.sink_data.temperatures):
            ax[0].plot(  # type: ignore
                np.arange(0, len(temp), 1),  # type: ignore
                temp,
                label=f"Temperatur Senke {i+1}",
                color="forestgreen",
                linestyle=LINESTYLE_STD[i % 4][0],
            )
        for i, mass in enumerate(self.source_data.masses):
            ax[1].plot(  # type: ignore
                np.arange(0, len(mass), 1),  # type: ignore
                mass,
                label=f"Massenstrom Quelle {i+1}",
                color="yellowgreen",
                linestyle=LINESTYLE_STD[i % 4][0],
            )
        for i, mass in enumerate(self.sink_data.masses):
            ax[1].plot(  # type: ignore
                np.arange(0, len(mass), 1),  # type: ignore
                mass,
                label=f"Massenstrom Senke {i+1}",
                color="forestgreen",
                linestyle=LINESTYLE_STD[i % 4][0],
            )
        ax[0].legend()  # type: ignore
        ax[0].grid(True)  # type: ignore
        ax[0].set_title("Temperaturen der Quellen und Senken")  # type: ignore
        ax[0].set_ylabel("$\degree C$")  # type: ignore
        ax[0].set_xlabel("Zeit")  # type: ignore
        ax[1].legend()  # type: ignore
        ax[1].grid(True)  # type: ignore
        ax[1].set_title("Volumenströme der Quellen und Senken")  # type: ignore
        ax[1].set_ylabel("$m^3/h$")  # type: ignore
        ax[1].set_xlabel("Zeit")  # type: ignore
        plt.show()  # type: ignore
        return fig, ax


@dataclass
class ControllerPowerPlot:
    controller_results: tuple[
        npt.NDArray[np.float64],
        npt.NDArray[np.float64],
    ]
    sim_type: ControllerType

    def __post_init__(self):
        self.power = self.controller_results[0]
        self.energy = self.controller_results[1]

    def plot_results(self):
        fig, ax = plt.subplots()  # type: ignore
        ax.plot(  # type: ignore
            np.arange(0, len(self.energy), 1),  # type: ignore
            self.energy,
            "-+",
            label="Leistung in kW",
        )
        ax.grid(True)  # type: ignore
        ax.legend()  # type: ignore
        ax.set_title(f"Leistungsverbrauch {self.sim_type.value}, Gesamtverbrauch: {sum(self.energy): .2f}kWh")  # type: ignore
        ax.set_ylabel("kW")  # type: ignore
        ax.set_xlabel("Zeit")  # type: ignore
        plt.show()  # type: ignore
        return fig, ax
