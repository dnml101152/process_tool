from rule_widget import process_input_string, evaluate_tree_conditions,evaluate_expression
from trades import trade_valid_fields
import json
from pymongo import MongoClient

teststring = ("$AND(?trade.broker==\"SI\"?,?trade.datetime > (*,*,*,8,50,0)?,?trade.datetime < (*,*,*,9,0,0)?,?trade.isin<>\"DE\"?)")
ast = process_input_string(teststring,valid_fields=trade_valid_fields)
file = r"C:\Users\dnml1\Downloads\trading_data.trades.json"

db = MongoClient()
z = db["trading_data"]
trades = z["trades"]
all_trades = list(trades.find())
for trade in all_trades:
    eval_data = {"trade":trade}
    data = ast
    evaluate_tree_conditions(data, eval_data)
    data = evaluate_expression(data)
    if data:
        print(22,trade)

print(888,teststring)


"""
how to add data:
every line is a condition and all lines are connected with logical operator AND

?cond_A?
?cond_B?
equals 
$AND(?cond_A?,?cond_B?)


logical operators to use:
- $NOT(?cond?)
- $AND(?cond_1?,?cond_2?)
- $OR($NOT(?cond_1?),?cond_2?)


How to construct conditions:
- start and end conditions with ? --> ?sec.region == "CA"?
- first arg is db.field -> ?sec.region := ["CA","US"]?
- second is operator ?sec.tdg_listing < {0,0,30,0,0,0}?
- third is value ?trade.price := /7,11/?

operators are
- == (equals)
- >, >=, <=, < (greater, lesser)
:= (in)
<> (contains)

value_types are:
- number --> ?sec.price >2?
- string --> ?sec.region == "CA"? (Make sure to wrap string in "" --> "string" not string)
- list --> ?sec.region in ["CA","US"]? (No mixed lists allowed, either string or number lists)
- bool -->  ?sec.tdg_listing == TRUE? (Either TRUE or FALSE, case-sensitive so not enter True or true or TRUe)
- range --> ?trade.price := /7,11/? (7 and 11 are both valid)
- age --> ?sec.tdg_listing < {1,2,3,4,5,6}? (age has to be greater than 1year, 2 months, 3days, 4hours, 5 minutes and six seconds)
- datetime --> ?pos_first_trade < (2025,12,30,1,2,3)? (all positions with first trade before 30/12/25 01:02:03)
           --> datetimes can be used with wildcards ?pos.first_trade < (*,*,*,9,0,0)? so every trade before 09:00:00 on any given day
"""


