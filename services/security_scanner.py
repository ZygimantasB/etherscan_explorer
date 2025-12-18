# Contract Security Scanner Service
# Basic security checks for smart contracts

import re

# Known malicious patterns in bytecode
MALICIOUS_PATTERNS = {
    'selfdestruct': {
        'pattern': 'ff',  # SELFDESTRUCT opcode
        'risk': 'high',
        'description': 'Contract can self-destruct and drain funds'
    },
    'delegatecall': {
        'pattern': 'f4',  # DELEGATECALL opcode
        'risk': 'medium',
        'description': 'Uses delegatecall - potential for proxy attacks'
    },
}

# Known vulnerable function signatures
VULNERABLE_FUNCTIONS = {
    '0x095ea7b3': {'name': 'approve', 'risk': 'info', 'note': 'Token approval - check spender'},
    '0xa22cb465': {'name': 'setApprovalForAll', 'risk': 'medium', 'note': 'NFT approval for all tokens'},
    '0x42842e0e': {'name': 'safeTransferFrom', 'risk': 'info', 'note': 'NFT transfer'},
    '0x23b872dd': {'name': 'transferFrom', 'risk': 'info', 'note': 'Token transfer'},
}

# Known scam contract patterns
SCAM_PATTERNS = {
    'honeypot': [
        'Cannot sell tokens',
        'High buy/sell tax',
        'Blacklist functionality',
        'Owner can pause trading'
    ],
    'rugpull': [
        'Owner can mint unlimited tokens',
        'Owner can drain liquidity',
        'No renounced ownership',
        'Hidden owner functions'
    ],
    'phishing': [
        'Fake token name mimicking popular token',
        'Similar contract to known scam',
        'Unverified contract'
    ]
}

# Known safe contracts (whitelisted)
SAFE_CONTRACTS = {
    '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT',
    '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDC',
    '0x6b175474e89094c44da98b954eedeac495271d0f': 'DAI',
    '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'WETH',
    '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'WBTC',
    '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984': 'UNI',
    '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9': 'AAVE',
    '0x514910771af9ca656af840dff83e8264ecf986ca': 'LINK',
}


def scan_contract_security(contract_info, transactions=None):
    """
    Perform security scan on a contract.
    """
    findings = []
    risk_score = 0

    if not contract_info:
        return {'findings': [], 'risk_score': 0, 'status': 'no_data'}

    contract_address = contract_info.get('address', '').lower()

    # Check if known safe contract
    if contract_address in SAFE_CONTRACTS:
        return {
            'findings': [{'type': 'info', 'message': f'Known safe contract: {SAFE_CONTRACTS[contract_address]}'}],
            'risk_score': 0,
            'status': 'safe',
            'is_whitelisted': True
        }

    # Check verification status
    is_verified = contract_info.get('is_verified', False)
    if not is_verified:
        findings.append({
            'type': 'warning',
            'risk': 'medium',
            'message': 'Contract is not verified - source code unavailable'
        })
        risk_score += 30

    # Check proxy status
    if contract_info.get('proxy'):
        findings.append({
            'type': 'info',
            'risk': 'low',
            'message': 'Contract is a proxy - implementation can be changed'
        })
        risk_score += 10

    # Analyze source code if available
    source_code = contract_info.get('source_code', '')
    if source_code:
        source_findings = analyze_source_code(source_code)
        findings.extend(source_findings)
        risk_score += sum(f.get('score', 0) for f in source_findings)

    # Check contract age
    # Newer contracts are riskier
    creation_tx = contract_info.get('creation_tx')
    if creation_tx:
        # Could analyze creation date here
        pass

    # Normalize risk score
    risk_score = min(risk_score, 100)

    # Determine risk level
    if risk_score >= 70:
        risk_level = 'critical'
    elif risk_score >= 50:
        risk_level = 'high'
    elif risk_score >= 30:
        risk_level = 'medium'
    elif risk_score >= 10:
        risk_level = 'low'
    else:
        risk_level = 'minimal'

    return {
        'findings': findings,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'status': 'scanned',
        'is_verified': is_verified
    }


