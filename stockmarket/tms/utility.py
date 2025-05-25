import json
import logging
import os
import re

def filter_stock_data(stock_data):
    # Add top_price_diff to each stock entry
    for symbol, data in stock_data.items():
        if "error" not in data or data["error"] is None:
            try:
                buyer_price = data["top_buyer"]["price"]
                seller_price = data["top_seller"]["price"]
                data["top_price_diff"] = round(seller_price - buyer_price, 4)
            except (KeyError, TypeError):
                data["top_price_diff"] = None
        else:
            data["top_price_diff"] = None

    # Filter out invalid or incomplete entries (optional)
    filtered_data = {
        symbol: data for symbol, data in stock_data.items()
        if data.get("top_price_diff") is not None and data.get("top_price_diff") >= 0
    }

    # Sort the dictionary based on top_price_diff (ascending)
    sorted_data = dict(
        sorted(filtered_data.items(), key=lambda item: item[1]["top_price_diff"])
    )
    return sorted_data