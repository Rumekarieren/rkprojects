# =============================================================================
# STREAMLIT DASHBOARD: RISK MANAGEMENT & WALLET MONITORING SYSTEM
# =============================================================================
# A web-based dashboard for monitoring Hyperliquid wallet, positions, and trades
# =============================================================================

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import ccxt
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

# =============================================================================
# CONFIGURATION
# =============================================================================
# Configuration is loaded from Streamlit secrets (secrets.toml)
# For local development, create a .streamlit/secrets.toml file
# For Streamlit Cloud, add secrets via the dashboard settings
# =============================================================================

def get_config():
    """Load configuration from Streamlit secrets or use defaults"""
    try:
        # Try to load from Streamlit secrets
        secrets = st.secrets["risk_management"]
        return {
            'wallet_address': secrets.get('wallet_address'),
            'private_key': secrets.get('private_key'),
            'testnet': secrets.get('testnet', False),
            'trade_history_days': secrets.get('trade_history_days', 2),
        }
    except (KeyError, AttributeError):
        # Fallback to environment variables or show error
        import os
        wallet_address = os.getenv('WALLET_ADDRESS')
        private_key = os.getenv('PRIVATE_KEY')
        
        if not wallet_address or not private_key:
            st.error("""
            ⚠️ **Configuration Error**
            
            Please set up your secrets in one of the following ways:
            
            **For Local Development:**
            1. Create a `.streamlit/secrets.toml` file
            2. Add your configuration (see `secrets.toml.example`)
            
            **For Streamlit Cloud:**
            1. Go to your app settings
            2. Click "Secrets" in the sidebar
            3. Add the secrets in TOML format
            """)
            st.stop()
        
        return {
            'wallet_address': wallet_address,
            'private_key': private_key,
            'testnet': os.getenv('TESTNET', 'False').lower() == 'true',
            'trade_history_days': int(os.getenv('TRADE_HISTORY_DAYS', '2')),
        }

RISK_MGMT_CONFIG = get_config()

# =============================================================================
# HYPERLIQUID CLIENT
# =============================================================================

class RiskManagementClient:
    """Independent Hyperliquid client for risk management monitoring"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Hyperliquid connection"""
        try:
            self.client = ccxt.hyperliquid({
                "walletAddress": self.config['wallet_address'],
                "privateKey": self.config['private_key'],
            })
        except Exception as e:
            st.error(f"Error initializing client: {e}")
            self.client = None
    
    def get_account_balance(self) -> Optional[Dict]:
        """Get account balance"""
        if not self.client:
            return None
        try:
            return self.client.fetch_balance()
        except Exception as e:
            st.error(f"Error fetching balance: {e}")
            return None
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        if not self.client:
            return []
        try:
            positions = self.client.fetch_positions()
            # Filter out positions with zero size
            active_positions = [pos for pos in positions if pos.get('contracts', 0) != 0]
            return active_positions
        except Exception as e:
            st.error(f"Error fetching positions: {e}")
            return []
    
    def get_trade_history(self, days: int = 2) -> List[Dict]:
        """Get trade history for the last N days"""
        if not self.client:
            return []
        try:
            # Calculate timestamp for N days ago
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            # Fetch all trades since the timestamp
            all_trades = []
            symbols = ['BTC/USDC:USDC', 'ETH/USDC:USDC', 'SOL/USDC:USDC', 
                      'XRP/USDC:USDC', 'AVAX/USDC:USDC']  # Common symbols
            
            for symbol in symbols:
                try:
                    trades = self.client.fetch_my_trades(symbol=symbol, since=since)
                    all_trades.extend(trades)
                except:
                    # Symbol might not exist or have no trades
                    continue
            
            # Sort by timestamp (newest first)
            all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return all_trades
        except Exception as e:
            st.error(f"Error fetching trade history: {e}")
            return []

# =============================================================================
# STREAMLIT APP
# =============================================================================

