import os
from tms.models import Trade
import requests
import logging

logger = logging.getLogger("tms")
BASE_STOCK_API_URL = os.getenv("BASE_STOCK_API_URL")

market_prices = {}
def get_all_market_prices():
    try:
        url = BASE_STOCK_API_URL+"api/data/v2/live-market/"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        result = {entry["symbol"].upper(): float(entry["ltp"]) for entry in response.json()}
        market_prices.update(result)
        logger.info(f"Fetched {len(result)} market prices successfully.")
        return result
    except Exception as e:
        logger.error(f"Fetching all prices failed: {e}")
        return {}
market_prices = get_all_market_prices()


def get_latest_price(symbol):
    """
    Fetches the latest traded price (ltp) for a given stock symbol.
    """
    symbol = symbol.upper()
    try:
        if "ltp" not in market_prices.get(symbol, {}) or market_prices.get(symbol)["ltp"] is None:
            raise ValueError(f"'ltp' not found for symbol '{symbol}' in live market data.")
        return market_prices.get(symbol, {}).get("ltp", None)
    except Exception as e:
        print(f"[ERROR] Fetching latest price for {symbol} failed: {e}")
        return None
    
def evaluate_trades():
    trades = Trade.objects.filter(is_active=True)

    for trade in trades:
        current_price = get_latest_price(trade.stock_symbol)
        sl_price = trade.buy_price * (1 - trade.stop_loss_percent / 100) if trade.stop_loss_percent else None
        tp_price = trade.buy_price * (1 + trade.take_profit_percent / 100) if trade.take_profit_percent else None

        # Update highest price seen (for trailing stop)
        if trade.trailing_stop_loss_percent:
            if trade.highest_price_seen is None or current_price > trade.highest_price_seen:
                trade.highest_price_seen = current_price
                trade.save()

        tsl_price = (
            trade.highest_price_seen * (1 - trade.trailing_stop_loss_percent / 100)
            if trade.trailing_stop_loss_percent and trade.highest_price_seen
            else None
        )

        # Evaluate triggers
        should_sell = False
        reason = ""

        if sl_price and current_price <= sl_price:
            should_sell = True
            reason = f"Stop Loss hit at {current_price}"
        elif tp_price and current_price >= tp_price:
            should_sell = True
            reason = f"Take Profit hit at {current_price}"
        elif tsl_price and current_price <= tsl_price:
            should_sell = True
            reason = f"Trailing Stop Loss hit at {current_price}"

        if should_sell:
            if trade.auto_execute:
                execute_sell(trade, current_price)
            else:
                notify_user(trade.user, trade, reason)
                
def execute_sell(trade, current_price):
    # Broker API call to execute sell order
    # Example placeholder
    # broker_api.sell(trade.stock_symbol, trade.quantity)

    # Mark trade as inactive
    trade.is_active = False
    trade.is_executed = True
    trade.save()
    
def notify_user(user, trade, reason):
    # Example: email or in-app notification
    logger.info(f"Notify {user.username}: {reason}")
