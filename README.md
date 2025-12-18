# Crypto Explorer

A comprehensive multi-chain blockchain address explorer with advanced analytics, link analysis, and trading intelligence features. Built with Flask and powered by Etherscan APIs.

## Features

### Core Features
- **Multi-Chain Support** - Ethereum, BSC, Polygon, Arbitrum, Base, Optimism
- **Address Search** - Search any address across supported chains
- **Balance & Tokens** - View native balance + ERC-20 token holdings with USD values
- **Transaction History** - Complete transaction history with decoded function calls
- **NFT Holdings** - View NFT collections and transfers
- **Link Analysis** - Interactive D3.js graph showing address relationships

### Analytics Dashboard
- **Wallet Score/Reputation** - 0-100 score based on wallet age, activity, DeFi usage
- **Activity Heatmap** - GitHub-style activity visualization
- **Token Distribution** - Pie chart of token holdings
- **Hourly Activity Chart** - Transaction patterns by hour
- **P&L Calculator** - Profit/Loss tracking using FIFO method
- **MEV Exposure** - Detect sandwich attacks and MEV bot interactions

### Advanced Analytics
- **Wallet Profiler** - Classify wallets as Whale, Trader, Hodler, DeFi Degen, NFT Collector, Bot, etc.
- **Whale Tracker** - Monitor large transactions and whale activity patterns
- **Flash Loan Detection** - Identify flash loans and arbitrage transactions
- **Token Sniper Detection** - Detect early buyers and sniper bot activity
- **Copy Trading Signals** - Analyze wallet performance and generate trading signals
- **Funding Flow** - Trace money movement with suspicious pattern detection
- **Liquidity Pool Tracker** - Track LP positions across DEXs
- **Governance Participation** - DAO voting history and governance token holdings

### Security & Compliance
- **Contract Security Scanner** - Basic security checks for smart contracts
- **Token Approval Scanner** - Track and assess risk of token approvals
- **Tax Report Generator** - Generate tax-ready reports with CSV export
- **Address Clustering** - Detect related addresses and sybil patterns

### Additional Features
- **Gas Optimizer** - Historical gas analysis and optimization tips
- **Airdrop Checker** - Check claimed airdrops and estimate eligibility
- **ENS Integration** - Detect ENS transactions and owned names
- **Smart Money Tracker** - Identify interactions with known smart money wallets
- **Portfolio Tracker** - Track multiple addresses
- **Address Comparison** - Compare multiple wallets side by side
- **Watchlist** - Save addresses to localStorage
- **Address Notes** - Add private notes to addresses

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/etherscan_explorer.git
cd etherscan_explorer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file with your API keys:
```env
ETHERSCAN_API_KEY=your_etherscan_api_key
BSCSCAN_API_KEY=your_bscscan_api_key
POLYGONSCAN_API_KEY=your_polygonscan_api_key
ARBISCAN_API_KEY=your_arbiscan_api_key
BASESCAN_API_KEY=your_basescan_api_key
OPTIMISM_API_KEY=your_optimism_api_key
```

4. Run the application:
```bash
python app.py
```

5. Open http://localhost:5001 in your browser

## API Endpoints

### Core APIs
| Endpoint | Description |
|----------|-------------|
| `GET /api/graph/<chain>/<address>` | Get D3.js graph data for link analysis |
| `GET /api/gas/<chain>` | Get current gas prices |
| `GET /api/tx-summary/<chain>/<address>` | Get transaction type breakdown |

### Analytics APIs
| Endpoint | Description |
|----------|-------------|
| `GET /api/analytics/<chain>/<address>` | Activity heatmap, hourly stats, token distribution |
| `GET /api/reputation/<chain>/<address>` | Wallet score and badges |
| `GET /api/pnl/<chain>/<address>` | Profit/Loss calculations |
| `GET /api/mev/<chain>/<address>` | MEV exposure analysis |
| `GET /api/approvals/<chain>/<address>` | Token approval scanner |

### Advanced APIs
| Endpoint | Description |
|----------|-------------|
| `GET /api/wallet-profile/<chain>/<address>` | Wallet classification and behavior analysis |
| `GET /api/whale-tracker/<chain>/<address>` | Whale transaction tracking |
| `GET /api/flash-loans/<chain>/<address>` | Flash loan detection |
| `GET /api/sniper-detection/<chain>/<address>` | Token sniper detection |
| `GET /api/copy-trading/<chain>/<address>` | Copy trading analysis |
| `GET /api/funding-flow/<chain>/<address>` | Fund flow tracing |
| `GET /api/liquidity-pools/<chain>/<address>` | LP position tracking |
| `GET /api/governance/<chain>/<address>` | Governance participation |
| `GET /api/tax-report/<chain>/<address>` | Tax report generation |
| `GET /api/tax-report/<chain>/<address>/export` | Export tax report as CSV |

