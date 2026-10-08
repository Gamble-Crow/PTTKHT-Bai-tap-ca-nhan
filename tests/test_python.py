import json
from io import BytesIO
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw

from app import ShopHandler
from http.server import ThreadingHTTPServer
from shop.services import InputError, ShopService


def sample_image(kind):
    image = Image.new("RGB", (240, 240), "white")
    draw = ImageDraw.Draw(image)
    if kind == "shoe":
        draw.polygon([(20, 125), (65, 125), (95, 95), (127, 117), (185, 137),
                      (215, 151), (217, 168), (20, 168)], fill="black")
    elif kind == "bag":
        draw.rectangle((75, 55, 165, 200), fill="black")
        draw.arc((95, 25, 145, 95), 180, 360, fill="black", width=8)
    elif kind == "shirt":
        draw.polygon([(75, 50), (165, 50), (215, 80), (185, 120), (165, 105),
                      (165, 200), (75, 200), (75, 105), (55, 120), (25, 80)], fill="black")
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


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

    def test_uploaded_images_are_read_and_ranked_by_shape(self):
        for kind, category in (("shoe", "Shoes"), ("bag", "Bags"),
                               ("shirt", "Clothing")):
            with self.subTest(kind=kind):
                output = self.shop.search_image_bytes(sample_image(kind))
                self.assertEqual(output["query"]["type"], "image")
                self.assertEqual(len(output["query"]["vector"]), 3)
                self.assertEqual(output["results"][0]["product"]["category"], category)

    def test_rejects_missing_or_broken_image(self):
        for data in (b"", b"not an image"):
            with self.subTest(data=data), self.assertRaises(InputError):
                self.shop.search_image_bytes(data)

    def test_transparent_png_is_composited_on_white(self):
        image = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        ImageDraw.Draw(image).polygon(
            [(20, 125), (65, 125), (95, 95), (127, 117),
             (185, 137), (215, 151), (217, 168), (20, 168)], fill="black")
        stream = BytesIO()
        image.save(stream, format="PNG")
        result = self.shop.search_image_bytes(stream.getvalue())
        self.assertEqual(result["results"][0]["product"]["category"], "Shoes")

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

    def test_uploaded_image_api(self):
        request = Request(self.base + "/api/search/image", data=sample_image("shoe"),
                          headers={"Content-Type": "image/png"})
        with urlopen(request) as response:
            result = json.load(response)
        self.assertEqual(result["results"][0]["product"]["category"], "Shoes")

        invalid = Request(self.base + "/api/search/image", data=b"broken image",
                          headers={"Content-Type": "image/png"})
        with self.assertRaises(HTTPError) as error:
            urlopen(invalid)
        self.assertEqual(error.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
