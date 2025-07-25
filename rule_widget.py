import re
import pydantic

from pydantic import BaseModel
import typing
from datetime import datetime, timedelta
test_string = "$OR($AND(?security.region == \"CA\"?, ?research.last_trade == (*,*,*,8,*,*)?),?security.price := /2,4/?, ?research.last_trade>{0,0,0,0,5,0}?)"

test_data = {
    "security": {
        "region": "CA",            # matches == "CA"
        "price": 4                 # matches := [2,4]
    },
    "research": {
        "last_trade": datetime(2025, 7, 11, 2, 15, 30)  # hour=8 → matches (*,*,*,8,*,*)
                                                        # also > {0,0,0,5,0,0}
    }
}



LOGICAL_OPERATORS = {'$NOT', '$AND', '$OR'}
Booloperators = {'TRUE', 'FALSE'}

schema = {
    "security.region": "string",
    "security.price": "float",
    "research.last_trade": "datetime",
    "orders.quantity": "int",
    "user.active": "boolean",
}


def logical_tokenize(input_str):
    tokens = []
    pos = 0
    length = len(input_str)

    while pos < length:
        # Skip whitespace
        if input_str[pos].isspace():
            pos += 1
            continue

        # Logical operators
        for op in LOGICAL_OPERATORS:
            if input_str.startswith(op, pos):
                tokens.append(('OPERATOR', op))
                pos += len(op)
                break
        else:
            if input_str[pos] == '(':
                tokens.append(('LPAREN', '('))
                pos += 1
                continue
            if input_str[pos] == ')':
                tokens.append(('RPAREN', ')'))
                pos += 1
                continue
            if input_str[pos] == ',':
                tokens.append(('COMMA', ','))
                pos += 1
                continue

            # Condition delimited by '?'
            if input_str[pos] == '?':
                end_pos = input_str.find('?', pos + 1)
                if end_pos == -1:
                    raise SyntaxError("Unterminated condition (missing closing '?')")
                cond = input_str[pos+1:end_pos].strip()
                tokens.append(('CONDITION', cond))
                pos = end_pos + 1
                continue

            raise SyntaxError(f"Unexpected character {input_str[pos]} at position {pos}")

    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def advance(self):
        self.pos += 1

    def expect(self, expected_type):
        token_type, token_value = self.peek()
        if token_type != expected_type:
            raise SyntaxError(f"Expected token {expected_type} but got {token_type}")
        self.advance()
        return token_value

    def parse_expression(self):
        token_type, token_value = self.peek()

        if token_type == 'OPERATOR':
            return self.parse_operator_expression()
        elif token_type == 'CONDITION':
            self.advance()
            return {"type": "condition", "value": token_value}
        else:
            raise SyntaxError(f"Unexpected token {token_type} at position {self.pos}")

    def parse_operator_expression(self):
        op = self.expect('OPERATOR')
        self.expect('LPAREN')

        args = []
        while True:
            args.append(self.parse_expression())
            token_type, _ = self.peek()
            if token_type == 'COMMA':
                self.advance()
            else:
                break

        self.expect('RPAREN')

        if op == '$NOT' and len(args) != 1:
            raise SyntaxError(f"$NOT operator expects exactly one argument, got {len(args)}")

        return {
            "type": "operator",
            "operator": op,
            "args": args
        }


