import battery_param_pipeline as bpp


class Calculation(bpp.pipeline._PipelineElement):
    def __init__(self, source):
        super().__init__(source)
        self._type = "calculation"
