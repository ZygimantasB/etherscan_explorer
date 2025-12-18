import os
from dotenv import load_dotenv

load_dotenv()

# Chain configurations with their respective API endpoints and keys
CHAINS = {
    'ethereum': {
        'name': 'Ethereum',
        'api_url': 'https://api.etherscan.io/api',
        'api_key': os.getenv('ETHERSCAN_API_KEY', ''),
        'explorer_url': 'https://etherscan.io',
        'symbol': 'ETH',
        'decimals': 18
    },
    'bsc': {
        'name': 'BNB Smart Chain',
        'api_url': 'https://api.bscscan.com/api',
        'api_key': os.getenv('BSCSCAN_API_KEY', ''),
        'explorer_url': 'https://bscscan.com',
        'symbol': 'BNB',
        'decimals': 18
    },
    'polygon': {
        'name': 'Polygon',
        'api_url': 'https://api.polygonscan.com/api',
        'api_key': os.getenv('POLYGONSCAN_API_KEY', ''),
        'explorer_url': 'https://polygonscan.com',
        'symbol': 'MATIC',
        'decimals': 18
    },
    'arbitrum': {
        'name': 'Arbitrum One',
        'api_url': 'https://api.arbiscan.io/api',
        'api_key': os.getenv('ARBISCAN_API_KEY', ''),
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
