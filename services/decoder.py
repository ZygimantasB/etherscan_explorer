# Transaction decoder for common contract interactions
import re

# Common function signatures (4-byte selectors)
FUNCTION_SIGNATURES = {
    # ERC-20 Token
    '0xa9059cbb': {'name': 'transfer', 'params': ['address', 'uint256'], 'description': 'Transfer tokens'},
    '0x23b872dd': {'name': 'transferFrom', 'params': ['address', 'address', 'uint256'], 'description': 'Transfer tokens from'},
    '0x095ea7b3': {'name': 'approve', 'params': ['address', 'uint256'], 'description': 'Approve token spending'},
    '0x70a08231': {'name': 'balanceOf', 'params': ['address'], 'description': 'Check token balance'},
    '0xdd62ed3e': {'name': 'allowance', 'params': ['address', 'address'], 'description': 'Check token allowance'},

    # Uniswap V2
    '0x38ed1739': {'name': 'swapExactTokensForTokens', 'params': ['uint256', 'uint256', 'address[]', 'address', 'uint256'], 'description': 'Swap exact tokens for tokens'},
    '0x8803dbee': {'name': 'swapTokensForExactTokens', 'params': ['uint256', 'uint256', 'address[]', 'address', 'uint256'], 'description': 'Swap tokens for exact tokens'},
    '0x7ff36ab5': {'name': 'swapExactETHForTokens', 'params': ['uint256', 'address[]', 'address', 'uint256'], 'description': 'Swap exact ETH for tokens'},
    '0xfb3bdb41': {'name': 'swapETHForExactTokens', 'params': ['uint256', 'address[]', 'address', 'uint256'], 'description': 'Swap ETH for exact tokens'},
    '0x18cbafe5': {'name': 'swapExactTokensForETH', 'params': ['uint256', 'uint256', 'address[]', 'address', 'uint256'], 'description': 'Swap exact tokens for ETH'},
    '0x4a25d94a': {'name': 'swapTokensForExactETH', 'params': ['uint256', 'uint256', 'address[]', 'address', 'uint256'], 'description': 'Swap tokens for exact ETH'},
    '0xe8e33700': {'name': 'addLiquidity', 'params': ['address', 'address', 'uint256', 'uint256', 'uint256', 'uint256', 'address', 'uint256'], 'description': 'Add liquidity to pool'},
    '0xf305d719': {'name': 'addLiquidityETH', 'params': ['address', 'uint256', 'uint256', 'uint256', 'address', 'uint256'], 'description': 'Add liquidity with ETH'},
    '0xbaa2abde': {'name': 'removeLiquidity', 'params': ['address', 'address', 'uint256', 'uint256', 'uint256', 'address', 'uint256'], 'description': 'Remove liquidity'},
    '0x02751cec': {'name': 'removeLiquidityETH', 'params': ['address', 'uint256', 'uint256', 'uint256', 'address', 'uint256'], 'description': 'Remove liquidity as ETH'},

    # Uniswap V3
    '0xc04b8d59': {'name': 'exactInput', 'params': ['tuple'], 'description': 'V3 Exact input swap'},
    '0xdb3e2198': {'name': 'exactOutput', 'params': ['tuple'], 'description': 'V3 Exact output swap'},
    '0x414bf389': {'name': 'exactInputSingle', 'params': ['tuple'], 'description': 'V3 Single exact input swap'},
    '0x5023b4df': {'name': 'exactOutputSingle', 'params': ['tuple'], 'description': 'V3 Single exact output swap'},

    # 1inch
    '0x12aa3caf': {'name': 'swap', 'params': ['address', 'tuple', 'bytes', 'bytes'], 'description': '1inch swap'},
    '0x0502b1c5': {'name': 'uniswapV3Swap', 'params': ['uint256', 'uint256', 'uint256[]'], 'description': '1inch V3 swap'},
    '0xe449022e': {'name': 'uniswapV3SwapTo', 'params': ['address', 'uint256', 'uint256', 'uint256[]'], 'description': '1inch V3 swap to'},

    # ERC-721 NFT
    '0x42842e0e': {'name': 'safeTransferFrom', 'params': ['address', 'address', 'uint256'], 'description': 'Safe NFT transfer'},
    '0xb88d4fde': {'name': 'safeTransferFrom', 'params': ['address', 'address', 'uint256', 'bytes'], 'description': 'Safe NFT transfer with data'},
    '0xa22cb465': {'name': 'setApprovalForAll', 'params': ['address', 'bool'], 'description': 'Set NFT approval for all'},

    # ERC-1155
    '0xf242432a': {'name': 'safeTransferFrom', 'params': ['address', 'address', 'uint256', 'uint256', 'bytes'], 'description': 'ERC-1155 transfer'},
    '0x2eb2c2d6': {'name': 'safeBatchTransferFrom', 'params': ['address', 'address', 'uint256[]', 'uint256[]', 'bytes'], 'description': 'ERC-1155 batch transfer'},

    # WETH
    '0xd0e30db0': {'name': 'deposit', 'params': [], 'description': 'Wrap ETH to WETH'},
    '0x2e1a7d4d': {'name': 'withdraw', 'params': ['uint256'], 'description': 'Unwrap WETH to ETH'},

    # Aave
    '0xe8eda9df': {'name': 'deposit', 'params': ['address', 'uint256', 'address', 'uint16'], 'description': 'Aave deposit'},
    '0x69328dec': {'name': 'withdraw', 'params': ['address', 'uint256', 'address'], 'description': 'Aave withdraw'},
    '0xa415bcad': {'name': 'borrow', 'params': ['address', 'uint256', 'uint256', 'uint16', 'address'], 'description': 'Aave borrow'},
    '0x573ade81': {'name': 'repay', 'params': ['address', 'uint256', 'uint256', 'address'], 'description': 'Aave repay'},
    '0x617ba037': {'name': 'supply', 'params': ['address', 'uint256', 'address', 'uint16'], 'description': 'Aave V3 supply'},

    # Compound
    '0x1249c58b': {'name': 'mint', 'params': [], 'description': 'Compound mint (ETH)'},
    '0xa0712d68': {'name': 'mint', 'params': ['uint256'], 'description': 'Compound mint tokens'},
    '0xdb006a75': {'name': 'redeem', 'params': ['uint256'], 'description': 'Compound redeem'},
    '0x852a12e3': {'name': 'redeemUnderlying', 'params': ['uint256'], 'description': 'Compound redeem underlying'},
    '0xc5ebeaec': {'name': 'borrow', 'params': ['uint256'], 'description': 'Compound borrow'},
    '0x0e752702': {'name': 'repayBorrow', 'params': ['uint256'], 'description': 'Compound repay'},

    # Lido
    '0xa1903eab': {'name': 'submit', 'params': ['address'], 'description': 'Stake ETH with Lido'},

    # OpenSea Seaport
    '0xfb0f3ee1': {'name': 'fulfillBasicOrder', 'params': ['tuple'], 'description': 'OpenSea basic order'},
    '0x87201b41': {'name': 'fulfillBasicOrder_efficient_6GL6yc', 'params': ['tuple'], 'description': 'OpenSea basic order'},
    '0xb3a34c4c': {'name': 'fulfillOrder', 'params': ['tuple', 'bytes32'], 'description': 'OpenSea fulfill order'},
    '0xe7acab24': {'name': 'fulfillAdvancedOrder', 'params': ['tuple', 'tuple[]', 'bytes32', 'address'], 'description': 'OpenSea advanced order'},

    # Blur
    '0x9a1fc3a7': {'name': 'execute', 'params': ['tuple', 'tuple'], 'description': 'Blur execute trade'},

    # ENS
    '0xf14fcbc8': {'name': 'commit', 'params': ['bytes32'], 'description': 'ENS commit name'},
    '0x85f6d155': {'name': 'register', 'params': ['string', 'address', 'uint256', 'bytes32', 'address', 'bytes[]', 'bool', 'uint16'], 'description': 'ENS register name'},
    '0xacf1a841': {'name': 'renew', 'params': ['string', 'uint256'], 'description': 'ENS renew name'},
    '0x1896f70a': {'name': 'setResolver', 'params': ['bytes32', 'address'], 'description': 'ENS set resolver'},

    # Multicall
    '0xac9650d8': {'name': 'multicall', 'params': ['bytes[]'], 'description': 'Multicall batch'},
    '0x5ae401dc': {'name': 'multicall', 'params': ['uint256', 'bytes[]'], 'description': 'Multicall with deadline'},
    '0x1f0464d1': {'name': 'multicall', 'params': ['bytes32', 'bytes[]'], 'description': 'Multicall with previous blockhash'},

    # Permit
    '0xd505accf': {'name': 'permit', 'params': ['address', 'address', 'uint256', 'uint256', 'uint8', 'bytes32', 'bytes32'], 'description': 'ERC-20 Permit'},
    '0x8fcbaf0c': {'name': 'permit', 'params': ['address', 'address', 'uint256', 'uint256', 'bool', 'uint8', 'bytes32', 'bytes32'], 'description': 'DAI-style Permit'},
}

