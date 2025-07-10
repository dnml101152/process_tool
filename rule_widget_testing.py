import unittest
from rule_widget import Parser
from rule_widget import logical_tokenize as tokenize
from rule_widget import tokenize_condition, ConditionParser
# Assuming the tokenize() and Parser class are defined above as before


class TestParserDictOutput(unittest.TestCase):

    def test_simple_not(self):
        input_str = '$NOT(?a == 1?)'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$NOT",
            "args": [
                {"type": "condition", "value": "a == 1"}
            ]
        }
        self.assertEqual(ast, expected)

    def test_simple_and(self):
        input_str = '$AND(?a == 1?, ?b == 2?)'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$AND",
            "args": [
                {"type": "condition", "value": "a == 1"},
                {"type": "condition", "value": "b == 2"}
            ]
        }
        self.assertEqual(ast, expected)

    def test_simple_or(self):
        input_str = '$OR(?a == 1?, ?b == 2?)'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$OR",
            "args": [
                {"type": "condition", "value": "a == 1"},
                {"type": "condition", "value": "b == 2"}
            ]
        }
        self.assertEqual(ast, expected)

    def test_nested_not_or(self):
        input_str = '$OR($NOT(?a == 1?), ?b == 2?)'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$OR",
            "args": [
                {
                    "type": "operator",
                    "operator": "$NOT",
                    "args": [
                        {"type": "condition", "value": "a == 1"}
                    ]
                },
                {"type": "condition", "value": "b == 2"}
            ]
        }
        self.assertEqual(ast, expected)

    def test_nested_or_not(self):
        input_str = '$NOT($OR(?a == 1?, ?b == 2?))'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$NOT",
            "args": [
                {
                    "type": "operator",
                    "operator": "$OR",
                    "args": [
                        {"type": "condition", "value": "a == 1"},
                        {"type": "condition", "value": "b == 2"}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected)

    def test_double_not(self):
        input_str = '$NOT($NOT(?a == 1?))'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$NOT",
            "args": [
                {
                    "type": "operator",
                    "operator": "$NOT",
                    "args": [
                        {"type": "condition", "value": "a == 1"}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected)

    def test_three_level_nested(self):
        input_str = '$OR($NOT($OR(?a == 1?, ?b == 2?)), $NOT(?c == 3?))'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$OR",
            "args": [
                {
                    "type": "operator",
                    "operator": "$NOT",
                    "args": [
                        {
                            "type": "operator",
                            "operator": "$OR",
                            "args": [
                                {"type": "condition", "value": "a == 1"},
                                {"type": "condition", "value": "b == 2"}
                            ]
                        }
                    ]
                },
                {
                    "type": "operator",
                    "operator": "$NOT",
                    "args": [
                        {"type": "condition", "value": "c == 3"}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected)

    def test_three_level_nested_swapped(self):
        input_str = '$NOT($OR($NOT(?a == 1?), ?b == 2?))'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        ast = parser.parse_expression()
        expected = {
            "type": "operator",
            "operator": "$NOT",
            "args": [
                {
                    "type": "operator",
                    "operator": "$OR",
                    "args": [
                        {
                            "type": "operator",
                            "operator": "$NOT",
                            "args": [
                                {"type": "condition", "value": "a == 1"}
                            ]
                        },
                        {"type": "condition", "value": "b == 2"}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected)

    def test_invalid_condition_unterminated(self):
        input_str = '$AND(?a == 1?, ?b == 2)'  # missing trailing '?'
        with self.assertRaises(SyntaxError):
            tokenize(input_str)

    def test_invalid_condition_unstarted(self):
        input_str = '$AND(a == 1?, ?b == 2?)'  # missing trailing '?'
        with self.assertRaises(SyntaxError):
            tokenize(input_str)

    def test_invalid_unexpected_token(self):
        input_str = '( $NOT(?a == 1?) )'  # starts with '(' but no operator before
        with self.assertRaises(SyntaxError):
            tokens = tokenize(input_str)
            parser = Parser(tokens)
            parser.parse_expression()

    def test_invalid_missing_rparen(self):
        input_str = '$OR(?a == 1?, ?b == 2?'  # missing closing ')'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        with self.assertRaises(SyntaxError):
            parser.parse_expression()

    def test_invalid_not_multiple_args(self):
        input_str = '$NOT(?a == 1?, ?b == 2?)'
        tokens = tokenize(input_str)
        parser = Parser(tokens)
        with self.assertRaises(SyntaxError):
            parser.parse_expression()


class TestFullParsing(unittest.TestCase):

    def parse_condition(self, cond_str):
        tokens = tokenize_condition(cond_str)
        parser = ConditionParser(tokens)
        return parser.parse()

    # --- Valid condition tests ---

    def test_valid_condition_simple_string(self):
        cond = 'security.region == "CA"'
        expected = {
            "type": "condition",
            "db": "security",
            "field": "region",
            "op": "==",
            "value": "CA"
        }
        result = self.parse_condition(cond)
        self.assertEqual(result, expected)

    def test_valid_condition_simple_number(self):
        cond = 'research.price >= 1000'
        expected = {
            "type": "condition",
            "db": "research",
            "field": "price",
            "op": ">=",
            "value": "1000"
        }
        result = self.parse_condition(cond)
        self.assertEqual(result, expected)

    def test_valid_condition_timedelta(self):
        cond = 'timing.delay := {1,2,3,4,5,6}'
        expected = {
            "type": "condition",
            "db": "timing",
            "field": "delay",
            "op": ":=",
            "value": {
                "type": "timedelta",
                "value": ['1','2','3','4','5','6']
            }
        }
        result = self.parse_condition(cond)
        self.assertEqual(result, expected)

    def test_valid_condition_datetime_with_wildcards(self):
        cond = 'event.start == (2025,*,3,4,*,6)'
        expected = {
            "type": "condition",
            "db": "event",
            "field": "start",
            "op": "==",
            "value": {
                "type": "datetime",
                "value": ['2025','*','3','4','*','6']
            }
        }
        result = self.parse_condition(cond)
        self.assertEqual(result, expected)

    def test_valid_condition_range(self):
        cond = 'value.range <> /-2,6/'
        expected = {
            "type": "condition",
            "db": "value",
            "field": "range",
            "op": "<>",
            "value": {
                "type": "range",
                "low": "-2",
                "high": "6"
            }
        }
        result = self.parse_condition(cond)
        self.assertEqual(result, expected)

    def test_valid_condition_string_list(self):
        cond = 'filter.names == ["A","B","C"]'
        expected = {
            "type": "condition",
            "db": "filter",
            "field": "names",
            "op": "==",
            "value": {
                "type": "list",
                "value_type": "string",
                "values": ['A','B','C']
            }
        }
        result = self.parse_condition(cond)
        self.assertEqual(result, expected)

    def test_valid_condition_wildcard_star(self):
        cond = 'wildcard.value == *'
        expected = {
            "type": "condition",
            "db": "wildcard",
            "field": "value",
            "op": "==",
            "value": "*"
        }
        result = self.parse_condition(cond)
        self.assertEqual(result, expected)

    # --- Invalid condition tests ---

    def test_invalid_condition_missing_dot(self):
        cond = 'securityregion == "NY"'  # missing dot in field name
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)

    def test_invalid_condition_unterminated_string(self):
        cond = 'security.region == "NY'  # missing closing quote
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)

    def test_invalid_condition_timedelta_too_few_numbers(self):
        cond = 'timing.delay := {1,2,3,4,5}'  # only 5 numbers instead of 6
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)

    def test_invalid_condition_datetime_too_few_elements(self):
        cond = 'event.start == (2025,2,3,4,5)'  # only 5 elements in datetime
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)

    def test_invalid_condition_range_missing_closing_slash(self):
        cond = 'value.range <> /-2,6'  # missing closing slash
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)

    def test_invalid_condition_list_unterminated_string(self):
        cond = 'filter.names == ["A","B]'  # unterminated string in list
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)

    def test_invalid_condition_list_invalid_string_elements(self):
        cond = 'filter.names == [A,B,C]'  # missing quotes for string elements
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)

    def test_invalid_condition_list_invalid_miexed_elements(self):
        cond = 'filter.names == ["A","B",1]'  # missing quotes for string elements
        with self.assertRaises(SyntaxError):
            self.parse_condition(cond)
if __name__ == "__main__":
    unittest.main()




