import unittest
import copy
from rule_widget import reconstruct_expression, process_input_string

# ----- bring these into scope ------------------------------------------------
# from my_module import reconstruct_expression, parse_expression_string
# -----------------------------------------------------------------------------

VALID_FIELDS = {
    # security (sec)
    "sec.price": "float",  # Used with numeric, range, comparisons
    "sec.region": "string",  # Strings like "US", "CA", "EU", "APAC"
    "sec.tags": "string",  # List of strings, e.g. ["vip","urgent"]

    # user
    "user.active": "bool",  # Boolean True/False
    "user.roles": "string",  # List of strings, e.g. ["admin","editor"]
    "user.age": "int",  # Numeric age
    "user.score": "float",  # Numeric score
    "user.login_count": "float",  # Numeric count
    "user.verified": "bool",  # Boolean verified

    # research (research)
    "research.last_trade": "datetime",  # List of 6 ints or wildcards ["*", "*", "*", "8", "*", "*"]
    "research.age": "datetime",  # List of 6 ints as timedelta components

    # metrics (metrics)
    "metrics.value": "float",
    "metrics.score": "float",
    "metrics.rank": "int",

    # m (from your previous examples)
    "m.score": "float",
    "m.rank": "float",

    # u (from your previous examples)
    "u.active": "bool",

    # r (research alias or shorthand)
    "r.tags": "string",
    "r.last_trade": "datetime",
    "r.age": "datetime",

    # db shorthand:
    # sec = security
    # user = user
    # research = research
    # metrics = metrics
    # m, u, r = short aliases or extra dbs

}

def strip_eval(node):
    """Remove eval_result fields so they don’t interfere with equality check."""
    if isinstance(node, dict):
        node = {k: strip_eval(v) for k, v in node.items() if k != 'eval_result'}
    elif isinstance(node, list):
        node = [strip_eval(v) for v in node]
    return node


class TestRoundTripDictString(unittest.TestCase):

    # ---------- helper -------------------------------------------------------
    def round_trip(self, test_string):
        print(22,test_string)
        resulting_ast_dict = process_input_string(test_string, VALID_FIELDS)
        print(33,resulting_ast_dict)
        expr_str = reconstruct_expression(resulting_ast_dict)
        print(44,expr_str)

        resulting_ast_dict__ii = process_input_string(expr_str, VALID_FIELDS)

        print(55,resulting_ast_dict__ii)
        # rebuilt   = process_input_string(expr_str,VALID_FIELDS)
        self.assertEqual(resulting_ast_dict, resulting_ast_dict__ii)

    # ---------- TEST‑CASES ----------------------------------------------------
    #


    # 2. AND(price:=/2,4/, NOT(region=="US"))  – includes range + string
    def test_and_range_and_not_string(self):
        teststring = "$OR(?sec.price == 52?,$NOT(?sec.region:=[\"US\",\"CA\"]?))"
        self.round_trip(teststring)

    def test_01_and_range_and_not_string(self):
        teststring = "$AND(?sec.price:=/10,20/?,$NOT(?sec.region==\"US\"?))"
        self.round_trip(teststring)

    def test_02_or_list_and_bool(self):
        teststring = "$OR(?sec.tags<>\"vip\"?,?user.active==TRUE?)"
        self.round_trip(teststring)

    def test_03_not_or_datetime_and_number(self):
        teststring = "$NOT($OR(?research.last_trade==(*,*,*,9,*,*)?,?metrics.score>=75?))"
        self.round_trip(teststring)

    def test_04_and_timedelta_or_string(self):
        teststring = "$AND(?research.age> {0,0,1,0,0,0}?,$OR(?sec.region==\"CA\"?,?sec.region==\"US\"?))"
        self.round_trip(teststring)

    def test_05_or_and_and(self):
        teststring = "$OR($AND(?sec.price>100?,$NOT(?sec.region==\"EU\"?)),$AND(?user.active==TRUE?,?user.login_count>=5?))"
        self.round_trip(teststring)

    def test_06_not_and_or(self):
        teststring = "$NOT($AND(?sec.tags:= [\"premium\"]?,$OR(?user.age<30?,?user.score>80?)))"
        self.round_trip(teststring)

    def test_07_and_datetime_wildcards(self):
        teststring = "$AND(?research.last_trade==(*,*,*,8,30,*)?,?sec.region==\"CA\"?)"
        self.round_trip(teststring)

    def test_08_or_number_and_bool(self):
        teststring = "$OR(?metrics.value<100?,?user.verified==FALSE?)"
        self.round_trip(teststring)

    def test_09_and_list_not_bool(self):
        teststring = "$AND(?user.roles<>\"admin\"?,$NOT(?user.active==FALSE?))"
        self.round_trip(teststring)

    def test_10_not_or_range_and(self):
        teststring = "$NOT($OR(?metrics.score:=/50,70/?,$AND(?sec.region==\"US\"?,?sec.price<=200?)))"
        self.round_trip(teststring)

    def test_11_complex_nesting(self):
        teststring = "$AND($OR(?sec.region==\"CA\"?,?sec.region==\"US\"?),$NOT($AND(?user.active==FALSE?,?metrics.value<50?)))"
        self.round_trip(teststring)

    def test_12_timedelta_and_list(self):
        teststring = "$AND(?research.age>= {0,0,0,1,0,0}?,?sec.tags:= [\"vip\",\"urgent\"]?)"
        self.round_trip(teststring)

    def test_13_or_not_and(self):
        teststring = "$OR($NOT(?user.active==TRUE?),$AND(?sec.price>150?,?user.login_count>=10?))"
        self.round_trip(teststring)

    def test_14_not_nested_or(self):
        teststring = "$NOT($OR($AND(?sec.region==\"EU\"?,?sec.price<100?),$AND(?user.active==FALSE?,?metrics.score>60?)))"
        self.round_trip(teststring)

    def test_15_or_and_datetime(self):
        teststring = "$OR(?research.last_trade==(*,*,*,10,*,*)?,$AND(?sec.region==\"US\"?,?sec.price>=50?))"
        self.round_trip(teststring)

    def test_16_and_range_not_list(self):
        teststring = "$AND(?metrics.rank:=/1,5/?,$NOT(?user.roles<>\"member\"?))"
        self.round_trip(teststring)

    def test_17_not_bool_or_number(self):
        teststring = "$NOT($OR(?user.verified==FALSE?,?metrics.value>500?))"
        self.round_trip(teststring)

    def test_18_or_timedelta_and_string(self):
        teststring = "$OR(?research.age< {0,0,0,2,0,0}?,?sec.region==\"APAC\"?)"
        self.round_trip(teststring)

    def test_19_and_not_or(self):
        teststring = "$AND($NOT(?user.active==FALSE?),$OR(?sec.price<300?,?metrics.score>=90?))"
        self.round_trip(teststring)

    def test_20_nested_not_and_or(self):
        teststring = "$NOT($AND($OR(?sec.region==\"US\"?,?sec.region==\"CA\"?),$NOT(?user.active==TRUE?)))"
        self.round_trip(teststring)



if __name__ == "__main__":
    unittest.main()