# Page configuration
st.set_page_config(
    page_title="Risk Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .positive-pnl {
        color: #00cc00;
        font-weight: bold;
    }
    .negative-pnl {
        color: #ff0000;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = RiskManagementClient(RISK_MGMT_CONFIG)

# Update last_update timestamp on every refresh (including auto-refresh)
st.session_state.last_update = datetime.now()

# Header
st.markdown('<div class="main-header">📊 Risk Management & Wallet Monitor</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.write(f"**Wallet:** `{RISK_MGMT_CONFIG['wallet_address'][:10]}...`")
    st.write(f"**Network:** {'TESTNET' if RISK_MGMT_CONFIG['testnet'] else 'MAINNET'}")
    
    st.header("🔄 Refresh")
    if st.button("🔄 Refresh Now", type="primary"):
        st.rerun()
    
    st.info("🔄 Auto-refresh: **Enabled** (60s)")
    
    st.header("📅 Settings")
    trade_history_days = st.slider("Trade History Days", 1, 7, RISK_MGMT_CONFIG['trade_history_days'])

# Main content
client = st.session_state.client

# Last update time
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.info(f"🕐 Last Update: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# Account Balance Section
st.header("💰 Account Balance")
balance = client.get_account_balance()

if balance and 'USDC' in balance:
    usdc = balance['USDC']
    if isinstance(usdc, dict):
        total = usdc.get('total', 0)
        free = usdc.get('free', 0)
        used = usdc.get('used', 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Balance", f"${total:,.2f}")
        with col2:
            st.metric("Free Balance", f"${free:,.2f}")
        with col3:
            st.metric("Used Margin", f"${used:,.2f}")
        
        # Progress bar for used margin
        if total > 0:
            usage_percent = (used / total) * 100
            st.progress(usage_percent / 100, text=f"Margin Usage: {usage_percent:.1f}%")
else:
    st.warning("Unable to fetch account balance")

# Open Positions Section
st.header("📈 Open Positions")
positions = client.get_open_positions()

if positions:
    total_unrealized_pnl = sum(pos.get('unrealizedPnl', 0) for pos in positions)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Positions", len(positions))
    with col2:
        pnl_color = "positive-pnl" if total_unrealized_pnl >= 0 else "negative-pnl"
        st.markdown(f"<div class='{pnl_color}'>Total Unrealized PnL: ${total_unrealized_pnl:,.2f}</div>", unsafe_allow_html=True)
    with col3:
        total_notional = sum(pos.get('notional', 0) for pos in positions)
        st.metric("Total Notional", f"${total_notional:,.2f}")
    
    # Positions table
    positions_data = []
    for pos in positions:
        symbol = pos.get('symbol', 'N/A')
        contracts = pos.get('contracts', 0)
        side = pos.get('side', 'N/A')
        entry_price = pos.get('entryPrice', 0)
        mark_price = pos.get('markPrice', 0)
        notional = pos.get('notional', 0)
        unrealized_pnl = pos.get('unrealizedPnl', 0)
        percentage = pos.get('percentage', 0)
        
        positions_data.append({
            'Symbol': symbol,
            'Side': side.upper(),
            'Size': f"{abs(contracts):.6f}",
            'Entry Price': f"${entry_price:,.2f}",
            'Mark Price': f"${mark_price:,.2f}",
            'Notional': f"${notional:,.2f}",
            'Unrealized PnL': f"${unrealized_pnl:,.2f}",
            'PnL %': f"{percentage:.2f}%"
        })
    
    df_positions = pd.DataFrame(positions_data)
    st.dataframe(df_positions, use_container_width=True, hide_index=True)
    
    # Individual position details
    with st.expander("📋 Position Details"):
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            contracts = pos.get('contracts', 0)
            side = pos.get('side', 'N/A')
            entry_price = pos.get('entryPrice', 0)
            mark_price = pos.get('markPrice', 0)
            notional = pos.get('notional', 0)
            unrealized_pnl = pos.get('unrealizedPnl', 0)
            percentage = pos.get('percentage', 0)
            
            pnl_color = "🟢" if unrealized_pnl >= 0 else "🔴"
            
            st.markdown(f"""
            **{symbol}** ({side.upper()})
            - Size: {abs(contracts):.6f} contracts
            - Entry: ${entry_price:,.2f} | Mark: ${mark_price:,.2f}
            - Notional: ${notional:,.2f}
            - {pnl_color} PnL: ${unrealized_pnl:,.2f} ({percentage:.2f}%)
            """)
else:
    st.info("No open positions")

# Trade History Section
st.header("📜 Trade History")
trades = client.get_trade_history(days=trade_history_days)

if trades:
    st.metric("Total Trades", len(trades))
    
    # Prepare trade data for table
    trades_data = []
    for trade in trades:
        symbol = trade.get('symbol', 'N/A')
        side = trade.get('side', 'N/A')
        amount = trade.get('amount', 0)
        price = trade.get('price', 0)
        cost = trade.get('cost', 0)
        fee = trade.get('fee', {})
        fee_cost = fee.get('cost', 0) if isinstance(fee, dict) else 0
        
        # Get closedPnl and oid from the nested 'info' dictionary
        info = trade.get('info', {})
        closed_pnl = info.get('closedPnl', None)
        if closed_pnl is None:
            closed_pnl = 0.0
        else:
            closed_pnl = float(closed_pnl)
        
        order_id = info.get('oid', None)
        if order_id is None:
            order_id = 'N/A'
        else:
            order_id = str(order_id)
        
        timestamp = trade.get('timestamp', 0)
        dt = datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now()
        
        trades_data.append({
            'Time': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'Symbol': symbol,
            'Side': side.upper(),
            'OID': order_id,
            'Amount': f"{amount:.6f}",
            'Price': f"${price:,.2f}",
            'Cost': f"${cost:,.2f}",
            'Fee': f"${fee_cost:.4f}",
            'Closed PnL': f"${closed_pnl:,.2f}"
        })
    
    df_trades = pd.DataFrame(trades_data)
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_symbol = st.selectbox("Filter by Symbol", ["All"] + list(df_trades['Symbol'].unique()))
    with col2:
        filter_side = st.selectbox("Filter by Side", ["All", "BUY", "SELL"])
    
    # Apply filters
    filtered_df = df_trades.copy()
    if filter_symbol != "All":
        filtered_df = filtered_df[filtered_df['Symbol'] == filter_symbol]
    if filter_side != "All":
        filtered_df = filtered_df[filtered_df['Side'] == filter_side]
    
    # Display table
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    # Summary statistics
    with st.expander("📊 Trade Statistics"):
        if len(filtered_df) > 0:
            total_closed_pnl = sum(float(pnl.replace('$', '').replace(',', '')) for pnl in filtered_df['Closed PnL'])
            total_fees = sum(float(fee.replace('$', '').replace(',', '')) for fee in filtered_df['Fee'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Closed PnL", f"${total_closed_pnl:,.2f}")
            with col2:
                st.metric("Total Fees", f"${total_fees:,.4f}")
            with col3:
                net_pnl = total_closed_pnl - total_fees
                st.metric("Net PnL", f"${net_pnl:,.2f}")
else:
    st.info(f"No trades in the last {trade_history_days} days")

# Footer
st.markdown("---")
st.markdown("**Risk Management Dashboard** | Built with Streamlit")

# Auto-refresh every 60 seconds (60000 milliseconds)
st_autorefresh(interval=60 * 1000, key="dataframerefresh")