def tokenize_condition(cond: str):
    """
    Turn a condition like
        'security.region == "CA"'
    or
        'research.last_trade >= (*,*,*,8,*,*)'
    into a list of (TOKEN_TYPE, TEXT) pairs.
    """
    tokens = []
    i = 0
    n = len(cond)

    while i < n:

        # 0. Handle whitespace as before
        if cond[i].isspace():
            i += 1
            continue

        # -------------------------------------------------
        # 1. Timedelta: {1,2,3,4,5,6}
        # -------------------------------------------------
        if cond[i] == '{':
            j = i + 1
            parts = []
            max_iter = 1000
            count = 0
            while j < n and cond[j] != '}':
                count += 1
                if count > max_iter:
                    raise SyntaxError("Too many iterations while parsing timedelta, possible malformed input")

                start = j
                while j < n and (cond[j].isdigit() or cond[j] == '-'):
                    j += 1
                if j == start:
                    raise SyntaxError("Expected number inside timedelta")
                parts.append(cond[start:j])
                if j < n and cond[j] == ',':
                    j += 1
            if len(parts) != 6 or j >= n or cond[j] != '}':
                raise SyntaxError("Invalid timedelta format, expected 6 comma-separated integers in {}")
            tokens.append(("TIMEDELTA", parts))
            i = j + 1
            continue

        # -------------------------------------------------
        # 2. Datetime: (YYYY,M,D,H,M,S) or with *
        # -------------------------------------------------
        if cond[i] == '(':
            j = i + 1
            parts = []
            max_iter = 1000
            count = 0
            while j < n and cond[j] != ')':
                count += 1
                if count > max_iter:
                    raise SyntaxError("Too many iterations while parsing datetime, possible malformed input")

                # allow numbers or '*'
                if cond[j] == '*':
                    parts.append('*')
                    j += 1
                else:
                    start = j
                    while j < n and (cond[j].isdigit() or cond[j] == '-'):
                        j += 1
                    if j == start:
                        raise SyntaxError("Expected number or '*' inside datetime")
                    parts.append(cond[start:j])
                if j < n and cond[j] == ',':
                    j += 1
            if len(parts) != 6 or j >= n or cond[j] != ')':
                raise SyntaxError("Invalid datetime format, expected 6 items in ()")
            tokens.append(("DATETIME", parts))
            i = j + 1
            continue

        # -------------------------------------------------
        # 3. Range: /-2,6/
        # -------------------------------------------------
        if cond[i] == '/':
            j = i + 1
            max_iter = 1000
            count = 0

            start = j
            while j < n and (cond[j].isdigit() or cond[j] == '-'):
                j += 1
                count += 1
                if count > max_iter:
                    raise SyntaxError("Too many iterations while parsing range low bound")
            low = cond[start:j]

            if j >= n or cond[j] != ',':
                raise SyntaxError("Expected comma in range")
            j += 1

            start = j
            count = 0
            while j < n and (cond[j].isdigit() or cond[j] == '-'):
                j += 1
                count += 1
                if count > max_iter:
                    raise SyntaxError("Too many iterations while parsing range high bound")
            high = cond[start:j]

            if j >= n or cond[j] != '/':
                raise SyntaxError("Expected closing '/' in range")
            tokens.append(("RANGE", (low, high)))
            i = j + 1
            continue

        # -------------------------------------------------
        # 4. List: [1,2,3] or ["A","B"]
        # -------------------------------------------------
        if cond[i] == '[':
            j = i + 1
            parts = []
            max_iter = 10000  # more items possible
            count = 0

            in_string = cond[j] == '"'

            while j < n and cond[j] != ']':
                count += 1
                if count > max_iter:
                    raise SyntaxError("Too many iterations while parsing list, possible malformed input")

                if in_string:
                    if cond[j] != '"':
                        raise SyntaxError("Expected string literal")
                    start = j + 1
                    j = start
                    while j < n and cond[j] != '"':
                        if cond[j] == '\\' and j + 1 < n:
                            j += 2
                        else:
                            j += 1
                    if j >= n:
                        raise SyntaxError("Unterminated string in list")
                    parts.append(cond[start:j])
                    j += 1  # skip closing quote
                else:
                    start = j
                    while j < n and (cond[j].isdigit() or cond[j] == '-'):
                        j += 1
                    if j == start:
                        raise SyntaxError("Expected number in list")
                    parts.append(cond[start:j])

                if j < n and cond[j] == ',':
                    j += 1

            if j >= n or cond[j] != ']':
                raise SyntaxError("Unclosed list")
            token_type = "STRING_LIST" if in_string else "NUMBER_LIST"
            tokens.append((token_type, parts))
            i = j + 1
            continue

        # Check for TRUE/FALSE (case-insensitive)
        if cond[i:i+4].upper() == "TRUE":
            tokens.append(("BOOL", True))
            i += 4
            continue
        elif cond[i:i+5].upper() == "FALSE":
            tokens.append(("BOOL", False))
            i += 5
            continue

        # -------------------------------------------------
        # 1. database.field    (exactly one dot)
        # -------------------------------------------------
        # read first identifier
        if cond[i].isalpha() or cond[i] == '_':

            j = i + 1
            while j < n and (cond[j].isalnum() or cond[j] == '_'):
                j += 1
            # must have a dot next
            if j < n and cond[j] == '.':
                k = j + 1
                if k >= n or not (cond[k].isalpha() or cond[k] == '_'):
                    raise SyntaxError("Invalid field name after dot")
                while k < n and (cond[k].isalnum() or cond[k] == '_'):
                    k += 1
                tokens.append(("FIELD", cond[i:k]))
                i = k
                continue
            else:
                raise SyntaxError("Expected '.' in database.field")

        # -------------------------------------------------
        # 2. Comparison / assignment operators
        #    Order matters: check the 2‑char forms first
        # -------------------------------------------------
        if cond.startswith('<=', i) or cond.startswith('>=', i) \
                or cond.startswith('==', i) or cond.startswith('<>', i):
            tokens.append(("OP", cond[i:i + 2]))
            i += 2
            continue
        if cond[i] in '<>':
            tokens.append(("OP", cond[i]))
            i += 1
            continue
        if cond.startswith(':=', i):
            tokens.append(("OP", ':='))
            i += 2
            continue

        # -------------------------------------------------
        # 3. Literal asterisk *
        # -------------------------------------------------
        if cond[i] == '*':
            tokens.append(("STAR", '*'))
            i += 1
            continue

        # -------------------------------------------------
        # 4. Comma or parentheses
        # -------------------------------------------------
        if cond[i] == ',':
            tokens.append(("COMMA", ','))
            i += 1
            continue
        if cond[i] == '(':
            tokens.append(("LPAREN", '('))
            i += 1
            continue
        if cond[i] == ')':
            tokens.append(("RPAREN", ')'))
            i += 1
            continue




        # -------------------------------------------------
        # 5. String literal  "...."
        # -------------------------------------------------
        if cond[i] == '"':
            j = i + 1
            while j < n and cond[j] != '"':
                # simple escape handling for \" inside string
                if cond[j] == '\\' and j + 1 < n:
                    j += 2
                else:
                    j += 1
            if j >= n:
                raise SyntaxError("Unterminated string literal")
            tokens.append(("STRING", cond[i + 1:j]))  # drop the quotes
            i = j + 1
            continue

        # -------------------------------------------------
        # 6. Number (supporting optional '-' and decimals)
        # -----------------------------------------------
        if cond[i].isdigit() or (
                cond[i] == '-' and i + 1 < n and (cond[i + 1].isdigit() or cond[i + 1] == '.')
        ) or (
                cond[i] == '.' and i + 1 < n and cond[i + 1].isdigit()
        ):
            j = i
            has_dot = False

            if cond[j] == '-':
                j += 1  # Skip minus

            while j < n and (cond[j].isdigit() or (cond[j] == '.' and not has_dot)):
                if cond[j] == '.':
                    has_dot = True
                j += 1

            tokens.append(("NUMBER", cond[i:j]))
            i = j
            continue



        # -------------------------------------------------
        # 8. Anything else is an error
        # -------------------------------------------------
        raise SyntaxError(f"Unexpected character '{cond[i]}' at position {i}")

    return tokens

class ConditionParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return (None, None)

    def advance(self):
        self.pos += 1

    def expect(self, expected_type):
        token_type, token_value = self.peek()
        if token_type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, but got {token_type}")
        self.advance()
        return token_value

    def parse(self):
        # OLD: just parsed FIELD, OP, VALUE
        db_field = self.expect("FIELD")  # e.g., "security.region"
        db, field = db_field.split('.', 1)
        op = self.expect("OP")
        token_type, token_value = self.peek()

        # Here we add support for the extended value types
        if token_type in ("STRING"):
            self.advance()
            value = {"type": "string", "content": token_value}
        elif token_type in ("NUMBER"):
            self.advance()
            value = {"type": "number", "content": float(token_value)}
        elif token_type == "TIMEDELTA":
            self.advance()
            value = {"type": "timedelta", "content": token_value}
        elif token_type == "DATETIME":
            self.advance()
            value = {"type": "datetime", "content": token_value}
        elif token_type == "BOOL":
            self.advance()
            value = {"type": "bool", "content": token_value}
        elif token_type == "RANGE":
            self.advance()
            value = {"type": "range", "low": token_value[0], "high": token_value[1]}
        elif token_type == "STRING_LIST":
            self.advance()
            value = {"type": "list", "value_type": "string", "content": token_value}
        elif token_type == "NUMBER_LIST":
            self.advance()
            value = {"type": "list", "value_type": "number", "content": token_value}
        elif token_type == "STAR":
            self.advance()
            value = "*"
        else:
            raise SyntaxError(f"Unexpected value type {token_type}")

        return {
            "type": "condition",
            "db": db,
            "field": field,
            "op": op,
            "value": value
        }


