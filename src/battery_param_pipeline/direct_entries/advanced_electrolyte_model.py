import pybamm
import battery_param_pipeline as bpp
import numpy as np
import pandas as pd
from functools import partial
from scipy.interpolate import interp1d


def _get_2d_mesh_data(data, parameter):
    cs_interp = np.linspace(0, 3, 1000)
    Ts = np.unique(data["Temperature(C)"])
    data_interp = np.empty((len(cs_interp), len(Ts)))
    for i, T in enumerate(Ts):
        subdata = data[data["Temperature(C)"] == T]
        data_interp[:, i] = interp1d(
            subdata["c"],
            subdata[parameter],
            bounds_error=False,
            fill_value="extrapolate",
        )(cs_interp)
    return cs_interp, Ts, data_interp


def _pybamm_interp(cs_interp, Ts, data, c, T):
    return pybamm.Interpolant((cs_interp, Ts), data, [c, T])


def advanced_electrolyte_model(filename):
    aem_data = pd.read_csv(filename)

    # Get electrolyte parameters from data
    c_e = 1000
    electrolyte_parameters = {
        "Typical electrolyte concentration [mol.m-3]": c_e,
        "Initial concentration in electrolyte [mol.m-3]": c_e,
        "1 + dlnf/dlnc": 1,
    }
    for pybamm_name, aem_name, conversion_factor in [
        ("Electrolyte conductivity [S.m-1]", "Cond (mS) 2", 0.1),
        ("Cation transference number", "t+(a)", 1),
        ("Electrolyte diffusivity [m2.s-1]", "Diff. Coeff. cm^2/s", 1e-4),
    ]:
        cs_interp, Ts, data_interp = _get_2d_mesh_data(aem_data, aem_name)

        electrolyte_parameters[pybamm_name] = partial(
            _pybamm_interp,
            cs_interp * 1000,
            Ts + 273.15,
            conversion_factor * data_interp.T,
        )

    source = (
        "Electrolyte properties from Advanced Electrolyte Model "
        r"(with data from \\\verb!" + filename + r"!)"
    )
    return bpp.direct_entries.DirectEntry(
        parameters=electrolyte_parameters, source=source
    )
