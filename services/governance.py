# Governance Participation Service
# Track DAO voting and governance activity

from collections import defaultdict

# Known governance contracts
GOVERNANCE_CONTRACTS = {
    # Compound
    '0xc0da02939e1441f497fd74f78ce7decb17b66529': {'name': 'Compound Governor Bravo', 'protocol': 'Compound'},
    # Uniswap
    '0x408ed6354d4973f66138c91495f2f2fcbd8724c3': {'name': 'Uniswap Governor', 'protocol': 'Uniswap'},
    # Aave
    '0xec568fffba86c094cf06b22134b23074dfe2252c': {'name': 'Aave Governance V2', 'protocol': 'Aave'},
    # MakerDAO
    '0x0a3f6849f78076aefadf113f5bed87720274ddc0': {'name': 'MakerDAO Chief', 'protocol': 'MakerDAO'},
    # ENS
    '0x323a76393544d5ecca80cd6ef2a560c6a395b7e3': {'name': 'ENS Governor', 'protocol': 'ENS'},
    # Gitcoin
    '0xdbf72370021babafbceb05ab10f99ad275c6220a': {'name': 'Gitcoin Governor', 'protocol': 'Gitcoin'},
    # Arbitrum
    '0x789fc99093b09ad01c34dc7251d0c89ce743e5a4': {'name': 'Arbitrum Governor', 'protocol': 'Arbitrum'},
    # Optimism
    '0xcdf27f107725988f2261ce2256bdfcde8b382b10': {'name': 'Optimism Governor', 'protocol': 'Optimism'},
}

# Governance function signatures
GOVERNANCE_SIGNATURES = {
    '0x15373e3d': 'castVote',
    '0x56781388': 'castVoteWithReason',
    '0x3bccf4fd': 'castVoteBySig',
    '0x7b3c71d3': 'castVoteWithReasonAndParams',
    '0xda95691a': 'propose',
    '0x2fe99ab5': 'queue',
    '0xfe0d94c1': 'execute',
    '0x5c19a95c': 'delegate',
    '0xe7a324dc': 'delegateBySig',
}

# Known governance tokens
GOVERNANCE_TOKENS = {
    '0xc00e94cb662c3520282e6f5717214004a7f26888': {'symbol': 'COMP', 'protocol': 'Compound'},
    '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984': {'symbol': 'UNI', 'protocol': 'Uniswap'},
    '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9': {'symbol': 'AAVE', 'protocol': 'Aave'},
    '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2': {'symbol': 'MKR', 'protocol': 'MakerDAO'},
    '0xc18360217d8f7ab5e7c516566761ea12ce7f9d72': {'symbol': 'ENS', 'protocol': 'ENS'},
    '0xde30da39c46104798bb5aa3fe8b9e0e1f348163f': {'symbol': 'GTC', 'protocol': 'Gitcoin'},
    '0x912ce59144191c1204e64559fe8253a0e49e6548': {'symbol': 'ARB', 'protocol': 'Arbitrum'},
    '0x4200000000000000000000000000000000000042': {'symbol': 'OP', 'protocol': 'Optimism'},
}


def detect_governance_activity(transactions, token_balances, address):
    """
    Detect governance-related activity.
    """
    activity = {
        'votes': [],
        'proposals': [],
        'delegations': [],
        'governance_tokens_held': [],
        'protocols_participated': set()
    }

    for tx in transactions:
        to_addr = (tx.get('to') or '').lower()
        input_data = tx.get('input', '0x')
        func_sig = input_data[:10] if len(input_data) >= 10 else ''

        # Check if interacting with governance contract
        if to_addr in GOVERNANCE_CONTRACTS:
            gov_info = GOVERNANCE_CONTRACTS[to_addr]
            activity['protocols_participated'].add(gov_info['protocol'])

            action = {
                'tx_hash': tx.get('hash'),
                'timestamp': tx.get('timestamp'),
                'protocol': gov_info['protocol'],
                'contract_name': gov_info['name'],
                'gas_used': tx.get('gas_used'),
                'type': 'unknown'
            }

            if func_sig in GOVERNANCE_SIGNATURES:
                action_type = GOVERNANCE_SIGNATURES[func_sig]
                action['function'] = action_type

                if 'vote' in action_type.lower():
                    action['type'] = 'vote'
                    activity['votes'].append(action)
                elif 'propose' in action_type.lower():
                    action['type'] = 'proposal'
                    activity['proposals'].append(action)
                elif 'delegate' in action_type.lower():
                    action['type'] = 'delegation'
                    activity['delegations'].append(action)

    # Check for governance tokens
    for token in token_balances:
        contract = (token.get('contract_address') or '').lower()
        if contract in GOVERNANCE_TOKENS:
            token_info = GOVERNANCE_TOKENS[contract]
            activity['governance_tokens_held'].append({
                'symbol': token_info['symbol'],
                'protocol': token_info['protocol'],
                'balance': token.get('balance', 0),
                'value_usd': token.get('value_usd', 0)
            })
            activity['protocols_participated'].add(token_info['protocol'])

    activity['protocols_participated'] = list(activity['protocols_participated'])

    return activity