def integrate_condition_tokenizer(tree, condition_tokenizer):
    if tree['type'] == 'condition':
        cond_str = tree['value']
        tokens = condition_tokenizer(cond_str)
        dict_updater = ConditionParser(tokens)
        parsed_condition = dict_updater.parse()
        # Update the current tree node with the parsed condition
        tree.clear()
        tree.update(parsed_condition)
    elif tree['type'] == 'operator':
        for arg in tree['args']:
            integrate_condition_tokenizer(arg, condition_tokenizer)
    else:
        raise ValueError(f"Unknown node type {tree['type']}")


def validate_condition_node(node, schema):
    print(999,node)

    db = node['db']
    field = node['field']
    op = node["op"]

    full_field = f"{db}.{field}"

    if full_field not in schema:
        raise ValueError(f"Unknown field: {full_field}")

    scheme_type = schema[full_field]
    value = node['value']
    type = value.get("type")
    content = value.get("content")
    print(888, value)

    if scheme_type == "string":
        #if string then the potential scenarios are possible
        if value.get("type") == "string" and isinstance(value.get("content"),str) and op=="==":
            return None
        elif value.get("type") == "string" and isinstance(value.get("content"),str) and op=="<>":
            return None
        elif value.get("type") == "list" and isinstance(value.get("content"),list) and op==":=" and all([isinstance(item,str) for item in value.get("content")]):
            return None
        else:
            raise ValueError(f"String validation failed at: {full_field}")

    if scheme_type in ["float","int"]:
        if type == "number" and isinstance(content,(float,int)):
            if op in ["<","<=","==",">",">="]:
                return None
        elif type == "list" and isinstance(content,(list)) and op==":=" and all([isinstance(item,(int,float)) for item in value.get("content")]):
            return None
        elif type == "range" and isinstance(value.get("low"),(float,int)) and isinstance(value.get("high"),(float,int)) and op==":=":
            return None
        else:
            raise ValueError(f"Number validation failed at: {full_field}")
    print(value)

    if scheme_type == "datetime":
        if type == "timedelta" and op in ["<","<=","==",">",">="] and all([is_number_or_string(number) for number in content]):
            return None
        if type == "datetime" and op in ["<","<=","==",">",">="] and all([is_number_or_string(number,additional_strings=["*"]) for number in content]):
            return None
        else:
            raise ValueError(f"Datetime validation failed at: {full_field}")


def is_number_or_string(val, additional_strings=None):
    if additional_strings is None:
        additional_strings = []
    if isinstance(val, (int, float)):
        return True
    if isinstance(val, str):
        return val in additional_strings
    return False

def validate_condition_node(node, schema):
    print(node)
    db = node['db']
    field = node['field']
    op = node["op"]
    full_field = f"{db}.{field}"

    if full_field not in schema:
        raise ValueError(f"Unknown field: {full_field}")

    schema_type = schema[full_field]
    value = node['value']
    val_type = value.get("type")
    content = value.get("content")  # fallback for old structure

    # --- String Validation ---
    if schema_type == "string":
        if val_type == "string" and isinstance(content, str) and op in ["==", "<>"]:
            return
        elif val_type == "list" and isinstance(content, list) and op == ":=" and all(isinstance(item, str) for item in content):
            return
        else:
            raise ValueError(f"String validation failed at: {full_field} with op {op} and value {value}")

    # --- Number Validation ---
    elif schema_type in ["int", "float"]:
        print(555,schema_type,val_type,content)
        if val_type == "number" and isinstance(content, (int, float)) and op in ["<", "<=", "==", ">", ">="]:
            return
        elif val_type == "list" and isinstance(content, list) and op == ":=" and all(isinstance(item, (int, float)) for item in content):
            return
        elif val_type == "range" and is_number_or_string(value.get("low")) and is_number_or_string(value.get("high")) and op == ":=":
            return
        else:
            raise ValueError(f"Number validation failed at: {full_field} with op {op} and value {value}")

    # --- Datetime Validation ---
    elif schema_type == "datetime":
        if val_type == "timedelta" and op in ["<", "<=", "==", ">", ">="] and all(is_number_or_string(x) for x in content):
            return
        if val_type == "datetime" and op in ["<", "<=", "==", ">", ">="] and all(is_number_or_string(x, ["*"]) for x in content):
            return
        else:
            raise ValueError(f"Datetime validation failed at: {full_field} with op {op} and value {value}")

    elif schema_type == "bool":
        if val_type == "bool" and op == "==":
            return
        else:
            raise ValueError(f"Boolean validation failed at: {full_field} with op {op} and value {value}")

    raise ValueError(f"Unhandled schema type: {schema_type}")

