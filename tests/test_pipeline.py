import battery_param_pipeline as bpp
import pytest


def test_pipeline_element():
    element = bpp.pipeline._PipelineElement("source")
    assert element.source == "source"


def test_read_only_dict():
    data = {"a": 1, "b": 2}
    read_only_dict = bpp.pipeline._ReadOnlyDict(data)
    assert read_only_dict["a"] == 1
    assert read_only_dict["b"] == 2
    assert len(read_only_dict) == 2
    assert list(read_only_dict) == ["a", "b"]
    with pytest.raises(TypeError):
        read_only_dict["c"] = 3


class TestPipeline:
    def test_pipeline(self):
        pipeline = bpp.pipeline.Pipeline([])
        assert pipeline.cache is None
        assert pipeline.report_ is None