def analyze_source_code(source_code):
    """
    Analyze contract source code for security issues.
    """
    findings = []

    # Check for dangerous patterns
    dangerous_patterns = [
        {
            'pattern': r'selfdestruct|suicide',
            'message': 'Contains selfdestruct - contract can be destroyed',
            'risk': 'high',
            'score': 25
        },
        {
            'pattern': r'delegatecall',
            'message': 'Uses delegatecall - potential proxy vulnerability',
            'risk': 'medium',
            'score': 15
        },
        {
            'pattern': r'tx\.origin',
            'message': 'Uses tx.origin - vulnerable to phishing attacks',
            'risk': 'high',
            'score': 20
        },
        {
            'pattern': r'block\.timestamp',
            'message': 'Uses block.timestamp - can be manipulated by miners',
            'risk': 'low',
            'score': 5
        },
        {
            'pattern': r'\.call\{value:',
            'message': 'Uses low-level call with value - check for reentrancy',
            'risk': 'medium',
            'score': 15
        },
        {
            'pattern': r'onlyOwner|Ownable',
            'message': 'Has owner privileges - check for centralization risks',
            'risk': 'info',
            'score': 5
        },
        {
            'pattern': r'_mint\s*\([^)]*\)|mint\s*\(',
            'message': 'Has minting functionality',
            'risk': 'info',
            'score': 5
        },
        {
            'pattern': r'_burn|burn\s*\(',
            'message': 'Has burn functionality',
            'risk': 'info',
            'score': 0
        },
        {
            'pattern': r'pause|unpause|Pausable',
            'message': 'Contract can be paused by owner',
            'risk': 'medium',
            'score': 10
        },
        {
            'pattern': r'blacklist|whitelist|_blocked',
            'message': 'Has blacklist/whitelist functionality - potential honeypot',
            'risk': 'high',
            'score': 25
        },
        {
            'pattern': r'maxTx|maxWallet|_maxTxAmount',
            'message': 'Has transaction limits',
            'risk': 'medium',
            'score': 10
        },
        {
            'pattern': r'fee|_fee|taxFee|_taxFee',
            'message': 'Has fee mechanism - check fee amounts',
            'risk': 'medium',
            'score': 10
        },
    ]

    for pattern_info in dangerous_patterns:
        if re.search(pattern_info['pattern'], source_code, re.IGNORECASE):
            findings.append({
                'type': 'security',
                'risk': pattern_info['risk'],
                'message': pattern_info['message'],
                'score': pattern_info['score']
            })

    return findings


def check_honeypot_indicators(token_transfers, address):
    """
    Check for honeypot indicators based on transaction patterns.
    """
    indicators = []

    buys = [t for t in token_transfers if t.get('direction') == 'in']
    sells = [t for t in token_transfers if t.get('direction') == 'out']

    # If many buys but no sells, might be honeypot
    if len(buys) > 5 and len(sells) == 0:
        indicators.append({
            'type': 'honeypot_warning',
            'message': 'Multiple buys but no sells detected - potential honeypot',
            'risk': 'high'
        })

    # Check sell success rate
    # This would require checking if sell transactions failed

    return indicators


def get_security_recommendations(findings):
    """
    Generate security recommendations based on findings.
    """
    recommendations = []

    has_high_risk = any(f.get('risk') == 'high' for f in findings)
    has_medium_risk = any(f.get('risk') == 'medium' for f in findings)

    if has_high_risk:
        recommendations.append({
            'priority': 'critical',
            'action': 'Exercise extreme caution',
            'detail': 'High-risk patterns detected. Do not interact without thorough review.'
        })

    if has_medium_risk:
        recommendations.append({
            'priority': 'warning',
            'action': 'Review carefully',
            'detail': 'Medium-risk patterns found. Verify contract behavior before interacting.'
        })

    # Check for unverified
    unverified = any('not verified' in f.get('message', '').lower() for f in findings)
    if unverified:
        recommendations.append({
            'priority': 'warning',
            'action': 'Request verification',
            'detail': 'Contract source code is not verified. Consider avoiding unverified contracts.'
        })

    if not recommendations:
        recommendations.append({
            'priority': 'info',
            'action': 'Standard precautions',
            'detail': 'No major issues detected, but always verify before large transactions.'
        })

    return recommendations


def generate_security_report(contract_info, scan_results, honeypot_check):
    """
    Generate comprehensive security report.
    """
    findings = scan_results.get('findings', []) + honeypot_check
    recommendations = get_security_recommendations(findings)

    return {
        'contract_address': contract_info.get('address'),
        'contract_name': contract_info.get('contract_name'),
        'is_verified': contract_info.get('is_verified', False),
        'risk_score': scan_results.get('risk_score', 0),
        'risk_level': scan_results.get('risk_level', 'unknown'),
        'findings': findings,
        'recommendations': recommendations,
        'is_whitelisted': scan_results.get('is_whitelisted', False),
        'scan_timestamp': None  # Would add current timestamp
    }
