import pybamm
import battery_param_pipeline as bpp
import os
import matplotlib.pyplot as plt
import numpy as np
import scipy
from calendar_aging import CalendarAgeing


def schimpe2018():
    def negative_ocp(sto):
        u_eq = (
            0.6379
            + 0.5416 * pybamm.exp(-305.5309 * sto)
            + 0.044 * pybamm.tanh(-(sto - 0.1958) / 0.1088)
            - 0.1978 * pybamm.tanh((sto - 1.0571) / 0.0854)
            - 0.6875 * pybamm.tanh((sto + 0.0117) / 0.0529)
            - 0.0175 * pybamm.tanh((sto - 0.5692) / 0.0875)
        )

        return u_eq

    def positive_ocp(sto):
        u_eq = (
            3.4323
            - 0.8428 * pybamm.exp(-80.2493 * (1 - sto) ** 1.3198)
            - 3.2474e-6 * pybamm.exp(20.2645 * (1 - sto) ** 3.8003)
            + 3.2482e-6 * pybamm.exp(20.2646 * (1 - sto) ** 3.7995)
        )

        return u_eq

    parameters = {
        # negative electrode
        "Maximum concentration in negative electrode [mol.m-3]": 3.14e4,
        "Negative electrode thickness [m]": 6.01e-5,
        "Negative electrode active material volume fraction": 0.486,
        "Negative electrode OCP [V]": negative_ocp,
        "Negative electrode OCP entropic change [V.K-1]": 0,
        "Maximum stoichiometry in negative electrode": 0.78,
        "Minimum stoichiometry in negative electrode": 0.0085,
        "Negative particle radius [m]": 1e-6,
        # Positive electrode
        "Maximum concentration in positive electrode [mol.m-3]": 2.28e4,
        "Positive electrode thickness [m]": 7.9e-5,
        "Positive electrode active material volume fraction": 0.455,
        "Positive electrode OCP [V]": positive_ocp,
        "Positive electrode OCP entropic change [V.K-1]": 0,
        "Minimum stoichiometry in positive electrode": 0.045,
        "Maximum stoichiometry in positive electrode": 0.916,
        "Positive particle radius [m]": 1e-6,
        # cell
        "Electrode area [m2]": 1.57e-1,
        "Initial SOC": 1,
    }
    source = "Parameters for a graphite-LFP system from Schimpe et al. (2018)"

    return bpp.direct_entries.DirectEntry(parameters, source)


class CapacityCalculation(bpp.calculations.Calculation):
    """
    Calculate the capacity of the electrodes from the loading
    """

    def __init__(self):
        source = "Calculation of electrode capacity from loading"
        super().__init__(source)

    def run(self, parameter_values):
        F = pybamm.constants.F.value
        A_cc = parameter_values["Electrode area [m2]"]

        capacity_parameter_values = {}
        for side in ["negative", "positive"]:
            Side = side.capitalize()
            L = parameter_values[f"{Side} electrode thickness [m]"]
            c_max = parameter_values[
                f"Maximum concentration in {side} electrode [mol.m-3]"
            ]
            eps = parameter_values[f"{Side} electrode active material volume fraction"]

            Q_loading = L * eps * c_max * F / 3600  # A.h.m-2
            Q = Q_loading * A_cc  # Ah

            capacity_parameter_values.update(
                {
                    f"{Side} electrode loading [A.h.cm-2]": Q_loading / 1e4,
                    f"{Side} electrode capacity [A.h]": Q,
                }
            )

            sto_min = parameter_values[f"Minimum stoichiometry in {side} electrode"]
            sto_max = parameter_values[f"Maximum stoichiometry in {side} electrode"]
            Q_cell = Q * (sto_max - sto_min)
            capacity_parameter_values.update(
                {f"Cell capacity from {side} electrode [A.h]": Q_cell}
            )

        # Evaluate whole-cell quantities
        x_100 = parameter_values["Maximum stoichiometry in negative electrode"]
        x_0 = parameter_values["Minimum stoichiometry in negative electrode"]
        y_100 = parameter_values["Minimum stoichiometry in positive electrode"]
        y_0 = parameter_values["Maximum stoichiometry in positive electrode"]
        U_n = parameter_values["Negative electrode OCP [V]"]
        U_p = parameter_values["Positive electrode OCP [V]"]
        Q_n = capacity_parameter_values["Negative electrode capacity [A.h]"]
        Q_p = capacity_parameter_values["Positive electrode capacity [A.h]"]
        Q_cell_n = capacity_parameter_values[
            "Cell capacity from negative electrode [A.h]"
        ]
        Q_cell_p = capacity_parameter_values[
            "Cell capacity from positive electrode [A.h]"
        ]

        V_max = (U_p(y_100) - U_n(x_100)).evaluate()
        V_min = (U_p(y_0) - U_n(x_0)).evaluate()
        Q_Li = Q_n * x_100 + Q_p * y_100
        Q_cell = (Q_cell_n + Q_cell_p) / 2

        capacity_parameter_values.update(
            {
                "Upper voltage cut-off [V]": V_max,
                "Lower voltage cut-off [V]": V_min,
                "Cyclable lithium capacity [A.h]": Q_Li,
                "Nominal cell capacity [A.h]": Q_cell,
            }
        )
        return capacity_parameter_values


