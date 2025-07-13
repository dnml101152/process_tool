from pydantic import BaseModel
import typing
from datetime import datetime as dt, timedelta

class TradeModel(BaseModel):
    """ Represents a trade document in the securities collection. """
    _id: typing.Optional[str] = None
    acc_ccy: typing.Optional[str] = None # TODO: Might be removed
    acc_price: typing.Optional[float] = None # TODO: Might be removed
    broker: typing.Literal["IB", "SI"]
    comment: typing.Optional[str] = None
    datetime: typing.Optional[dt] = None
    description: typing.Optional[str] = None
    exchange: str
    fee: float
    fee_CCY: typing.Optional[str] = None # TODO: Might be removed
    fee_ccy: str
    fee_adj_price_rt: typing.Optional[float] = None
    fifo_price_buy: typing.Optional[float] = None
    isin: typing.Optional[str] = None
    par_ccy: typing.Optional[str] = None
    par_factor: typing.Optional[float] = None
    par_factor_rt: typing.Optional[float] = None
    par_fee: typing.Optional[float] = None
    par_fee_ccy: typing.Optional[str] = None
    par_fee_rt: typing.Optional[float] = None
    par_price: typing.Optional[float] = None
    par_price_rt: typing.Optional[float] = None
    pos_index: typing.Optional[int] = None # TODO: Might be removed
    price: float
    proceeds: typing.Optional[float] = None
    proceeds_ccy: typing.Optional[str] = None
    proceeds_delta: typing.Optional[float] = None
    proceedsmultiplier: typing.Optional[float] = None # TODO: Rename with "_"
    quantity: float
    sectype: str
    tax: float
    tax_ccy: typing.Optional[str] = None # TODO
    trade_CCY: typing.Optional[str] = None # TODO: Might be removed
    trade_ccy: str
    tradeid: str
    trader: typing.Optional[str] = None
    busted: typing.Optional[bool] = None
    busted_comment: typing.Optional[str] = None
    INVALID: typing.Optional[bool] = None
    error_logs: typing.Optional[typing.List] = None

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
    elif ann is dt:
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


trade_valid_fields  = create_valid_fields_dict