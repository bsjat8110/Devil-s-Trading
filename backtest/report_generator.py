"""
Backtest Report Generator
Creates HTML reports with interactive charts
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime


def generate_equity_curve_chart(equity_df: pd.DataFrame) -> go.Figure:
    """Generate equity curve chart"""
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=equity_df['timestamp'],
        y=equity_df['equity'],
        mode='lines',
        name='Equity',
        line=dict(color='#2E86DE', width=2)
    ))
    
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Date',
        yaxis_title='Capital (₹)',
        template='plotly_white',
        hovermode='x unified'
    )
    
    return fig


def generate_drawdown_chart(equity_df: pd.DataFrame) -> go.Figure:
    """Generate drawdown chart"""
    
    equity_df['peak'] = equity_df['equity'].cummax()
    equity_df['drawdown'] = ((equity_df['equity'] - equity_df['peak']) / equity_df['peak']) * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=equity_df['timestamp'],
        y=equity_df['drawdown'],
        fill='tozeroy',
        name='Drawdown',
        line=dict(color='#EE5A6F', width=2)
    ))
    
    fig.update_layout(
        title='Drawdown %',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        template='plotly_white'
    )
    
    return fig


def generate_html_report(results: dict, output_file: str = 'backtest_report.html'):
    """
    Generate complete HTML report
    
    Args:
        results: Backtest results dictionary
        output_file: Output HTML file path
    """
    
    equity_chart = generate_equity_curve_chart(results['equity_curve'])
    drawdown_chart = generate_drawdown_chart(results['equity_curve'])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Backtest Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2E86DE;
                border-bottom: 3px solid #2E86DE;
                padding-bottom: 10px;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .metric-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #2E86DE;
            }}
            .metric-label {{
                color: #666;
                font-size: 14px;
                margin-bottom: 5px;
            }}
            .metric-value {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }}
            .positive {{ color: #27AE60; }}
            .negative {{ color: #E74C3C; }}
            .chart {{
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Backtest Report</h1>
            <p>Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}</p>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-label">Initial Capital</div>
                    <div class="metric-value">₹{results['initial_capital']:,.0f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Final Capital</div>
                    <div class="metric-value {'positive' if results['final_capital'] > results['initial_capital'] else 'negative'}">
                        ₹{results['final_capital']:,.0f}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total P&L</div>
                    <div class="metric-value {'positive' if results['total_pnl'] > 0 else 'negative'}">
                        ₹{results['total_pnl']:+,.2f}
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{results['total_trades']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{results['win_rate']:.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value negative">₹{results['max_drawdown']:,.0f} ({results['max_drawdown_pct']:.1f}%)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{results['sharpe_ratio']:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Win</div>
                    <div class="metric-value positive">₹{results['avg_win']:,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Loss</div>
                    <div class="metric-value negative">₹{results['avg_loss']:,.2f}</div>
                </div>
            </div>
            
            <div class="chart" id="equity-chart"></div>
            <div class="chart" id="drawdown-chart"></div>
            
        </div>
        
        <script>
            {equity_chart.to_html(full_html=False, include_plotlyjs=False, div_id='equity-chart')}
            {drawdown_chart.to_html(full_html=False, include_plotlyjs=False, div_id='drawdown-chart')}
        </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ HTML report generated: {output_file}")


if __name__ == "__main__":
    print("📈 Report Generator ready")
