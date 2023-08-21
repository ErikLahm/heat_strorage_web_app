from enum import Enum


class SimType(Enum):
    SOURCE = "Quelle"
    SINK = "Senke"


class ControllerType(Enum):
    HEATER = "Heizung"
    COOLER = "Kühler"


class InitialStateType(Enum):
    EVEN_DISTRIBUTION = "linear"
    CONSTANT_DISTRIBUTION = "konstant"
