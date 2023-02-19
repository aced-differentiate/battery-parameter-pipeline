import pybamm
import numpy as np
from .calculation import Calculation


class ElectrodeVolumeFractionFromLoading(Calculation):
    """
    Calculate the volume fraction of active material in the electrodes from the
    loading
    """

    def __init__(self, side="both"):
        source = "Calculation of electrode volume fraction from loading"
        super().__init__(source)
        self.side = side

    def run(self, parameter_values):
        F = pybamm.constants.F.value
        H = parameter_values["Electrode height [m]"]
        W = parameter_values["Electrode width [m]"]
        A_cc = H * W

        if self.side == "both":
            sides = ["negative", "positive"]
        else:
            sides = [self.side]

        capacity_parameter_values = {}
        for side in sides:
            Side = side.capitalize()
            L = parameter_values[f"{Side} electrode thickness [m]"]
            c_max = parameter_values[
                f"Maximum concentration in {side} electrode [mol.m-3]"
            ]
            elec_loading = parameter_values[f"{Side} electrode loading [A.h.cm-2]"]
            elec_cap = elec_loading * A_cc * 1e4  # Ah

            capacity_parameter_values.update(
                {
                    f"{Side} electrode capacity [A.h]": elec_cap,
                    f"{Side} electrode active material volume fraction": elec_cap
                    / (A_cc * L * c_max * F / 3600),
                }
            )

        return capacity_parameter_values


class AreaToSquareWidthHeight(Calculation):
    """
    Calculate the volume fraction of active material in the electrodes from the
    """

    def __init__(self):
        source = "Setting electrode height and width to be the square root of area"
        super().__init__(source)

    def run(self, parameter_values):
        A_cc = parameter_values["Electrode area [m2]"]

        H = np.sqrt(A_cc)
        W = H

        parameter_values = {"Electrode height [m]": H, "Electrode width [m]": W}

        return parameter_values


class SurfaceArea(Calculation):
    def __init__(self):
        source = (
            "Calculation of surface area to volume ratio from particle radius "
            "and active material volume fraction"
        )
        super().__init__(source)

    def run(self, parameter_values):
        surface_area_parameter_values = {}
        for side in ["negative", "positive"]:
            Side = side.capitalize()
            eps = parameter_values[f"{Side} electrode active material volume fraction"]
            R = parameter_values[f"{Side} particle radius [m]"]
            surface_area_parameter_values.update(
                {f"{Side} electrode surface area to volume ratio [m-1]": 3 * eps / R}
            )
        return surface_area_parameter_values
