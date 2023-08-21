from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt
import pandas as pd
from sim_enums import SimType


def cal_mix_temp(
    t_1: npt.NDArray[np.float64],
    t_2: npt.NDArray[np.float64],
    m_1: npt.NDArray[np.float64],
    m_2: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:  # calculate  mixing temperature
    t_mix: npt.NDArray[np.float64] = ((t_1 * m_1) + (t_2 * m_2)) / (m_1 + m_2)
    return t_mix


@dataclass
class RawDataLoader:
    path: str
    sheet_name: str
    sim_type: SimType
    number_of_inputs: int = field(init=False)
    data: pd.DataFrame = field(init=False)
    temperatures: list[npt.NDArray[np.float64]] = field(init=False)
    masses: list[npt.NDArray[np.float64]] = field(init=False)
    initial_temp: list[npt.NDArray[np.float64]] = field(init=False)
    initial_mass: list[npt.NDArray[np.float64]] = field(init=False)

    def __post_init__(self):
        self.read_xlsx_to_pd()
        self.number_of_inputs = int(self.get_number_of_columns() / 2)
        self.data.rename(columns=self.generate_header(), inplace=True)
        self.df_to_numpy()
        self.initial_temp = self.temperatures.copy()
        self.initial_mass = self.masses.copy()

    def generate_header(self) -> dict[str, str]:
        new_header: list[str] = [
            f"temperature_{i}" for i in range(self.number_of_inputs)
        ]
        new_header.extend([f"mass_{i}" for i in range(self.number_of_inputs)])
        rename_dict: dict[str, str] = {
            list(self.data.columns)[i]: new_header
            for (i, new_header) in enumerate(new_header)
        }
        return rename_dict

    def read_xlsx_to_pd(self) -> None:
        self.data = pd.read_excel(self.path, sheet_name=self.sheet_name)  # type: ignore

    def get_number_of_columns(self) -> int:
        return len(self.data.columns)

    def df_to_numpy(self) -> None:
        self.temperatures = [
            self.data[f"temperature_{i}"].to_numpy()  # type: ignore
            for i in range(self.number_of_inputs)
        ]
        self.masses = [
            self.data[f"mass_{i}"].to_numpy() for i in range(self.number_of_inputs)  # type: ignore
        ]

    def combine_inputs(
        self, index: list[int]
    ) -> None:  # TODO: index 2 must be bigger than index 1
        temperature = cal_mix_temp(
            t_1=self.temperatures[index[0]],  # type: ignore
            t_2=self.temperatures[index[1]],  # type: ignore
            m_1=self.masses[index[0]],  # type: ignore
            m_2=self.masses[index[1]],  # type: ignore
        )
        mass = self.masses[index[0]] + self.masses[index[1]]
        self.temperatures.append(temperature)
        self.masses.append(mass)
        for indice in reversed(index):  # TODO: index 2 must be bigger than index 1
            del self.temperatures[indice]
            del self.masses[indice]
        self.number_of_inputs -= 1
        # update initial values
        self.initial_temp = self.temperatures.copy()
        self.initial_mass = self.masses.copy()

    def get_single_data(self, index: int) -> npt.NDArray[np.float64]:
        return np.vstack((self.temperatures[index], self.masses[index]))  # type: ignore
