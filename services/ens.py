# ENS (Ethereum Name Service) Integration
# Resolve ENS names and detect ENS ownership

import requests

# ENS Registry contract
ENS_REGISTRY = '0x00000000000c2e074ec69a0dfb2997ba6c7d2e1e'

# ENS Registrar Controller
ENS_REGISTRAR = '0x253553366da8546fc250f225fe3d25d0c782303b'

# Common ENS function selectors
ENS_SELECTORS = {
    '0xf14fcbc8': 'commit',
    '0x85f6d155': 'register',
    '0xacf1a841': 'renew',
    '0x1896f70a': 'setResolver',
    '0x3b3b57de': 'addr',  # Resolve address
}


def detect_ens_transactions(transactions):
    """
    Detect ENS-related transactions.
    Returns list of ENS operations.
    """
    ens_operations = []

    for tx in transactions:
        to_addr = tx.get('to', '').lower()
        input_data = tx.get('input', '')

        # Check if interacting with ENS contracts
        if to_addr == ENS_REGISTRY.lower() or to_addr == ENS_REGISTRAR.lower():
            selector = input_data[:10] if input_data else ''
            operation = ENS_SELECTORS.get(selector, 'Unknown ENS operation')

            ens_operations.append({
                'tx_hash': tx.get('hash', ''),
                'operation': operation,
                'timestamp': tx.get('timestamp', 0),
                'value': tx.get('value', 0),
                'gas_used': tx.get('gas_used', 0)
            })

    return ens_operations


def extract_ens_names_from_transfers(token_transfers):
    """
    Look for ENS NFT transfers (ERC-721) to detect owned names.
    ENS names are NFTs in the ENS BaseRegistrar contract.
    """
    ENS_BASE_REGISTRAR = '0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85'

    ens_tokens = []

    for transfer in token_transfers:
        contract = transfer.get('contract_address', '').lower()
        if contract == ENS_BASE_REGISTRAR.lower():
            # This is an ENS name NFT
            # The token ID is the labelhash of the name
            ens_tokens.append({
                'token_id': transfer.get('token_id', ''),
                'direction': transfer.get('direction', ''),
                'timestamp': transfer.get('timestamp', 0),
                'tx_hash': transfer.get('hash', '')
            })

    return ens_tokens


def get_ens_summary(ens_operations, ens_tokens, direction_filter='in'):
    """
    Generate ENS activity summary.
    """
    # Count incoming ENS tokens (names owned)
    owned_count = sum(1 for t in ens_tokens if t['direction'] == direction_filter)

    # Count operations
    registrations = sum(1 for op in ens_operations if 'register' in op['operation'].lower())
    renewals = sum(1 for op in ens_operations if 'renew' in op['operation'].lower())

    return {
        'names_owned': owned_count,
        'total_operations': len(ens_operations),
        'registrations': registrations,
        'renewals': renewals,
        'total_spent': sum(op['value'] for op in ens_operations)
    }


# Note: For actual ENS name resolution, you would need to:
# 1. Use web3.py with an ENS resolver
# 2. Or call the ENS resolver contract directly
# 3. Or use a service like The Graph

def format_ens_display(address, ens_name=None):
    """
    Format address with ENS name if available.
    """
    if ens_name:
        return f"{ens_name} ({address[:6]}...{address[-4:]})"
    return f"{address[:6]}...{address[-4:]}"
