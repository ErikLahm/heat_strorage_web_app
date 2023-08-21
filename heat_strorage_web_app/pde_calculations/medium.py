from dataclasses import dataclass


@dataclass
class Medium:
    density: float  # [kg/m^3]
    alpha: float
    c_p: float  # [J kg-1 K-1]
