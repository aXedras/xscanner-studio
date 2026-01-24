"""Unit tests for extraction post-processing."""

from xscanner.strategy.post_processor import ExtractionPostProcessor, normalize_weight


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

    def test_normalizes_producer_credit_suisse_variants(self):
        assert ExtractionPostProcessor.process({"Producer": "CS"})["Producer"] == "Credit Suisse"
        assert ExtractionPostProcessor.process({"Producer": "C.S."})["Producer"] == "Credit Suisse"
        assert (
            ExtractionPostProcessor.process({"Producer": "Credit-Suisse"})["Producer"]
            == "Credit Suisse"
        )
        assert (
            ExtractionPostProcessor.process({"Producer": "CREDIT SUISSE"})["Producer"]
            == "Credit Suisse"
        )


class TestNormalizeWeight:
    """Test weight normalization functionality."""

    def test_kg_conversion(self):
        """Test conversion of kg to grams."""
        data = {"Weight": "1kg"}
        result = normalize_weight(data)

        assert result["Weight"] == "1000"
        assert result["WeightUnit"] == "g"

    def test_grams_unchanged(self):
        """Test that grams stay as grams."""
        data = {"Weight": "100g"}
        result = normalize_weight(data)

        assert result["Weight"] == "100"
        assert result["WeightUnit"] == "g"

    def test_decimal_kg(self):
        """Test decimal kg values."""
        data = {"Weight": "1.5kg"}
        result = normalize_weight(data)

        assert result["Weight"] == "1500"
        assert result["WeightUnit"] == "g"

    def test_number_only(self):
        """Test plain numbers (default to grams)."""
        data = {"Weight": "250"}
        result = normalize_weight(data)

        assert result["Weight"] == "250"
        assert result["WeightUnit"] == "g"

    def test_with_space(self):
        """Test weight with space between value and unit."""
        data = {"Weight": "1 kg"}
        result = normalize_weight(data)

        assert result["Weight"] == "1000"
        assert result["WeightUnit"] == "g"

    def test_gram_alternatives(self):
        """Test alternative gram spellings."""
        test_cases = [
            ("100 gram", "100", "g"),
            ("100 grams", "100", "g"),
            ("1 kilogram", "1000", "g"),
            ("1 kilograms", "1000", "g"),
        ]

        for input_val, expected_weight, expected_unit in test_cases:
            data = {"Weight": input_val}
            result = normalize_weight(data)

            assert result["Weight"] == expected_weight
            assert result["WeightUnit"] == expected_unit

    def test_no_weight_field(self):
        """Test that missing Weight field returns unchanged data."""
        data = {"Metal": "Au"}
        result = normalize_weight(data)

        assert result == {"Metal": "Au"}
        assert "Weight" not in result
        assert "WeightUnit" not in result

    def test_preserves_other_fields(self):
        """Test that other fields are preserved."""
        data = {"Weight": "1kg", "Metal": "Au", "Fineness": "9999", "SerialNumber": "123456"}
        result = normalize_weight(data)

        assert result["Weight"] == "1000"
        assert result["WeightUnit"] == "g"
        assert result["Metal"] == "Au"
        assert result["Fineness"] == "9999"
        assert result["SerialNumber"] == "123456"

    def test_already_normalized(self):
        """Test data that's already normalized (separate Weight and WeightUnit)."""
        data = {"Weight": "1000", "WeightUnit": "g"}
        result = normalize_weight(data)

        # Should not change already normalized data
        assert result["Weight"] == "1000"
        assert result["WeightUnit"] == "g"

    def test_invalid_format_unchanged(self):
        """Test that invalid formats are left unchanged."""
        data = {"Weight": "invalid"}
        result = normalize_weight(data)

        # Should return original data unchanged
        assert result["Weight"] == "invalid"
        assert "WeightUnit" not in result
