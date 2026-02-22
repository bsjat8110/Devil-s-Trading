"""
Machine Learning Signal Predictor
Uses ML to predict buy/sell signals
"""

import pandas as pd
import numpy as np
from typing import Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class SimpleMLPredictor:
    """
    Simple ML-based signal predictor
    """
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.classes_ = None
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create features for ML model
        """
        
        features = pd.DataFrame(index=df.index)
        
        # Price features
        features['returns'] = df['close'].pct_change()
        features['returns_5'] = df['close'].pct_change(5)
        features['returns_10'] = df['close'].pct_change(10)
        
        # Moving averages
        features['sma_10'] = df['close'].rolling(10).mean()
        features['sma_20'] = df['close'].rolling(20).mean()
        features['sma_50'] = df['close'].rolling(50).mean()
        
        # Price relative to MAs
        features['price_to_sma10'] = df['close'] / features['sma_10'] - 1
        features['price_to_sma20'] = df['close'] / features['sma_20'] - 1
        
        # Volatility
        features['volatility'] = df['close'].pct_change().rolling(20).std()
        
        # Volume
        features['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        # RSI-like indicator
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD-like
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        features['macd'] = ema12 - ema26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        
        return features.fillna(0)
    
    def create_labels(self, df: pd.DataFrame, forward_periods: int = 5, threshold: float = 0.02) -> pd.Series:
        """
        Create labels (1 for buy, 0 for sell)
        """
        
        future_returns = df['close'].pct_change(forward_periods).shift(-forward_periods)
        
        labels = pd.Series(index=df.index, dtype=int)
        labels[future_returns > threshold] = 1  # Buy signal
        labels[future_returns < -threshold] = 0  # Sell signal
        labels[(future_returns >= -threshold) & (future_returns <= threshold)] = 2  # Hold
        
        return labels
    
    def train(self, df: pd.DataFrame):
        """
        Train the ML model
        """
        
        logger.info("Training ML model...")
        
        # Create features and labels
        features = self.create_features(df)
        labels = self.create_labels(df)
        
        # Remove NaN rows
        valid_idx = ~(features.isna().any(axis=1) | labels.isna())
        X = features[valid_idx]
        y = labels[valid_idx]
        
        if len(X) < 50:
            logger.warning("Not enough data to train model")
            return
        
        # Train-test split (use last 20% for validation)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.classes_ = self.model.classes_
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        logger.info(f"Model trained successfully")
        logger.info(f"Train accuracy: {train_score:.2%}, Test accuracy: {test_score:.2%}")
        
        self.is_trained = True
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """
        Predict signal for current market
        """
        
        if not self.is_trained:
            logger.warning("Model not trained yet")
            return {
                'signal': 'NEUTRAL', 
                'confidence': 0, 
                'probability': 0,
                'probabilities': {'sell': 0, 'buy': 0, 'hold': 0}
            }
        
        # Create features for latest data
        features = self.create_features(df)
        latest_features = features.iloc[-1:].fillna(0)
        
        # Scale
        latest_scaled = self.scaler.transform(latest_features)
        
        # Predict
        prediction = self.model.predict(latest_scaled)[0]
        probabilities = self.model.predict_proba(latest_scaled)[0]
        
        # Map prediction to signal
        signal_map = {0: 'SELL', 1: 'BUY', 2: 'HOLD'}
        signal = signal_map.get(int(prediction), 'NEUTRAL')
        
        # Get confidence (max probability)
        confidence = float(np.max(probabilities)) * 100
        
        # FIXED: Handle variable number of classes
        # Build probabilities dict based on actual classes
        probs_dict = {'sell': 0.0, 'buy': 0.0, 'hold': 0.0}
        
        for i, class_label in enumerate(self.classes_):
            if i < len(probabilities):
                if class_label == 0:
                    probs_dict['sell'] = float(probabilities[i])
                elif class_label == 1:
                    probs_dict['buy'] = float(probabilities[i])
                elif class_label == 2:
                    probs_dict['hold'] = float(probabilities[i])
        
        # Get probability for predicted class
        pred_idx = int(prediction)
        class_position = list(self.classes_).index(pred_idx) if pred_idx in self.classes_ else 0
        probability = float(probabilities[class_position]) if class_position < len(probabilities) else 0.0
        
        return {
            'signal': signal,
            'confidence': round(confidence, 2),
            'probability': round(probability, 4),
            'probabilities': probs_dict
        }


if __name__ == "__main__":
    print("🤖 Testing ML Signal Predictor...\n")
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=500, freq='1D')
    
    # Create trending data
    trend = np.cumsum(np.random.randn(500) * 0.02 + 0.005)
    close = 100 * (1 + trend)
    
    sample_df = pd.DataFrame({
        'open': close * 0.99,
        'high': close * 1.02,
        'low': close * 0.98,
        'close': close,
        'volume': np.random.randint(100000, 500000, 500)
    }, index=dates)
    
    predictor = SimpleMLPredictor()
    
    # Train
    print("Training model...")
    predictor.train(sample_df)
    
    # Predict
    prediction = predictor.predict(sample_df)
    
    print("\n🤖 ML PREDICTION RESULTS:")
    print("=" * 60)
    print(f"Signal: {prediction['signal']}")
    print(f"Confidence: {prediction['confidence']:.1f}%")
    print(f"\nProbabilities:")
    print(f"   Buy:  {prediction['probabilities']['buy']*100:.1f}%")
    print(f"   Sell: {prediction['probabilities']['sell']*100:.1f}%")
    print(f"   Hold: {prediction['probabilities']['hold']*100:.1f}%")
