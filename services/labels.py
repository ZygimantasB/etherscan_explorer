# Known wallet labels database
# Categories: exchange, defi, bridge, nft, scam, mixer, whale, contract

KNOWN_ADDRESSES = {
    # Major Exchanges
    '0x28c6c06298d514db089934071355e5743bf21d60': {'name': 'Binance 14', 'category': 'exchange', 'risk': 'low'},
    '0x21a31ee1afc51d94c2efccaa2092ad1028285549': {'name': 'Binance 15', 'category': 'exchange', 'risk': 'low'},
    '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': {'name': 'Binance 16', 'category': 'exchange', 'risk': 'low'},
    '0x56eddb7aa87536c09ccc2793473599fd21a8b17f': {'name': 'Binance 17', 'category': 'exchange', 'risk': 'low'},
    '0x9696f59e4d72e237be84ffd425dcad154bf96976': {'name': 'Binance 18', 'category': 'exchange', 'risk': 'low'},
    '0x4976a4a02f38326660d17bf34b431dc6e2eb2327': {'name': 'Binance 19', 'category': 'exchange', 'risk': 'low'},
    '0xd551234ae421e3bcba99a0da6d736074f22192ff': {'name': 'Binance 20', 'category': 'exchange', 'risk': 'low'},
    '0x503828976d22510aad0201ac7ec88293211d23da': {'name': 'Coinbase 1', 'category': 'exchange', 'risk': 'low'},
    '0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740': {'name': 'Coinbase 2', 'category': 'exchange', 'risk': 'low'},
    '0x3cd751e6b0078be393132286c442345e5dc49699': {'name': 'Coinbase 3', 'category': 'exchange', 'risk': 'low'},
    '0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511': {'name': 'Coinbase 4', 'category': 'exchange', 'risk': 'low'},
    '0xeb2629a2734e272bcc07bda959863f316f4bd4cf': {'name': 'Coinbase 5', 'category': 'exchange', 'risk': 'low'},
    '0x02466e547bfdab679fc49e96bbfc62b9747d997c': {'name': 'Coinbase 6', 'category': 'exchange', 'risk': 'low'},
    '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43': {'name': 'Coinbase 7', 'category': 'exchange', 'risk': 'low'},
    '0x77134cbc06cb00b66f4c7e623d5fdbf6777635ec': {'name': 'Coinbase 8', 'category': 'exchange', 'risk': 'low'},
    '0x7c195d981abfdc3ddecd2ca0fed0958430488e34': {'name': 'Coinbase 9', 'category': 'exchange', 'risk': 'low'},
    '0x95a9bd206ae52c4ba8eecfc93d18eacdd41c88cc': {'name': 'Coinbase 10', 'category': 'exchange', 'risk': 'low'},
    '0x2910543af39aba0cd09dbb2d50200b3e800a63d2': {'name': 'Kraken', 'category': 'exchange', 'risk': 'low'},
    '0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13': {'name': 'Kraken 2', 'category': 'exchange', 'risk': 'low'},
    '0xe853c56864a2ebe4576a807d26fdc4a0ada51919': {'name': 'Kraken 3', 'category': 'exchange', 'risk': 'low'},
    '0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0': {'name': 'Kraken 4', 'category': 'exchange', 'risk': 'low'},
    '0xfa52274dd61e1643d2205169732f29114bc240b3': {'name': 'Kraken 5', 'category': 'exchange', 'risk': 'low'},
    '0x53d284357ec70ce289d6d64134dfac8e511c8a3d': {'name': 'Kraken 6', 'category': 'exchange', 'risk': 'low'},
    '0x89e51fa8ca5d66cd220baed62ed01e8951aa7c40': {'name': 'Kraken 7', 'category': 'exchange', 'risk': 'low'},
    '0xc6bed363b30df7f35b601a5547fe56cd31ec63da': {'name': 'Kraken 8', 'category': 'exchange', 'risk': 'low'},
    '0x29728d0efd284d85187362faa2d4d76c2cfc2612': {'name': 'Kraken 9', 'category': 'exchange', 'risk': 'low'},
    '0xae2d4617c862309a3d75a0ffb358c7a5009c673f': {'name': 'Kraken 10', 'category': 'exchange', 'risk': 'low'},
    '0x1151314c646ce4e0efd76d1af4760ae66a9fe30f': {'name': 'Bitfinex', 'category': 'exchange', 'risk': 'low'},
    '0x742d35cc6634c0532925a3b844bc454e4438f44e': {'name': 'Bitfinex 2', 'category': 'exchange', 'risk': 'low'},
    '0x876eabf441b2ee5b5b0554fd502a8e0600950cfa': {'name': 'Bitfinex 3', 'category': 'exchange', 'risk': 'low'},
    '0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98': {'name': 'Bittrex', 'category': 'exchange', 'risk': 'low'},
    '0xe94b04a0fed112f3664e45adb2b8915693dd5ff3': {'name': 'Bittrex 2', 'category': 'exchange', 'risk': 'low'},
    '0x0681d8db095565fe8a346fa0277bffde9c0edbbf': {'name': 'KuCoin', 'category': 'exchange', 'risk': 'low'},
    '0xd6216fc19db775df9774a6e33526131da7d19a2c': {'name': 'KuCoin 2', 'category': 'exchange', 'risk': 'low'},
    '0xf16e9b0d03470827a95cdfd0cb8a8a3b46969b91': {'name': 'KuCoin 3', 'category': 'exchange', 'risk': 'low'},
    '0x88ff79eb2bc5850f27315415da8685282c7610f9': {'name': 'KuCoin 4', 'category': 'exchange', 'risk': 'low'},
    '0x2b5634c42055806a59e9107ed44d43c426e58258': {'name': 'KuCoin 5', 'category': 'exchange', 'risk': 'low'},
    '0x689c56aef474df92d44a1b70850f808488f9769c': {'name': 'KuCoin 6', 'category': 'exchange', 'risk': 'low'},
    '0xa7efae728d2936e78bda97dc267687568dd593f3': {'name': 'OKX', 'category': 'exchange', 'risk': 'low'},
    '0x6cc5f688a315f3dc28a7781717a9a798a59fda7b': {'name': 'OKX 2', 'category': 'exchange', 'risk': 'low'},
    '0x236f9f97e0e62388479bf9e5ba4889e46b0273c3': {'name': 'OKX 3', 'category': 'exchange', 'risk': 'low'},
    '0x98ec059dc3adfbdd63429454aeb0c990fba4a128': {'name': 'OKX 4', 'category': 'exchange', 'risk': 'low'},
    '0x5041ed759dd4afc3a72b8192c143f72f4724081a': {'name': 'OKX 5', 'category': 'exchange', 'risk': 'low'},
    '0xf89d7b9c864f589bbf53a82105107622b35eaa40': {'name': 'Bybit', 'category': 'exchange', 'risk': 'low'},
    '0x1db92e2eebc8e0c075a02bea49a2935bcd2dfcf4': {'name': 'Gate.io', 'category': 'exchange', 'risk': 'low'},
    '0xd793281182a0e3e023116004778f45c29fc14f19': {'name': 'Gate.io 2', 'category': 'exchange', 'risk': 'low'},
    '0x0d0707963952f2fba59dd06f2b425ace40b492fe': {'name': 'Gate.io 3', 'category': 'exchange', 'risk': 'low'},
    '0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c': {'name': 'Gate.io 4', 'category': 'exchange', 'risk': 'low'},
    '0xd24400ae8bfebb18ca49be86258a3c749cf46853': {'name': 'Gemini', 'category': 'exchange', 'risk': 'low'},
    '0x6fc82a5fe25a5cdb58bc74600a40a69c065263f8': {'name': 'Gemini 2', 'category': 'exchange', 'risk': 'low'},
    '0x61edcdf5bb737adffe5043706e7c5bb1f1a56eea': {'name': 'Gemini 3', 'category': 'exchange', 'risk': 'low'},
    '0x5f65f7b609678448494de4c87521cdf6cef1e932': {'name': 'Gemini 4', 'category': 'exchange', 'risk': 'low'},
    '0xb302bfe9c246c6e150af70b1caaa5e3df60dac05': {'name': 'Gemini 5', 'category': 'exchange', 'risk': 'low'},
    '0x8d6f396d210d385033b348bcae9e4f9ea4e045bd': {'name': 'Gemini 6', 'category': 'exchange', 'risk': 'low'},
    '0xd69b0089d9ca950640f5dc9931a41a5965f00303': {'name': 'Gemini 7', 'category': 'exchange', 'risk': 'low'},

    # DeFi Protocols
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': {'name': 'Uniswap V2 Router', 'category': 'defi', 'risk': 'low'},
    '0xe592427a0aece92de3edee1f18e0157c05861564': {'name': 'Uniswap V3 Router', 'category': 'defi', 'risk': 'low'},
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45': {'name': 'Uniswap V3 Router 2', 'category': 'defi', 'risk': 'low'},
    '0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b': {'name': 'Uniswap Universal Router', 'category': 'defi', 'risk': 'low'},
    '0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad': {'name': 'Uniswap Universal Router 2', 'category': 'defi', 'risk': 'low'},
    '0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f': {'name': 'SushiSwap Router', 'category': 'defi', 'risk': 'low'},
    '0x1111111254fb6c44bac0bed2854e76f90643097d': {'name': '1inch Router V4', 'category': 'defi', 'risk': 'low'},
    '0x1111111254eeb25477b68fb85ed929f73a960582': {'name': '1inch Router V5', 'category': 'defi', 'risk': 'low'},
    '0xdef1c0ded9bec7f1a1670819833240f027b25eff': {'name': '0x Exchange Proxy', 'category': 'defi', 'risk': 'low'},
    '0x881d40237659c251811cec9c364ef91dc08d300c': {'name': 'Metamask Swap Router', 'category': 'defi', 'risk': 'low'},
    '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': {'name': 'Aave V2 Pool', 'category': 'defi', 'risk': 'low'},
    '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2': {'name': 'Aave V3 Pool', 'category': 'defi', 'risk': 'low'},
    '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643': {'name': 'Compound cDAI', 'category': 'defi', 'risk': 'low'},
    '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5': {'name': 'Compound cETH', 'category': 'defi', 'risk': 'low'},
    '0xccf4429db6322d5c611ee964527d42e5d685dd6a': {'name': 'Compound cWBTC', 'category': 'defi', 'risk': 'low'},
    '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': {'name': 'WETH', 'category': 'defi', 'risk': 'low'},
    '0xae7ab96520de3a18e5e111b5eaab095312d7fe84': {'name': 'Lido stETH', 'category': 'defi', 'risk': 'low'},
    '0xbe9895146f7af43049ca1c1ae358b0541ea49704': {'name': 'Coinbase cbETH', 'category': 'defi', 'risk': 'low'},
    '0xae78736cd615f374d3085123a210448e74fc6393': {'name': 'Rocket Pool rETH', 'category': 'defi', 'risk': 'low'},
    '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': {'name': 'USDC', 'category': 'defi', 'risk': 'low'},
    '0xdac17f958d2ee523a2206206994597c13d831ec7': {'name': 'USDT', 'category': 'defi', 'risk': 'low'},
    '0x6b175474e89094c44da98b954eedeac495271d0f': {'name': 'DAI', 'category': 'defi', 'risk': 'low'},
    '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': {'name': 'WBTC', 'category': 'defi', 'risk': 'low'},
    '0x5a98fcbea516cf06857215779fd812ca3bef1b32': {'name': 'Lido DAO', 'category': 'defi', 'risk': 'low'},

    # Bridges
    '0x8484ef722627bf18ca5ae6bcf031c23e6e922b30': {'name': 'Arbitrum Bridge', 'category': 'bridge', 'risk': 'low'},
    '0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f': {'name': 'Arbitrum Inbox', 'category': 'bridge', 'risk': 'low'},
    '0x99c9fc46f92e8a1c0dec1b1747d010903e884be1': {'name': 'Optimism Bridge', 'category': 'bridge', 'risk': 'low'},
    '0x5e4e65926ba27467555eb562121fac00d24e9dd2': {'name': 'Polygon Bridge', 'category': 'bridge', 'risk': 'low'},
    '0x401f6c983ea34274ec46f84d70b31c151321188b': {'name': 'zkSync Bridge', 'category': 'bridge', 'risk': 'low'},
    '0x3ee18b2214aff97000d974cf647e7c347e8fa585': {'name': 'Wormhole Bridge', 'category': 'bridge', 'risk': 'medium'},
    '0x3014ca10b91cb3d0ad85fef7a3cb95bcac9c0f79': {'name': 'Multichain Bridge', 'category': 'bridge', 'risk': 'high'},
    '0x5427fefa711eff984124bfbb1ab6fbf5e3da1820': {'name': 'cBridge', 'category': 'bridge', 'risk': 'medium'},
    '0x0a9f824c05a74f577a536a8a0c673183a872dff4': {'name': 'Across Bridge', 'category': 'bridge', 'risk': 'low'},
    '0x32400084c286cf3e17e7b677ea9583e60a000324': {'name': 'zkSync Era Bridge', 'category': 'bridge', 'risk': 'low'},
    '0xabea9132b05a70803a4e85094fd0e1800777fbef': {'name': 'zkSync Lite', 'category': 'bridge', 'risk': 'low'},

    # NFT Marketplaces
    '0x00000000006c3852cbef3e08e8df289169ede581': {'name': 'OpenSea Seaport', 'category': 'nft', 'risk': 'low'},
    '0x00000000000001ad428e4906ae43d8f9852d0dd6': {'name': 'OpenSea Seaport 1.4', 'category': 'nft', 'risk': 'low'},
    '0x00000000000000adc04c56bf30ac9d3c0aaf14dc': {'name': 'OpenSea Seaport 1.5', 'category': 'nft', 'risk': 'low'},
    '0x7be8076f4ea4a4ad08075c2508e481d6c946d12b': {'name': 'OpenSea Wyvern', 'category': 'nft', 'risk': 'low'},
    '0x7f268357a8c2552623316e2562d90e642bb538e5': {'name': 'OpenSea Wyvern V2', 'category': 'nft', 'risk': 'low'},
    '0x74312363e45dcaba76c59ec49a7aa8a65a67eed3': {'name': 'X2Y2', 'category': 'nft', 'risk': 'low'},
    '0x59728544b08ab483533076417fbbb2fd0b17ce3a': {'name': 'LooksRare', 'category': 'nft', 'risk': 'low'},
    '0x0000000000e655fae4d56241588680f86e3b2377': {'name': 'LooksRare V2', 'category': 'nft', 'risk': 'low'},
    '0x29469395eaf6f95920e59f858042f0e28d98a20b': {'name': 'Blur Pool', 'category': 'nft', 'risk': 'low'},
    '0x000000000000ad05ccc4f10045630fb830b95127': {'name': 'Blur Marketplace', 'category': 'nft', 'risk': 'low'},
    '0xb4fbf271143f4fbf7b91a5ded31805e42b2208d6': {'name': 'Blur Bidding', 'category': 'nft', 'risk': 'low'},

    # Mixers / High Risk
    '0xd90e2f925da726b50c4ed8d0fb90ad053324f31b': {'name': 'Tornado Cash Router', 'category': 'mixer', 'risk': 'high'},
    '0x722122df12d4e14e13ac3b6895a86e84145b6967': {'name': 'Tornado Cash Proxy', 'category': 'mixer', 'risk': 'high'},
    '0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc': {'name': 'Tornado Cash 0.1 ETH', 'category': 'mixer', 'risk': 'high'},
    '0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936': {'name': 'Tornado Cash 1 ETH', 'category': 'mixer', 'risk': 'high'},
    '0x910cbd523d972eb0a6f4cae4618ad62622b39dbf': {'name': 'Tornado Cash 10 ETH', 'category': 'mixer', 'risk': 'high'},
    '0xa160cdab225685da1d56aa342ad8841c3b53f291': {'name': 'Tornado Cash 100 ETH', 'category': 'mixer', 'risk': 'high'},

    # Known Scam/Exploit Addresses
    '0x098b716b8aaf21512996dc57eb0615e2383e2f96': {'name': 'Ronin Exploiter', 'category': 'scam', 'risk': 'critical'},
    '0x59abf3837fa962d6853b4cc0a19513aa031fd32b': {'name': 'Euler Exploiter', 'category': 'scam', 'risk': 'critical'},
    '0xb5c8678386c17847e2e7b48b90c29c7f5e4e1d3b': {'name': 'Nomad Bridge Exploiter', 'category': 'scam', 'risk': 'critical'},
}


