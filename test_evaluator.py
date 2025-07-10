import unittest
from datetime import datetime, timedelta
from rule_widget import condition_evaluator
# Assume condition_evaluator is imported or defined in this scope
import unittest
from datetime import datetime, timedelta

# Assume condition_evaluator is imported or defined in this scope

class TestConditionEvaluator(unittest.TestCase):

    def setUp(self):
        # Common timestamps for datetime and timedelta tests
        self.now = datetime.now()
        self.one_hour_ago = self.now - timedelta(hours=1)
        self.one_day_ago = self.now - timedelta(days=1)
        self.two_days_ago = self.now - timedelta(days=2)

    # --- STRING TESTS ---
    def test_string_equality_true(self):
        # Expect True because strings match exactly
        cond = {"db":"db1","field":"f1","op":"==","value":{"type":"string","content":"hello"}}
        data = {"db1":{"f1":"hello"}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_string_equality_false(self):
        # Expect False because strings differ
        cond = {"db":"db1","field":"f1","op":"==","value":{"type":"string","content":"hello"}}
        data = {"db1":{"f1":"world"}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    def test_string_contains_operator_lt_gt(self):
        # Expect True because 'ell' is substring of 'hello'
        cond = {"db":"db1","field":"f1","op":"<>","value":{"type":"string","content":"ell"}}
        data = {"db1":{"f1":"hello"}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_string_contains_operator_lt_gt_false(self):
        # Expect False because 'xyz' is NOT substring of 'hello'
        cond = {"db":"db1","field":"f1","op":"<>","value":{"type":"string","content":"xyz"}}
        data = {"db1":{"f1":"hello"}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    def test_string_in_operator_true(self):
        # Expect True because reference 'hello' is substring of 'hello world'
        cond = {"db":"db1","field":"f1","op":":=","value":{"type":"string","content":"hello world"}}
        data = {"db1":{"f1":"hello"}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_string_in_operator_false(self):
        # Expect False because 'hello' is NOT substring of 'world'
        cond = {"db":"db1","field":"f1","op":":=","value":{"type":"string","content":"world"}}
        data = {"db1":{"f1":"hello"}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    # --- NUMBER TESTS ---
    def test_number_equal(self):
        # Expect True because numbers are equal
        cond = {"db":"db1","field":"f1","op":"==","value":{"type":"number","content":5}}
        data = {"db1":{"f1":5}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_number_gte(self):
        # Expect True because 6 >= 5
        cond = {"db":"db1","field":"f1","op":">=","value":{"type":"number","content":5}}
        data = {"db1":{"f1":6}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_number_gt_false(self):
        # Expect False because 4 > 5 is False
        cond = {"db":"db1","field":"f1","op":">","value":{"type":"number","content":5}}
        data = {"db1":{"f1":4}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    def test_number_lt(self):
        # Expect True because 5 < 10
        cond = {"db":"db1","field":"f1","op":"<","value":{"type":"number","content":10}}
        data = {"db1":{"f1":5}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_number_lte(self):
        # Expect True because 5 <= 5
        cond = {"db":"db1","field":"f1","op":"<=","value":{"type":"number","content":5}}
        data = {"db1":{"f1":5}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    # --- RANGE TESTS ---
    def test_range_inclusive_true(self):
        # Expect True because 5 in range [3,7]
        cond = {"db":"db1","field":"f1","op":":=","value":{"type":"range","low":3,"high":7}}
        data = {"db1":{"f1":5}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_range_outside_false(self):
        # Expect False because 8 not in range [3,7]
        cond = {"db":"db1","field":"f1","op":":=","value":{"type":"range","low":3,"high":7}}
        data = {"db1":{"f1":8}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    # --- LIST TESTS ---
    def test_list_membership_true(self):
        # Expect True because reference 'b' in list ['a','b','c']
        cond = {"db":"db1","field":"f1","op":":=","value":{"type":"list","content":["a","b","c"]}}
        data = {"db1":{"f1":"b"}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_list_membership_false(self):
        # Expect False because 'd' not in list ['a','b','c']
        cond = {"db":"db1","field":"f1","op":":=","value":{"type":"list","content":["a","b","c"]}}
        data = {"db1":{"f1":"d"}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    def test_list_all_in_reference_true(self):
        # Expect True because all ['a','b'] in reference list ['a','b','c','d']
        cond = {"db":"db1","field":"f1","op":"<>","value":{"type":"list","content":["a","b"]}}
        data = {"db1":{"f1":["a","b","c","d"]}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_list_all_in_reference_false(self):
        # Expect False because 'x' not in reference list ['a','b','c']
        cond = {"db":"db1","field":"f1","op":"<>","value":{"type":"list","content":["a","x"]}}
        data = {"db1":{"f1":["a","b","c"]}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    # --- DATETIME TESTS ---
    def test_datetime_equal_true(self):
        # Expect True because datetime matches exactly
        cond = {
            "db":"db1",
            "field":"f1",
            "op":"==",
            "value":{"type":"datetime", "content":[self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second]}
        }
        data = {"db1":{"f1":self.now}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_datetime_equal_false(self):
        # Expect False because seconds differ by 1
        dt_content = [self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, (self.now.second + 1) % 60]
        cond = {
            "db":"db1",
            "field":"f1",
            "op":"==",
            "value":{"type":"datetime", "content":dt_content}
        }
        data = {"db1":{"f1":self.now}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    def test_datetime_wildcard_true(self):
        # Expect True because seconds are wildcard '*'
        dt_content = [self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, "*"]
        cond = {
            "db":"db1",
            "field":"f1",
            "op":"==",
            "value":{"type":"datetime", "content":dt_content}
        }
        data = {"db1":{"f1":self.now}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_datetime_greater_than_true(self):
        # Expect True because data time is later than condition time
        later = self.now + timedelta(seconds=10)
        cond = {
            "db":"db1",
            "field":"f1",
            "op":">",
            "value":{"type":"datetime", "content":[self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second]}
        }
        data = {"db1":{"f1":later}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_datetime_less_than_false(self):
        # Expect True because data time is earlier than condition time
        earlier = self.now - timedelta(seconds=10)
        cond = {
            "db":"db1",
            "field":"f1",
            "op":"<",
            "value":{"type":"datetime", "content":[self.now.year, self.now.month, self.now.day, self.now.hour, self.now.minute, self.now.second]}
        }
        data = {"db1":{"f1":earlier}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    # --- TIMEDELTA TESTS ---
    def test_timedelta_equal_true(self):
        # Expect True because timedelta matches exactly (1 hour difference)
        cond = {
            "db":"db1",
            "field":"f1",
            "op":"==",
            "value":{"type":"timedelta", "content":["0","0","0","1","0","0"]}  # 1 hour
        }
        data = {"db1":{"f1":self.now - timedelta(hours=1)}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_timedelta_greater_than_true(self):
        # Expect True because age is greater than 30 minutes
        cond = {
            "db":"db1",
            "field":"f1",
            "op":">",
            "value":{"type":"timedelta", "content":["0","0","0","0","30","0"]}  # 30 minutes
        }
        data = {"db1":{"f1":self.now - timedelta(hours=1)}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_timedelta_less_than_false(self):
        # Expect True because age (1 hour) is less than 2 hours
        cond = {
            "db":"db1",
            "field":"f1",
            "op":"<",
            "value":{"type":"timedelta", "content":["0","0","0","2","0","0"]}  # 2 hours
        }
        data = {"db1":{"f1":self.now - timedelta(hours=1)}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    # --- BOOL TESTS ---
    def test_bool_true(self):
        # Expect True because bool matches True
        cond = {"db":"db1","field":"f1","op":"==","value":{"type":"bool","content":True}}
        data = {"db1":{"f1":True}}
        self.assertTrue(condition_evaluator(cond, data))  # Expected: True

    def test_bool_false(self):
        # Expect False because bool in data is True but condition expects False
        cond = {"db":"db1","field":"f1","op":"==","value":{"type":"bool","content":False}}
        data = {"db1":{"f1":True}}
        self.assertFalse(condition_evaluator(cond, data))  # Expected: False

    # --- EDGE CASES ---
    def test_missing_field(self):
        # Expect AttributeError because missing field in data dictionary
        cond = {"db":"db1","field":"missing","op":"==","value":{"type":"string","content":"hello"}}
        data = {"db1":{"f1":"hello"}}
        with self.assertRaises(AttributeError):
            condition_evaluator(cond, data)  # Expected: raises AttributeError

    def test_unknown_value_type(self):
        # Expect Exception because value type is unknown
        cond = {"db":"db1","field":"f1","op":"==","value":{"type":"unknown","content":"abc"}}
        data = {"db1":{"f1":"abc"}}
        with self.assertRaises(Exception):
            condition_evaluator(cond, data)  # Expected: raises Exception

    def test_unknown_operator(self):
        # Expect ValueError because operator '???' is invalid
        cond = {"db":"db1","field":"f1","op":"???","value":{"type":"string","content":"abc"}}
        data = {"db1":{"f1":"abc"}}
        with self.assertRaises(ValueError):
            condition_evaluator(cond, data)  # Expected: raises ValueError

class TestDatetimeWildcardsRandomSamples(unittest.TestCase):
    def setUp(self):
        # Fixed datetime to test against: 2025-07-10 15:30:45
        self.ref_datetime = datetime(2025, 7, 10, 15, 30, 45)
        self.db = "db1"
        self.field = "field1"
        self.data = {self.db: {self.field: self.ref_datetime}}

    def make_condition(self, op, wildcards):
        return {
            "db": self.db,
            "field": self.field,
            "op": op,
            "value": {"type": "datetime", "content": wildcards}
        }

    # 1 wildcard, operator ==
    def test_eq_1_wildcard(self):
        # Wildcard in year, should match
        cond = self.make_condition("==", ['*', 7, 10, 15, 30, 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 1 wildcard, operator <
    def test_lt_1_wildcard(self):
        # Wildcard in minute, testing less than reference by setting minute lower
        cond = self.make_condition("<", [2025, 7, 10, 15, 29, 45])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 1 wildcard, operator >
    def test_gt_1_wildcard(self):
        # Wildcard in day, testing greater than by setting day higher
        cond = self.make_condition(">", [2025, 7, 11, 15, 30, 45])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 1 wildcard, operator <=
    def test_le_1_wildcard(self):
        # Wildcard in hour, testing less or equal by setting hour same as reference
        cond = self.make_condition("<=", [2025, 7, 10, 15, 30, 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 1 wildcard, operator >=
    def test_ge_1_wildcard(self):
        # Wildcard in second, testing greater or equal by setting second same as reference
        cond = self.make_condition(">=", [2025, 7, 10, 15, 30, 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 2 wildcards, operator ==
    def test_eq_2_wildcards(self):
        # Wildcards in year and month, should match
        cond = self.make_condition("==", ['*', '*', 10, 15, 30, 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 2 wildcards, operator <
    def test_lt_2_wildcards(self):
        # Wildcards in year and month, testing less than by setting day lower
        cond = self.make_condition("<", ['*', '*', 9, 15, 30, 45])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 2 wildcards, operator >
    def test_gt_2_wildcards(self):
        # Wildcards in hour and minute, testing greater than by setting day higher
        cond = self.make_condition(">", [2025, 7, 11, '*', '*', 45])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 3 wildcards, operator <=
    def test_le_3_wildcards(self):
        # Wildcards in year, month, day, testing less or equal by matching reference
        cond = self.make_condition("<=", ['*', '*', '*', 15, 30, 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 3 wildcards, operator >=
    def test_ge_3_wildcards(self):
        # Wildcards in month, day, hour, testing greater or equal by matching reference
        cond = self.make_condition(">=", [2025, '*', '*', '*', 30, 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 4 wildcards, operator ==
    def test_eq_4_wildcards(self):
        # Wildcards in year, month, day, hour, should match
        cond = self.make_condition("==", ['*', '*', '*', '*', 30, "*"])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 4 wildcards, operator <
    def test_lt_4_wildcards(self):
        # Wildcards in year, month, day, hour, testing less than with minute lower
        cond = self.make_condition("<", ['*', '*', '*', '*', 29, 45])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 5 wildcards, operator >
    def test_gt_5_wildcards(self):
        # Wildcards in year, month, day, hour, minute, testing greater than with second higher
        cond = self.make_condition(">", ['*', '*', '*', '*', '*', 46])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 5 wildcards, operator <=
    def test_le_5_wildcards(self):
        # Wildcards in year, month, day, hour, minute, testing less or equal with second same
        cond = self.make_condition("<=", ['*', '*', '*', '*', '*', 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 6 wildcards, operator ==
    def test_eq_6_wildcards(self):
        # All wildcards, should match anything including reference
        cond = self.make_condition("==", ['*', '*', '*', '*', '*', '*'])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 6 wildcards, operator <
    def test_lt_6_wildcards(self):
        # All wildcards with a value less than reference in last position
        cond = self.make_condition("<", ['*', '*', '*', '*', '*', 44])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 6 wildcards, operator >
    def test_gt_6_wildcards(self):
        # All wildcards with a value greater than reference in last position
        cond = self.make_condition(">", ['*', '*', '*', '*', '*', 46])
        self.assertFalse(condition_evaluator(cond, self.data))  # Expected: True

    # 6 wildcards, operator <=
    def test_le_6_wildcards(self):
        # All wildcards with value equal to reference in last position
        cond = self.make_condition("<=", ['*', '*', '*', '*', '*', 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # 6 wildcards, operator >=
    def test_ge_6_wildcards(self):
        # All wildcards with value equal to reference in last position
        cond = self.make_condition(">=", ['*', '*', '*', '*', '*', 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # Mixed wildcards and values, operator ==
    def test_eq_mixed_wildcards(self):
        # Wildcards at start and exact match at end
        cond = self.make_condition("==", ['*', '*', 10, 15, '*', 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

    # Mixed wildcards and values, operator >
    def test_gt_mixed_wildcards(self):
        # Wildcards with greater day value
        cond = self.make_condition(">", ['*', 7, 9, '*', 30, 45])
        self.assertTrue(condition_evaluator(cond, self.data))  # Expected: True

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
