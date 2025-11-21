# Risk Management Dashboard

A Streamlit web-based dashboard for monitoring your Hyperliquid wallet, open positions, and trade history.

## Features

- 📊 **Real-time Account Balance**: View total, free, and used USDC balance
- 📈 **Open Positions**: Monitor all active positions with detailed metrics
- 📜 **Trade History**: View trades from the last 2 days (configurable) with OID and closed PnL
- 🔄 **Auto-refresh**: Optional automatic data refresh every 60 seconds
- 🎨 **Modern UI**: Clean, responsive interface built with Streamlit

## Installation

1. Install required packages:
```bash
pip install -r requirements_dashboard.txt
```

## Running the Dashboard

1. Start the Streamlit app:
```bash
streamlit run risk_management_dashboard.py
```

2. The dashboard will open in your default web browser at `http://localhost:8501`

## Dashboard Sections

### Account Balance
- Total balance in USDC
- Free balance available for trading
- Used margin
- Margin usage progress bar

### Open Positions
- Summary metrics (total positions, total unrealized PnL, total notional)
- Detailed positions table with:
  - Symbol and side (LONG/SHORT)
  - Position size
  - Entry and mark prices
  - Notional value
  - Unrealized PnL (dollar and percentage)
- Expandable position details

### Trade History
- Configurable time period (1-7 days)
- Trade table with:
  - Timestamp
  - Symbol and side
  - Order ID (OID)
  - Amount and price
  - Cost and fees
  - Closed PnL
- Filter by symbol and side
- Trade statistics (total closed PnL, fees, net PnL)

## Configuration

Edit the `RISK_MGMT_CONFIG` dictionary in `risk_management_dashboard.py` to:
- Update wallet address
- Change network (testnet/mainnet)
- Adjust trade history days

## Notes

- The dashboard uses the same `RiskManagementClient` class as the notebook version
- Data is fetched directly from Hyperliquid via CCXT
- All sensitive information (private keys) should be kept secure
- The dashboard auto-refreshes when enabled in the sidebar