def get_address_label(address):
    """Get label for an address if known."""
    if not address:
        return None
    return KNOWN_ADDRESSES.get(address.lower())


def get_address_labels_batch(addresses):
    """Get labels for multiple addresses."""
    result = {}
    for addr in addresses:
        label = get_address_label(addr)
        if label:
            result[addr.lower()] = label
    return result


def get_category_color(category):
    """Get display color for category."""
    colors = {
        'exchange': '#28a745',  # Green
        'defi': '#17a2b8',       # Cyan
        'bridge': '#6f42c1',     # Purple
        'nft': '#fd7e14',        # Orange
        'mixer': '#dc3545',      # Red
        'scam': '#dc3545',       # Red
        'whale': '#ffc107',      # Yellow
        'contract': '#6c757d'    # Gray
    }
    return colors.get(category, '#6c757d')


def get_risk_level(category, address=None):
    """Determine risk level for an address."""
    if address:
        label = get_address_label(address)
        if label:
            return label.get('risk', 'unknown')

    high_risk_categories = ['mixer', 'scam']
    if category in high_risk_categories:
        return 'high'

    return 'low'


def get_category_addresses(category):
    """Get all addresses for a specific category."""
    return {
        addr: info for addr, info in KNOWN_ADDRESSES.items()
        if info['category'] == category
    }


