from enum import Enum


class Params(Enum):
    DELTA_T = "delta_t"
    DAYS = "days"
    HEIGHT = "height"
    RADIUS = "radius"
    NUM_SEGS = "n_segments"
    INIT_STATE = "init_state"
    INIT_MAX_T = "init_max_t"
    INIT_MIN_T = "init_min_t"
    DENSITY = "density"
    C_P = "c_p"
    DIFFUSIVITY = "diffusivity"
    T_ENV = "t_env"
    HEAT_PERC = "heat_perc"
    HEAT_CRIT_T = "heat_crit_t"
    HEAT_GOAL_T = "heat_goal_t"
    HEAT_T = "heat_t"
    COOLER_GOAL_T = "cooler_goal_t"

class ParamDefaultChoices(Enum):
    DEFAULT_DASH = '-'
    NEW_SET = 'Neuen Parametersatz speichern'
