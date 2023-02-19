import pybamm
import collections
import json
import os
import battery_param_pipeline as bpp


class _PipelineElement:
    def __init__(self, source):
        self._source = source

    def serialize(self, parameters):
        serialized = {}
        for k, v in parameters.items():
            if callable(v):
                try:
                    v = v.__name__
                except AttributeError:
                    v = "partial"
            else:
                v = str(v)
            serialized[k] = v
        return serialized

    def _generate_report(self, parameter_values):
        self.parameters_ = parameter_values
        self.report_ = {
            "source": self._source,
            "type": self._type,
            "parameters": self.serialize(parameter_values),
        }

    def _generate_latex(self):
        report = self._source + "\n\n"
        report += bpp.latex.parameter_dict_to_table(self.parameters_)
        return report


class _ReadOnlyDict(collections.abc.Mapping):
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)


class Pipeline:
    def __init__(self, named_components, cache=None):
        self.named_components = named_components
        self._cache = cache

        # Attributes generated when pipeline is run
        self.report_ = None

    @property
    def cache(self):
        return self._cache

    def run(self):
        parameter_values = _ReadOnlyDict({})
        report = {}
        for named_component in self.named_components:
            name, component = named_component
            new_params = component.run(parameter_values)
            component._generate_report(new_params)
            report[name] = component.report_
            duplicate_keys = [p for p in new_params if p in parameter_values]
            if any(duplicate_keys):
                raise ValueError(
                    "Parameter '{}' already exists in parameter values".format(
                        duplicate_keys[0]
                    )
                )
            parameter_values._data.update(new_params)

        self.report_ = report

        if self.cache is not None:
            self._save_cache()

        return pybamm.ParameterValues(parameter_values._data)

    def _save_cache(self):
        cache = os.path.join(self.cache, "parameters.json")
        json.dump(self.report_, open(cache, "w"), indent=4)
