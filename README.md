# Quick Start
## Installation

You can install the Nucleus SDK using pip:
Using Pip

`pip install nucleus-sdk-python`

## Create A Client

The Client contains API information and creates your individual queues
Create a Client
```python
from nucleus_sdk_python.client import Client
client = Client(nucleus_api_key="YOUR_API_KEY")
```
Create a calldata_queue

The calldata queue stores your calldata to execute in First In First Out order.
```python
calldata_queue = client.create_calldata_queue(
    network_string="eth",
    strategist_address="STRATEGIST_ADDRESS",
    rpc_url="RPC_URL",
    symbol="tETH"
)
```
## Add a call

Using the new calldata queue you can add new calls as long as they are approved for your address.
```python
    calldata_queue.add_call(
        USDC,                           # target address
        "approve(address,uint256)",     # function signature
        [uniswap_router, int(1e6)],     # function arguments array
        0                               # native value
    )
```
## Execute

You can execute the calls directly from the manager script using the web3.py library. Calls will be executed FIFO atomically in a single transaction.
```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("RPC_URL"))
acc = w3.eth.account.from_key("PRIVATE_KEY")

receipt = calldata_queue.execute(w3, acc)
```
## Get Calldata

If you are using another method of submitting the tx you may just want the raw calldata. You can get it like so
```python
print("Manager Contract: ", calldata_queue.manager_address)
print("Calldata after adding approve call:\n", calldata_queue.get_calldata().hex())
```
