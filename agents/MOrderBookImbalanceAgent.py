#
#
# Author: Anej Rozman
# 
# Description: The OrderBookImbalanceAgent is a simple example of an agent that predicts the short term
# price movement of a security by the preponderance of directionality in the limit order
# book.  Specifically, it predicts the price will fall if the ratio of bid volume to total volume
# in the first N levels of the book is smaller than a configurable threshold, and will rise if
# that ratio is above a symmetric value.  It represents traders that attempt to predict 
# short term price movements based on order book imbalance, which is statistically correlated with 
# short term price movements in real markets.  
# 
# 
# Usage: This agent is constructed to work with the ABIDE simulator


from agent.TradingAgent import TradingAgent
import pandas as pd
from util.util import log_print



class OrderBookImbalanceAgent(TradingAgent):

    # The OrderBookImbalanceAgent is a simple example of an agent that predicts the short term
    # price movement of a security by the preponderance of directionality in the limit order
    # book.  Specifically, it predicts the price will fall if the ratio of bid volume to total volume
    # in the first N levels of the book is smaller than a configurable threshold, and will rise if
    # that ratio is above a symmetric value.  There is a trailing stop on the bid_pct to exit.
    #
    # Note that this means the current iteration of the OBI agent is treating order book imbalance
    # as an oscillating indicator rather than a momentum indicator.  (Imbalance to the buy side
    # indicates "overbought" rather than an upward trend.)
    #
    # Parameters unique to this agent:
    # Levels: how much order book depth should be considered when evaluating imbalance?
    # Entry Threshold: how much imbalance is required before the agent takes a non-flat position?
    #                  For example, entry_threshold=0.1 causes long entry at 0.6 or short entry at 0.4.
    # Trail Dist: how far behind the peak bid_pct should the trailing stop follow?

    def __init__(self, id, name, type, symbol=None, levels=10, entry_threshold=0.17, trail_dist=0.085, freq=3600000000000, starting_cash=1000000, log_orders=True, random_state=None):
        super().__init__(id, name, type, starting_cash=starting_cash, log_orders=log_orders, random_state=random_state)
        self.symbol = symbol
        self.levels = levels
        self.entry_threshold = entry_threshold
        self.trail_dist = trail_dist
        self.freq = freq
        self.last_market_data_update = None
        self.is_long = False
        self.is_short = False

        self.trailing_stop = None
        self.plotme = []


    def kernelStarting(self, startTime):
        super().kernelStarting(startTime)

    def wakeup(self, currentTime):
        super().wakeup(currentTime)
        super().requestDataSubscription(self.symbol, levels=self.levels, freq=self.freq)
        self.setComputationDelay(1)

    def receiveMessage(self, currentTime, msg):
        super().receiveMessage(currentTime, msg)
        if msg.body['msg'] == 'MARKET_DATA':
            self.cancelOrders()

            self.last_market_data_update = currentTime
            bids, asks = msg.body['bids'], msg.body['asks']

            bid_liq = sum(x[1] for x in bids)
            ask_liq = sum(x[1] for x in asks)

            # OBI strategy.
            target = 0

            if bid_liq == 0 or ask_liq == 0:
                log_print("OBI agent inactive: zero bid or ask liquidity")
                return
            else:
                # bid_pct: Fraction of total volume on the buy side.
                # High bid_pct (> 0.5) now implies Buy Pressure (Momentum).
                bid_pct = bid_liq / (bid_liq + ask_liq)

                # 1. Manage SHORT Position (Betting on low bid_pct / price drop)
                if self.is_short:
                    # Trailing Stop is a CEILING (follows bid_pct down).
                    # If bid_pct drops (trend strengthens), lower the stop.
                    if bid_pct + self.trail_dist < self.trailing_stop:
                        self.trailing_stop = bid_pct + self.trail_dist
                    
                    # Exit if bid_pct rises above the trailing stop (trend reverses).
                    if bid_pct > self.trailing_stop: 
                        log_print("OBI exiting SHORT: bid_pct > stop ({:.2f} > {:.2f})", bid_pct, self.trailing_stop)
                        target = 0
                        self.is_short = False
                        self.trailing_stop = None
                    else:
                        log_print("OBI holding SHORT: bid_pct < stop ({:.2f} < {:.2f})", bid_pct, self.trailing_stop)
                        target = -100

                # 2. Manage LONG Position (Betting on high bid_pct / price rise)
                elif self.is_long:
                    # Trailing Stop is a FLOOR (follows bid_pct up).
                    # If bid_pct rises (trend strengthens), raise the stop.
                    if bid_pct - self.trail_dist > self.trailing_stop:
                        self.trailing_stop = bid_pct - self.trail_dist
                    
                    # Exit if bid_pct drops below the trailing stop (trend fades).
                    if bid_pct < self.trailing_stop: 
                        log_print("OBI exiting LONG: bid_pct < stop ({:.2f} < {:.2f})", bid_pct, self.trailing_stop)
                        target = 0
                        self.is_long = False
                        self.trailing_stop = None
                    else:
                        log_print("OBI holding LONG: bid_pct > stop ({:.2f} > {:.2f})", bid_pct, self.trailing_stop)
                        target = 100

                # 3. Entry Logic (Flat)
                else:
                    # MOMENTUM ENTRY: High Bids -> Buy
                    if bid_pct > (0.5 + self.entry_threshold):
                        log_print("OBI entering LONG: Buy Pressure (bid_pct {:.2f} > {:.2f})", bid_pct, 0.5 + self.entry_threshold)
                        target = 100
                        self.is_long = True
                        # Set initial stop below current level (Floor)
                        self.trailing_stop = bid_pct - self.trail_dist 
                    
                    # MOMENTUM ENTRY: Low Bids -> Sell
                    elif bid_pct < (0.5 - self.entry_threshold):
                        log_print("OBI entering SHORT: Sell Pressure (bid_pct {:.2f} < {:.2f})", bid_pct, 0.5 - self.entry_threshold)
                        target = -100
                        self.is_short = True
                        # Set initial stop above current level (Ceiling)
                        self.trailing_stop = bid_pct + self.trail_dist 
                    
                    else:
                        # Neutral Zone
                        target = 0

                self.plotme.append( { 'currentTime' : self.currentTime, 'midpoint' : (asks[0][0] + bids[0][0]) / 2, 'bid_pct' : bid_pct } )

            # Adjust holdings to target.
            holdings = self.holdings[self.symbol] if self.symbol in self.holdings else 0
            delta = target - holdings
            direction = True if delta > 0 else False
            price = self.computeRequiredPrice(direction, abs(delta), bids, asks)

            if delta != 0:
                self.placeLimitOrder(self.symbol, abs(delta), direction, price)



    def getWakeFrequency(self):
        return pd.Timedelta('1s')


    # Computes required limit price to immediately execute a trade for the specified quantity
    # of shares.
    def computeRequiredPrice (self, direction, shares, known_bids, known_asks):
        book = known_asks if direction else known_bids

        # Start at the inside and add up the shares.
        t = 0

        for i in range(len(book)):
            p, v = book[i]
            t += v

            # If we have accumulated enough shares, return this price.
            if t >= shares:
                return p

        # Not enough shares.  Just return worst price (highest ask, lowest bid).
        return book[-1][0]


    # Cancel all open orders.
    # Return value: did we issue any cancellation requests?
    def cancelOrders(self):
        if not self.orders: return False

        for id, order in self.orders.items():
            self.cancelOrder(order)

        return True


    # Lifecycle.
    def kernelTerminating(self):
      # Plotting code is probably not needed here long term, but helps during development.

      #df = pd.DataFrame(self.plotme)
      #df.set_index('currentTime', inplace=True)
      #df.rolling(30).mean().plot(secondary_y=['bid_pct'], figsize=(12,9))
      #plt.show()
      super().kernelTerminating()