def calculate_governance_score(activity):
    """
    Calculate governance participation score.
    """
    score = 0
    factors = []

    # Voting activity (max 40 points)
    vote_count = len(activity.get('votes', []))
    if vote_count >= 20:
        score += 40
        factors.append(f"Active voter ({vote_count} votes)")
    elif vote_count >= 10:
        score += 30
        factors.append(f"Regular voter ({vote_count} votes)")
    elif vote_count >= 5:
        score += 20
        factors.append(f"Occasional voter ({vote_count} votes)")
    elif vote_count > 0:
        score += 10
        factors.append(f"Some voting ({vote_count} votes)")

    # Proposal activity (max 30 points)
    proposal_count = len(activity.get('proposals', []))
    if proposal_count >= 3:
        score += 30
        factors.append(f"Active proposer ({proposal_count} proposals)")
    elif proposal_count > 0:
        score += 20
        factors.append(f"Has proposed ({proposal_count} proposals)")

    # Delegation activity (max 15 points)
    delegation_count = len(activity.get('delegations', []))
    if delegation_count > 0:
        score += 15
        factors.append("Has delegated voting power")

    # Token holdings (max 15 points)
    tokens_held = len(activity.get('governance_tokens_held', []))
    if tokens_held >= 3:
        score += 15
        factors.append(f"Holds multiple governance tokens ({tokens_held})")
    elif tokens_held > 0:
        score += 10
        factors.append(f"Holds governance tokens ({tokens_held})")

    # Protocol diversity bonus
    protocols = len(activity.get('protocols_participated', []))
    if protocols >= 3:
        score += 10
        factors.append(f"Multi-protocol participant ({protocols} protocols)")

    return {
        'score': min(score, 100),
        'factors': factors,
        'tier': get_governance_tier(score)
    }


def get_governance_tier(score):
    """
    Get governance participation tier.
    """
    if score >= 80:
        return {'name': 'Power Voter', 'color': 'success'}
    elif score >= 60:
        return {'name': 'Active Participant', 'color': 'primary'}
    elif score >= 40:
        return {'name': 'Engaged Holder', 'color': 'info'}
    elif score >= 20:
        return {'name': 'Passive Holder', 'color': 'warning'}
    else:
        return {'name': 'Non-Participant', 'color': 'secondary'}


def get_voting_history(activity):
    """
    Get formatted voting history.
    """
    votes = activity.get('votes', [])

    # Sort by timestamp
    votes.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

    return votes[:50]  # Return last 50 votes


def get_governance_recommendations(activity, score_info):
    """
    Generate governance participation recommendations.
    """
    recommendations = []

    tokens_held = activity.get('governance_tokens_held', [])
    votes = activity.get('votes', [])
    delegations = activity.get('delegations', [])

    # If holding tokens but not voting
    if tokens_held and not votes:
        recommendations.append({
            'priority': 'high',
            'action': 'Start Voting',
            'detail': 'You hold governance tokens but haven\'t voted. Participate in governance to have your voice heard!'
        })

    # If not delegating
    if tokens_held and not delegations:
        recommendations.append({
            'priority': 'medium',
            'action': 'Consider Delegating',
            'detail': 'If you can\'t actively vote, delegate your voting power to an active participant'
        })

    # If only participating in one protocol
    protocols = activity.get('protocols_participated', [])
    if len(protocols) == 1 and len(tokens_held) < 2:
        recommendations.append({
            'priority': 'low',
            'action': 'Diversify Participation',
            'detail': 'Consider participating in governance of multiple protocols'
        })

    # General encouragement
    if score_info.get('score', 0) < 40:
        recommendations.append({
            'priority': 'info',
            'action': 'Get Involved',
            'detail': 'Active governance participation can influence protocol direction and may qualify for future airdrops'
        })

    return recommendations


def generate_governance_report(address, transactions, token_balances):
    """
    Generate comprehensive governance participation report.
    """
    activity = detect_governance_activity(transactions, token_balances, address)
    score_info = calculate_governance_score(activity)
    voting_history = get_voting_history(activity)
    recommendations = get_governance_recommendations(activity, score_info)

    return {
        'address': address,
        'activity': activity,
        'score': score_info,
        'voting_history': voting_history,
        'recommendations': recommendations,
        'summary': {
            'total_votes': len(activity.get('votes', [])),
            'total_proposals': len(activity.get('proposals', [])),
            'protocols_active': len(activity.get('protocols_participated', [])),
            'governance_tokens': len(activity.get('governance_tokens_held', [])),
            'is_active_voter': len(activity.get('votes', [])) > 0
        }
    }
