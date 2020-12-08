import hmac
import hashlib
import time
import requests
import json
from urllib.parse import urlencode

# Replace these two with your own. Find them at the API Management tab in Binance
api_key = 'XXXX'
api_secret = 'YYYY'


# Cryptos of interest
# Replace/Add the cryptos you have in your SPOT account over here
cryptos_list = ["BNB", "BTC", "XLM", "XMR", "XRP", "MANA", "ENJ", "RVN"]

# Go to this website and check the "Minimum Trade Amount" column to figure out the precision
# https://www.binance.com/en/trade-rule
precision = {
    "BNBBUSD" : 2,
    "BTCBUSD" : 6,
    "XLMBUSD" : 1,
    "XMRBUSD" : 5,
    "XRPBUSD" : 1,
    "MANABUSD" : 1,
    "ENJBUSD" : 1,
    "RVNBUSD" : 1
}

def hashing(query_string):
    return hmac.new(str(api_secret).encode('utf-8'), str(query_string).encode('utf-8'),hashlib.sha256).hexdigest()

def check_open_orders(symbol):
    # Here I want to check what happens if there are no open orders

    servertime = requests.get("https://api.binance.com/api/v1/time")
    servertimeobject = json.loads(servertime.text)
    servertimeint = servertimeobject['serverTime']

    params = urlencode({
        "symbol" : symbol,
        "recvWindow" : 5000,
        "timestamp" : servertimeint,
    })

    hashedsig = hashing(params)

    open_orders = requests.get("https://api.binance.com/api/v3/openOrders",
        params = {
            "symbol" : symbol,
            "recvWindow" : 5000,
            "timestamp" : servertimeint,
            "signature" : hashedsig,
        },
        headers = {
            "X-MBX-APIKEY" : api_key,
        }
    )

    # You might want to be careful here, because an error will return a JSON of length 2
    if(len(open_orders.json()) == 0):
        return "Order Executed Successfully"
    elif(len(open_orders.json()) == 1) :
        # At this point, you either have a partially filled or not filled at all order
        difference = float(open_orders.json()[0].get('origQty') - float(open_orders.json()[0].get('executedQty')))
        return difference
    else:
        # At this point, you have an error, because there should not be more than one active order at a time
        return "Error"

def cancel_order(symbol):
    servertime = requests.get("https://api.binance.com/api/v1/time")
    servertimeobject = json.loads(servertime.text)
    servertimeint = servertimeobject['serverTime']

    params = urlencode({
        "symbol" : symbol,
        "recvWindow" : 5000,
        "timestamp" : servertimeint,
    })

    hashedsig = hashing(params)

    cancelled_order = requests.delete("https://api.binance.com/api/v3/openOrders",
        params = {
            "symbol" : symbol,
            "recvWindow" : 5000,
            "timestamp" : servertimeint,
            "signature" : hashedsig,
        },
        headers = {
            "X-MBX-APIKEY" : api_key,
        }
    )

    if(cancelled_order.json()[0].get('status') == "CANCELED"):
        return("Canceled Successfully")
    else:
        return("Warning")

def order_request(side,symbol,quantity):
    servertime = requests.get("https://api.binance.com/api/v1/time")
    servertimeobject = json.loads(servertime.text)
    servertimeint = servertimeobject['serverTime']

    params = urlencode({
        "symbol" : symbol,
        "side" : side,
        "type" : "MARKET",
        "quantity" : quantity,
        "recvWindow" : 5000,
        "timestamp" : servertimeint,
    })

    hashedsig = hashing(params)

    order_sheet = requests.post("https://api.binance.com/api/v3/order/test",
        params = {
            "symbol" : symbol,
            "side" : side,
            "type" : "MARKET",
            "quantity" : quantity,
            "recvWindow" : 5000,
            "timestamp" : servertimeint,
            "signature" : hashedsig,
        },
        headers = {
            "X-MBX-APIKEY" : api_key,
        }
    )

def actual_order(side, pair, adjustment):
    trade_success = False
    adjustment = adjustment
    while trade_success == False:
        order_request(side,pair,adjustment)

        # Wait for two seconds to see it through
        time.sleep(2)
        # Get the latest order from the book
        # If there are no open orders, we're good to proceed forward
        check_status = check_open_orders(pair)
        if(check_status == "Order Executed Successfully"):
            trade_success = True
        elif(check_status == "Error"):
            # At this point, an error has occurred
            # Cancel all trades and throw exception
            if(cancel_order(pair) == "Canceled Successfully"):
                raise Exception("Error occurred. Canceled Successfully. Halting all trading activity now.")
            else:
                raise Exception("Error occurred. Manual Cancellation required. Halting all trading activity now.")
        else:

            # Cancel the existing open order first
            if(cancel_order(pair) == "Warning"):
                raise Exception("Error occurred in cancellation process. Halting all trading activity now.")
            else:
                # check_status contains the float of the remaining crypto that needs to be sold
                adjustment = check_status

def swap(list,pos1,pos2):
    list[pos1], list[pos2] = list[pos2], list[pos1]
    return list

