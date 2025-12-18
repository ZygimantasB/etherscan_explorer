import requests
from config import get_chain_config


class BlockchainClient:
    """Client for interacting with blockchain explorer APIs (Etherscan-like)."""

    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.config = get_chain_config(chain_id)
        if not self.config:
            raise ValueError(f"Unsupported chain: {chain_id}")

        self.api_url = self.config['api_url']
        self.api_key = self.config['api_key']

    def _make_request(self, params):
        """Make API request with common parameters."""
        params['apikey'] = self.api_key
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
            # Convert from wei to native token
            balance_wei = int(result)
            balance = balance_wei / (10 ** self.config['decimals'])
            return {
                'balance_wei': balance_wei,
                'balance': balance,
                'symbol': self.config['symbol']
            }
        return {'balance_wei': 0, 'balance': 0, 'symbol': self.config['symbol']}

    def get_transactions(self, address, limit=50):
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
            return self._format_transactions(transactions)
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
            return self._format_transactions(transactions, is_internal=True)
        return []

    def get_token_transfers(self, address, limit=100):
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
            return self._format_token_transfers(transfers)
        return []

    def get_token_balances(self, address):
        """
        Get ERC-20 token balances.
        Note: This requires getting token transfers and calculating balances,
        as the free API doesn't have a direct token balance endpoint.
        """
        transfers = self.get_token_transfers(address, limit=1000)

        # Calculate balances from transfers
        token_balances = {}
        for transfer in transfers:
            token_key = transfer['contract_address']
            if token_key not in token_balances:
                token_balances[token_key] = {
                    'contract_address': transfer['contract_address'],
                    'token_name': transfer['token_name'],
                    'token_symbol': transfer['token_symbol'],
                    'token_decimal': transfer['token_decimal'],
                    'balance': 0
                }

            # Add or subtract based on direction
            amount = transfer['value']
            if transfer['to'].lower() == address.lower():
                token_balances[token_key]['balance'] += amount
            else:
                token_balances[token_key]['balance'] -= amount

        # Filter out zero balances and format
        result = []
        for token in token_balances.values():
            if token['balance'] > 0:
                result.append(token)

        return sorted(result, key=lambda x: x['balance'], reverse=True)

    def _format_transactions(self, transactions, is_internal=False):
        """Format transaction data."""
        formatted = []
        for tx in transactions:
            value_wei = int(tx.get('value', 0))
            value = value_wei / (10 ** self.config['decimals'])

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
                'gas_price': tx.get('gasPrice', ''),
                'is_error': tx.get('isError', '0') == '1',
                'is_internal': is_internal,
                'method': tx.get('functionName', '').split('(')[0] if tx.get('functionName') else ''
            })
        return formatted

    def _format_token_transfers(self, transfers):
        """Format token transfer data."""
        formatted = []
        for tx in transfers:
            decimals = int(tx.get('tokenDecimal', 18))
            value_raw = int(tx.get('value', 0))
            value = value_raw / (10 ** decimals)

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
                'token_decimal': decimals
            })
        return formatted

    def get_address_info(self, address):
        """Get comprehensive address information."""
        balance = self.get_balance(address)
        transactions = self.get_transactions(address, limit=25)
        token_transfers = self.get_token_transfers(address, limit=100)
        token_balances = self.get_token_balances(address)

        # Determine if address is a contract
        is_contract = False
        if transactions:
            # If address has created contracts or has no outgoing txs, might be contract
            for tx in transactions:
                if tx['to'] == '' and tx['from'].lower() == address.lower():
                    is_contract = True
                    break

        return {
            'address': address,
            'chain': self.chain_id,
            'chain_name': self.config['name'],
            'balance': balance,
            'is_contract': is_contract,
            'transactions': transactions,
            'token_transfers': token_transfers,
            'token_balances': token_balances,
            'tx_count': len(transactions),
            'explorer_url': f"{self.config['explorer_url']}/address/{address}"
        }