def calculate_risk_score(address, transactions=None, token_transfers=None):
    """
    Calculate risk score for an address (0-100).
    Factors:
    - Direct label risk
    - Interactions with high-risk addresses
    - Transaction patterns
    """
    risk_points = 0
    risk_factors = []

    # Check direct address label
    label = get_address_label(address)
    if label:
        risk_level = label.get('risk', 'low')
        if risk_level == 'critical':
            return {'score': 100, 'level': 'critical', 'factors': [f"Known {label['category']}: {label['name']}"]}
        elif risk_level == 'high':
            risk_points += 70
            risk_factors.append(f"Known high-risk: {label['name']}")
        elif risk_level == 'medium':
            risk_points += 30
            risk_factors.append(f"Known {label['category']}: {label['name']}")

    # Check interactions with known addresses
    if transactions:
        mixer_interactions = 0
        scam_interactions = 0
        exchange_interactions = 0

        for tx in transactions:
            counterparty = tx.get('to') if tx.get('direction') == 'out' else tx.get('from')
            counterparty_label = get_address_label(counterparty)

            if counterparty_label:
                category = counterparty_label.get('category')
                if category == 'mixer':
                    mixer_interactions += 1
                elif category == 'scam':
                    scam_interactions += 1
                elif category == 'exchange':
                    exchange_interactions += 1

        if mixer_interactions > 0:
            risk_points += min(mixer_interactions * 15, 40)
            risk_factors.append(f"{mixer_interactions} mixer interaction(s)")

        if scam_interactions > 0:
            risk_points += min(scam_interactions * 20, 50)
            risk_factors.append(f"{scam_interactions} scam address interaction(s)")

    # Check token transfer patterns
    if token_transfers:
        unique_tokens = set()
        for transfer in token_transfers:
            unique_tokens.add(transfer.get('token_symbol', ''))

        # Many different tokens could indicate airdrop farming or scam tokens
        if len(unique_tokens) > 50:
            risk_points += 10
            risk_factors.append("High token diversity (50+ unique tokens)")

    # Determine risk level
    if risk_points >= 70:
        level = 'high'
    elif risk_points >= 40:
        level = 'medium'
    elif risk_points >= 10:
        level = 'low'
    else:
        level = 'minimal'

    return {
        'score': min(risk_points, 100),
        'level': level,
        'factors': risk_factors
    }


def search_labels(query):
    """Search labels by name or category."""
    query = query.lower()
    results = []
    for addr, info in KNOWN_ADDRESSES.items():
        if query in info['name'].lower() or query in info['category'].lower():
            results.append({'address': addr, **info})
    return results
