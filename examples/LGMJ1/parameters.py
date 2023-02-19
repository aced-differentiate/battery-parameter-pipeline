import pybamm
import battery_param_pipeline as bpp
import os
import matplotlib.pyplot as plt
import numpy as np


def sturm2018():
    def negative_ocp(sto):
        u_eq = (
            1.9793 * pybamm.exp(-39.3631 * sto)
            + 0.2482
            - 0.0909 * pybamm.tanh(29.8538 * (sto - 0.1234))
            - 0.04478 * pybamm.tanh(14.9159 * (sto - 0.2769))
            - 0.0205 * pybamm.tanh(30.4444 * (sto - 0.6103))
        )

        return u_eq

    def negative_exchange_current_density(c_e, c_s_surf, c_s_max, T):
        m_ref = 1e-11 * pybamm.constants.F
        E_r = 3600
        arrhenius = pybamm.exp(E_r * (1 / 298.15 - 1 / T))

        return (
            m_ref
            * arrhenius
            * c_e**0.5
            * c_s_surf**0.5
            * (c_s_max - c_s_surf) ** 0.5
        )

    def positive_ocp(sto):
        u_eq = (
            -0.8090 * sto
            + 4.4875
            - 0.0428 * pybamm.tanh(18.5138 * (sto - 0.5542))
            - 17.7326 * pybamm.tanh(15.7890 * (sto - 0.3117))
            + 17.5842 * pybamm.tanh(15.9308 * (sto - 0.3120))
        )

        return u_eq

    def positive_exchange_current_density(c_e, c_s_surf, c_s_max, T):
        m_ref = 3e-11 * pybamm.constants.F
        E_r = 3600
        arrhenius = pybamm.exp(E_r * (1 / 298.15 - 1 / T))

        return (
            m_ref
            * arrhenius
            * c_e**0.5
            * c_s_surf**0.5
            * (c_s_max - c_s_surf) ** 0.5
        )

    def electrolyte_diffusivity_Valoen2005(c_e, T):
        # mol/m3 to molar
        c_e = c_e / 1000

        T_g = 229 + 5 * c_e
        D_0 = -4.43 - 54 / (T - T_g)
        D_1 = -0.22

        # cm2/s to m2/s
        # note, in the Valoen paper, ln means log10, so its inverse is 10^x
        return (10 ** (D_0 + D_1 * c_e)) * 1e-4

    def electrolyte_conductivity_Valoen2005(c_e, T):
        # mol/m3 to molar
        c_e = c_e / 1000
        # mS/cm to S/m
        return (1e-3 / 1e-2) * (
            c_e
            * (
                (-10.5 + 0.0740 * T - 6.96e-5 * T**2)
                + c_e * (0.668 - 0.0178 * T + 2.80e-5 * T**2)
                + c_e**2 * (0.494 - 8.86e-4 * T)
            )
            ** 2
        )

    parameters = {
        # negative electrode
        "Maximum concentration in negative electrode [mol.m-3]": 34684,
        "Negative electrode thickness [m]": 86.7e-6,
        "Negative electrode active material volume fraction": 0.694,
        "Negative electrode porosity": 0.216,
        "Negative electrode OCP [V]": negative_ocp,
        "Negative electrode exchange-current density [A.m-2]": negative_exchange_current_density,
        "Negative electrode OCP entropic change [V.K-1]": 0,
        "Negative particle radius [m]": 6.1e-6,
        "Negative electrode Bruggeman coefficient (electrolyte)": 1.5,
        "Negative electrode Bruggeman coefficient (electrode)": 1.5,
        "Negative electrode conductivity [S.m-1]": 100,
        "Negative electrode diffusivity [m2.s-1]": 5e-14,
        # Separator
        "Separator thickness [m]": 12e-6,
        "Separator porosity": 0.45,
        "Separator Bruggeman coefficient (electrolyte)": 1.5,
        # Positive electrode
        "Maximum concentration in positive electrode [mol.m-3]": 50060,
        "Positive electrode thickness [m]": 66.2e-6,
        "Positive electrode active material volume fraction": 0.745,
        "Positive electrode porosity": 0.171,
        "Positive electrode OCP [V]": positive_ocp,
        "Positive electrode exchange-current density [A.m-2]": positive_exchange_current_density,
        "Positive electrode OCP entropic change [V.K-1]": 0,
        "Positive particle radius [m]": 3.8e-6,
        "Positive electrode Bruggeman coefficient (electrolyte)": 1.85,
        "Positive electrode Bruggeman coefficient (electrode)": 1.85,
        "Positive electrode conductivity [S.m-1]": 0.17,
        "Positive electrode diffusivity [m2.s-1]": 5e-13,
        # electrolyte
        "Typical electrolyte concentration [mol.m-3]": 1000.0,
        "Initial concentration in electrolyte [mol.m-3]": 1000.0,
        "Cation transference number": 0.38,
        "Electrolyte diffusivity [m2.s-1]": electrolyte_diffusivity_Valoen2005,
        "Electrolyte conductivity [S.m-1]": electrolyte_conductivity_Valoen2005,
        "1 + dlnf/dlnc": 1.0,
        # cell
        "Electrode height [m]": 5.8e-2,
        "Electrode width [m]": 61.5e-2 * 2,
        "Lower voltage cut-off [V]": 2.5,
        "Upper voltage cut-off [V]": 4.2,
        "Typical current [A]": 3.35,
        "Current function [A]": 3.35,
        "Nominal cell capacity [A.h]": 3.35,
    }
    source = "Parameters for a LGMJ1 cell from Sturm et al. (2018)"

    return bpp.direct_entries.DirectEntry(parameters, source)


