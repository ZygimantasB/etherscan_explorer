# Token Approval Scanner Service
# Detects ERC-20 token approvals and identifies risky unlimited approvals

from services.labels import get_address_label

# Known malicious spender addresses
MALICIOUS_SPENDERS = {
    '0x0000000000000000000000000000000000000000': 'Null Address',
}

# Maximum uint256 value (unlimited approval)
MAX_UINT256 = 2**256 - 1
UNLIMITED_THRESHOLD = 2**255  # Consider anything above this as "unlimited"


def parse_approval_data(input_data):
    """Parse approval transaction input data."""
    if not input_data or len(input_data) < 138:
        return None

    # approve(address,uint256) selector: 0x095ea7b3
    if not input_data.startswith('0x095ea7b3'):
        return None

    try:
        # Extract spender address (32 bytes, padded)
        spender = '0x' + input_data[34:74]
        # Extract amount (32 bytes)
        amount_hex = input_data[74:138]
        amount = int(amount_hex, 16)

        return {
            'spender': spender,
            'amount': amount,
            'is_unlimited': amount >= UNLIMITED_THRESHOLD
        }
    except:
        return None


def get_token_approvals(token_transfers, transactions):
    """
    Extract token approvals from transaction history.
    Returns list of active approvals with risk assessment.
    """
    approvals = {}

    for tx in transactions:
        input_data = tx.get('input', '')

        # Check if this is an approval transaction
        if input_data.startswith('0x095ea7b3'):
            approval = parse_approval_data(input_data)
            if approval:
                token_address = tx.get('to', '').lower()
                spender = approval['spender'].lower()

                key = f"{token_address}_{spender}"

                # Get token info from transfers if available
                token_info = None
                for transfer in token_transfers:
                    if transfer.get('contract_address', '').lower() == token_address:
                        token_info = {
                            'symbol': transfer.get('token_symbol', 'Unknown'),
                            'name': transfer.get('token_name', 'Unknown Token'),
                            'decimals': transfer.get('token_decimal', 18)
                        }
                        break

                approvals[key] = {
                    'token_address': token_address,
                    'token_symbol': token_info['symbol'] if token_info else 'Unknown',
                    'token_name': token_info['name'] if token_info else 'Unknown Token',
                    'spender': spender,
                    'spender_label': get_address_label(spender),
                    'amount': approval['amount'],
                    'is_unlimited': approval['is_unlimited'],
                    'tx_hash': tx.get('hash', ''),
                    'timestamp': tx.get('timestamp', 0),
                    'risk_level': assess_approval_risk(spender, approval['is_unlimited'])
                }

    return list(approvals.values())


def assess_approval_risk(spender, is_unlimited):
    """Assess the risk level of an approval."""
    spender_lower = spender.lower()

    # Check if known malicious
    if spender_lower in MALICIOUS_SPENDERS:
        return 'critical'

    # Check if known safe (exchanges, major DeFi)
    label = get_address_label(spender)
    if label:
        category = label.get('category', '')
        if category in ['exchange', 'defi', 'nft']:
            if is_unlimited:
                return 'medium'  # Known but unlimited
            return 'low'
        if category in ['mixer', 'scam']:
            return 'critical'

    # Unknown spender
    if is_unlimited:
        return 'high'

    return 'medium'


def get_approval_summary(approvals):
    """Generate summary of approvals."""
    summary = {
        'total': len(approvals),
        'unlimited': 0,
        'high_risk': 0,
        'medium_risk': 0,
        'low_risk': 0,
        'critical': 0,
        'unique_spenders': set(),
        'unique_tokens': set()
    }

    for approval in approvals:
        if approval['is_unlimited']:
            summary['unlimited'] += 1

        risk = approval['risk_level']
        if risk == 'critical':
            summary['critical'] += 1
        elif risk == 'high':
            summary['high_risk'] += 1
        elif risk == 'medium':
            summary['medium_risk'] += 1
        else:
            summary['low_risk'] += 1

        summary['unique_spenders'].add(approval['spender'])
        summary['unique_tokens'].add(approval['token_address'])

    summary['unique_spenders'] = len(summary['unique_spenders'])
    summary['unique_tokens'] = len(summary['unique_tokens'])

    return summary


def format_approval_amount(amount, decimals=18):
    """Format approval amount for display."""
    if amount >= UNLIMITED_THRESHOLD:
        return 'Unlimited'

    formatted = amount / (10 ** decimals)
    if formatted >= 1_000_000_000:
        return f'{formatted/1_000_000_000:.2f}B'
    elif formatted >= 1_000_000:
        return f'{formatted/1_000_000:.2f}M'
    elif formatted >= 1_000:
        return f'{formatted/1_000:.2f}K'
    else:
        return f'{formatted:.4f}'
