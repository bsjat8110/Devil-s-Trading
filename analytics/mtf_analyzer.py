"""
Multi-Timeframe Analysis Engine - Advanced Version
Analyzes multiple timeframes to find confluence and high-probability setups
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas_ta as ta
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TimeframeSignal:
    """Signal from a specific timeframe"""
    timeframe: str
    trend: str
    strength: float
    support_levels: List[float]
    resistance_levels: List[float]
    key_indicators: Dict[str, float]
    timestamp: datetime


@dataclass
class ConfluenceZone:
    """Price zone with multiple timeframe confluence"""
    price_level: float
    zone_type: str
    strength: float
    timeframes: List[str]
    indicators: List[str]


class MultiTimeframeAnalyzer:
    """Analyzes multiple timeframes to find confluence and key levels"""
    
    TIMEFRAMES = {
        '1min': '1m',
        '5min': '5m',
        '15min': '15m',
        '1hour': '1h',
        'daily': '1d'
    }
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.data: Dict[str, pd.DataFrame] = {}
        self.signals: Dict[str, TimeframeSignal] = {}
        self.confluence_zones: List[ConfluenceZone] = []
        
    def fetch_data(self, timeframe: str, bars: int = 500) -> pd.DataFrame:
        """Fetch OHLCV data"""
        try:
            import yfinance as yf
            
            yf_symbol = self._convert_symbol(self.symbol)
            
            df = yf.download(
                yf_symbol,
                period="60d",
                interval=self.TIMEFRAMES[timeframe],
                progress=False
            )
            
            if df.empty:
                logger.warning(f"No data for {timeframe}, using sample")
                return self._generate_sample_data(bars)
            
            df.columns = [col.lower() for col in df.columns]
            df = df.tail(bars)
            
            logger.info(f"✅ Fetched {len(df)} bars for {timeframe}")
            return df
            
        except Exception as e:
            logger.warning(f"Error: {e}, using sample data")
            return self._generate_sample_data(bars)
    
    def _generate_sample_data(self, bars: int) -> pd.DataFrame:
        """Generate sample data"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=bars, freq='15min')
        close = 23000 + np.cumsum(np.random.randn(bars) * 10)
        
        return pd.DataFrame({
            'open': close + np.random.randn(bars) * 3,
            'high': close + np.abs(np.random.randn(bars) * 5),
            'low': close - np.abs(np.random.randn(bars) * 5),
            'close': close,
            'volume': np.random.randint(100000, 500000, bars)
        }, index=dates)
    
    def _convert_symbol(self, symbol: str) -> str:
        """Convert to Yahoo Finance format"""
        symbol_map = {
            'NIFTY': '^NSEI',
            'BANKNIFTY': '^NSEBANK',
            'SENSEX': '^BSESN'
        }
        return symbol_map.get(symbol, f"{symbol}.NS")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators"""
        if df.empty:
            return df
        
        try:
            df['ema_9'] = ta.ema(df['close'], length=9)
            df['ema_21'] = ta.ema(df['close'], length=21)
            df['ema_50'] = ta.ema(df['close'], length=50)
            df['ema_200'] = ta.ema(df['close'], length=200)
            df['rsi'] = ta.rsi(df['close'], length=14)
            
            macd = ta.macd(df['close'])
            if macd is not None:
                df = pd.concat([df, macd], axis=1)
            
            bbands = ta.bbands(df['close'], length=20, std=2)
            if bbands is not None:
                df = pd.concat([df, bbands], axis=1)
            
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
            
            supertrend = ta.supertrend(df['high'], df['low'], df['close'])
            if supertrend is not None:
                df = pd.concat([df, supertrend], axis=1)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def detect_trend(self, df: pd.DataFrame) -> Tuple[str, float]:
        """Detect trend"""
        if df.empty or len(df) < 50:
            return 'neutral', 0.0
        
        try:
            latest = df.iloc[-1]
            
            ema_bullish = (
                latest.get('ema_9', 0) > latest.get('ema_21', 0) > latest.get('ema_50', 0)
            )
            ema_bearish = (
                latest.get('ema_9', 0) < latest.get('ema_21', 0) < latest.get('ema_50', 0)
            )
            
            price_above = latest['close'] > latest.get('ema_50', 0)
            price_below = latest['close'] < latest.get('ema_50', 0)
            
            macd_col = 'MACD_12_26_9' if 'MACD_12_26_9' in df.columns else 'macd'
            signal_col = 'MACDs_12_26_9' if 'MACDs_12_26_9' in df.columns else 'macd_signal'
            
            macd_bullish = latest.get(macd_col, 0) > latest.get(signal_col, 0)
            macd_bearish = latest.get(macd_col, 0) < latest.get(signal_col, 0)
            
            bullish_signals = sum([ema_bullish, price_above, macd_bullish])
            bearish_signals = sum([ema_bearish, price_below, macd_bearish])
            
            strength = abs(bullish_signals - bearish_signals) / 3.0 * 100
            
            if bullish_signals > bearish_signals:
                return 'bullish', strength
            elif bearish_signals > bullish_signals:
                return 'bearish', strength
            else:
                return 'neutral', 0.0
                
        except Exception as e:
            logger.error(f"Error detecting trend: {e}")
            return 'neutral', 0.0
    
    def find_support_resistance(self, df: pd.DataFrame, num_levels: int = 5) -> Tuple[List[float], List[float]]:
        """Find S/R levels"""
        if df.empty or len(df) < 20:
            return [], []
        
        try:
            df['pivot_high'] = (
                (df['high'] > df['high'].shift(1)) &
                (df['high'] > df['high'].shift(2)) &
                (df['high'] > df['high'].shift(-1)) &
                (df['high'] > df['high'].shift(-2))
            )
            
            df['pivot_low'] = (
                (df['low'] < df['low'].shift(1)) &
                (df['low'] < df['low'].shift(2)) &
                (df['low'] < df['low'].shift(-1)) &
                (df['low'] < df['low'].shift(-2))
            )
            
            resistance = df[df['pivot_high']]['high'].tolist()
            support = df[df['pivot_low']]['low'].tolist()
            
            resistance = sorted(resistance, reverse=True)[:num_levels]
            support = sorted(support, reverse=True)[:num_levels]
            
            return support, resistance
            
        except Exception as e:
            logger.error(f"Error finding S/R: {e}")
            return [], []
    
    def analyze_timeframe(self, timeframe: str) -> Optional[TimeframeSignal]:
        """Analyze single timeframe"""
        try:
            df = self.fetch_data(timeframe)
            if df.empty:
                return None
            
            df = self.calculate_indicators(df)
            trend, strength = self.detect_trend(df)
            support, resistance = self.find_support_resistance(df)
            
            latest = df.iloc[-1]
            
            key_indicators = {
                'close': float(latest['close']),
                'rsi': float(latest.get('rsi', 50)),
                'atr': float(latest.get('atr', 0)),
                'volume': float(latest['volume'])
            }
            
            signal = TimeframeSignal(
                timeframe=timeframe,
                trend=trend,
                strength=strength,
                support_levels=support,
                resistance_levels=resistance,
                key_indicators=key_indicators,
                timestamp=datetime.now()
            )
            
            self.signals[timeframe] = signal
            self.data[timeframe] = df
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing {timeframe}: {e}")
            return None
    
    def analyze_all_timeframes(self) -> Dict[str, TimeframeSignal]:
        """Analyze all timeframes"""
        logger.info(f"🔍 Analyzing {self.symbol}...")
        
        for tf in ['daily', '1hour', '15min', '5min', '1min']:
            logger.info(f"  Analyzing {tf}...")
            self.analyze_timeframe(tf)
        
        logger.info(f"✅ Completed {len(self.signals)} timeframes")
        return self.signals
    
    def find_confluence_zones(self, tolerance: float = 0.5) -> List[ConfluenceZone]:
        """Find confluence zones"""
        all_levels = []
        
        for tf, signal in self.signals.items():
            for level in signal.support_levels:
                all_levels.append({'price': level, 'type': 'support', 'timeframe': tf})
            for level in signal.resistance_levels:
                all_levels.append({'price': level, 'type': 'resistance', 'timeframe': tf})
        
        if not all_levels:
            return []
        
        zones = []
        processed = set()
        
        for i, level1 in enumerate(all_levels):
            if i in processed:
                continue
            
            zone_levels = [level1]
            processed.add(i)
            
            for j, level2 in enumerate(all_levels):
                if j in processed or i == j:
                    continue
                
                price_diff = abs(level2['price'] - level1['price']) / level1['price'] * 100
                
                if price_diff <= tolerance:
                    zone_levels.append(level2)
                    processed.add(j)
            
            if len(zone_levels) >= 2:
                avg_price = np.mean([l['price'] for l in zone_levels])
                timeframes = [l['timeframe'] for l in zone_levels]
                types = [l['type'] for l in zone_levels]
                
                zone_type = 'support' if types.count('support') > types.count('resistance') else 'resistance'
                strength = len(zone_levels) / len(self.TIMEFRAMES) * 100
                
                zone = ConfluenceZone(
                    price_level=avg_price,
                    zone_type=zone_type,
                    strength=strength,
                    timeframes=timeframes,
                    indicators=['S/R']
                )
                zones.append(zone)
        
        zones.sort(key=lambda x: x.strength, reverse=True)
        self.confluence_zones = zones
        
        return zones
    
    def get_trading_bias(self) -> Dict:
        """Get trading bias"""
        if not self.signals:
            return {
                'bias': 'neutral',
                'confidence': 0,
                'bullish_timeframes': 0,
                'bearish_timeframes': 0,
                'total_timeframes': 0
            }
        
        bullish = sum(1 for s in self.signals.values() if s.trend == 'bullish')
        bearish = sum(1 for s in self.signals.values() if s.trend == 'bearish')
        
        weights = {'daily': 3, '1hour': 2, '15min': 1.5, '5min': 1, '1min': 0.5}
        
        weighted_bull = sum(
            weights.get(s.timeframe, 1) * s.strength 
            for s in self.signals.values() 
            if s.trend == 'bullish'
        )
        
        weighted_bear = sum(
            weights.get(s.timeframe, 1) * s.strength 
            for s in self.signals.values() 
            if s.trend == 'bearish'
        )
        
        total = weighted_bull + weighted_bear
        
        if total == 0:
            return {
                'bias': 'neutral',
                'confidence': 0,
                'bullish_timeframes': bullish,
                'bearish_timeframes': bearish,
                'total_timeframes': len(self.signals)
            }
        
        if weighted_bull > weighted_bear:
            bias = 'bullish'
            confidence = (weighted_bull / total) * 100
        else:
            bias = 'bearish'
            confidence = (weighted_bear / total) * 100
        
        return {
            'bias': bias,
            'confidence': round(confidence, 2),
            'bullish_timeframes': bullish,
            'bearish_timeframes': bearish,
            'total_timeframes': len(self.signals)
        }
    
    def generate_report(self) -> str:
        """Generate report"""
        report = []
        report.append("=" * 70)
        report.append(f"MULTI-TIMEFRAME ANALYSIS: {self.symbol}")
        report.append("=" * 70)
        
        bias = self.get_trading_bias()
        report.append(f"\n📊 OVERALL BIAS: {bias['bias'].upper()}")
        report.append(f"   Confidence: {bias['confidence']:.1f}%")
        report.append(f"   Bullish TFs: {bias['bullish_timeframes']}/{bias['total_timeframes']}")
        
        report.append(f"\n📈 TIMEFRAME SIGNALS:")
        report.append("-" * 70)
        
        for tf in ['daily', '1hour', '15min', '5min', '1min']:
            if tf in self.signals:
                s = self.signals[tf]
                emoji = "🟢" if s.trend == 'bullish' else "🔴" if s.trend == 'bearish' else "⚪"
                report.append(f"{emoji} {tf.upper():8s} | {s.trend:8s} | Strength: {s.strength:.0f}% | RSI: {s.key_indicators.get('rsi', 0):.1f}")
        
        if self.confluence_zones:
            report.append(f"\n🎯 CONFLUENCE ZONES:")
            report.append("-" * 70)
            for i, zone in enumerate(self.confluence_zones[:5], 1):
                report.append(f"{i}. ₹{zone.price_level:.2f} ({zone.zone_type.upper()}) - Strength: {zone.strength:.0f}%")
        
        report.append("=" * 70)
        return "\n".join(report)


if __name__ == "__main__":
    print("🚀 Running Multi-Timeframe Analysis...\n")
    
    analyzer = MultiTimeframeAnalyzer('NIFTY')
    signals = analyzer.analyze_all_timeframes()
    zones = analyzer.find_confluence_zones()
    
    print(analyzer.generate_report())
    
    bias = analyzer.get_trading_bias()
    print(f"\n💡 TRADING BIAS: {bias['bias'].upper()} ({bias['confidence']:.1f}% confidence)")
    print(f"📊 Confluence Zones Found: {len(zones)}")
