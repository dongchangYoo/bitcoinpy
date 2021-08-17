import requests
import toml
from requests.auth import HTTPBasicAuth
from typing import Union
from unittest import TestCase


class BasicClient:
    def __init__(self, url: str, rpc_id: str, rpc_pw: str, wallet_name: str = None):
        self.basic_url = url
        self.multi_wallet_url = url + "/wallet/"
        # basic auth setting
        self._rpc_auth = HTTPBasicAuth(rpc_id, rpc_pw)
        # used by wallet-specific-requests
        self.wallet_name = wallet_name

    def basic_request(self, method_name: str, params: list) -> Union[dict, str, list]:
        """ Send rpc request to bitcoin-core without sending-wallet option. """
        url = self.basic_url
        return self._request(url, method_name, params)

    def wallet_specific_request(self, method_name: str, params: list) -> Union[dict, str, list]:
        """
        Send rpc request to bitcoin-core with sending-wallet option
        Note> url: http://<node_url>:<port>/wallet/<wallet_name>
        """
        url = self.multi_wallet_url + self.wallet_name
        return self._request(url, method_name, params)

    def _request(self, url: str, method_name: str, params: list) -> Union[dict, str, list]:
        """ Build and send a rpc request to bitcoin core """
        # build rpc request message
        payload = dict()
        payload["jsonrpc"] = "1.0"
        payload["method"] = method_name
        payload["params"] = params

        # send rpc response
        resp = requests.post(url, json=payload, auth=self._rpc_auth)
        resp_json = resp.json()
        if resp.status_code == 200:
            return resp_json["result"]
        else:
            raise Exception("rpc fails: {}".format(resp_json["error"]))


class BitcoinClient(BasicClient):
    def __init__(self, url: str, rpc_id: str, rpc_pw: str, wallet_name: str = None):
        super().__init__(url, rpc_id, rpc_pw, wallet_name)

    # get block hash
    def get_latest_block_hash(self) -> str:
        return self.basic_request("getbestblockhash", list())

    # get block hash
    def get_block_hash_by_height(self, height: int) -> str:
        return self.basic_request("getblockhash", [height])

    # get block
    def get_block_by_hash(self, block_hash: str, verbose: int = 1) -> dict:
        return self.basic_request("getblock", [block_hash, verbose])

    # get block header
    def get_block_header_by_hash(self, block_hash: str, verbose: bool = False) -> dict:
        return self.basic_request("getblockheader", [block_hash, verbose])

    def get_latest_height(self) -> int:
        block_hash = self.get_latest_block_hash()
        block = self.get_block_by_hash(block_hash)
        return block["height"]

    # get block
    def get_block_by_height(self, height: int, verbose: int = 1) -> dict:
        block_hash = self.get_block_hash_by_height(height)
        return self.get_block_by_hash(block_hash, verbose)

    # get block header
    def get_block_header_by_height(self, height: int, verbose: bool = False):
        block_hash = self.get_block_hash_by_height(height)
        return self.get_block_header_by_hash(block_hash, verbose)


class BtcClientTest(TestCase):
    def setUp(self):
        config = toml.load("./rpc_config.toml")
        self.cli = BitcoinClient(config["url"], config["id"], config["pwd"], config["wallet_name"])

    def test_get_header(self):
        actual_header = self.cli.get_block_header_by_height(100)
        expected_header = "0100000095194b8567fe2e8bbda931afd01a7acd399b9325cb54683e64129bcd00000000660802c98f18fd34fd16d61c63cf447568370124ac5f3be626c2e1c3c9f0052d19a76949ffff001d33f3c25d"
        self.assertEqual(actual_header, expected_header)
