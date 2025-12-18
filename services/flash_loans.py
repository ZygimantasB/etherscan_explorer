# Flash Loan Detection Service
# Identify flash loan transactions and arbitrage patterns

# Known flash loan provider contracts
FLASH_LOAN_PROVIDERS = {
    # Aave V2
    '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': {'name': 'Aave V2 Lending Pool', 'protocol': 'Aave'},
    '0x398ec7346dcd622edc5ae82352f02be94c62d119': {'name': 'Aave V1 Lending Pool', 'protocol': 'Aave'},
    # Aave V3
    '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2': {'name': 'Aave V3 Pool', 'protocol': 'Aave'},
    # dYdX
    '0x1e0447b19bb6ecfdae1e4ae1694b0c3659614e4e': {'name': 'dYdX Solo Margin', 'protocol': 'dYdX'},
    # Uniswap V2
    '0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f': {'name': 'Uniswap V2 Factory', 'protocol': 'Uniswap'},
    # Uniswap V3
    '0x1f98431c8ad98523631ae4a59f267346ea31f984': {'name': 'Uniswap V3 Factory', 'protocol': 'Uniswap'},
    # Balancer
    '0xba12222222228d8ba445958a75a0704d566bf2c8': {'name': 'Balancer Vault', 'protocol': 'Balancer'},
    # MakerDAO
    '0x1eb4cf3a948e7d72a198fe073ccb8c7a948cd853': {'name': 'MakerDAO Flash Mint', 'protocol': 'MakerDAO'},
    # Compound
    '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b': {'name': 'Compound Comptroller', 'protocol': 'Compound'},
}

# Flash loan function signatures
FLASH_LOAN_SIGNATURES = {
    '0xab9c4b5d': 'flashLoan(address,address[],uint256[],uint256[],address,bytes,uint16)',  # Aave V2
    '0xe0232b42': 'flashLoan(address,address,uint256,bytes)',  # Aave V3
    '0x5cffe9de': 'flashLoan(address,address[],uint256[],bytes)',  # Balancer
    '0x490e6cbc': 'operate(tuple[],tuple[])',  # dYdX
    '0xd9d98ce4': 'flashMint(address,uint256,bytes)',  # MakerDAO
}

# Arbitrage indicators
ARBITRAGE_PATTERNS = {
    'multi_dex_swap': 'Multiple DEX swaps in single transaction',
    'same_token_in_out': 'Same token input and output',
    'profit_extraction': 'Profit extracted at end of transaction',
    'complex_routing': 'Complex token routing through multiple pools'
}


def detect_flash_loans(transactions, internal_transactions):
    """
    Detect flash loan transactions.
    """
    flash_loans = []

    for tx in transactions:
        is_flash_loan = False
        flash_loan_info = {
            'hash': tx.get('hash'),
            'timestamp': tx.get('timestamp'),
            'gas_used': tx.get('gas_used'),
            'gas_price_gwei': tx.get('gas_price_gwei'),
            'indicators': [],
            'protocols': [],
            'confidence': 0
        }

        to_addr = (tx.get('to') or '').lower()
        input_data = tx.get('input', '0x')

        # Check if interacting with known flash loan provider
        if to_addr in FLASH_LOAN_PROVIDERS:
            is_flash_loan = True
            provider = FLASH_LOAN_PROVIDERS[to_addr]
            flash_loan_info['indicators'].append(f"Direct {provider['protocol']} interaction")
            flash_loan_info['protocols'].append(provider['protocol'])
            flash_loan_info['confidence'] += 40

        # Check function signature
        if len(input_data) >= 10:
            func_sig = input_data[:10]
            if func_sig in FLASH_LOAN_SIGNATURES:
                is_flash_loan = True
                flash_loan_info['indicators'].append('Flash loan function signature detected')
                flash_loan_info['confidence'] += 50

        # Check for high gas usage (flash loans typically use more gas)
        gas_used = tx.get('gas_used', 0)
        if gas_used > 500000:
            flash_loan_info['indicators'].append('High gas usage')
            flash_loan_info['confidence'] += 10

        # Check internal transactions for flash loan patterns
        tx_hash = tx.get('hash', '').lower()
        related_internals = [itx for itx in internal_transactions
                           if itx.get('hash', '').lower() == tx_hash]

        if len(related_internals) > 5:
            flash_loan_info['indicators'].append(f'{len(related_internals)} internal transactions')
            flash_loan_info['confidence'] += 15

            # Check for circular flow (borrow -> operations -> repay)
            addresses_involved = set()
            for itx in related_internals:
                addresses_involved.add(itx.get('from', '').lower())
                addresses_involved.add(itx.get('to', '').lower())

            if len(addresses_involved) > 3:
                flash_loan_info['indicators'].append('Complex multi-contract interaction')
                flash_loan_info['confidence'] += 10

        # Check for zero value but high gas (common in arbitrage)
        if tx.get('value', 0) == 0 and gas_used > 200000:
            flash_loan_info['indicators'].append('Zero value with high gas')
            flash_loan_info['confidence'] += 5

        if is_flash_loan or flash_loan_info['confidence'] >= 30:
            flash_loan_info['confidence'] = min(flash_loan_info['confidence'], 100)
            flash_loans.append(flash_loan_info)

    return flash_loans


