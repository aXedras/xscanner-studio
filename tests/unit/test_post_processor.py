"""Unit tests for extraction post-processing."""

from xscanner.strategy.post_processor import ExtractionPostProcessor


class TestExtractionPostProcessor:
    def test_normalizes_fineness_decimal_separator(self):
        result = ExtractionPostProcessor.process(
            {
                "SerialNumber": " N 36676 ",
                "Fineness": "999,9",
                "Weight": "1kg",
            }
        )

        assert result["SerialNumber"] == "N36676"
        assert result["Weight"] == "1000"
        assert result["WeightUnit"] == "g"
        assert result["Fineness"] == "999.9"

    def test_normalizes_fineness_decimal_notation(self):
        result = ExtractionPostProcessor.process({"Fineness": "0,9999"})
        assert result["Fineness"] == "999.9"

    def test_keeps_non_numeric_fineness(self):
        result = ExtractionPostProcessor.process({"Fineness": "unknown"})
        assert result["Fineness"] == "unknown"
