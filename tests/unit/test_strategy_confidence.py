"""Unit tests for extraction strategy confidence scoring."""

import pytest

from xscanner.strategy.confidence import compute_confidence


class TestComputeConfidence:
    """Test compute_confidence helper."""

    def test_full_completeness_with_default_fields(self):
        """Test 6/6 fields filled with model confidence 0.95."""
        data = {
            "SerialNumber": "123456",
            "Metal": "Gold",
            "Weight": "100",
            "WeightUnit": "g",
            "Fineness": "999.9",
            "Producer": "Heraeus",
        }
        confidence = compute_confidence(0.95, data)
        assert confidence == pytest.approx(0.95)

    def test_partial_completeness_with_default_fields(self):
        """Test 4/6 fields filled with model confidence 0.95."""
        data = {
            "SerialNumber": "123456",
            "Metal": "Gold",
            "Weight": "100",
            "WeightUnit": "g",
            # Missing: Fineness, Producer
        }
        confidence = compute_confidence(0.95, data)
        # 4/6 * 0.95 = 0.633...
        assert confidence == pytest.approx(0.95 * 4 / 6)

    def test_no_fields_filled(self):
        """Test 0/6 fields filled."""
        data = {}
        confidence = compute_confidence(0.95, data)
        assert confidence == pytest.approx(0.0)

    def test_half_fields_filled(self):
        """Test 3/6 fields filled."""
        data = {
            "SerialNumber": "123456",
            "Metal": "Gold",
            "Weight": "100",
        }
        confidence = compute_confidence(0.95, data)
        # 3/6 * 0.95 = 0.475
        assert confidence == pytest.approx(0.95 * 3 / 6)

    def test_custom_fields_all_filled(self):
        """Test with custom expected fields, all filled."""
        data = {
            "Field1": "value1",
            "Field2": "value2",
            "Field3": "value3",
        }
        custom_fields = ["Field1", "Field2", "Field3"]
        confidence = compute_confidence(1.0, data, custom_fields)
        assert confidence == pytest.approx(1.0)

    def test_custom_fields_partial(self):
        """Test with custom expected fields, partially filled."""
        data = {
            "Field1": "value1",
            "Field3": "value3",
        }
        custom_fields = ["Field1", "Field2", "Field3"]
        confidence = compute_confidence(1.0, data, custom_fields)
        # 2/3 * 1.0 = 0.666...
        assert confidence == pytest.approx(1.0 * 2 / 3)

    def test_empty_expected_fields_returns_model_confidence(self):
        """Test empty expected fields list returns model confidence as-is."""
        data = {"SerialNumber": "123456"}
        confidence = compute_confidence(0.8, data, [])
        assert confidence == pytest.approx(0.8)

    def test_none_values_not_counted_as_filled(self):
        """Test that None/empty values are not counted as filled."""
        data = {
            "SerialNumber": "123456",
            "Metal": None,
            "Weight": "100",
            "WeightUnit": "",  # Empty string also not filled
            "Fineness": "999.9",
            "Producer": "Heraeus",
        }
        confidence = compute_confidence(0.95, data)
        # Only SerialNumber, Weight, Fineness, Producer are filled = 4/6
        assert confidence == pytest.approx(0.95 * 4 / 6)

    def test_model_confidence_zero(self):
        """Test model confidence 0.0 always results in 0.0."""
        data = {
            "SerialNumber": "123456",
            "Metal": "Gold",
            "Weight": "100",
            "WeightUnit": "g",
            "Fineness": "999.9",
            "Producer": "Heraeus",
        }
        confidence = compute_confidence(0.0, data)
        assert confidence == pytest.approx(0.0)

    def test_model_confidence_one_full_data(self):
        """Test model confidence 1.0 with all fields."""
        data = {
            "SerialNumber": "123456",
            "Metal": "Gold",
            "Weight": "100",
            "WeightUnit": "g",
            "Fineness": "999.9",
            "Producer": "Heraeus",
        }
        confidence = compute_confidence(1.0, data)
        assert confidence == pytest.approx(1.0)

    def test_chatgpt_typical_case(self):
        """Test typical ChatGPT case: 0.95 model confidence."""
        # Full data
        data_full = {
            "SerialNumber": "D08744",
            "Metal": "Gold",
            "Weight": "500",
            "WeightUnit": "g",
            "Fineness": "999.9",
            "Producer": "Degussa",
        }
        assert compute_confidence(0.95, data_full) == pytest.approx(0.95)

        # Incomplete data
        data_incomplete = {
            "SerialNumber": "D08744",
            "Metal": "Gold",
            "Weight": "500",
            # Missing WeightUnit, Fineness, Producer
        }
        assert compute_confidence(0.95, data_incomplete) == pytest.approx(0.95 * 3 / 6)

    def test_gemini_typical_case(self):
        """Test typical Gemini case: 1.0 model confidence."""
        # Full data
        data_full = {
            "SerialNumber": "AB55221",
            "Metal": "Gold",
            "Weight": "1",
            "WeightUnit": "kg",
            "Fineness": "999.9",
            "Producer": "Credit Suisse",
        }
        assert compute_confidence(1.0, data_full) == pytest.approx(1.0)

        # Incomplete data
        data_incomplete = {
            "Metal": "Gold",
            "Producer": "Credit Suisse",
        }
        assert compute_confidence(1.0, data_incomplete) == pytest.approx(1.0 * 2 / 6)