def standard_sei_parameters():
    parameters = {
        "Ratio of lithium moles to SEI moles": 2.0,
        "SEI partial molar volume [m3.mol-1]": 9.585e-05,
        "Bulk solvent concentration [mol.m-3]": 2636.0,
        "Lithium interstitial reference concentration [mol.m-3]": 15.0,
        "EC initial concentration in electrolyte [mol.m-3]": 4541.0,
        "SEI open-circuit potential [V]": 0.4,
        "SEI growth activation energy [J.mol-1]": 0.0,
        "SEI growth transfer coefficient": 0.5,
    }
    source = "Standard parameters for SEI"

    return bpp.direct_entries.DirectEntry(parameters, source)


class InitialSEIThickness(bpp.calculations.Calculation):
    def __init__(self):
        source = "Calculation of initial SEI thickness from min/max stoichiometries"
        super().__init__(source)

    def run(self, parameter_values):
        Q_n = parameter_values["Negative electrode capacity [A.h]"]
        Q_p = parameter_values["Positive electrode capacity [A.h]"]
        Q_Li = parameter_values["Cyclable lithium capacity [A.h]"]
        F = pybamm.constants.F.value
        L_n = parameter_values["Negative electrode thickness [m]"]
        A_cc = parameter_values["Electrode area [m2]"]
        V_sei = parameter_values["SEI partial molar volume [m3.mol-1]"]
        a = parameter_values["Negative electrode surface area to volume ratio [m-1]"]

        Q_sei_formation = Q_p - Q_Li  # Ah
        mol_sei_formation = Q_sei_formation * 3600 / F  # mol
        c_sei_formation = mol_sei_formation / (L_n * A_cc)  # mol.m-3
        L_sei_formation = c_sei_formation * V_sei / a  # m

        thickness_parameter_values = {
            "Capacity lost to SEI in formation [A.h]": Q_sei_formation,
            "Moles of SEI formed in formation [mol]": mol_sei_formation,
            "Initial SEI concentration [mol.m-3]": c_sei_formation,
            "Initial SEI thickness [m]": L_sei_formation,
        }

        return thickness_parameter_values


class TargetSEICalendarRate(bpp.calculations.Calculation):
    def __init__(self, target_percent_growth_per_month, sei_model):
        source = "SEI parameters to hit a target aging rate"
        super().__init__(source)
        self.target_percent_growth_per_month = target_percent_growth_per_month
        self.sei_model = sei_model

    def run(self, parameter_values):

        pybamm_parameter_values = pybamm.ParameterValues(dict(parameter_values))
        pybamm_parameter_values.update(
            {
                "SEI reaction exchange current density [A.m-2]": pybamm.InputParameter(
                    "j0_sei"
                )
            },
            check_already_exists=False,
        )
        model = pybamm_parameter_values.process_model(self.sei_model, inplace=False)
        pybamm.Discretisation().process_model(model)

        L_init = parameter_values["Initial SEI thickness [m]"]
        V_bar_SEI = parameter_values["SEI partial molar volume [m3.mol-1]"]
        F = pybamm.constants.F.value
        z_sei = parameter_values["Ratio of lithium moles to SEI moles"]
        seconds_per_month = 60 * 60 * 24 * 30
        dLdt_target = L_init * (
            0.01 * self.target_percent_growth_per_month / seconds_per_month
        )
        j_sei_target = dLdt_target / (-V_bar_SEI / (F * z_sei))

        y0 = model.concatenated_initial_conditions.evaluate()
        var = model.variables["SEI current density [A.m-2]"]

        def objective(j_sei):
            return (
                var.evaluate(y=y0, inputs={"j0_sei": j_sei}) - j_sei_target
            ).flatten()

        # fit using scipy
        j0_sei_target = scipy.optimize.root(objective, 1e-9).x[0]

        target_parameter_values = {
            "SEI reaction exchange current density [A.m-2]": j0_sei_target,
        }

        return target_parameter_values


output_dir = os.path.dirname(__file__)
model = CalendarAgeing({"SEI": "reaction limited"})
pipeline = bpp.Pipeline(
    [
        ("defaults", bpp.direct_entries.standard_defaults()),
        ("temperatures", bpp.direct_entries.temperatures(298.15)),
        ("Schimpe2018", schimpe2018()),
        ("dimensions", bpp.calculations.AreaToSquareWidthHeight()),
        ("initial soc", bpp.calculations.InitialSOC()),
        ("surface area", bpp.calculations.SurfaceArea()),
        ("capacity", CapacityCalculation()),
        ("standard SEI", standard_sei_parameters()),
        ("initial SEI thickness", InitialSEIThickness()),
        ("sei rates", TargetSEICalendarRate(1, model)),
    ],
    cache=output_dir,
)
parameter_values = pipeline.run()
# print(parameter_values)

# # pickle the parameter values
# import pickle

# output_dir = "/Users/vsulzer/Documents/Energy_storage/battery-model-parameterization"
# with open(os.path.join(output_dir, "parameter_values.pkl"), "wb") as f:
#     pickle.dump(parameter_values, f)
# print(parameter_values)

# bpp.plots.open_circuit(parameter_values)
# plt.show()
