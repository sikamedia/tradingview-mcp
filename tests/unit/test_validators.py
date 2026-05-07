from types import SimpleNamespace

from tradingview_mcp.core.services import scanner_service, screener_service
from tradingview_mcp.core.services.assetlist import load_symbols
from tradingview_mcp.core.utils.validators import (
    EXCHANGE_SCREENER,
    build_tv_symbol,
    get_asset_type,
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
    assert get_asset_type("OMXSTO") == "stock"


def test_omxsto_uses_tradingview_prefix_for_apotea():
    exchange = sanitize_exchange("OMXSTO", "KUCOIN")
    full_symbol = build_tv_symbol("APOTEA", exchange)

    assert full_symbol == "OMXSTO:APOTEA"


def test_omxsto_assetlist_includes_apotea():
    assert "OMXSTO:APOTEA" in load_symbols("omxsto")


def test_crypto_symbol_can_append_usdt_when_requested():
    assert build_tv_symbol("BTC", "kucoin", append_usdt_for_crypto=True) == "KUCOIN:BTCUSDT"


def test_prequalified_symbol_is_preserved():
    assert build_tv_symbol("OMXSTO:APOTEA", "omxsto") == "OMXSTO:APOTEA"


def test_volume_confirmation_treats_apotea_as_stock(monkeypatch):
    captured = {}

    def fake_get_multiple_analysis(*, screener, interval, symbols):
        captured["screener"] = screener
        captured["symbols"] = symbols
        return {
            "OMXSTO:APOTEA": SimpleNamespace(
                indicators={
                    "volume": 100000,
                    "volume.SMA20": 50000,
                    "open": 80,
                    "close": 84,
                    "high": 85,
                    "low": 79,
                    "RSI": 55,
                    "BB.upper": 90,
                    "BB.lower": 70,
                }
            )
        }

    monkeypatch.setattr(scanner_service, "get_multiple_analysis", fake_get_multiple_analysis)

    result = scanner_service.volume_confirmation_analyze("APOTEA", "omxsto", "1D")

    assert captured["screener"] == "sweden"
    assert captured["symbols"] == ["OMXSTO:APOTEA"]
    assert result["symbol"] == "OMXSTO:APOTEA"
    assert result["asset_type"] == "stock"


def test_analyze_asset_returns_stock_asset_type(monkeypatch):
    full_symbol = "OMXSTO:APOTEA"

    monkeypatch.setattr(screener_service, "_TA_AVAILABLE", True)
    monkeypatch.setattr(
        screener_service,
        "get_multiple_analysis",
        lambda *, screener, interval, symbols: {
            full_symbol: SimpleNamespace(
                indicators={
                    "volume": 100000,
                    "open": 80,
                    "close": 84,
                    "high": 85,
                    "low": 79,
                }
            )
        },
    )
    monkeypatch.setattr(
        screener_service,
        "compute_metrics",
        lambda indicators: {
            "price": 84,
            "change": 5.0,
            "rating": 2,
            "signal": "BUY",
            "bbw": 0.03,
        },
    )

    from tradingview_mcp.core.services import indicators

    monkeypatch.setattr(
        indicators,
        "extract_extended_indicators",
        lambda raw: {
            "rsi": {},
            "macd": {},
            "sma": {},
            "ema": {},
            "bollinger_bands": {},
            "atr": {},
            "volume": {},
            "obv": {},
            "support_resistance": {},
            "stochastic": {},
            "adx": {},
            "market_structure": {},
        },
    )
    monkeypatch.setattr(indicators, "analyze_timeframe_context", lambda raw, timeframe: {})
    monkeypatch.setattr(
        indicators,
        "compute_stock_score",
        lambda raw: {"score": 75, "grade": "B", "trend_state": "Uptrend"},
    )
    monkeypatch.setattr(indicators, "compute_trade_setup", lambda raw: None)

    result = screener_service.analyze_asset("APOTEA", "omxsto", "1D")

    assert result["symbol"] == full_symbol
    assert result["asset_type"] == "stock"
    assert result["stock_score"] == 75
