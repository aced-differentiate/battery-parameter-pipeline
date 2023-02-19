import battery_param_pipeline as bpp


class DirectEntry(bpp.pipeline._PipelineElement):
    def __init__(self, parameters, source):
        super().__init__(source)
        self._parameters = parameters
        self._type = "direct entry"

    def run(self, parameter_values):
        # ignores the parameter values but provided for consistent interface
        return self._parameters.copy()


def standard_defaults():
    parameters = {
        "Negative electrode cation signed stoichiometry": -1.0,
        "Negative electrode electrons in reaction": 1.0,
        "Positive electrode cation signed stoichiometry": -1.0,
        "Positive electrode electrons in reaction": 1.0,
        "Number of cells connected in series to make a battery": 1.0,
        "Number of electrodes connected in parallel to make a cell": 1.0,
    }
    source = "Standard defaults for parameters that are not explicitly set by the user"
    return DirectEntry(parameters, source)


def temperatures(T):
    parameters = {
        "Reference temperature [K]": T,
        "Ambient temperature [K]": T,
        "Initial temperature [K]": T,
    }
    source = f"All 'temperature' parameters set to {T} [K]"
    return DirectEntry(parameters, source)


def constant_electrolyte(c_e):
    parameters = {
        "Initial concentration in electrolyte [mol.m-3]": c_e,
        "Typical electrolyte concentration [mol.m-3]": c_e,
    }
    source = f"Electrolyte concentration set to {c_e} [mol.m-3]"
    return DirectEntry(parameters, source)