# Event signatures (topic0)
EVENT_SIGNATURES = {
    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef': {'name': 'Transfer', 'type': 'ERC-20/721'},
    '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925': {'name': 'Approval', 'type': 'ERC-20/721'},
    '0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31': {'name': 'ApprovalForAll', 'type': 'ERC-721/1155'},
    '0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62': {'name': 'TransferSingle', 'type': 'ERC-1155'},
    '0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb': {'name': 'TransferBatch', 'type': 'ERC-1155'},
    '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822': {'name': 'Swap', 'type': 'Uniswap V2'},
    '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67': {'name': 'Swap', 'type': 'Uniswap V3'},
    '0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c': {'name': 'Deposit', 'type': 'Aave'},
    '0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7': {'name': 'Withdraw', 'type': 'Aave'},
}


def decode_function_call(input_data):
    """Decode function call from transaction input data."""
    if not input_data or input_data == '0x' or len(input_data) < 10:
        return {'type': 'transfer', 'name': 'ETH Transfer', 'description': 'Native token transfer'}

    selector = input_data[:10].lower()
    sig_info = FUNCTION_SIGNATURES.get(selector)

    if sig_info:
        return {
            'type': 'contract_call',
            'selector': selector,
            'name': sig_info['name'],
            'params': sig_info['params'],
            'description': sig_info['description']
        }

    return {
        'type': 'unknown',
        'selector': selector,
        'name': 'Unknown Function',
        'description': f'Unknown contract interaction (selector: {selector})'
    }


