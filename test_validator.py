import unittest
from rule_widget import validate_condition_node

class TestConditionValidator(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "security.region": "string",
            "price.last": "float",
            "trades.count": "int",
            "research.last_trade": "datetime",
            "research.window": "datetime"
        }

    # ---------- STRING VALIDATIONS ----------

    # Valid: simple string equality
    def test_valid_string_eq(self):
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': '==',
            'value': {'type': 'string', 'content': 'CA'}
        }
        validate_condition_node(node, self.schema)

    # Valid: string contains operator
    def test_valid_string_neq(self):
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': '<>',
            'value': {'type': 'string', 'content': 'NY'}
        }
        validate_condition_node(node, self.schema)

    # Valid: string IN list
    def test_valid_string_list_in(self):
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': ':=',
            'value': {'type': 'list', 'content': ['CA', 'NY']}
        }
        validate_condition_node(node, self.schema)

    # Invalid: string comparison with unsupported operator
    def test_invalid_string_operator(self):
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': '>',
            'value': {'type': 'string', 'content': 'CA'}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # Invalid: list with non-string elements
    def test_invalid_string_list_with_non_strings(self):
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': ':=',
            'value': {'type': 'list', 'content': ['CA', 123]}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # ---------- NUMBER VALIDATIONS ----------

    # Valid: float value with supported comparison
    def test_valid_number_float(self):
        node = {
            'type': 'condition',
            'db': 'price',
            'field': 'last',
            'op': '>=',
            'value': {'type': 'number', 'content': 10.5}
        }
        validate_condition_node(node, self.schema)

    # Valid: integer value with supported comparison
    def test_valid_number_int(self):
        node = {
            'type': 'condition',
            'db': 'trades',
            'field': 'count',
            'op': '<',
            'value': {'type': 'number', 'content': 42}
        }
        validate_condition_node(node, self.schema)

    # Valid: numeric range with float bounds
    def test_valid_number_range(self):
        node = {
            'type': 'condition',
            'db': 'price',
            'field': 'last',
            'op': ':=',
            'value': {'type': 'range', 'low': 1.1, 'high': 2.2}
        }
        validate_condition_node(node, self.schema)

    # Valid: list of integers for `:=` operator
    def test_valid_number_list(self):
        node = {
            'type': 'condition',
            'db': 'trades',
            'field': 'count',
            'op': ':=',
            'value': {'type': 'list', 'content': [1, 2, 3]}
        }
        validate_condition_node(node, self.schema)

    # Invalid: unsupported operator for numbers
    def test_invalid_number_operator(self):
        node = {
            'type': 'condition',
            'db': 'price',
            'field': 'last',
            'op': '<>',
            'value': {'type': 'number', 'content': 10.0}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # Invalid: non-numeric type in range bounds
    def test_invalid_number_range_wrong_type(self):
        node = {
            'type': 'condition',
            'db': 'price',
            'field': 'last',
            'op': ':=',
            'value': {'type': 'range', 'low': 'a', 'high': 5}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # Invalid: number list with mixed types
    def test_invalid_number_list_with_str(self):
        node = {
            'type': 'condition',
            'db': 'trades',
            'field': 'count',
            'op': ':=',
            'value': {'type': 'list', 'content': [1, '2', 3]}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # ---------- DATETIME VALIDATIONS ----------

    # Valid: datetime wildcard + number pattern
    def test_valid_datetime(self):
        node = {
            'type': 'condition',
            'db': 'research',
            'field': 'last_trade',
            'op': '==',
            'value': {'type': 'datetime', 'content': ['*', '*', '*', 8, '*', '*']}
        }
        validate_condition_node(node, self.schema)

    # Valid: timedelta with 6 numeric values
    def test_valid_timedelta(self):
        node = {
            'type': 'condition',
            'db': 'research',
            'field': 'window',
            'op': '>=',
            'value': {'type': 'timedelta', 'content': [0, 0, 0, 2, 0, 0]}
        }
        validate_condition_node(node, self.schema)

    # Invalid: bad string inside datetime content
    def test_invalid_datetime_bad_item(self):
        node = {
            'type': 'condition',
            'db': 'research',
            'field': 'last_trade',
            'op': '==',
            'value': {'type': 'datetime', 'content': ['*', 'bad', '*', 1, 2, 3]}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # ---------- GENERAL / STRUCTURE VALIDATIONS ----------

    # Invalid: unknown field not in schema
    def test_unknown_field(self):
        node = {
            'type': 'condition',
            'db': 'unknown',
            'field': 'field',
            'op': '==',
            'value': {'type': 'string', 'content': 'test'}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # Invalid: unhandled schema type
    def test_unhandled_schema_type(self):
        self.schema["security.region"] = "custom"
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': '==',
            'value': {'type': 'string', 'content': 'x'}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)
        self.schema["security.region"] = "string"  # restore

    # Invalid: value dict missing 'type'
    def test_missing_value_type(self):
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': '==',
            'value': {'content': 'CA'}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

    # Invalid: value dict missing 'content'
    def test_missing_value_content(self):
        node = {
            'type': 'condition',
            'db': 'security',
            'field': 'region',
            'op': '==',
            'value': {'type': 'string'}
        }
        with self.assertRaises(ValueError):
            validate_condition_node(node, self.schema)

if __name__ == '__main__':
    unittest.main()
