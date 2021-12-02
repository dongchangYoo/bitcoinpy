import json
import subprocess
import time
from typing import Union
from decimal import Decimal, getcontext

from .exceptions import *


class TestBase:
    def __init__(self, src_path: str, rpc_port: int = 18443, rpc_user: str = "admin", rpc_password: str = "0000"):
        # remove last "/"
        src_path = src_path if src_path.endswith("/") else src_path + "/"
        self.bitcoind_path = src_path + "bitcoind"
        self.cli_path = src_path + "bitcoin-cli"

        self.rpc_port = rpc_port
        self.rpc_user = rpc_user
        self.rpc_pwd = rpc_password

    @property
    def basic_cmd(self) -> list:
        cmd = list()
        cmd.append("-rpcport=" + str(self.rpc_port))
        cmd.append("-rpcuser=" + self.rpc_user)
        cmd.append("-rpcpassword=" + self.rpc_pwd)
        cmd.append("-regtest")
        return cmd

    def build_and_request(self, method: str, params: list = None) -> str:
        cmd = list()
        cmd.append(self.cli_path)
        cmd += self.basic_cmd
        cmd.append(method)

        if params is not None:
            for param in params:
                cmd.append(param)

        resp = TestNode._execute(cmd)

        if resp.startswith("error: timeout on transient error"):
            raise RegtestNodeNotRunning
        return resp

    @staticmethod
    def _execute(cmd) -> str:
        pipe = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        fd_err = pipe.stderr
        fd_stdout = pipe.stdout

        # get message from stderr and stdout of subprocess
        err = fd_err.read().strip()
        stdout = fd_stdout.read().strip()

        fd_err.close()
        fd_stdout.close()

        # return non-empty message
        if err == b'':
            return stdout.decode('utf-8')
        else:
            return err.decode('utf-8')

    def generate_block(self, blocks: int, address: str):
        resp = self.build_and_request("generatetoaddress", [str(blocks), address])
        # block hashes
        return json.loads(resp)

    """ create wallet and generate "coinbase" address of the wallet """
    def create_wallet(self, wallet_name):
        # request "createwallet"
        resp = self.build_and_request("createwallet", [wallet_name])

        # check that the request was successed
        success = False
        try:
            resp_dict = json.loads(resp)
            if "name" in resp_dict and "warning" in resp_dict:
                success = True
        except json.JSONDecodeError as e:
            if resp.startswith("error code: -4"):
                success = True
            else:
                success = False

        if success:
            return self.setup_coinbase()
        else:
            return None

    def unload_wallet(self, wallet_name: str):
        resp = self.build_and_request("unloadwallet", [wallet_name])
        if resp.startswith("error code: -18"):
            return False  # the wallet is not loaded
        return True

    def load_wallet(self, wallet_name: str):
        resp = self.build_and_request("loadwallet", [wallet_name])
        if resp.startswith("error code: -18"):
            raise WalletNotFounded

        # unload all wallet except to target wallet
        loaded_wallets = self.loaded_wallet_list()
        if len(loaded_wallets) > 1:
            for wallet in loaded_wallets:
                if wallet != wallet_name:
                    self.unload_wallet(wallet)

        return self.setup_coinbase()

    def loaded_wallet_list(self):
        resp = self.build_and_request("listwallets")

        resp_list = json.loads(resp)
        return resp_list

    def list_wallet_dir(self):
        resp = self.build_and_request("listwalletdir")

        resp_dict = json.loads(resp)
        wallet_list = [wallets["name"] for wallets in resp_dict["wallets"]]
        return wallet_list

    def new_address(self, label: str = "", address_type: str = "bech32"):
        if address_type not in ["legacy", "p2sh-segwit", "bech32"]:
            raise InvalidAddressType

        return self.build_and_request("getnewaddress", [label, address_type])  # new address

    def get_address_by_label(self, label: str):
        resp = self.build_and_request("getaddressesbylabel", [label])

        if resp.startswith("error code: -11"):
            return list()
        else:
            return json.loads(resp)

    def address_list(self):
        resp = self.build_and_request("listaddressgroupings")
        return json.loads(resp)

    def get_balances_each(self):
        resp = self.build_and_request("getbalances")
        return json.loads(resp)

    def get_balance(self):
        resp = self.build_and_request("getbalance")
        return json.loads(resp)

    def get_utxo(self, minconf: int = 6, min_amount: float = 1.0):
        if minconf < 1:
            raise InvalidParameter

        opt_str = json.dumps({
            "minimumAmount": str(min_amount)
        })

        resp = self.build_and_request("listunspent", [str(minconf), str(9999999), str([]), "false", opt_str])
        # resp = self.build_and_request("listunspent", [str(minconf), str(9999999)])
        return json.loads(resp)

    def get_address_info(self, address: str):
        resp = self.build_and_request("getaddressinfo", [address])
        # TODO error handling?
        return json.loads(resp)

    def send_to(self, _to: str, amount: Union[float, int]):
        getcontext().prec = 8
        if isinstance(amount, float):
            btc = Decimal(amount) * Decimal(1)
        elif isinstance(amount, int):
            btc = Decimal(amount) * Decimal(0.00000001)
        else:
            raise InvalidParameterType

        params = list()
        params.append(_to)
        params.append(str(btc))

        # tx_id
        return self.build_and_request("sendtoaddress", params)

    def get_transaction_with_txid_and_blockhash(self, tx_id: str, block_hash: str) -> dict:
        resp = self.build_and_request("getrawtransaction", [tx_id, "true", block_hash])
        return json.loads(resp)

    def test_mempool_accept(self, rawtx: str, maxfeerate: int = 1000):
        param = json.dumps([rawtx])
        resp = self.build_and_request("testmempoolaccept", [param, str(maxfeerate)])

        resp_list = json.loads(resp)
        return resp_list[0]

    def decode_raw_transaction(self, serialized_raw_tx: str):
        resp = self.build_and_request("decoderawtransaction", [serialized_raw_tx])
        return json.loads(resp)

    def signrawtransactionwithwallet(self, hexstring: str):
        resp = self.build_and_request("signrawtransactionwithwallet", [hexstring])
        return json.loads(resp)

    def get_block_count(self):
        resp = self.build_and_request("getblockcount")
        return json.loads(resp)

    def create_raw_transaction(self, inputs: list, outputs: list):
        input_str = json.dumps(inputs)
        out_str = json.dumps(outputs)

        return self.build_and_request("createrawtransaction", [input_str, out_str])

    def sign_raw_transaction_with_wallet(self, tx_hex: str):
        resp = self.build_and_request("signrawtransactionwithwallet", [tx_hex])

        resp_json = json.loads(resp)
        assert resp_json["complete"]
        assert "errors" not in resp_json

        return resp_json

    def send_raw_transaction(self, tx_hex: str):
        return self.build_and_request("sendrawtransaction", [tx_hex, "0"])


