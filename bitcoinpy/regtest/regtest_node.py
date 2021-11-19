import json
import subprocess
import time

from exceptions import *


class LocalRegtestNode:
    def __init__(self, src_path: str, rpc_port: int = 18443, rpc_user: str = "admin", rpc_password: str = "0000"):
        # remove last "/"
        src_path = src_path if src_path.endswith("/") else src_path + "/"
        self.bitcoind_path = src_path + "src/bitcoind"
        self.cli_path = src_path + "src/bitcoin-cli"

        self.rpc_port = rpc_port
        self.rpc_user = rpc_user
        self.rpc_pwd = rpc_password

        self.coinbase_addr = None

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

        resp = LocalRegtestNode._execute(cmd)
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

    def up(self, reload: bool = False):
        cmd = list()
        cmd.append(self.bitcoind_path)
        cmd += self.basic_cmd
        cmd.append("-daemon")

        msg = LocalRegtestNode._execute(cmd)
        time.sleep(1)
        if msg.startswith("Error"):
            if reload:
                self.shutdown()
                time.sleep(0.5)
                self.up()
            else:
                raise RegtestAlreadyRunning

        self.create_and_load_wallet("default")

        addrs = self.get_address_by_label("coinbase")
        if len(addrs) == 0:
            self.coinbase_addr = self.new_address("coinbase")
        else:
            self.coinbase_addr = list(addrs.keys())[0]
        return True

    def shutdown(self) -> bool:
        resp = self.build_and_request("stop")
        if resp == "Bitcoin Core stopping":
            return True
        else:
            return False

    def make_block_and_rewarding_to(self, blocks: int, address: str = None):
        if address is not None:
            winner = address
        elif self.coinbase_addr is not None:
            winner = self.coinbase_addr
        else:
            raise NoCoinbase

        resp = self.build_and_request("generatetoaddress", [str(blocks), winner])
        return json.loads(resp)[-1]  # latest block hash

    def create_and_load_wallet(self, wallet_name: str):
        resp = self.build_and_request("createwallet", [wallet_name])

        if resp.startswith("error code: -4"):
            return self.load_wallet(wallet_name)

        raise UnknownException

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
        return True

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

    def get_utxo(self, minconf: int = 6):
        if minconf < 1:
            raise InvalidParameter

        resp = self.build_and_request("listunspent", [str(minconf), str(9999999)])
        return json.loads(resp)


if __name__ == "__main__":
    node = LocalRegtestNode("/Users/dc/research_project/bitcoin/")
    node.up(reload=True)

    result = node.loaded_wallet_list()
    print(result)

    node.create_and_load_wallet("test")
    result = node.loaded_wallet_list()
    print(result)



