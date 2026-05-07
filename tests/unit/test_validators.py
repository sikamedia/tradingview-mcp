from tradingview_mcp.core.services.coinlist import load_symbols
from tradingview_mcp.core.utils.validators import (
    EXCHANGE_SCREENER,
    get_tv_exchange_prefix,
    is_stock_exchange,
    sanitize_exchange,
    sanitize_timeframe,
)


def test_sanitize_timeframe_accepts_lowercase_day_week_month():
    assert sanitize_timeframe("1d") == "1D"
    assert sanitize_timeframe("1w") == "1W"
    assert sanitize_timeframe("1m") == "1M"


def test_sanitize_timeframe_accepts_uppercase_with_whitespace():
    assert sanitize_timeframe(" 1D ") == "1D"
    assert sanitize_timeframe(" 1W ") == "1W"
    assert sanitize_timeframe(" 1M ") == "1M"


def test_sanitize_timeframe_preserves_intraday_timeframes():
    assert sanitize_timeframe("5m") == "5m"
    assert sanitize_timeframe("15m") == "15m"
    assert sanitize_timeframe("1h") == "1h"
    assert sanitize_timeframe("4h") == "4h"


def test_sanitize_timeframe_falls_back_to_default():
    assert sanitize_timeframe("invalid", "15m") == "15m"


def test_omxsto_is_valid_sweden_stock_exchange():
    assert sanitize_exchange("OMXSTO", "KUCOIN") == "omxsto"
    assert EXCHANGE_SCREENER["omxsto"] == "sweden"
    assert is_stock_exchange("OMXSTO") is True


def test_omxsto_uses_tradingview_prefix_for_apotea():
    exchange = sanitize_exchange("OMXSTO", "KUCOIN")
    full_symbol = f"{get_tv_exchange_prefix(exchange)}:APOTEA"

    assert full_symbol == "OMXSTO:APOTEA"


def test_omxsto_coinlist_includes_apotea():
    assert "OMXSTO:APOTEA" in load_symbols("omxsto")
