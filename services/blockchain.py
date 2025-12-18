import requests
from config import get_chain_config, ETHERSCAN_V2_API
from services.prices import get_eth_price, get_native_price, get_multiple_token_prices, get_token_price_by_symbol
from services.labels import get_address_label, get_category_addresses, calculate_risk_score
from services.defi import detect_defi_positions, get_defi_summary


class BlockchainClient:
    """Client for interacting with Etherscan V2 API (supports multiple chains)."""

    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.config = get_chain_config(chain_id)
        if not self.config:
            raise ValueError(f"Unsupported chain: {chain_id}")

        self.api_url = ETHERSCAN_V2_API
        self.api_key = self.config['api_key']
        self.network_chain_id = self.config['chain_id']

    def _make_request(self, params):
        """Make API request with common parameters."""
        params['apikey'] = self.api_key
        params['chainid'] = self.network_chain_id
        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == '1' or data.get('message') == 'OK':
                return data.get('result', [])
            return []
        except requests.RequestException as e:
            print(f"API request error: {e}")
            return []

    def get_balance(self, address):
        """Get native token balance for an address."""
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest'
        }
        result = self._make_request(params)
        if result:
            balance_wei = int(result)
            balance = balance_wei / (10 ** self.config['decimals'])
            return {
                'balance_wei': balance_wei,
                'balance': balance,
                'symbol': self.config['symbol']
            }
        return {'balance_wei': 0, 'balance': 0, 'symbol': self.config['symbol']}

    def get_transactions(self, address, limit=100):
        """Get normal transactions for an address."""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        transactions = self._make_request(params)
        if isinstance(transactions, list):
            return self._format_transactions(transactions, address)
        return []

    def get_internal_transactions(self, address, limit=50):
        """Get internal transactions for an address."""
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        transactions = self._make_request(params)
        if isinstance(transactions, list):
            return self._format_internal_transactions(transactions, address)
        return []

    def get_token_transfers(self, address, limit=200):
        """Get ERC-20 token transfers for an address."""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        transfers = self._make_request(params)
        if isinstance(transfers, list):
            return self._format_token_transfers(transfers, address)
        return []

    def get_nft_transfers(self, address, limit=100):
        """Get ERC-721 NFT transfers for an address."""
        params = {
            'module': 'account',
            'action': 'tokennfttx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        transfers = self._make_request(params)
        if isinstance(transfers, list):
            return self._format_nft_transfers(transfers, address)
        return []

    def get_erc1155_transfers(self, address, limit=100):
        """Get ERC-1155 token transfers for an address."""
        params = {
            'module': 'account',
            'action': 'token1155tx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        transfers = self._make_request(params)
        if isinstance(transfers, list):
            return self._format_erc1155_transfers(transfers, address)
        return []

    def get_contract_info(self, address):
        """Get contract source code and ABI if available."""
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address
        }
        result = self._make_request(params)
        if result and isinstance(result, list) and len(result) > 0:
            contract = result[0]
            return {
                'is_verified': contract.get('SourceCode', '') != '',
                'contract_name': contract.get('ContractName', ''),
                'compiler_version': contract.get('CompilerVersion', ''),
                'optimization_used': contract.get('OptimizationUsed', '0') == '1',
                'runs': contract.get('Runs', ''),
                'license_type': contract.get('LicenseType', ''),
                'proxy': contract.get('Proxy', '0') == '1',
                'implementation': contract.get('Implementation', ''),
                'abi': contract.get('ABI', '')
            }
        return None

    def get_token_balances(self, address):
        """Get ERC-20 token balances by analyzing transfers."""
        transfers = self.get_token_transfers(address, limit=1000)

        token_balances = {}
        for transfer in transfers:
            token_key = transfer['contract_address']
            if token_key not in token_balances:
                token_balances[token_key] = {
                    'contract_address': transfer['contract_address'],
                    'token_name': transfer['token_name'],
                    'token_symbol': transfer['token_symbol'],
                    'token_decimal': transfer['token_decimal'],
                    'balance': 0,
                    'transfers_in': 0,
                    'transfers_out': 0
                }

            amount = transfer['value']
            if transfer['direction'] == 'in':
                token_balances[token_key]['balance'] += amount
                token_balances[token_key]['transfers_in'] += 1
            else:
                token_balances[token_key]['balance'] -= amount
                token_balances[token_key]['transfers_out'] += 1

        result = []
        for token in token_balances.values():
            if token['balance'] > 0:
                result.append(token)

        return sorted(result, key=lambda x: x['balance'], reverse=True)

    def _format_transactions(self, transactions, address):
        """Format transaction data with full details."""
        formatted = []
        address_lower = address.lower()

        for tx in transactions:
            value_wei = int(tx.get('value', 0))
            value = value_wei / (10 ** self.config['decimals'])
            gas_price_wei = int(tx.get('gasPrice', 0))
            gas_used = int(tx.get('gasUsed', 0))
            gas_fee_wei = gas_price_wei * gas_used
            gas_fee = gas_fee_wei / (10 ** self.config['decimals'])

            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()

            if from_addr == address_lower:
                direction = 'out'
            elif to_addr == address_lower:
                direction = 'in'
            else:
                direction = 'self'

            formatted.append({
                'hash': tx.get('hash', ''),
                'block_number': tx.get('blockNumber', ''),
                'timestamp': int(tx.get('timeStamp', 0)),
                'from': tx.get('from', ''),
                'to': tx.get('to', ''),
                'value_wei': value_wei,
                'value': value,
                'symbol': self.config['symbol'],
                'gas': int(tx.get('gas', 0)),
                'gas_used': gas_used,
                'gas_price_wei': gas_price_wei,
                'gas_price_gwei': gas_price_wei / 1e9,
                'gas_fee_wei': gas_fee_wei,
                'gas_fee': gas_fee,
                'nonce': int(tx.get('nonce', 0)),
                'is_error': tx.get('isError', '0') == '1',
                'tx_receipt_status': tx.get('txreceipt_status', ''),
                'input': tx.get('input', ''),
                'contract_address': tx.get('contractAddress', ''),
                'confirmations': tx.get('confirmations', ''),
                'method_id': tx.get('methodId', ''),
                'function_name': tx.get('functionName', ''),
                'direction': direction
            })
        return formatted

    def _format_internal_transactions(self, transactions, address):
        """Format internal transaction data."""
        formatted = []
        address_lower = address.lower()

        for tx in transactions:
            value_wei = int(tx.get('value', 0))
            value = value_wei / (10 ** self.config['decimals'])

            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()

            if from_addr == address_lower:
                direction = 'out'
            else:
                direction = 'in'

            formatted.append({
                'hash': tx.get('hash', ''),
                'block_number': tx.get('blockNumber', ''),
                'timestamp': int(tx.get('timeStamp', 0)),
                'from': tx.get('from', ''),
                'to': tx.get('to', ''),
                'value_wei': value_wei,
                'value': value,
                'symbol': self.config['symbol'],
                'gas': tx.get('gas', ''),
                'gas_used': tx.get('gasUsed', ''),
                'is_error': tx.get('isError', '0') == '1',
                'trace_id': tx.get('traceId', ''),
                'type': tx.get('type', 'call'),
                'contract_address': tx.get('contractAddress', ''),
                'direction': direction
            })
        return formatted

    def _format_token_transfers(self, transfers, address):
        """Format token transfer data."""
        formatted = []
        address_lower = address.lower()

        for tx in transfers:
            decimals = int(tx.get('tokenDecimal', 18))
            value_raw = int(tx.get('value', 0))
            value = value_raw / (10 ** decimals) if decimals > 0 else value_raw

            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()

            if from_addr == address_lower:
                direction = 'out'
            else:
                direction = 'in'

            formatted.append({
                'hash': tx.get('hash', ''),
                'block_number': tx.get('blockNumber', ''),
                'timestamp': int(tx.get('timeStamp', 0)),
                'from': tx.get('from', ''),
                'to': tx.get('to', ''),
                'value': value,
                'value_raw': value_raw,
                'contract_address': tx.get('contractAddress', ''),
                'token_name': tx.get('tokenName', 'Unknown'),
                'token_symbol': tx.get('tokenSymbol', '???'),
                'token_decimal': decimals,
                'gas': tx.get('gas', ''),
                'gas_price': tx.get('gasPrice', ''),
                'gas_used': tx.get('gasUsed', ''),
                'nonce': tx.get('nonce', ''),
                'direction': direction
            })
        return formatted

    def _format_nft_transfers(self, transfers, address):
        """Format NFT (ERC-721) transfer data."""
        formatted = []
        address_lower = address.lower()

        for tx in transfers:
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()

            if from_addr == address_lower:
                direction = 'out'
            else:
                direction = 'in'

            formatted.append({
                'hash': tx.get('hash', ''),
                'block_number': tx.get('blockNumber', ''),
                'timestamp': int(tx.get('timeStamp', 0)),
                'from': tx.get('from', ''),
                'to': tx.get('to', ''),
                'contract_address': tx.get('contractAddress', ''),
                'token_id': tx.get('tokenID', ''),
                'token_name': tx.get('tokenName', 'Unknown NFT'),
                'token_symbol': tx.get('tokenSymbol', 'NFT'),
                'gas': tx.get('gas', ''),
                'gas_price': tx.get('gasPrice', ''),
                'gas_used': tx.get('gasUsed', ''),
                'direction': direction
            })
        return formatted

    def _format_erc1155_transfers(self, transfers, address):
        """Format ERC-1155 transfer data."""
        formatted = []
        address_lower = address.lower()

        for tx in transfers:
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()

            if from_addr == address_lower:
                direction = 'out'
            else:
                direction = 'in'

            formatted.append({
                'hash': tx.get('hash', ''),
                'block_number': tx.get('blockNumber', ''),
                'timestamp': int(tx.get('timeStamp', 0)),
                'from': tx.get('from', ''),
                'to': tx.get('to', ''),
                'contract_address': tx.get('contractAddress', ''),
                'token_id': tx.get('tokenID', ''),
                'token_value': tx.get('tokenValue', '1'),
                'token_name': tx.get('tokenName', 'Unknown'),
                'token_symbol': tx.get('tokenSymbol', '???'),
                'direction': direction
            })
        return formatted

    def get_address_info(self, address):
        """Get comprehensive address information."""
        balance = self.get_balance(address)
        transactions = self.get_transactions(address, limit=100)
        internal_transactions = self.get_internal_transactions(address, limit=50)
        token_transfers = self.get_token_transfers(address, limit=200)
        token_balances = self.get_token_balances(address)
        nft_transfers = self.get_nft_transfers(address, limit=100)
        erc1155_transfers = self.get_erc1155_transfers(address, limit=50)

        # Calculate statistics
        stats = self._calculate_stats(transactions, internal_transactions, token_transfers, address)

        # Check if contract and get contract info
        contract_info = None
        is_contract = False

        # Detect if this is a contract
        if transactions:
            for tx in transactions:
                if tx['to'] == '' and tx['from'].lower() == address.lower():
                    is_contract = True
                    break

        # If it might be a contract (received txs but never sent), check
        if not is_contract and transactions:
            outgoing = [tx for tx in transactions if tx['direction'] == 'out']
            if len(outgoing) == 0:
                contract_info = self.get_contract_info(address)
                if contract_info and contract_info.get('is_verified'):
                    is_contract = True

        # Get contract info if it's a contract
        if is_contract and not contract_info:
            contract_info = self.get_contract_info(address)

        # Calculate NFT holdings
        nft_holdings = self._calculate_nft_holdings(nft_transfers, address)

        # Get USD prices
        native_price = get_native_price(self.chain_id)
        balance_usd = balance['balance'] * native_price if native_price else 0

        # Get token prices and calculate USD values
        token_symbols = [t['token_symbol'] for t in token_balances]
        token_prices = get_multiple_token_prices(token_symbols) if token_symbols else {}
        total_token_usd = 0
        for token in token_balances:
            symbol = token['token_symbol'].upper()
            price = token_prices.get(symbol, 0)
            token['price_usd'] = price
            token['value_usd'] = token['balance'] * price if price else 0
            total_token_usd += token['value_usd']

        # Get address label and risk score
        address_label = get_address_label(address)
        risk_score = calculate_risk_score(address, transactions, token_transfers)

        # Add labels to interacted addresses
        self._add_labels_to_transactions(transactions)
        self._add_labels_to_transactions(internal_transactions)
        self._add_labels_to_token_transfers(token_transfers)

        # Detect DeFi positions
        defi_positions = detect_defi_positions(token_balances, transactions)
        defi_summary = get_defi_summary(defi_positions)

        return {
            'address': address,
            'chain': self.chain_id,
            'chain_name': self.config['name'],
            'balance': balance,
            'balance_usd': balance_usd,
            'native_price': native_price,
            'is_contract': is_contract,
            'contract_info': contract_info,
            'transactions': transactions,
            'internal_transactions': internal_transactions,
            'token_transfers': token_transfers,
            'token_balances': token_balances,
            'total_token_usd': total_token_usd,
            'total_portfolio_usd': balance_usd + total_token_usd,
            'nft_transfers': nft_transfers,
            'nft_holdings': nft_holdings,
            'erc1155_transfers': erc1155_transfers,
            'stats': stats,
            'tx_count': len(transactions),
            'explorer_url': f"{self.config['explorer_url']}/address/{address}",
            'label': address_label,
            'risk_score': risk_score,
            'defi_positions': defi_positions,
            'defi_summary': defi_summary
        }

    def _add_labels_to_transactions(self, transactions):
        """Add labels to transaction addresses."""
        for tx in transactions:
            tx['from_label'] = get_address_label(tx.get('from', ''))
            tx['to_label'] = get_address_label(tx.get('to', ''))

    def _add_labels_to_token_transfers(self, transfers):
        """Add labels to token transfer addresses."""
        for tx in transfers:
            tx['from_label'] = get_address_label(tx.get('from', ''))
            tx['to_label'] = get_address_label(tx.get('to', ''))

    def _calculate_stats(self, transactions, internal_transactions, token_transfers, address):
        """Calculate address statistics."""
        address_lower = address.lower()

        stats = {
            'total_transactions': len(transactions),
            'total_internal': len(internal_transactions),
            'total_token_transfers': len(token_transfers),
            'outgoing_txs': 0,
            'incoming_txs': 0,
            'total_gas_spent_wei': 0,
            'total_gas_spent': 0,
            'total_value_sent': 0,
            'total_value_received': 0,
            'first_tx_timestamp': None,
            'last_tx_timestamp': None,
            'unique_addresses_interacted': set(),
            'unique_tokens_interacted': set()
        }

        for tx in transactions:
            if tx['from'].lower() == address_lower:
                stats['outgoing_txs'] += 1
                stats['total_gas_spent_wei'] += tx['gas_fee_wei']
                stats['total_value_sent'] += tx['value']
            else:
                stats['incoming_txs'] += 1
                stats['total_value_received'] += tx['value']

            # Track unique addresses
            if tx['from'].lower() != address_lower:
                stats['unique_addresses_interacted'].add(tx['from'].lower())
            if tx['to'] and tx['to'].lower() != address_lower:
                stats['unique_addresses_interacted'].add(tx['to'].lower())

            # Track timestamps
            if tx['timestamp']:
                if stats['first_tx_timestamp'] is None or tx['timestamp'] < stats['first_tx_timestamp']:
                    stats['first_tx_timestamp'] = tx['timestamp']
                if stats['last_tx_timestamp'] is None or tx['timestamp'] > stats['last_tx_timestamp']:
                    stats['last_tx_timestamp'] = tx['timestamp']

        for transfer in token_transfers:
            stats['unique_tokens_interacted'].add(transfer['token_symbol'])

        # Convert sets to counts
        stats['unique_addresses_count'] = len(stats['unique_addresses_interacted'])
        stats['unique_tokens_count'] = len(stats['unique_tokens_interacted'])
        stats['total_gas_spent'] = stats['total_gas_spent_wei'] / 1e18

        del stats['unique_addresses_interacted']
        del stats['unique_tokens_interacted']

        return stats

    def _calculate_nft_holdings(self, nft_transfers, address):
        """Calculate current NFT holdings from transfers."""
        address_lower = address.lower()
        holdings = {}

        for transfer in nft_transfers:
            key = f"{transfer['contract_address']}_{transfer['token_id']}"

            if transfer['direction'] == 'in':
                holdings[key] = {
                    'contract_address': transfer['contract_address'],
                    'token_id': transfer['token_id'],
                    'token_name': transfer['token_name'],
                    'token_symbol': transfer['token_symbol']
                }
            elif key in holdings:
                del holdings[key]

        return list(holdings.values())
