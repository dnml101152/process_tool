from pydantic import BaseModel
import typing
from datetime import datetime

class PositionModel(BaseModel):
    _id: typing.Optional[str] = None
    position_uid: str
    direction: typing.Optional[str] = None  # e.g., "LONG" or "SHORT"
    description: typing.Optional[str] = None
    remaining_quantity: typing.Optional[float] = None
    isin: typing.Optional[str] = None
    pnl: typing.Optional[float] = None
    max_size: typing.Optional[float] = None
    max_value: typing.Optional[float] = None
    avg_buy: typing.Optional[float] = None
    avg_sell: typing.Optional[float] = None
    margin_percent: typing.Optional[float] = None
    first_trade: typing.Optional[datetime] = None
    last_trade: typing.Optional[datetime] = None
    data_invalid: typing.Optional[bool] = None
    duration: typing.Optional[float] = None
    de_only: typing.Optional[bool] = None
    number_of_trades: typing.Optional[int] = None
    region: typing.Optional[str] = None

class SecurityModel(BaseModel):
    """ Represents a security document in the securities collection. """
    _id: typing.Optional[str] = None
    adr_exch: typing.Optional[str] = None
    description: typing.Optional[str] = None
    ref_ticker: str
    ref_exchange: str
    adr_ticker: typing.Optional[str] = None
    rtrs_ticker: typing.Optional[str] = None
    #ccy: str = typing.Field(min_length=3, max_length=7) # TODO: verlinken wie bei exchange
    lsx: typing.Optional[bool] = None
    naics:  typing.Optional[str] = None
    # TODO: Check the constraints
    #de_subscription: typing.Optional[conlist(str, min_length=2, max_length=2)] = None # TODO: not required
    #ref_subscription: typing.Optional[conlist(str, min_length=2, max_length=2)] = None # TODO: not required
    tdg: typing.Optional[bool] = None
    business_description: typing.Optional[str] = None
    eod_exchange: typing.Optional[str] = None
    de_ticker: typing.Optional[str] = None
    rtrs_exch: typing.Optional[str] = None
    sector: typing.Optional[str] = "unknown"
    is_adr: typing.Optional[bool] = None
    rt_source: typing.Optional[str] = None
    gics_sector: typing.Optional[str] = None
    rtrs_ric: typing.Optional[str] = None
    trbc_sector: typing.Optional[str] = None
    xnps_ticker: typing.Optional[str] = None
    adr_ccy: typing.Optional[str] = None
    region: str
    #con_ids: typing.List[int] = typing.Field(default_factory=list) # TODO: List of ints
    eod_source: typing.Optional[str] = None
    ignore: typing.Optional[bool] = None
    # TODO: Unique
    isin: str # TODO: Exact length and first two chars always letters than wayne
    eod_ticker: typing.Optional[str] = None
    adr_ratio: typing.Optional[float] = None
    INVALID: typing.Optional[bool] = None
    error_logs: typing.Optional[typing.List] = None
