"""
Automated Trading Bot
Runs every 15 minutes and executes trades automatically
"""

from master_system import DevilTradingMasterSystem
import schedule
import time
from datetime import datetime

# Initialize system
system = DevilTradingMasterSystem(total_capital=500000)

# Setup strategies
system.portfolio.add_strategy("EMA Crossover", allocation_pct=30, max_positions=2)
system.portfolio.add_strategy("RSI Reversal", allocation_pct=25, max_positions=3)
system.portfolio.add_strategy("Bollinger Breakout", allocation_pct=25, max_positions=2)
system.portfolio.add_strategy("MACD Momentum", allocation_pct=20, max_positions=2)

print("✅ Portfolio setup complete")


def trade():
    """Execute trading logic"""
    print(f"\n{'='*80}")
    print(f"🤖 AUTO TRADING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Analyze market
        analysis = system.analyze_market('NIFTY')
        
        consensus = analysis['strategy_consensus']
        current_price = analysis['current_price']
        
        print(f"📊 Current Price: ₹{current_price:.2f}")
        print(f"📊 Consensus: {consensus['consensus']}")
        print(f"📊 Agreement: {consensus['agreement']:.1f}%")
        
        # Trading logic - only trade if strong signal
        if consensus['agreement'] > 75:
            
            if consensus['consensus'] == 'BUY':
                print(f"\n✅ STRONG BUY SIGNAL - Agreement: {consensus['agreement']:.1f}%")
                
                # Check if we can open position
                if system.portfolio.can_open_position('EMA Crossover'):
                    
                    # Calculate position size
                    quantity = system.portfolio.calculate_position_size(
                        'EMA Crossover',
                        current_price,
                        consensus['stop_loss']
                    )
                    
                    if quantity > 0:
                        # Execute trade
                        position_id = system.execute_strategy(
                            symbol='NIFTY',
                            strategy_name='EMA Crossover',
                            signal_type='BUY',
                            quantity=quantity,
                            entry_price=current_price,
                            stop_loss=consensus['stop_loss'],
                            target=consensus['target']
                        )
                        
                        if position_id:
                            print(f"✅ Position opened: {position_id}")
                            print(f"   Quantity: {quantity}")
                            print(f"   Entry: ₹{current_price:.2f}")
                            print(f"   SL: ₹{consensus['stop_loss']:.2f}")
                            print(f"   Target: ₹{consensus['target']:.2f}")
                        else:
                            print("⚠️  Failed to open position")
                    else:
                        print("⚠️  Position size too small")
                else:
                    print("⚠️  Cannot open position (max positions reached)")
            
            elif consensus['consensus'] == 'SELL':
                print(f"\n🔴 STRONG SELL SIGNAL - Agreement: {consensus['agreement']:.1f}%")
                print("ℹ️  Sell logic not implemented (add your logic here)")
            
            else:
                print(f"\n⚪ NEUTRAL SIGNAL")
        
        else:
            print(f"\n⚪ No strong signal - Agreement only {consensus['agreement']:.1f}%")
            print("   Waiting for stronger setup...")
        
        # Check stop loss/targets
        print("\n🎯 Checking stop loss and targets...")
        to_close = system.portfolio.check_stop_loss_targets()
        
        if to_close:
            for position_id, price, reason in to_close:
                pnl = system.portfolio.close_position(position_id, price, reason)
                print(f"🎯 {reason} hit - Position closed")
                print(f"   P&L: ₹{pnl:,.2f}")
        else:
            print("   No SL/Target hits")
        
        # Portfolio summary
        print("\n💼 Portfolio Summary:")
        summary = system.portfolio.get_portfolio_summary()
        print(f"   Total P&L: ₹{summary['total_pnl']:,.2f} ({summary['total_return_pct']:.2f}%)")
        print(f"   Active Positions: {summary['active_positions']}")
        print(f"   Available Capital: ₹{summary['available_capital']:,.2f}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


def morning_routine():
    """Run at market open"""
    print("\n" + "🌅" * 40)
    print("MORNING ROUTINE - MARKET OPEN")
    print("🌅" * 40 + "\n")
    trade()


def evening_routine():
    """Run before market close"""
    print("\n" + "🌆" * 40)
    print("EVENING ROUTINE - BEFORE MARKET CLOSE")
    print("🌆" * 40 + "\n")
    trade()
    
    # Daily report
    print("\n" + system.portfolio.generate_report())


# Schedule jobs
schedule.every(15).minutes.do(trade)              # Every 15 minutes
schedule.every().day.at("09:20").do(morning_routine)  # Market open
schedule.every().day.at("15:20").do(evening_routine)  # Before market close

print("\n" + "🤖" * 40)
print("AUTO TRADER STARTED")
print("🤖" * 40)
print("\n📅 Schedule:")
print("   • Every 15 minutes: Trade check")
print("   • 09:20 AM: Morning routine")
print("   • 03:20 PM: Evening routine")
print("\n⚠️  Press Ctrl+C to stop\n")

# Run first trade immediately
print("Running initial trade check...")
trade()

# Main loop
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n🛑 AUTO TRADER STOPPED")
    print("Final Portfolio Status:")
    print(system.portfolio.generate_report())
