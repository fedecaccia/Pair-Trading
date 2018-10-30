import numpy as np
import pandas as pd
import ccxt

# functions

# one trade profit calculation
def calculate_profit(ask, bid, ask_fee, bid_fee):
    return bid*(1-bid_fee)-ask*(1+ask_fee)

# load data
def load_csv(symbol, exchange):    
    return pd.read_csv("data/orderbook"+exchange.capitalize()+symbol+".csv", parse_dates=True, sep = ",", index_col=0)

# weight orderbook
def get_weight_val(row, side, amount):
    
    count = 0
    price = 0

    if side=="ask":     

        price = row["ask_val_0"]
        count = row["ask_count_0"]        
        if count < amount:
            more_orders = row["ask_count_1"]
            if count+more_orders<=amount:
                new_count = more_orders
            else:
                new_count = amount-count
            price = (price * count + row["ask_val_1"]*new_count ) / (count+new_count)
            count += new_count

            if count < amount:
                more_orders = row["ask_count_2"]
                if count+more_orders>=amount:
                    new_count = amount-count
                    price = (price * count + row["ask_val_2"]*new_count ) / (count+new_count)
                else:
                    price = row["ask_weight_val_2"]
        
    elif side=="bid":
        
        price = row["bid_val_0"]
        count = row["bid_count_0"]        
        if count < amount:
            more_orders = row["bid_count_1"]
            if count+more_orders<=amount:
                new_count = more_orders
            else:
                new_count = amount-count
            price = (price * count + row["bid_val_1"]*new_count ) / (count+new_count)
            count += new_count

            if count < amount:
                more_orders = row["bid_count_2"]
                if count+more_orders>=amount:
                    new_count = amount-count
                    price = (price * count + row["bid_val_2"]*new_count ) / (count+new_count)
                else:
                    price = row["bid_weight_val_2"]
    
    return price

# settings

exchanges = [
    "binance",
    "bitfinex",
    "bitstamp",
    "bittrex",
    "cex",
    "coinex",
    "exmo",
    "gatecoin",
    "gateio",
    "gdax",
    "gemini",
    "hitbtc",
    "huobipro",
    "kraken",
    "kucoin",
    "okex",
    "poloniex",
    "yobit"
]
exchanges = ["bitstamp", "bittrex"]
min_percentual_profit = 0.0001
usd_min_profit = 0.001
usd_per_trade = 1000
btc_price = 6500
period = 30
symbols = [
    "XTZBTC",
    "XRPUSD",

    "ETHBTC",
    "BCHBTC",
    "EOSBTC",
    "XRPBTC",
    "EOSBTC",
    "LTCBTC",
    "XLMBTC",
    "ADABTC",
    "IOTABTC",
    "TRXBTC",
    "XMRBTC",
    "NEOBTC",

    "DASHBTC",
    "ETCBTC",
    "XEMBTC",
    "XTZBTC",
    "VENBTC",
    "OMGBTC",
    "ZECBTC",
    "QTUMBTC",
    "MITBTC",
    "SNTBTC",
    "IOSTBTC",
    "LRCBTC",
    "ZENBTC",

    "BTCUSD",
    "BTCUSDT",
    "BTCEUR",
    "ETHUSD",
    "ETHUSDT",
    "ETHEUR",
    "XRPUSD",
    "XRPUSDT",
    "XRPEUR",
    "BCHUSD",
    "BCHUSDT",
    "BCHEUR",
    "EOSUSD",
    "EOSUSDT",
    "EOSEUR",
    "LTCUSD",
    "LTCUSDT",
    "LTCEUR",
    "XLMUSD",
    "XLMUSDT",
    "XLMEUR",
    "ADAUSDT"
]
symbols = ["XRPUSD"]

# useful variables

min_fractional_profit = min_percentual_profit/100
fees = {exchange.capitalize():getattr(ccxt, exchange)().describe()["fees"]["trading"]["taker"] for exchange in exchanges}

# symbol loop

