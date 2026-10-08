import json
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import ShopHandler
from http.server import ThreadingHTTPServer
from shop.services import InputError, ShopService


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.shop = ShopService()

    def test_text_and_supplied_voice_share_ranking(self):
        text = self.shop.search("text", "find white running shoes")
        voice = self.shop.search("voice", "find white running shoes")
        self.assertEqual([item["product"]["id"] for item in text["results"]],
                         [item["product"]["id"] for item in voice["results"]])
        self.assertEqual(text["results"][0]["product"]["id"], "P02")
        self.assertEqual(text["results"][0]["score"], 3)

    def test_image_cosine_ranking_and_query_object(self):
        output = self.shop.search("image", [1, 0, 0])
        self.assertEqual(output["query"]["type"], "image")
        self.assertEqual(output["query"]["tokens"], [])
        self.assertEqual(output["query"]["vector"], [1.0, 0.0, 0.0])
        self.assertEqual(output["results"][0]["product"]["id"], "P01")
        self.assertGreater(output["results"][0]["score"], 0.99)

    def test_stable_tie_order_and_no_match(self):
        results = self.shop.search("text", "black")["results"]
        self.assertEqual([row["product"]["id"] for row in results],
                         ["P01", "P05", "P08", "P10"])
        self.assertEqual(self.shop.search("text", "unfindable")["results"], [])

    def test_order_total_uses_saved_line_price(self):
        order = self.shop.order("o001")
        self.assertEqual(order["status"], "Đã giao")
        self.assertEqual(order["total"], 160)
        self.assertIsNone(self.shop.order("O999"))

    def test_invalid_inputs(self):
        for mode, value in (("text", " "), ("voice", " "),
                            ("image", [0, 0, 0]), ("image", [-1, 0, 0]),
                            ("image", [1, 2]), ("other", "x")):
            with self.subTest(mode=mode, value=value), self.assertRaises(InputError):
                self.shop.search(mode, value)
        with self.assertRaises(InputError):
            self.shop.order(" ")


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ShopHandler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def read_json(self, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        request = Request(self.base + path, data=body,
                          headers={"Content-Type": "application/json"} if body else {})
        with urlopen(request) as response:
            return response.status, json.load(response)

    def test_catalogue_and_search_api(self):
        status, catalogue = self.read_json("/api/products")
        self.assertEqual(status, 200)
        self.assertEqual(len(catalogue), 10)
        status, output = self.read_json("/api/search", {"mode": "text", "value": "black running shoes"})
        self.assertEqual(status, 200)
        self.assertEqual(output["results"][0]["product"]["id"], "P01")

    def test_invalid_query_and_unknown_order_api(self):
        with self.assertRaises(HTTPError) as invalid:
            self.read_json("/api/search", {"mode": "image", "value": [0, 0, 0]})
        self.assertEqual(invalid.exception.code, 400)
        with self.assertRaises(HTTPError) as missing:
            self.read_json("/api/orders/O999")
        self.assertEqual(missing.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
