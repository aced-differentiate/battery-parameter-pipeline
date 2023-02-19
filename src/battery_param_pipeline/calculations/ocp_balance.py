import pybamm
from scipy.optimize import least_squares
from .calculation import Calculation


class OCPBalance(Calculation):
    def __init__(self):
        source = "OCP Balance"
        super().__init__(source)