# symbol = "BATBTC"
for symbol in symbols:

    # exchanges loop

    for i, exchange0 in enumerate(exchanges):
        for exchange1 in exchanges[i+1:]:

            # exchange0 = "Binance"
            # exchange1 = "Bitfinex"
            exchange0 = exchange0.capitalize()
            exchange1 = exchange1.capitalize()

            print("\n")
            print(symbol, exchange0, exchange1)

            load = False
            try:
                pair0 = load_csv(symbol, exchange0)
                pair1 = load_csv(symbol, exchange1)
                load = True
            except Exception as e:
                pass
                # print(e)
            
            if load:
                # resample

                max_delay = "2s"
                pair0 = pair0.resample(max_delay).mean().dropna()
                pair1 = pair1.resample(max_delay).mean().dropna()

                # unique index between pairs

                pair0 = pair0[pair0.index.isin(pair1.index)]
                pair1 = pair1[pair1.index.isin(pair0.index)]

                # particular useful variables

                long_exchange0 = False
                long_exchange1 = False
                closed = True
                acumulated_profit = 0
                asset_price = pair0.iloc[0]["ask_val_0"]
                if symbol[-3:]=="BTC":
                    asset_usd_price = asset_price*btc_price
                    amount = usd_per_trade / asset_usd_price
                elif symbol[-3:]=="USD" or symbol[-4:]=="USDT":
                    asset_usd_price = asset_price
                    amount = usd_per_trade / asset_usd_price
                pair0_fee = fees[exchange0]
                pair1_fee = fees[exchange1]
                p01 = np.array([])
                p10 = np.array([])
                prev_profit = 0

                # loop

                for t in pair0.index: # both pairs have same index

                    pair0_bid = get_weight_val(pair0.loc[t], "bid", amount) #pair0.loc[t]["bid_val_0"]
                    pair0_ask = get_weight_val(pair0.loc[t], "ask", amount) #pair0.loc[t]["ask_val_0"]
                    
                    pair1_bid = get_weight_val(pair1.loc[t], "bid", amount) #pair1.loc[t]["bid_val_0"]
                    pair1_ask = get_weight_val(pair1.loc[t], "ask", amount) #pair1.loc[t]["ask_val_0"]
                    
                    p01 = np.append(p01, calculate_profit(pair0_ask, pair1_bid, pair0_fee, pair1_fee))
                    p10 = np.append(p10, calculate_profit(pair1_ask, pair0_bid, pair1_fee, pair0_fee))
                    
                    # print("*************************")
                    # print(t)
                    # print(pair0_bid, pair0_ask)
                    # print(pair1_bid, pair1_ask)
                    # print(pair0_fee, pair1_fee)
                    
                    # print("p01", -pair0_ask*(1+pair0_fee)+pair1_bid*(1-pair1_fee))
                    # print("p10", -pair1_ask*(1+pair1_fee)+pair0_bid*(1-pair0_fee))

                    if len(p01)>period:

                        p01 = np.delete(p01, 0)
                        p10 = np.delete(p10, 0)

                        p01_avg = p01.mean()
                        p01_std = p01.std()
                        p10_avg = p10.mean()
                        p10_std = p10.std()
                        
                        if closed == True:

                            # evaluate type A: long 0 and short 1
                            # if p01[-1] > - p10_avg and\
                            # (p01[-1]  + p10_avg)*amount > usd_min_profit and\
                            # (p01[-1]  + p10_avg) / (2*asset_price) > min_fractional_profit:
                            if p01[-1] > 0:
                            # if p01[-1] + p10_avg > 0:

                                long_exchange0 = True
                                closed = False
                                long_price = pair0_ask
                                short_price = pair1_bid
                                prev_profit = p01[-1]
                                print(t, "Opening")
                                print("Buy in", exchange0, "at %.8f"%pair0_ask)
                                print("Sell in", exchange1, "at %.8f"%pair1_bid)

                            # evaluate type B: long 1 and short 0
                            # if p10[-1] > - p01_avg and\
                            # (p10[-1]  + p01_avg)*amount > usd_min_profit and\
                            # (p10[-1]  + p01_avg) / (2*asset_price) > min_fractional_profit:
                            elif p10[-1] > 0:
                            # elif p10[-1] + p01_avg > 0:

                                long_exchange1 = True
                                closed = False
                                long_price = pair1_ask
                                short_price = pair0_bid
                                prev_profit = p10[-1]
                                print(t, "Opening")
                                print("Buy in", exchange1, "at %.8f"%pair1_ask)
                                print("Sell in", exchange0, "at %.8f"%pair0_bid)
                        
                        elif long_exchange0:
                            
                            # evaluate close type A
                            if prev_profit + p10[-1] > 0 and\
                            amount*(prev_profit + p10[-1]) > usd_min_profit and\
                            (prev_profit + p10[-1]) / (2*asset_price) > min_fractional_profit:                            
                                long_exchange0 = False
                                closed = True
                                net_profit = (prev_profit + p10[-1])*amount
                                acumulated_profit += net_profit
                                print(t, "Closing")
                                print("Sell in", exchange0, "at %.8f"%pair0_bid)
                                print("Buy in", exchange1, "at %.8f"%pair1_ask)
                                print("Percent profit: %.2f"%((prev_profit + p10[-1]) / (2*asset_price)*100)+"%")
                                print("Net profit: %.8f"%(net_profit)+" QUOTE")
                                
                                
                        elif long_exchange1:
                            
                            # evaluate close type B
                            if prev_profit + p01[-1] > 0 and\
                            amount*(prev_profit + p01[-1]) > usd_min_profit and\
                            (prev_profit + p01[-1]) / (2*asset_price) > min_fractional_profit:
                                long_exchange1 = False
                                closed = True
                                net_profit = (prev_profit + p01[-1])*amount
                                acumulated_profit += net_profit
                                print(t, "Closing")
                                print("Sell in", exchange1, "at %.8f"%pair1_bid)
                                print("Buy in", exchange0, "at %.8f"%pair0_ask)
                                print("Percent profit: %.2f"%((prev_profit + p01[-1]) / (2*asset_price)*100)+"%")
                                print("Net profit: %.8f"%(net_profit)+" QUOTE")


                print("Acumulated profit: %.8f"%acumulated_profit+" QUOTE")
