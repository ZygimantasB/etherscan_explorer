import os
from dotenv import load_dotenv

load_dotenv()

# Etherscan V2 API base URL (supports all chains with chainid parameter)
ETHERSCAN_V2_API = 'https://api.etherscan.io/v2/api'

# Chain configurations with their respective chain IDs for V2 API
CHAINS = {
    'ethereum': {
        'name': 'Ethereum',
        'chain_id': 1,
        'api_key': os.getenv('ETHERSCAN_API_KEY', ''),
        'explorer_url': 'https://etherscan.io',
        'symbol': 'ETH',
        'decimals': 18
    },
    'bsc': {
        'name': 'BNB Smart Chain',
        'chain_id': 56,
        'api_key': os.getenv('ETHERSCAN_API_KEY', ''),  # V2 API uses same key for all chains
        'explorer_url': 'https://bscscan.com',
        'symbol': 'BNB',
        'decimals': 18
    },
    'polygon': {
        'name': 'Polygon',
        'chain_id': 137,
        'api_key': os.getenv('ETHERSCAN_API_KEY', ''),  # V2 API uses same key for all chains
        'explorer_url': 'https://polygonscan.com',
        'symbol': 'POL',
        'decimals': 18
    },
    'arbitrum': {
        'name': 'Arbitrum One',
        'chain_id': 42161,
        'api_key': os.getenv('ETHERSCAN_API_KEY', ''),  # V2 API uses same key for all chains
        'explorer_url': 'https://arbiscan.io',
        'symbol': 'ETH',
        'decimals': 18
    }
}

def get_chain_config(chain_id):
    """Get configuration for a specific chain."""
    return CHAINS.get(chain_id.lower())

def get_all_chains():
    """Get list of all supported chains."""
    return [{'id': k, **v} for k, v in CHAINS.items()]
