import pybamm
from scipy.optimize import least_squares
from .calculation import Calculation


class ElectrodeSOH(Calculation):
    def __init__(self):
        source = "Calculation of initial concentration in electrodes from capacity"
        super().__init__(source)

    def run(self, parameter_values):
        # Fit the value of nLi that gives the correct capacity
        esoh_solver = pybamm.lithium_ion.ElectrodeSOHSolver(
            pybamm.ParameterValues(parameter_values._data)
        )
        C_target = parameter_values["Nominal cell capacity [A.h]"]
        Cn = parameter_values["Negative electrode capacity [A.h]"]
        Cp = parameter_values["Positive electrode capacity [A.h]"]
        V_min = parameter_values["Lower voltage cut-off [V]"]
        V_max = parameter_values["Upper voltage cut-off [V]"]
        c_n_max = parameter_values[
            "Maximum concentration in negative electrode [mol.m-3]"
        ]
        c_p_max = parameter_values[
            "Maximum concentration in positive electrode [mol.m-3]"
        ]

        inputs = {"C_n": Cn, "C_p": Cp, "V_min": V_min, "V_max": V_max}

        def obj(nLi):
            inputs["n_Li"] = nLi[0]
            try:
                esoh_sol = esoh_solver.solve(inputs)
            except ValueError:
                return 1e5
            return C_target - esoh_sol["C"].data[0]

        x0 = min(Cn, Cp) * 3600 / pybamm.constants.F.value
        nLi = least_squares(obj, x0).x[0]
        inputs["n_Li"] = nLi
        esoh_sol = esoh_solver.solve(inputs)

        x100 = esoh_sol["x_100"].data[0]
        y100 = esoh_sol["y_100"].data[0]
        parameter_values = {
            "Initial concentration in negative electrode [mol.m-3]": x100 * c_n_max,
            "Initial concentration in positive electrode [mol.m-3]": y100 * c_p_max,
        }

        return parameter_values


class InitialSOC(Calculation):
    def __init__(self):
        source = "Initial concentrations for a target SOC"
        super().__init__(source)

    def run(self, parameter_values):
        x_100 = parameter_values["Maximum stoichiometry in negative electrode"]
        x_0 = parameter_values["Minimum stoichiometry in negative electrode"]
        y_100 = parameter_values["Minimum stoichiometry in positive electrode"]
        y_0 = parameter_values["Maximum stoichiometry in positive electrode"]
        soc = parameter_values["Initial SOC"]

        x = x_0 + soc * (x_100 - x_0) + x_0
        y = y_0 - soc * (y_0 - y_100)

        c_n_max = parameter_values[
            "Maximum concentration in negative electrode [mol.m-3]"
        ]
        c_p_max = parameter_values[
            "Maximum concentration in positive electrode [mol.m-3]"
        ]

        initial_concentration = {
            "Initial concentration in negative electrode [mol.m-3]": x * c_n_max,
            "Initial concentration in positive electrode [mol.m-3]": y * c_p_max,
        }
        return initial_concentration
