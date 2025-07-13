import unittest
from rule_widget import evaluate_expression as evaluate_logical_expression
class TestLogicalEvaluation(unittest.TestCase):

    def make_leaf(self, result: bool):
        return {"type": "condition", "eval_result": result}

    def test_simple_and(self):
        # AND(TRUE, TRUE)
        expr = {"type": "operator", "operator": "$AND", "args": [self.make_leaf(True), self.make_leaf(True)]}
        self.assertTrue(evaluate_logical_expression(expr))

    def test_simple_or(self):
        # OR(FALSE, TRUE)
        expr = {"type": "operator", "operator": "$OR", "args": [self.make_leaf(False), self.make_leaf(True)]}
        self.assertTrue(evaluate_logical_expression(expr))

    def test_simple_not(self):
        # NOT(TRUE)
        expr = {"type": "operator", "operator": "$NOT", "args": [self.make_leaf(True)]}
        self.assertFalse(evaluate_logical_expression(expr))

    def test_nested_1(self):
        # OR(AND(NOT(TRUE), FALSE), TRUE, FALSE)
        expr = {
            "type": "operator", "operator": "$OR", "args": [
                {
                    "type": "operator", "operator": "$AND", "args": [
                        {"type": "operator", "operator": "$NOT", "args": [self.make_leaf(True)]},
                        self.make_leaf(False)
                    ]
                },
                self.make_leaf(True),
                self.make_leaf(False)
            ]
        }
        self.assertTrue(evaluate_logical_expression(expr))

    def test_nested_2(self):
        # AND(OR(FALSE, FALSE), NOT(FALSE)) -> AND(FALSE, TRUE) = FALSE
        expr = {
            "type": "operator", "operator": "$AND", "args": [
                {
                    "type": "operator", "operator": "$OR", "args": [
                        self.make_leaf(False),
                        self.make_leaf(False)
                    ]
                },
                {
                    "type": "operator", "operator": "$NOT", "args": [
                        self.make_leaf(False)
                    ]
                }
            ]
        }
        self.assertFalse(evaluate_logical_expression(expr))

    def test_nested_3(self):
        # NOT(OR(FALSE, AND(TRUE, FALSE))) -> NOT(OR(FALSE, FALSE)) = NOT(FALSE) = TRUE
        expr = {
            "type": "operator", "operator": "$NOT", "args": [
                {
                    "type": "operator", "operator": "$OR", "args": [
                        self.make_leaf(False),
                        {
                            "type": "operator", "operator": "$AND", "args": [
                                self.make_leaf(True),
                                self.make_leaf(False)
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertTrue(evaluate_logical_expression(expr))

    def test_nested_4(self):
        # AND(NOT(FALSE), OR(FALSE, TRUE)) -> AND(TRUE, TRUE) = TRUE
        expr = {
            "type": "operator", "operator": "$AND", "args": [
                {
                    "type": "operator", "operator": "$NOT", "args": [self.make_leaf(False)]
                },
                {
                    "type": "operator", "operator": "$OR", "args": [self.make_leaf(False), self.make_leaf(True)]
                }
            ]
        }
        self.assertTrue(evaluate_logical_expression(expr))

    def test_nested_5(self):
        # NOT(AND(TRUE, NOT(TRUE))) -> NOT(AND(TRUE, FALSE)) = NOT(FALSE) = TRUE
        expr = {
            "type": "operator", "operator": "$NOT", "args": [
                {
                    "type": "operator", "operator": "$AND", "args": [
                        self.make_leaf(True),
                        {
                            "type": "operator", "operator": "$NOT", "args": [
                                self.make_leaf(True)
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertTrue(evaluate_logical_expression(expr))



if __name__ == "__main__":
    unittest.main()