# Airdrop Eligibility Checker Service
# Check common airdrop criteria and past claims

# Known airdrop contracts and criteria
AIRDROP_CAMPAIGNS = {
    'arbitrum': {
        'name': 'Arbitrum (ARB)',
        'token': 'ARB',
        'contract': '0x67a24ce4321ab3af51c2d0a4801c3e111d88c9d9',
        'snapshot_date': '2023-02-06',
        'claim_deadline': '2023-09-24',
        'criteria': [
            'Bridged to Arbitrum before snapshot',
            'Conducted transactions on Arbitrum',
            'Transaction volume and frequency'
        ]
    },
    'optimism': {
        'name': 'Optimism (OP)',
        'token': 'OP',
        'contract': '0xfedfaf1a10335448b7fa0268f56d2b44dbd357de',
        'snapshot_date': '2022-03-25',
        'criteria': [
            'Used Optimism before snapshot',
            'DAO voters',
            'Multi-sig signers',
            'Gitcoin donors'
        ]
    },
    'blur': {
        'name': 'Blur (BLUR)',
        'token': 'BLUR',
        'contract': '0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511',
        'criteria': [
            'NFT trading activity',
            'Listed NFTs on Blur',
            'Bid activity'
        ]
    },
    'ens': {
        'name': 'ENS (ENS)',
        'token': 'ENS',
        'contract': '0xc18360217d8f7ab5e7c516566761ea12ce7f9d72',
        'snapshot_date': '2021-10-31',
        'criteria': [
            'Owned .eth domain before snapshot',
            'Primary ENS set'
        ]
    },
    'uniswap': {
        'name': 'Uniswap (UNI)',
        'token': 'UNI',
        'contract': '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984',
        'snapshot_date': '2020-09-01',
        'criteria': [
            'Used Uniswap V1 or V2 before snapshot',
            'Liquidity providers got bonus'
        ]
    },
    'dydx': {
        'name': 'dYdX (DYDX)',
        'token': 'DYDX',
        'contract': '0x92d6c1e31e14520e676a687f0a93788b716beff5',
        'criteria': [
            'Traded on dYdX',
            'Deposited to dYdX'
        ]
    },
    'apecoin': {
        'name': 'ApeCoin (APE)',
        'token': 'APE',
        'contract': '0x4d224452801aced8b2f0aebe155379bb5d594381',
        'snapshot_date': '2022-03-17',
        'criteria': [
            'BAYC holder',
            'MAYC holder',
            'BAKC holder'
        ]
    }
}

# Upcoming potential airdrops (speculative)
POTENTIAL_AIRDROPS = [
    {
        'name': 'LayerZero',
        'status': 'Speculated',
        'criteria': [
            'Bridge assets using LayerZero',
            'Use Stargate Finance',
            'Cross-chain transactions'
        ],
        'protocols': ['Stargate', 'LayerZero bridges']
    },
    {
        'name': 'zkSync',
        'status': 'Speculated',
        'criteria': [
            'Bridge to zkSync Era',
            'Use zkSync dApps',
            'Transaction volume on zkSync'
        ],
        'protocols': ['zkSync Era', 'zkSync Lite']
    },
    {
        'name': 'Scroll',
        'status': 'Speculated',
        'criteria': [
            'Bridge to Scroll',
            'Use Scroll dApps',
            'Testnet participation'
        ],
        'protocols': ['Scroll mainnet']
    },
    {
        'name': 'Linea',
        'status': 'Speculated',
        'criteria': [
            'Bridge to Linea',
            'Use Linea dApps',
            'Voyage NFT holders'
        ],
        'protocols': ['Linea', 'Consensys ecosystem']
    },
    {
        'name': 'Base',
        'status': 'Speculated',
        'criteria': [
            'Early Base user',
            'Bridge to Base',
            'NFT minting on Base'
        ],
        'protocols': ['Base', 'Coinbase ecosystem']
    }
]


