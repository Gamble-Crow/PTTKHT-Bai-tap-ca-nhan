"""Local Python HTTP server for Hieu Ecommerce Shop (standard library only)."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from shop.services import InputError, ShopService


ROOT = Path(__file__).resolve().parent
SHOP = ShopService()
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/ui.js": ("ui.js", "text/javascript; charset=utf-8"),
}


class ShopHandler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/api/products":
            self.send_json(200, SHOP.all_products())
            return
        if path.startswith("/api/products/"):
            product = SHOP.product(path.removeprefix("/api/products/"))
            self.send_json(200 if product else 404, product or {"error": "Không tìm thấy sản phẩm."})
            return
        if path.startswith("/api/orders/"):
            try:
                order = SHOP.order(path.removeprefix("/api/orders/"))
            except InputError as error:
                self.send_json(400, {"error": str(error)})
                return
            self.send_json(200 if order else 404, order or {"error": "Không tìm thấy đơn hàng. Hãy thử O001, O002 hoặc O003."})
            return
        if path not in STATIC:
            self.send_json(404, {"error": "Không tìm thấy đường dẫn."})
            return
        filename, content_type = STATIC[path]
        body = (ROOT / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/search":
            self.send_json(404, {"error": "Không tìm thấy đường dẫn."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise InputError("Dữ liệu tìm kiếm không hợp lệ.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise InputError("Dữ liệu tìm kiếm không hợp lệ.")
            result = SHOP.search(payload.get("mode"), payload.get("value"))
        except (InputError, ValueError, UnicodeDecodeError) as error:
            self.send_json(400, {"error": str(error)})
            return
        self.send_json(200, result)


def main():
    port = int(os.environ.get("PORT", "4173"))
    with ThreadingHTTPServer(("127.0.0.1", port), ShopHandler) as server:
        print(f"Hieu Ecommerce Shop (Python): http://localhost:{port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Đã dừng máy chủ.")


if __name__ == "__main__":
    main()