def is_number_or_string(s,additional_strings:list = None):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        if additional_strings:
            if s in additional_strings:
                return True
            else:
                return False
        return False

def validate_tree(tree, schema):
    if tree['type'] == 'condition':
        validate_condition_node(tree, schema)
    elif tree['type'] == 'operator':
        for arg in tree['args']:
            validate_tree(arg, schema)

def evaluate_tree_conditions(tree,data):
    if tree['type'] == 'condition':
        tree["eval_result"] = condition_evaluator(tree, data)
    elif tree['type'] == 'operator':
        for arg in tree['args']:
            evaluate_tree_conditions(arg, data)


def process_input_string(input_string:str ,valid_fields:dict):
    logical_tokens = logical_tokenize(input_string)
    parser = Parser(logical_tokens)
    ast = parser.parse_expression()
    integrate_condition_tokenizer(ast,tokenize_condition)
    validate_tree(ast,valid_fields)
    return ast




def condition_evaluator(condition,data):
    value = condition.get("value")
    reference = data.get(condition["db"]).get(condition["field"])
    op = condition.get("op")
    value_type = value.get("type")
    if value_type == "string":
        if op == "==":
            if reference == value.get("content"):
                return True
            else:
                return False

        elif op == "<>":
            if value.get("content") in reference:
                return True
            else:
                return False

        elif op == ":=":
            if  reference in value.get("content"):
                return True
            else:
                return False

        else:
            raise ValueError(f"String evaluation failed at: {condition}")

    elif value_type == "number":
        if op == "==":
            if reference == value.get("content"):
                return True
            else:
                return False
        elif op == ">=":
            if reference >= value.get("content"):
                return True
            else:
                return False
        elif op == ">":
            if reference > value.get("content"):
                return True
            else:
                return False
        elif op == "<":
            if reference < value.get("content"):
                return True
            else:
                return False

        elif op == "<=":
            if reference <= value.get("content"):
                return True
            else:
                return False
        else:
            raise ValueError(f"Number evaluation failed at: {condition}")

    elif value_type == "range":
        if op == ":=":

            if reference >= float(value.get("low")) and reference<=float(value.get("high")):
                return True
            else:
                return False
        else:
            raise ValueError(f"Range evaluation failed at: {condition}")

    elif value_type == "list":
        if op == ":=":
            if reference in value.get("content"):
                return True
            else:
                return False
        elif op == "<>":
            if all(elem in reference for elem in value.get("content")):
                return True
            else:
                return False
        else:
            raise ValueError(f"List evaluation failed at: {condition}")

    elif value_type == "datetime":
        reference = [reference.year, reference.month, reference.day, reference.hour, reference.minute, reference.second]

        comp_result = []

        if op == "==":
            for jj, time_number in enumerate(value.get("content")):
                if time_number =="*":
                    pass
                else:
                    if int(time_number) == reference[jj]:
                        comp_result.append(True)
                    else:
                        comp_result.append(False)

            if all(comp_result):
                return True
            else:
                return False

        elif op == "<":
            for jj, time_number in enumerate(value.get("content")):
                if time_number =="*":
                    if jj == len(value.get("content")) - 1:
                        return False
                    else:
                        pass
                elif int(time_number) == reference[jj]:
                    if jj == len(value.get("content")) - 1:
                        return False
                    else:
                        pass
                elif int(time_number) < reference[jj]:
                    return False
                elif int(time_number) > reference[jj]:
                    return True

        elif op == ">":

            for jj, condition_boundary in enumerate(value.get("content")):
                if condition_boundary =="*":
                    if jj == len(value.get("content")) - 1:
                        return False
                    else:
                        pass
                elif int(condition_boundary) == reference[jj]:
                    if jj == len(value.get("content")) - 1:
                        return False
                    else:
                        pass
                    print("tz")
                elif int(condition_boundary) < reference[jj]:
                    return True
                elif int(condition_boundary) > reference[jj]:
                    return False

        elif op == ">=":
            for jj, time_number in enumerate(value.get("content")):
                if time_number =="*":
                    if jj == len(value.get("content")) - 1:
                        return True
                    else:
                        pass
                elif int(time_number) == reference[jj]:
                    if jj == len(value.get("content")) - 1:
                        return True
                    else:
                        pass
                elif int(time_number) < reference[jj]:
                    return True
                elif int(time_number) > reference[jj]:
                    return False

        elif op == "<=":
            for jj, time_number in enumerate(value.get("content")):
                if time_number =="*":
                    if jj == len(value.get("content")) - 1:
                        return True
                    else:
                        pass
                elif int(time_number) == reference[jj]:
                    if jj == len(value.get("content")) - 1:
                        return True
                    else:
                        pass
                elif int(time_number) > reference[jj]:
                    return True
                elif int(time_number) < reference[jj]:
                    return False





    elif value_type == "timedelta":
        age = datetime.now() - reference
        timedelta_list = [float(number) for number in value.get("content")]
        number_of_days = 365*timedelta_list[0] + 30 * timedelta_list[1] + timedelta_list[2]
        td = timedelta(days = number_of_days, hours = timedelta_list[3], minutes = timedelta_list[4], seconds = timedelta_list[5])
        if op == "==":
            if age == td:
                return True
            else:
                return False
        elif op == ">=":
            if age >= td:
                return True
            else:
                return False
        elif op == ">":
            if age > td:
                return True
            else:
                return False
        elif op == "<":
            if age < td:
                return True
            else:
                return False

        elif op == "<=":
            if age <= td:
                return True
            else:
                return False
        else:
            raise ValueError(f"Number evaluation failed at: {condition}")




    elif value_type == "bool":
        return value.get("content") == reference