### Other APIs
| Endpoint | Description |
|----------|-------------|
| `GET /api/clustering/<chain>/<address>` | Related address detection |
| `GET /api/smartmoney/<chain>/<address>` | Smart money interactions |
| `GET /api/airdrops/<chain>/<address>` | Airdrop eligibility |
| `GET /api/gas-optimizer/<chain>/<address>` | Gas optimization analysis |
| `GET /api/ens/<chain>/<address>` | ENS activity |
| `GET /api/security-scan/<chain>/<address>` | Contract security scan |

## Project Structure

```
etherscan_explorer/
├── app.py                      # Flask application
├── config.py                   # Chain configuration
├── requirements.txt            # Dependencies
├── .env                        # API keys (create this)
├── services/
│   ├── blockchain.py           # Multi-chain API client
│   ├── analyzer.py             # Link analysis
│   ├── prices.py               # Token prices
│   ├── labels.py               # Address labels
│   ├── decoder.py              # Transaction decoder
│   ├── defi.py                 # DeFi position detection
│   ├── approvals.py            # Token approval scanner
│   ├── pnl.py                  # P&L calculator
│   ├── clustering.py           # Address clustering
│   ├── mev.py                  # MEV detection
│   ├── analytics.py            # Activity analytics
│   ├── reputation.py           # Wallet scoring
│   ├── airdrops.py             # Airdrop checker
│   ├── gas_optimizer.py        # Gas optimization
│   ├── ens.py                  # ENS integration
│   ├── smartmoney.py           # Smart money tracking
│   ├── whale_tracker.py        # Whale tracking
│   ├── flash_loans.py          # Flash loan detection
│   ├── token_sniper.py         # Sniper detection
│   ├── security_scanner.py     # Contract security
│   ├── copy_trading.py         # Copy trading
│   ├── tax_report.py           # Tax reports
│   ├── funding_flow.py         # Funding flow
│   ├── liquidity_tracker.py    # LP tracking
│   ├── governance.py           # Governance
│   └── wallet_profiler.py      # Wallet profiling
├── templates/
│   ├── base.html               # Base template
│   ├── index.html              # Homepage
│   ├── address.html            # Address details
│   ├── analytics.html          # Analytics dashboard
│   ├── advanced.html           # Advanced analytics
│   ├── portfolio.html          # Portfolio tracker
│   └── compare.html            # Address comparison
└── static/
    ├── css/
    │   └── style.css           # Custom styles
    └── js/
        └── graph.js            # D3.js visualization
```

## Tech Stack

- **Backend**: Flask, Python 3.8+
- **Frontend**: Bootstrap 5, D3.js, Chart.js
- **APIs**: Etherscan V2 API (and compatible APIs)
- **Storage**: localStorage (client-side)

## Supported Chains

| Chain | Chain ID | Explorer |
|-------|----------|----------|
| Ethereum | 1 | etherscan.io |
| BSC | 56 | bscscan.com |
| Polygon | 137 | polygonscan.com |
| Arbitrum | 42161 | arbiscan.io |
| Base | 8453 | basescan.org |
| Optimism | 10 | optimistic.etherscan.io |

## Getting API Keys

1. **Etherscan**: https://etherscan.io/apis
2. **BSCScan**: https://bscscan.com/apis
3. **PolygonScan**: https://polygonscan.com/apis
4. **Arbiscan**: https://arbiscan.io/apis
5. **BaseScan**: https://basescan.org/apis
6. **Optimism**: https://optimistic.etherscan.io/apis

Free tier API keys are sufficient for basic usage.

## Usage Examples

### Search an Address
Navigate to the homepage and enter an address with the selected chain.

### View Analytics
1. Go to `/analytics`
2. Enter an address
3. Click "Analyze" to see wallet score, activity heatmap, P&L, and more

### Advanced Analysis
1. Go to `/advanced`
2. Enter an address
3. Click "Full Analysis" for comprehensive wallet profiling including:
   - Wallet classification (Whale, Trader, Hodler, etc.)
   - Flash loan/arbitrage detection
   - Copy trading signals
   - Tax report generation

### Export Tax Report
1. Run analysis on `/advanced`
2. Select year filter
3. Click "Export CSV" to download tax-ready report

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Disclaimer

This tool is for informational purposes only. Always verify data independently before making financial decisions. The tax report feature is not financial advice - consult a tax professional for your specific situation.
