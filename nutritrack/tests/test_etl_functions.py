"""Tests for ETL cleaning/aggregation functions."""

import pandas as pd

from scripts.aggregate_clean import (
    clean_barcode,
    clean_nova_group,
    clean_numeric,
    clean_nutriscore,
    clean_text,
    convert_kj_to_kcal,
    standardize_columns,
)


class TestCleanBarcode:
    def test_valid_ean13(self):
        assert clean_barcode("3017620422003") == "3017620422003"

    def test_valid_ean8(self):
        assert clean_barcode("12345678") == "12345678"

    def test_strips_whitespace(self):
        assert clean_barcode("  3017620422003  ") == "3017620422003"

    def test_removes_non_numeric(self):
        assert clean_barcode("301-762-042-2003") == "3017620422003"

    def test_rejects_too_short(self):
        assert clean_barcode("12345") is None

    def test_rejects_too_long(self):
        assert clean_barcode("123456789012345") is None

    def test_rejects_none(self):
        assert clean_barcode(None) is None

    def test_rejects_nan(self):
        assert clean_barcode(float("nan")) is None


class TestCleanText:
    def test_strips_whitespace(self):
        assert clean_text("  hello world  ") == "hello world"

    def test_normalizes_whitespace(self):
        assert clean_text("hello   world") == "hello world"

    def test_removes_control_chars(self):
        result = clean_text("hello\x00world")
        assert "\x00" not in result

    def test_returns_none_for_empty(self):
        assert clean_text("") is None

    def test_returns_none_for_nan(self):
        assert clean_text(float("nan")) is None


class TestCleanNutriscore:
    def test_valid_grades(self):
        for grade in ["A", "B", "C", "D", "E"]:
            assert clean_nutriscore(grade) == grade

    def test_lowercase_normalized(self):
        assert clean_nutriscore("a") == "A"

    def test_invalid_grade(self):
        assert clean_nutriscore("F") is None

    def test_none_input(self):
        assert clean_nutriscore(None) is None


class TestCleanNovaGroup:
    def test_valid_groups(self):
        for group in [1, 2, 3, 4]:
            assert clean_nova_group(group) == group

    def test_float_conversion(self):
        assert clean_nova_group(3.0) == 3

    def test_invalid_zero(self):
        assert clean_nova_group(0) is None

    def test_invalid_five(self):
        assert clean_nova_group(5) is None

    def test_none_input(self):
        assert clean_nova_group(None) is None


class TestCleanNumeric:
    def test_valid_value(self):
        assert clean_numeric(50.5) == 50.5

    def test_rounds_to_two_decimals(self):
        assert clean_numeric(50.555) == 50.56

    def test_rejects_negative(self):
        assert clean_numeric(-1) is None

    def test_rejects_over_max(self):
        assert clean_numeric(999, max_val=100) is None

    def test_none_input(self):
        assert clean_numeric(None) is None


class TestConvertKjToKcal:
    def test_conversion(self):
        result = convert_kj_to_kcal(4184)
        assert result == 1000.0

    def test_none_input(self):
        assert convert_kj_to_kcal(None) is None


class TestStandardizeColumns:
    def test_renames_known_columns(self):
        df = pd.DataFrame({"code": ["123"], "brands": ["TestBrand"], "data_source": ["api"]})
        result = standardize_columns(df)
        assert "barcode" in result.columns
        assert "brand_name" in result.columns

    def test_drops_unknown_columns(self):
        df = pd.DataFrame({"code": ["123"], "unknown_col": ["x"], "data_source": ["api"]})
        result = standardize_columns(df)
        assert "unknown_col" not in result.columns