class TestNode(TestBase):
    """
    @ MUST enter directory path including binaries, bitcoind and bitcoin-cli.
    @ the others are optional
    """
    def __init__(self, src_path: str, rpc_port: int = 18443, rpc_user: str = "admin", rpc_password: str = "0000"):
        # remove last "/"
        src_path = src_path if src_path.endswith("/") else src_path + "/"
        self.bitcoind_path = src_path + "bitcoind"
        self.cli_path = src_path + "bitcoin-cli"

        self.rpc_port = rpc_port
        self.rpc_user = rpc_user
        self.rpc_pwd = rpc_password

        self.coinbase_addr = None

    def up(self, reload: bool = False, retry: int = 3, retry_sleep: float = 0.5) -> str:
        cmd = list()
        cmd.append(self.bitcoind_path)
        cmd += self.basic_cmd
        cmd.append("-fallbackfee=0.00001")
        cmd.append("-daemon")

        msg = TestNode._execute(cmd)
        time.sleep(1)
        if msg.startswith("Error"):
            if reload:
                self.shutdown(retry, retry_sleep)
                self.up(reload)
            else:
                raise RegtestAlreadyRunning

        return self.setup_wallet("default")

    def shutdown(self, retry: int, retry_sleep: float) -> bool:
        success = False
        for i in range(retry):
            try:
                resp = self.build_and_request("stop")
            except RegtestNodeNotRunning:
                time.sleep(retry_sleep)
                continue

            if resp == "Bitcoin Core stopping":
                success = True
                break
        return success

    def make_block_and_rewarding_to(self, blocks: int, address: str = None):
        if address is not None:
            winner = address
        elif self.coinbase_addr is not None:
            winner = self.coinbase_addr
        else:
            raise NoCoinbase

        # block hashes
        return  self.generate_block(blocks, winner)

    def setup_wallet(self, wallet_name: str):
        wallets = self.list_wallet_dir()

        if wallet_name in wallets:
            return self.load_wallet(wallet_name)
        else:
            self.create_wallet(wallet_name)
            return self.load_wallet(wallet_name)

    def setup_coinbase(self):
        addrs = self.get_address_by_label("coinbase")
        if len(addrs) < 1:
            self.coinbase_addr = self.new_address("coinbase")
        else:
            self.coinbase_addr = list(addrs.keys())[0]
        return self.coinbase_addr

    def send_new_transaction(self, inputs: list, outputs: list):
        raw_tx = self.create_raw_transaction(inputs, outputs)
        signed_tx = self.sign_raw_transaction_with_wallet(raw_tx)
        result = self.send_raw_transaction(signed_tx["hex"])
        return result

    # do not use. it is not tested
    def custuomized_send_to(self, _to: str, amount: Union[float, int]):
        getcontext().prec = 8
        if isinstance(amount, float):
            btc = Decimal(amount) * Decimal(1)
        elif isinstance(amount, int):
            btc = Decimal(amount) * Decimal(0.00000001)
        else:
            raise InvalidParameterType

        resp = self.get_utxo(1, min_amount=10.0)
        if len(resp) == 0:
            raise Exception("There is no utxo")

        utxo = resp[-1]

        unspent_input = {
            "txid": utxo["txid"],
            "vout": utxo["vout"],
        }

        return self.send_new_transaction([unspent_input], [{_to: str(btc)}])