def detect_arbitrage(transactions, token_transfers):
    """
    Detect arbitrage patterns in transactions.
    """
    arbitrage_txs = []

    # Group token transfers by transaction hash
    transfers_by_tx = {}
    for transfer in token_transfers:
        tx_hash = transfer.get('hash', '').lower()
        if tx_hash not in transfers_by_tx:
            transfers_by_tx[tx_hash] = []
        transfers_by_tx[tx_hash].append(transfer)

    for tx in transactions:
        tx_hash = tx.get('hash', '').lower()
        tx_transfers = transfers_by_tx.get(tx_hash, [])

        if len(tx_transfers) < 2:
            continue

        arb_info = {
            'hash': tx.get('hash'),
            'timestamp': tx.get('timestamp'),
            'patterns': [],
            'tokens_involved': [],
            'estimated_profit': None,
            'confidence': 0
        }

        tokens_in = {}
        tokens_out = {}

        for transfer in tx_transfers:
            symbol = transfer.get('token_symbol', 'UNKNOWN')
            value = transfer.get('value', 0)
            direction = transfer.get('direction')

            arb_info['tokens_involved'].append(symbol)

            if direction == 'in':
                tokens_in[symbol] = tokens_in.get(symbol, 0) + value
            else:
                tokens_out[symbol] = tokens_out.get(symbol, 0) + value

        arb_info['tokens_involved'] = list(set(arb_info['tokens_involved']))

        # Check for same token in and out (classic arbitrage)
        for symbol in tokens_in:
            if symbol in tokens_out:
                profit = tokens_in[symbol] - tokens_out[symbol]
                if profit > 0:
                    arb_info['patterns'].append(ARBITRAGE_PATTERNS['same_token_in_out'])
                    arb_info['estimated_profit'] = {
                        'token': symbol,
                        'amount': profit
                    }
                    arb_info['confidence'] += 40

        # Check for multiple swaps
        if len(tx_transfers) >= 4:
            arb_info['patterns'].append(ARBITRAGE_PATTERNS['multi_dex_swap'])
            arb_info['confidence'] += 20

        # Check for complex routing
        unique_tokens = len(arb_info['tokens_involved'])
        if unique_tokens >= 3:
            arb_info['patterns'].append(ARBITRAGE_PATTERNS['complex_routing'])
            arb_info['confidence'] += 15

        if arb_info['confidence'] >= 30:
            arb_info['confidence'] = min(arb_info['confidence'], 100)
            arbitrage_txs.append(arb_info)

    return arbitrage_txs


def analyze_flash_loan_activity(flash_loans, arbitrage_txs):
    """
    Analyze overall flash loan and arbitrage activity.
    """
    analysis = {
        'total_flash_loans': len(flash_loans),
        'total_arbitrage_txs': len(arbitrage_txs),
        'protocols_used': [],
        'high_confidence_flash_loans': 0,
        'total_gas_spent': 0,
        'is_flash_loan_user': False,
        'is_arbitrageur': False,
        'activity_summary': []
    }

    protocols = set()
    for fl in flash_loans:
        analysis['total_gas_spent'] += fl.get('gas_used', 0) * fl.get('gas_price_gwei', 0) / 1e9
        protocols.update(fl.get('protocols', []))
        if fl.get('confidence', 0) >= 70:
            analysis['high_confidence_flash_loans'] += 1

    analysis['protocols_used'] = list(protocols)

    if len(flash_loans) >= 3:
        analysis['is_flash_loan_user'] = True
        analysis['activity_summary'].append(f"Active flash loan user ({len(flash_loans)} detected)")

    if len(arbitrage_txs) >= 5:
        analysis['is_arbitrageur'] = True
        analysis['activity_summary'].append(f"Arbitrage activity detected ({len(arbitrage_txs)} transactions)")

    if analysis['high_confidence_flash_loans'] > 0:
        analysis['activity_summary'].append(
            f"{analysis['high_confidence_flash_loans']} high-confidence flash loans"
        )

    if not analysis['activity_summary']:
        analysis['activity_summary'].append("No significant flash loan/arbitrage activity")

    return analysis


def get_flash_loan_summary(flash_loans, arbitrage_txs, address):
    """
    Generate summary for flash loan activity.
    """
    analysis = analyze_flash_loan_activity(flash_loans, arbitrage_txs)

    return {
        'flash_loans': flash_loans[:20],  # Limit to 20
        'arbitrage': arbitrage_txs[:20],
        'analysis': analysis,
        'is_bot': analysis['is_flash_loan_user'] or analysis['is_arbitrageur'],
        'risk_level': 'high' if analysis['is_flash_loan_user'] else 'low'
    }