while True:
    # First grab the wallet information
    servertime = requests.get("https://api.binance.com/api/v1/time")
    servertimeobject = json.loads(servertime.text)
    servertimeint = servertimeobject['serverTime']

    params = urlencode({
        "timestamp" : servertimeint,
        "type" : "SPOT",
    })

    hashedsig = hashing(params)

    userdata = requests.get("https://api.binance.com/sapi/v1/capital/config/getall",
        params = {
            "timestamp" : servertimeint,
            "signature" : hashedsig,
            "type" : "SPOT",
        },
        headers = {
            "X-MBX-APIKEY" : api_key,
        }
    )

    # Next, get the amount of free coins from the entire crypto list
    free_coins = []
    rearranged_cryptolist = []

    for x in range(0,len(userdata.json())):
        for y in range(0,len(cryptos_list)):
            if(userdata.json()[x].get('coin') == cryptos_list[y]):
                rearranged_cryptolist.append(userdata.json()[x].get('coin'))
                free_coins.append(userdata.json()[x].get('free'))

    print("Crypto List: " + str(rearranged_cryptolist))
    print("Free Coins: " + str(free_coins))

    # Add 'BUSD' to the end of each coin in rearranged_cryptolist
    trade_pairs = []
    for x in range(0,len(rearranged_cryptolist)):
        trade_pairs.append(rearranged_cryptolist[x] + 'BUSD')
    print("Trade Pairs: " + str(trade_pairs))

    # From here, gather the dollar value of the free coins
    pair_confirm = []
    prices_array = []

    for x in range(0,len(trade_pairs)):

        prices = requests.get("https://api.binance.com/api/v3/ticker/price",
            params = {
                "symbol" : trade_pairs[x],
            }
        )

        pair_confirm.append(prices.json().get('symbol'))
        prices_array.append(prices.json().get('price'))

    print("Trade Prices: " + str(prices_array))

    # Only proceed on if the pair_confirm is the same as trade_pairs
    if(pair_confirm != trade_pairs):
        raise Exception("Pairs are not the same, aborting!")

    # From here, get the dollar value of all the free coins
    dollar_value = []
    for x in range(0, len(prices_array)):
        dollar_value.append(float(prices_array[x]) * float(free_coins[x]))

    total_portfolio_value = sum(dollar_value)

    print("Dollar Value of Coins: " + str(dollar_value))

    # Next, check each coin to see how far it is, in absolute terms from 5%
    disparity_check = []

    # This array contain the amount of crypto, in absolute terms, needed to rebalance
    buy_sell_adjustment = []

    for x in range(0, len(dollar_value)):
        # Percent difference can be positive (need to buy more) or negative (need to sell)

        # Right now it's set at 5% per asset, but this may or may not reflect your risk preferences
        # Consider adding a dictionary with different weights according to a custom algorithm
        percent_difference = 0.05 - (dollar_value[x]/total_portfolio_value)
        disparity_check.append(percent_difference)

        # Everything in buy_sell_adjustment needs to be positive. You cannot sell a negative amount of crypto.
        buy_sell_adjustment.append(round(abs((float(total_portfolio_value) * float(percent_difference))/float(prices_array[x])),precision.get(trade_pairs[x])))

    print("Disparity Check: " + str(disparity_check))
    print("Buy/Sell Adjustment: " + str(buy_sell_adjustment))

    # Prioritize coins with disparity checks less than 0%.
    # We want to SELL first in order to free up capital, before BUYING

    swapper = 0
    for x in range(0, len(disparity_check)):
        if(disparity_check[x] < 0.0):
            swap(free_coins,swapper,x)
            swap(rearranged_cryptolist,swapper,x)
            swap(trade_pairs,swapper,x)
            swap(pair_confirm,swapper,x)
            swap(prices_array,swapper,x)
            swap(dollar_value,swapper,x)
            swap(disparity_check,swapper,x)
            swap(buy_sell_adjustment,swapper,x)
            swapper = swapper + 1

    # Determine whether to buy or sell each crypto
    # Give a dynamic margin, with a fixed dollar value of $10

    margin_percentage = 10.0/total_portfolio_value
    print("Acceptable Margin: " + str(margin_percentage))

    # For each crypto, if the absolute value of the disparity is greater than the margin,
    # execute the trade
    # If disparity < 0, sell until it hits 0%
    # If disparity > 0, buy until it hits 0%

    trade_executed = []

    for x in range(0, len(disparity_check)):
        if(abs(disparity_check[x]) >= margin_percentage):
            trade_executed.append(True)
            if(disparity_check[x] < 0):
                # At this point, you should execute a sell order
                actual_order("SELL",trade_pairs[x],buy_sell_adjustment[x])
            else:
                # At this point, you should execute a buy order
                actual_order("BUY",trade_pairs[x],buy_sell_adjustment[x])

        else:
            trade_executed.append(False)

    print("Trade Executed? " + str(trade_executed))

    print("Balancing Completed. Going to sleep for a day!")
    time.sleep(86400)
