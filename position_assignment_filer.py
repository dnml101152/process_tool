import json
from rule_widget import evaluate_expression, evaluate_tree_conditions, condition_evaluator
from pymongo import MongoClient
with open(r"C:\Users\dnml1\Downloads\securities.json", "r", encoding="utf-8") as f:
    securities_data = json.load(f)

z = MongoClient()
y = z["trading_data"]
x = y["positions"]




def find_by_field(data,key,value):
    for item in data:
        if item.get(key) == value:
            return item
    return None

with open(r"test.json", "r", encoding="utf-8") as f:
    assigners = json.load(f)

positions = list(x.find())


def mapping_evaluator(mapping_assignments, data):
    for key,mapping in mapping_assignments.items():
        print(44,mapping)
        bools = []
        for rule in mapping.get("rule_dicts",[]):
            input = rule
            temp_data = data
            evaluate_tree_conditions(input,temp_data)
            bool = evaluate_expression(input)
            bools.append(bool)
        if all(bools):
            return key

    return None


for position in positions:
    sec_data = find_by_field(securities_data,"isin",position.get("isin"))
    processing_data = {"sec":sec_data,"pos":position}
    try:
        print(55555,mapping_evaluator(assigners,processing_data))
    except:
        print(696969,processing_data)