#def logical_evaluator(input_ast):


def evaluate_expression(node):
    if node["type"] == "condition":
        return node["eval_result"]

    elif node["type"] == "operator":
        op = node["operator"]
        args = node["args"]

        if op == "$AND":
            return all(evaluate_expression(arg) for arg in args)

        elif op == "$OR":
            return any(evaluate_expression(arg) for arg in args)

        elif op == "$NOT":
            if len(args) != 1:
                raise ValueError(f"$NOT expects exactly one argument, got {len(args)}")
            return not evaluate_expression(args[0])

        else:
            raise ValueError(f"Unknown operator: {op}")

def reconstruct_expression(node):
    if node["type"] == "operator":
        op = node["operator"]
        args = [reconstruct_expression(arg) for arg in node["args"]]
        return f"{op}({','.join(args)})"

    elif node["type"] == "condition":
        db = node["db"]
        field = node["field"]
        op = node["op"]
        val = node["value"]
        val_str = serialize_value(val)
        return f"?{db}.{field} {op} {val_str}?"

    else:
        raise ValueError(f"Unknown node type: {node['type']}")


def list_to_str(content):
    def quote_if_str(x):
        if isinstance(x, str):
            return f'"{x}"'
        else:
            return str(x)
    return "[" + ",".join(quote_if_str(x) for x in content) + "]"

def serialize_value(val):
    vtype = val["type"]
    content = val["content"] if "content" in val else None

    if vtype == "string":
        return f"\"{content}\""
    elif vtype == "number":
        return str(content)
    elif vtype == "range":
        return f"/{val['low']},{val['high']}/"
    elif vtype == "list":
        return list_to_str(content)
    elif vtype == "datetime":
        return "(" + ",".join(str(c) for c in content) + ")"
    elif vtype == "timedelta":
        return "{" + ",".join(str(c) for c in content) + "}"
    elif vtype == "bool":
        return str(content)
    else:
        raise ValueError(f"Unknown value type: {vtype}")