def decode_transaction(tx):
    """Decode a transaction and add human-readable information."""
    decoded = {
        'hash': tx.get('hash', ''),
        'from': tx.get('from', ''),
        'to': tx.get('to', ''),
        'value': tx.get('value', 0),
        'input': tx.get('input', '0x')
    }

    # Decode function call
    call_info = decode_function_call(tx.get('input', '0x'))
    decoded['function'] = call_info

    # Determine transaction type
    if not tx.get('to'):
        decoded['tx_type'] = 'contract_creation'
        decoded['description'] = 'Contract deployment'
    elif call_info['type'] == 'transfer':
        decoded['tx_type'] = 'transfer'
        decoded['description'] = f"Sent {tx.get('value', 0)} ETH"
    else:
        decoded['tx_type'] = 'contract_call'
        decoded['description'] = call_info['description']

    return decoded


def get_protocol_name(to_address):
    """Get protocol name from contract address."""
    from services.labels import get_address_label
    label = get_address_label(to_address)
    if label:
        return label.get('name', 'Unknown')
    return None


def categorize_transaction(tx):
    """Categorize transaction by type."""
    input_data = tx.get('input', '0x')
    to_addr = tx.get('to', '').lower()

    # Contract creation
    if not to_addr:
        return 'contract_creation'

    # Simple ETH transfer
    if input_data == '0x' or len(input_data) < 10:
        return 'transfer'

    selector = input_data[:10].lower()

    # Swap transactions
    swap_selectors = ['0x38ed1739', '0x7ff36ab5', '0x18cbafe5', '0xc04b8d59', '0x12aa3caf', '0x0502b1c5']
    if selector in swap_selectors:
        return 'swap'

    # Liquidity
    liquidity_selectors = ['0xe8e33700', '0xf305d719', '0xbaa2abde', '0x02751cec']
    if selector in liquidity_selectors:
        return 'liquidity'

    # NFT transactions
    nft_selectors = ['0x42842e0e', '0xb88d4fde', '0xfb0f3ee1', '0x87201b41', '0x9a1fc3a7']
    if selector in nft_selectors:
        return 'nft'

    # Token approvals
    if selector == '0x095ea7b3':
        return 'approval'

    # Token transfers
    if selector in ['0xa9059cbb', '0x23b872dd']:
        return 'token_transfer'

    # Lending/Borrowing
    lending_selectors = ['0xe8eda9df', '0x69328dec', '0xa415bcad', '0x573ade81', '0x617ba037', '0xa0712d68', '0xdb006a75', '0xc5ebeaec']
    if selector in lending_selectors:
        return 'lending'

    # Staking
    if selector == '0xa1903eab':
        return 'staking'

    return 'other'


def get_transaction_summary(transactions):
    """Get summary of transaction types."""
    summary = {
        'transfer': 0,
        'swap': 0,
        'liquidity': 0,
        'nft': 0,
        'approval': 0,
        'token_transfer': 0,
        'lending': 0,
        'staking': 0,
        'contract_creation': 0,
        'other': 0
    }

    for tx in transactions:
        category = categorize_transaction(tx)
        summary[category] = summary.get(category, 0) + 1

    return summary
