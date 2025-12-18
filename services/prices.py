import requests
from functools import lru_cache
import time

# CoinGecko API (free, no key required)
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Cache prices for 5 minutes
_price_cache = {}
_cache_time = {}
CACHE_DURATION = 300  # 5 minutes


def get_token_prices(token_ids=None, vs_currency='usd'):
    """
    Get current prices for tokens from CoinGecko.
    token_ids: list of CoinGecko token IDs or None for major tokens
    """
    cache_key = f"{','.join(token_ids or ['ethereum'])}-{vs_currency}"

    # Check cache
    if cache_key in _price_cache:
        if time.time() - _cache_time.get(cache_key, 0) < CACHE_DURATION:
            return _price_cache[cache_key]

    if token_ids is None:
        token_ids = ['ethereum', 'bitcoin', 'tether', 'usd-coin', 'binancecoin', 'matic-network']

    try:
        url = f"{COINGECKO_API}/simple/price"
        params = {
            'ids': ','.join(token_ids),
            'vs_currencies': vs_currency,
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Cache the result
        _price_cache[cache_key] = data
        _cache_time[cache_key] = time.time()

        return data
    except Exception as e:
        print(f"Price API error: {e}")
        return {}


def get_eth_price():
    """Get current ETH price in USD."""
    prices = get_token_prices(['ethereum'])
    return prices.get('ethereum', {}).get('usd', 0)


def get_native_price(chain_id):
    """Get native token price for a chain."""
    chain_tokens = {
        'ethereum': 'ethereum',
        'bsc': 'binancecoin',
        'polygon': 'matic-network',
        'arbitrum': 'ethereum'  # Arbitrum uses ETH
    }
    token_id = chain_tokens.get(chain_id, 'ethereum')
    prices = get_token_prices([token_id])
    return prices.get(token_id, {}).get('usd', 0)


# Token symbol to CoinGecko ID mapping (common tokens)
TOKEN_COINGECKO_MAP = {
    'ETH': 'ethereum',
    'WETH': 'weth',
    'BTC': 'bitcoin',
    'WBTC': 'wrapped-bitcoin',
    'USDT': 'tether',
    'USDC': 'usd-coin',
    'DAI': 'dai',
    'BNB': 'binancecoin',
    'MATIC': 'matic-network',
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'AAVE': 'aave',
    'CRV': 'curve-dao-token',
    'MKR': 'maker',
    'COMP': 'compound-governance-token',
    'SNX': 'havven',
    'SUSHI': 'sushi',
    'YFI': 'yearn-finance',
    'LDO': 'lido-dao',
    'RPL': 'rocket-pool',
    'ENS': 'ethereum-name-service',
    'APE': 'apecoin',
    'SHIB': 'shiba-inu',
    'PEPE': 'pepe',
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'BLUR': 'blur',
    'GRT': 'the-graph',
    'IMX': 'immutable-x',
    'FXS': 'frax-share',
    'FRAX': 'frax',
    'LUSD': 'liquity-usd',
    'BUSD': 'binance-usd',
    'TUSD': 'true-usd',
    'GUSD': 'gemini-dollar',
    'USDP': 'paxos-standard',
    'stETH': 'staked-ether',
    'rETH': 'rocket-pool-eth',
    'cbETH': 'coinbase-wrapped-staked-eth'
}


def get_token_price_by_symbol(symbol):
    """Get token price by symbol."""
    symbol_upper = symbol.upper()
    coingecko_id = TOKEN_COINGECKO_MAP.get(symbol_upper)

    if not coingecko_id:
        return None

    prices = get_token_prices([coingecko_id])
    return prices.get(coingecko_id, {}).get('usd')


def get_multiple_token_prices(symbols):
    """Get prices for multiple tokens by their symbols."""
    coingecko_ids = []
    symbol_to_id = {}

    for symbol in symbols:
        symbol_upper = symbol.upper()
        coingecko_id = TOKEN_COINGECKO_MAP.get(symbol_upper)
        if coingecko_id:
            coingecko_ids.append(coingecko_id)
            symbol_to_id[symbol_upper] = coingecko_id

    if not coingecko_ids:
        return {}

    prices_data = get_token_prices(list(set(coingecko_ids)))

    result = {}
    for symbol, cg_id in symbol_to_id.items():
        if cg_id in prices_data:
            result[symbol] = prices_data[cg_id].get('usd', 0)

    return result


def get_gas_prices():
    """Get current gas prices from Etherscan-like API."""
    # This would be called from blockchain service with proper API
    return {
        'low': 0,
        'average': 0,
        'high': 0,
        'base_fee': 0
    }
