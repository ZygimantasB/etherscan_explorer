from collections import defaultdict
from .blockchain import BlockchainClient


class LinkAnalyzer:
    """Analyzes address relationships and builds graph data for visualization."""

    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.client = BlockchainClient(chain_id)

    def build_graph(self, address, depth=1):
        """
        Build a relationship graph for an address.

        Args:
            address: The central address to analyze
            depth: How many levels of connections to explore (1 = direct only)

        Returns:
            Dict with 'nodes' and 'links' for D3.js visualization
        """
        address = address.lower()
        nodes = {}
        links = []
        link_set = set()  # Prevent duplicate links

        # Get transactions and token transfers
        transactions = self.client.get_transactions(address, limit=100)
        token_transfers = self.client.get_token_transfers(address, limit=100)

        # Add central address as main node
        nodes[address] = {
            'id': address,
            'label': self._shorten_address(address),
            'type': 'central',
            'value': 0,
            'tx_count': 0,
            'is_central': True
        }

        # Process normal transactions
        self._process_transactions(address, transactions, nodes, links, link_set)

        # Process token transfers
        self._process_token_transfers(address, token_transfers, nodes, links, link_set)

        # Calculate node sizes based on interaction count
        self._calculate_node_sizes(nodes, links)

        # Convert nodes dict to list
        nodes_list = list(nodes.values())

        return {
            'nodes': nodes_list,
            'links': links,
            'central_address': address,
            'chain': self.chain_id
        }

    def _process_transactions(self, central_address, transactions, nodes, links, link_set):
        """Process normal transactions to build graph."""
        for tx in transactions:
            from_addr = tx['from'].lower()
            to_addr = tx['to'].lower() if tx['to'] else None

            if not to_addr:
                continue  # Skip contract creation

            # Determine the other party
            if from_addr == central_address:
                other_addr = to_addr
                direction = 'out'
            else:
                other_addr = from_addr
                direction = 'in'

            # Add node for other address
            if other_addr not in nodes:
                nodes[other_addr] = {
                    'id': other_addr,
                    'label': self._shorten_address(other_addr),
                    'type': 'address',
                    'value': 0,
                    'tx_count': 0,
                    'is_central': False
                }

            nodes[other_addr]['tx_count'] += 1
            nodes[other_addr]['value'] += tx['value']

            # Create link
            link_key = tuple(sorted([central_address, other_addr]))
            if link_key not in link_set:
                link_set.add(link_key)
                links.append({
                    'source': from_addr,
                    'target': to_addr,
                    'value': tx['value'],
                    'type': 'transaction',
                    'direction': direction,
                    'symbol': tx['symbol']
                })

    def _process_token_transfers(self, central_address, transfers, nodes, links, link_set):
        """Process token transfers to build graph."""
        # Track token relationships per address
        token_links = defaultdict(lambda: {'tokens': set(), 'count': 0, 'direction': None})

        for tx in transfers:
            from_addr = tx['from'].lower()
            to_addr = tx['to'].lower()

            # Determine the other party
            if from_addr == central_address:
                other_addr = to_addr
                direction = 'out'
            else:
                other_addr = from_addr
                direction = 'in'

            # Add node for other address if not exists
            if other_addr not in nodes:
                nodes[other_addr] = {
                    'id': other_addr,
                    'label': self._shorten_address(other_addr),
                    'type': 'address',
                    'value': 0,
                    'tx_count': 0,
                    'is_central': False,
                    'tokens': []
                }

            # Track token info
            if 'tokens' not in nodes[other_addr]:
                nodes[other_addr]['tokens'] = []

            token_info = f"{tx['token_symbol']}"
            if token_info not in nodes[other_addr].get('tokens', []):
                nodes[other_addr].setdefault('tokens', []).append(token_info)

            token_links[other_addr]['tokens'].add(tx['token_symbol'])
            token_links[other_addr]['count'] += 1
            token_links[other_addr]['direction'] = direction

        # Add token transfer links
        for other_addr, info in token_links.items():
            link_key = ('token', tuple(sorted([central_address, other_addr])))
            if link_key not in link_set:
                link_set.add(link_key)
                links.append({
                    'source': central_address if info['direction'] == 'out' else other_addr,
                    'target': other_addr if info['direction'] == 'out' else central_address,
                    'type': 'token_transfer',
                    'tokens': list(info['tokens']),
                    'count': info['count'],
                    'direction': info['direction']
                })

    def _calculate_node_sizes(self, nodes, links):
        """Calculate node sizes based on interaction frequency."""
        # Count links per node
        link_counts = defaultdict(int)
        for link in links:
            source = link['source']
            target = link['target']
            link_counts[source] += 1
            link_counts[target] += 1

        # Set size attribute (min 10, max 50)
        for node_id, node in nodes.items():
            count = link_counts.get(node_id, 1)
            if node['is_central']:
                node['size'] = 50  # Central node is always largest
            else:
                node['size'] = min(10 + count * 5, 40)

    def _shorten_address(self, address):
        """Shorten address for display."""
        if len(address) > 10:
            return f"{address[:6]}...{address[-4:]}"
        return address

    def expand_node(self, address, existing_nodes=None):
        """
        Get connections for a specific node to expand the graph.

        Args:
            address: The address to expand from
            existing_nodes: List of node IDs already in the graph (to avoid duplicates)

        Returns:
            Dict with new 'nodes' and 'links' to add to the graph
        """
        address = address.lower()
        existing_nodes = set(n.lower() for n in (existing_nodes or []))

        nodes = {}
        links = []
        link_set = set()

        # Get transactions and token transfers for this address
        transactions = self.client.get_transactions(address, limit=50)
        token_transfers = self.client.get_token_transfers(address, limit=50)

        # Mark this node as expanded
        nodes[address] = {
            'id': address,
            'label': self._shorten_address(address),
            'type': 'expanded',
            'value': 0,
            'tx_count': 0,
            'is_central': False,
            'is_expanded': True
        }

        # Process transactions
        for tx in transactions:
            from_addr = tx['from'].lower()
            to_addr = tx['to'].lower() if tx['to'] else None

            if not to_addr:
                continue

            if from_addr == address:
                other_addr = to_addr
                direction = 'out'
            else:
                other_addr = from_addr
                direction = 'in'

            # Add new node if not already in graph
            if other_addr not in nodes and other_addr not in existing_nodes:
                nodes[other_addr] = {
                    'id': other_addr,
                    'label': self._shorten_address(other_addr),
                    'type': 'address',
                    'value': tx['value'],
                    'tx_count': 1,
                    'is_central': False,
                    'is_expanded': False
                }
            elif other_addr in nodes:
                nodes[other_addr]['tx_count'] += 1
                nodes[other_addr]['value'] += tx['value']

            # Create link
            link_key = tuple(sorted([address, other_addr]))
            if link_key not in link_set:
                link_set.add(link_key)
                links.append({
                    'source': from_addr,
                    'target': to_addr,
                    'value': tx['value'],
                    'type': 'transaction',
                    'direction': direction,
                    'symbol': tx['symbol']
                })

        # Process token transfers
        token_links = defaultdict(lambda: {'tokens': set(), 'count': 0, 'direction': None})

        for tx in token_transfers:
            from_addr = tx['from'].lower()
            to_addr = tx['to'].lower()

            if from_addr == address:
                other_addr = to_addr
                direction = 'out'
            else:
                other_addr = from_addr
                direction = 'in'

            if other_addr not in nodes and other_addr not in existing_nodes:
                nodes[other_addr] = {
                    'id': other_addr,
                    'label': self._shorten_address(other_addr),
                    'type': 'address',
                    'value': 0,
                    'tx_count': 0,
                    'is_central': False,
                    'is_expanded': False,
                    'tokens': [tx['token_symbol']]
                }
            elif other_addr in nodes:
                if 'tokens' not in nodes[other_addr]:
                    nodes[other_addr]['tokens'] = []
                if tx['token_symbol'] not in nodes[other_addr]['tokens']:
                    nodes[other_addr]['tokens'].append(tx['token_symbol'])

            token_links[other_addr]['tokens'].add(tx['token_symbol'])
            token_links[other_addr]['count'] += 1
            token_links[other_addr]['direction'] = direction

        # Add token transfer links
        for other_addr, info in token_links.items():
            link_key = ('token', tuple(sorted([address, other_addr])))
            if link_key not in link_set:
                link_set.add(link_key)
                links.append({
                    'source': address if info['direction'] == 'out' else other_addr,
                    'target': other_addr if info['direction'] == 'out' else address,
                    'type': 'token_transfer',
                    'tokens': list(info['tokens']),
                    'count': info['count'],
                    'direction': info['direction']
                })

        # Calculate sizes for new nodes
        self._calculate_node_sizes(nodes, links)

        # Remove the expanded node from new nodes (it already exists)
        if address in nodes:
            del nodes[address]

        return {
            'nodes': list(nodes.values()),
            'links': links,
            'expanded_address': address
        }

    def get_related_addresses(self, address, limit=20):
        """Get list of most related addresses with statistics."""
        address = address.lower()
        relationships = defaultdict(lambda: {
            'address': '',
            'tx_count': 0,
            'token_count': 0,
            'total_value': 0,
            'tokens': set(),
            'directions': {'in': 0, 'out': 0}
        })

        transactions = self.client.get_transactions(address, limit=100)
        token_transfers = self.client.get_token_transfers(address, limit=100)

        # Process transactions
        for tx in transactions:
            from_addr = tx['from'].lower()
            to_addr = tx['to'].lower() if tx['to'] else None

            if not to_addr:
                continue

            if from_addr == address:
                other = to_addr
                direction = 'out'
            else:
                other = from_addr
                direction = 'in'

            relationships[other]['address'] = other
            relationships[other]['tx_count'] += 1
            relationships[other]['total_value'] += tx['value']
            relationships[other]['directions'][direction] += 1

        # Process token transfers
        for tx in token_transfers:
            from_addr = tx['from'].lower()
            to_addr = tx['to'].lower()

            if from_addr == address:
                other = to_addr
            else:
                other = from_addr

            relationships[other]['address'] = other
            relationships[other]['token_count'] += 1
            relationships[other]['tokens'].add(tx['token_symbol'])

        # Convert to list and sort by interaction count
        result = []
        for addr, data in relationships.items():
            data['tokens'] = list(data['tokens'])
            data['short_address'] = self._shorten_address(addr)
            result.append(data)

        # Sort by total interactions
        result.sort(key=lambda x: x['tx_count'] + x['token_count'], reverse=True)

        return result[:limit]
