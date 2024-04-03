from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt
from pde_calculations.sim_enums import InitialStateType


def even_distribution(min_value: float, max_value: float, number_of_layers: int):
    initial_state = np.linspace(max_value, min_value, number_of_layers).reshape(
        (number_of_layers, 1)
    )
    initial_state = np.insert(initial_state, 0, np.array([0]), axis=0)  # type: ignore
    initial_state = np.append(initial_state, np.array([[0]]), axis=0)  # type: ignore
    return initial_state


@dataclass
class Vessel:
    height: float
    radius: float
    segmentation: int
    theta: float = 0.5  # Verhältnis von einem Segmentvolumen zu zwei Segmentvolumina
    initial_state: str = InitialStateType.EVEN_DISTRIBUTION.value
    min_value: float = 20
    max_value: float = 80
    init_state: npt.NDArray[np.float64] = field(init=False)
    thermal_conductance_iso = 1.8  # [W/(mK)] thermal conductivity of concrete

    def __post_init__(self):
        match self.initial_state:
            case InitialStateType.EVEN_DISTRIBUTION.value:
                self.init_state = even_distribution(
                    self.min_value, self.max_value, self.segmentation
                )
            case InitialStateType.CONSTANT_DISTRIBUTION.value:
                self.init_state = np.full(
                    shape=(self.segmentation + 2, 1), fill_value=self.max_value
                )
            case _:
                self.init_state = np.array([[0], [55], [50], [45], [40], [35], [0]])

    @property
    def volume(self) -> float:
        return np.pi * self.radius**2 * self.height  # [m^3]

    @property
    def layer_thickness(self) -> float:
        return self.height / self.segmentation  # [m]

    @property
    def cross_sec_area(self) -> float:
        return self.radius**2 * np.pi  # [m^2]

    @property
    def perimeter_layer(self) -> float:
        perimeter = (2 * self.layer_thickness) + (4 * self.radius)
        return perimeter