def check_airdrop_claims(token_transfers, address):
    """
    Check which airdrops the address has claimed.
    """
    address_lower = address.lower()
    claimed = []
    unclaimed = []

    for airdrop_id, airdrop in AIRDROP_CAMPAIGNS.items():
        token_symbol = airdrop['token']

        # Check if received this token
        received = False
        for transfer in token_transfers:
            if transfer.get('token_symbol', '').upper() == token_symbol.upper():
                if transfer.get('direction') == 'in':
                    received = True
                    claimed.append({
                        'id': airdrop_id,
                        'name': airdrop['name'],
                        'token': token_symbol,
                        'amount': transfer.get('value', 0),
                        'timestamp': transfer.get('timestamp', 0)
                    })
                    break

        if not received:
            unclaimed.append({
                'id': airdrop_id,
                'name': airdrop['name'],
                'token': token_symbol
            })

    return {
        'claimed': claimed,
        'unclaimed': unclaimed,
        'total_claimed': len(claimed)
    }


def estimate_airdrop_eligibility(transactions, token_transfers, defi_summary, address):
    """
    Estimate potential eligibility for speculated airdrops.
    """
    eligibility = []

    for potential in POTENTIAL_AIRDROPS:
        score = 0
        met_criteria = []

        # Check for cross-chain/bridge activity
        if 'LayerZero' in potential['name'] or 'Bridge' in str(potential['criteria']):
            # Check for bridge interactions
            bridge_count = sum(1 for tx in transactions
                             if 'bridge' in str(tx.get('to_label', {}).get('category', '')).lower())
            if bridge_count > 0:
                score += 30
                met_criteria.append('Bridge activity detected')

        # Check for L2 activity
        if any(l2 in potential['name'] for l2 in ['zkSync', 'Scroll', 'Linea', 'Base']):
            # Would need multi-chain data to properly check
            # For now, check general DeFi activity as proxy
            if defi_summary.get('protocol_count', 0) > 0:
                score += 20
                met_criteria.append('DeFi activity (check L2 separately)')

        # Check transaction count (general activity)
        if len(transactions) > 50:
            score += 20
            met_criteria.append('Active wallet')
        elif len(transactions) > 10:
            score += 10
            met_criteria.append('Some activity')

        # Check token diversity
        if len(token_transfers) > 100:
            score += 15
            met_criteria.append('High token activity')

        eligibility.append({
            'name': potential['name'],
            'status': potential['status'],
            'criteria': potential['criteria'],
            'protocols': potential['protocols'],
            'score': min(score, 100),
            'met_criteria': met_criteria,
            'likelihood': 'High' if score >= 60 else 'Medium' if score >= 30 else 'Low'
        })

    # Sort by score
    eligibility.sort(key=lambda x: x['score'], reverse=True)

    return eligibility


def get_airdrop_summary(claimed, eligibility):
    """
    Generate airdrop summary.
    """
    return {
        'total_claimed': len(claimed.get('claimed', [])),
        'tokens_received': [c['token'] for c in claimed.get('claimed', [])],
        'high_potential': sum(1 for e in eligibility if e['likelihood'] == 'High'),
        'medium_potential': sum(1 for e in eligibility if e['likelihood'] == 'Medium'),
        'recommendations': get_airdrop_recommendations(claimed, eligibility)
    }


def get_airdrop_recommendations(claimed, eligibility):
    """
    Generate recommendations for improving airdrop eligibility.
    """
    recommendations = []

    # Check for low bridge activity
    has_bridge_activity = any('Bridge' in c for e in eligibility for c in e.get('met_criteria', []))
    if not has_bridge_activity:
        recommendations.append({
            'action': 'Bridge assets to L2s',
            'reason': 'Many airdrops reward bridge users',
            'protocols': ['Arbitrum', 'Optimism', 'zkSync', 'Base']
        })

    # Check for DeFi activity
    has_defi = any('DeFi' in c for e in eligibility for c in e.get('met_criteria', []))
    if not has_defi:
        recommendations.append({
            'action': 'Use DeFi protocols',
            'reason': 'DeFi usage often qualifies for airdrops',
            'protocols': ['Uniswap', 'Aave', 'Compound']
        })

    # General recommendation
    if len(claimed.get('claimed', [])) < 3:
        recommendations.append({
            'action': 'Increase on-chain activity',
            'reason': 'More transactions = better airdrop chances',
            'protocols': ['Any active dApps']
        })

    return recommendations
