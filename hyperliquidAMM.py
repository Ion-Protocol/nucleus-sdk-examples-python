# =======================================
# Nucleus SDK Python Uniswap Swap Example
# =======================================

# Import the Nucleus SDK Python Client
from nucleus_sdk_python.client import Client
import os
from dotenv import load_dotenv
import time
from eth_abi.packed import encode_packed
from web3 import Web3

load_dotenv()

def main():
    # You will need an API key to use the Nucleus API. 
    # This example assumes you have an API key in your .env file.
    api_key = os.environ["API_KEY"]

    # Initialize the Nucleus SDK Python Client using the API key
    client = Client(api_key)

    # Define the chain ID for your manager call.
    chain_id = "999"
    
    # Define the strategist that will call the manager contract for your manager call object.
    # Each strategist will have a root that is published onchain and limits what calls can be made.
    strategist_address = os.environ["STRATEGIST_ADDRESS"]
    
    # Define the boring vault symbol you will conduct your manager call on.
    symbol = "TLP"

    # Create the calldata queue object.
    calldata_queue = client.create_calldata_queue(
        chain_id=chain_id,
        strategist_address=strategist_address,
        rpc_url=os.environ["RPC_URL"],
        symbol=symbol
    )

    # Each client comes with a built in address book.
    # The address book is a dictionary that maps chain IDs to protocols to a list of addresses.
    address_book = client.address_book
    router = address_book[chain_id]["hyperswap"]["router"]
    nft_manager = address_book[chain_id]["hyperswap"]["nonfungiblePositionManager"]
    WHYPE = address_book[chain_id]["token"]["WHYPE"]
    stHYPE = address_book[chain_id]["token"]["stHYPE"]
    boring_vault = address_book[chain_id]["nucleus"]["TLP"]["boring_vault"]

    # approve the router and manager to spend max stHYPE
    calldata_queue.add_call(
        WHYPE,
        "approve(address,uint256)",
        [router, int(115792089237316195423570985008687907853269984665640564039457584007913129639935)],
        0
    )

    calldata_queue.add_call(
        stHYPE,
        "approve(address,uint256)",
        [nft_manager, int(115792089237316195423570985008687907853269984665640564039457584007913129639935)],
        0
    )
    calldata_queue.add_call(
        WHYPE,
        "approve(address,uint256)",
        [nft_manager, int(115792089237316195423570985008687907853269984665640564039457584007913129639935)],
        0
    )

    # The following is the ExactInputParams struct which is the parameter for a uniswap v3 ExactInput call.
    #  struct ExactInputParams {
    #     bytes path;
    #     address recipient;
    #     uint256 deadline;
    #     uint256 amountIn;
    #     uint256 amountOutMinimum;
    # }

    exact_input_params = [
        bytes.fromhex('5555555555555555555555555555555555555555000064fFaa4a3D97fE9107Cef8a3F48c069F577Ff76cC1'),  # path WHYPE -> stHYPE
        boring_vault,  # recipient
        int(time.time()) + 1800,  # deadline
        Web3.to_wei(2, 'ether'),  # amountIn
        0  # amountOutMinimum
    ]

    # Execute swap
    calldata_queue.add_call(
        router,
        "exactInput((bytes,address,uint256,uint256,uint256))",
        [exact_input_params],
        0
    )

    # Create mint parameters struct for WHYPE/stHYPE pool
    # Parameters: token0, token1, fee, tickLower, tickUpper, amount0Desired, amount1Desired, amount0Min, amount1Min, recipient, deadline
    mint_params = [
        WHYPE,  # token0 (assuming WHYPE address is lower than stHYPE)
        stHYPE,  # token1
        100,    # fee (0.01%)
        -414480,  # tickLower (example tick range, adjust as needed)
        414480,   # tickUpper
        Web3.to_wei(0.11, 'ether'),  # amount0Desired
        Web3.to_wei(0.11, 'ether'),  # amount1Desired
        0,      # amount0Min
        0,      # amount1Min
        boring_vault,  # recipient
        int(time.time()) + 1800  # deadline (30 minutes from now)
    ]

    # Mint initial position
    calldata_queue.add_call(
        nft_manager,
        "mint((address,address,uint24,int24,int24,uint256,uint256,uint256,uint256,address,uint256))",
        [mint_params],
        0
    )

    # Create a web3.py provider to get the expected token id
    w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
    nft_manager_abi = [{"inputs": [], "name": "totalSupply", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
    token_id = w3.eth.contract(address=nft_manager, abi=nft_manager_abi).functions.totalSupply().call()

    # Create increaseLiquidity parameters
    # Parameters: tokenId, amount0Desired, amount1Desired, amount0Min, amount1Min, deadline
    increase_params = [
        token_id+1,  # tokenId
        Web3.to_wei(0.1, 'ether'),  # amount0Desired
        Web3.to_wei(0.1, 'ether'),  # amount1Desired
        0,  # amount0Min
        0,  # amount1Min
        int(time.time()) + 1800  # deadline
    ]

    # Increase liquidity
    calldata_queue.add_call(
        nft_manager,
        "increaseLiquidity((uint256,uint256,uint256,uint256,uint256,uint256))",
        [increase_params],
        0
    )

    # Create decreaseLiquidity parameters
    # Parameters: tokenId, liquidity, amount0Min, amount1Min, deadline
    decrease_params = [
        token_id+1,  # tokenId
        5,  # liquidity (example amount, adjust as needed)
        0,  # amount0Min
        0,  # amount1Min
        int(time.time()) + 1800  # deadline
    ]

    # Decrease liquidity
    calldata_queue.add_call(
        nft_manager,
        "decreaseLiquidity((uint256,uint128,uint256,uint256,uint256))",
        [decrease_params],
        0
    )

    # Now we can get the calldata in bytes.
    print("Manager Contract: ", calldata_queue.manager_address)
    print("Calldata after adding approve call:\n", calldata_queue.get_calldata().hex())

if __name__ == "__main__":
    main() 