class ElectrodeSOH(bpp.calculations.Calculation):
    def __init__(self):
        source = "Calculation of electrode SOH variables from target capacity"
        super().__init__(source)

    def run(self, parameter_values):
        param = pybamm.LithiumIonParameters()
        parameter_values = pybamm.ParameterValues(dict(parameter_values))
        T = parameter_values.evaluate(param.T_ref)

        x_0, x_100, y_100, y_0 = pybamm.lithium_ion.get_min_max_stoichiometries(
            parameter_values, param, known_value="cell capacity"
        )

        c_n_max = parameter_values[
            "Maximum concentration in negative electrode [mol.m-3]"
        ]
        c_p_max = parameter_values[
            "Maximum concentration in positive electrode [mol.m-3]"
        ]
        esoh_parameter_values = {
            "Initial concentration in negative electrode [mol.m-3]": c_n_max * x_100,
            "Maximum stoichiometry in negative electrode": x_100,
            "Minimum stoichiometry in negative electrode": x_0,
            "Initial concentration in positive electrode [mol.m-3]": c_p_max * y_100,
            "Minimum stoichiometry in positive electrode": y_100,
            "Maximum stoichiometry in positive electrode": y_0,
        }
        return esoh_parameter_values


output_dir = os.path.dirname(__file__)
pipeline = bpp.Pipeline(
    [
        ("defaults", bpp.direct_entries.standard_defaults()),
        ("temperatures", bpp.direct_entries.temperatures(298.15)),
        ("Sturm2018", sturm2018()),
        ("electrode SOH calculations", ElectrodeSOH()),
    ],
    cache=output_dir,
)
parameter_values = pipeline.run()

# pybamm.set_logging_level("INFO")
# # load models
# models = [
#     pybamm.lithium_ion.SPM(),
#     pybamm.lithium_ion.SPMe(),
#     pybamm.lithium_ion.DFN(),
# ]

# # create and run simulations
# sims = []
# parameter_values["Current function [A]"] = (
#     parameter_values["Nominal cell capacity [A.h]"] / 5
# )
# for model in models:
#     sim = pybamm.Simulation(model, parameter_values=parameter_values)
#     sim.solve(np.linspace(0, 3600 * 5, 1000))
#     sims.append(sim)

# # plot
# pybamm.dynamic_plot(sims, ["Terminal voltage [V]"])
bpp.plots.open_circuit(parameter_values)
plt.show()
