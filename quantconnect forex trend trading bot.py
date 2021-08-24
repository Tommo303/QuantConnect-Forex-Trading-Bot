Python 3.8.5 (tags/v3.8.5:580fbb0, Jul 20 2020, 15:43:08) [MSC v.1926 32 bit (Intel)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
>>> 
class ForexTrendTrader(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 7, 1)
        self.SetEndDate(2021, 8, 1)
        self.SetCash(1000)
        
        self.symbol = "EURUSD"
        
        self.AddForex(self.symbol, Resolution.Minute, Market.Oanda)
        
        self.c = self.Consolidate(self.symbol, timedelta(hours=4), self.OnFourHour)
        self.c2 = self.Consolidate(self.symbol, timedelta(minutes=15), self.OnFifteenMin)
        
        self.atr = AverageTrueRange(14)
        self.RegisterIndicator(self.symbol, self.atr, self.c2)
        
        self.higherPeriod = HigherPeriod(self, self.symbol, timedelta(hours=4), 20)
        
        self.quote = RollingWindow[QuoteBar](1)
        
        self.fillPrice = None
        self.stop = None
        

    def OnFourHour(self, bar):
        if self.higherPeriod.Value.IsReady:
            self.Plot("EURUSD", "4H", self.higherPeriod.Value[0])
            
            
    def OnFifteenMin(self, bar):
        if not (self.quote.IsReady and self.higherPeriod.Value.IsReady and self.atr.IsReady):
            self.quote.Add(bar)
            return
        
        self.Plot("EURUSD", "Low", bar.Low)
        self.Plot("EURUSD", "High", bar.High)
        
        quantity = self.CalculateOrderQuantity(self.symbol, 1)
        
        atr = self.atr.Current.Value
        price = self.Securities[self.symbol].Price
    
        position = self.Signal(bar)
        self.Plot("Signal", "Signal", position)
         
        if self.Portfolio[self.symbol].Invested:
            if self.Portfolio[self.symbol].IsLong:
                pass
                    
        else:
            if position == 1:
                self.StopLimitOrder(self.symbol, quantity, price * 0.999, price * 1.001)
                self.Debug(f"Long entry at {price}")
            
        self.quote.Add(bar)
        
    
    def Signal(self, bar):
        if (self.quote[0].Low <= self.higherPeriod.Value[1] and 
                bar.Low > self.higherPeriod.Value[0] and 
                self.higherPeriod.Value[0] < max([bar.Open, bar.Close]) and 
                self.higherPeriod.Value[1] < max([self.quote[0].Open, self.quote[0].Close])):
                    
                return 1

        elif (self.quote[0].High >= self.higherPeriod.Value[1] and 
            bar.High < self.higherPeriod.Value[0] and 
            self.higherPeriod.Value[0] > max([bar.Open, bar.Close]) and 
            self.higherPeriod.Value[1] > max([self.quote[0].Open, self.quote[0].Close])):
                
                return -1

        else:
            return 0


class HigherPeriod:
    
    def __init__(self, algorithm, symbol, timeframe, period):
        consolidator = QuoteBarConsolidator(timeframe)
        algorithm.SubscriptionManager.AddConsolidator(symbol, consolidator)
        consolidator.DataConsolidated += self.OnConsolidated
        
        self.ema = ExponentialMovingAverage(period)
        algorithm.RegisterIndicator(symbol, self.ema, consolidator)
        
        self.period = period
        
        self.emaWin = RollingWindow[float](2)
        self.Value = RollingWindow[float](2)
        
    def OnConsolidated(self, sender, bar):
        if not self.ema.IsReady:
            return
        
        if not self.emaWin.IsReady:
            self.emaWin.Add(self.ema.Current.Value)
            return
        
        alpha = 2 / (self.period + 1)
        
        self.emaWin.Add(alpha * self.ema.Current.Value + (1 - alpha) * self.emaWin[0])
        
        if not self.Value.IsReady:
            self.Value.Add(self.emaWin[0])
            
        self.Value.Add(alpha * self.emaWin[0] + (1 - alpha) * self.Value[0])