def resolve_type(ann) -> str:
    origin =typing.get_origin(ann)
    args = typing.get_args(ann)

    # Handle Optional or Union[..., None]
    if origin is typing.Union:
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) == 1:
            return resolve_type(non_none[0])
        else:
            return "union"

    # Handle Literal
    if origin is typing.Literal:
        if all(isinstance(arg, str) for arg in args):
            return "string"
        elif all(isinstance(arg, int) for arg in args):
            return "number"
        elif all(isinstance(arg, float) for arg in args):
            return "float"
        elif all(isinstance(arg, bool) for arg in args):
            return "bool"
        else:
            return "mixed"

    # Handle List[...] types
    if origin in (list, typing.List):
        inner = args[0]
        return f"list[{resolve_type(inner)}]"

    # Handle primitive types
    if ann is str:
        return "string"
    elif ann is int:
        return "int"
    elif ann is float:
        return "float"
    elif ann is bool:
        return "bool"
    elif ann in (datetime, getattr(__import__('datetime'), 'datetime', object())):
        return "datetime"
    elif ann is timedelta:
        return "timedelta"

    # Fallback
    return str(ann)
def create_valid_fields_dict(model: BaseModel,name: str = None) -> dict:
    """
    creates a dict with valid fields and type requirements
    :param model:
    :return:
    """
    model_name = name if name else model.__name__
    output = {}
    fields = list(model.model_fields.keys())
    for field in fields:
        try:
            info = model.model_fields[field]
            print(info)
            output_type = resolve_type(info.annotation)
            output[f"{model_name}.{field}"] = output_type
        except Exception as err:
            print(f"Error creating valid field for {field} {info} because of {err}")
            pass
    return output

# Formatted HTML tooltip
tooltip_html = """
<b>How to add data:</b><br>
Every line is a condition and all lines are connected with logical operator <code>AND</code><br><br>

<code>?cond_A?</code><br>
<code>?cond_B?</code><br>
equals<br>
<code>$AND(?cond_A?, ?cond_B?)</code><br><br>

<b>Logical operators to use:</b><br>
<ul>
  <li><code>$NOT(?cond?)</code></li>
  <li><code>$AND(?cond_1?, ?cond_2?)</code></li>
  <li><code>$OR($NOT(?cond_1?), ?cond_2?)</code></li>
</ul>

<b>How to construct conditions:</b><br>
<ul>
  <li>Start and end conditions with <code>?</code>: <code>?sec.region == "CA"?</code></li>
  <li>First arg is <code>db.field</code>: <code>?sec.region := ["CA","US"]?</code></li>
  <li>Second is operator: <code>?sec.tdg_listing &lt; {0,0,30,0,0,0}?</code></li>
  <li>Third is value: <code>?trade.price := /7,11/?</code></li>
</ul>

<b>Operators are:</b><br>
<ul>
  <li><code>==</code> (equals)</li>
  <li><code>&gt;, &gt;=, &lt;=, &lt;</code> (greater, lesser)</li>
  <li><code>:=</code> (in)</li>
  <li><code>&lt;&gt;</code> (contains)</li>
</ul>

<b>Value types:</b><br>
<ul>
  <li><b>Number</b>: <code>?sec.price &gt; 2?</code></li>
  <li><b>String</b>: <code>?sec.region == "CA"?</code> (wrap in <code>"..."</code>)</li>
  <li><b>List</b>: <code>?sec.region in ["CA","US"]?</code> (no mixed types)</li>
  <li><b>Bool</b>: <code>?sec.tdg_listing == TRUE?</code> (use <code>TRUE</code> or <code>FALSE</code>, case-sensitive)</li>
  <li><b>Range</b>: <code>?trade.price := /7,11/?</code></li>
  <li><b>Age</b>: <code>?sec.tdg_listing &lt; {1,2,3,4,5,6}?</code> (years, months, days, hours, mins, secs)</li>
  <li><b>Datetime</b>: <code>?pos_first_trade &lt; (2025,12,30,1,2,3)?</code><br>
      Use wildcards: <code>?pos.first_trade &lt; (*,*,*,9,0,0)?</code> (before 09:00:00 any day)</li>
</ul>
"""

if __name__ == "__main__":

    data = process_input_string(test_string ,schema)
    evaluate_tree_conditions(data,test_data)
    print(data)
    data = evaluate_expression(data)
    print(data)