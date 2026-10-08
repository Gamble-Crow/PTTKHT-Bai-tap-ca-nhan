"""In-memory repositories for the ten-product assignment catalogue."""

from copy import deepcopy


PRODUCTS = (
    {"id": "P01", "name": "Nike Black Running Shoes", "category": "Shoes", "color": "Black", "price": 120, "stock": 10, "description": "Giày chạy bộ màu đen, dáng thể thao gọn nhẹ cho luyện tập hằng ngày.", "art": "shoe"},
    {"id": "P02", "name": "Adidas White Running Shoes", "category": "Shoes", "color": "White", "price": 100, "stock": 15, "description": "Giày chạy bộ màu trắng với thiết kế năng động và đế êm.", "art": "shoe"},
    {"id": "P03", "name": "Blue Sports Shoes", "category": "Shoes", "color": "Blue", "price": 75, "stock": 12, "description": "Giày thể thao màu xanh phù hợp cho vận động thường ngày.", "art": "shoe"},
    {"id": "P04", "name": "White Canvas Sneakers", "category": "Shoes", "color": "White", "price": 60, "stock": 8, "description": "Giày sneaker vải canvas màu trắng, dễ phối trang phục.", "art": "shoe"},
    {"id": "P05", "name": "Black Urban Backpack", "category": "Bags", "color": "Black", "price": 85, "stock": 7, "description": "Ba lô đô thị màu đen với kiểu dáng tối giản và nhiều ngăn.", "art": "backpack"},
    {"id": "P06", "name": "Brown Leather Bag", "category": "Bags", "color": "Brown", "price": 95, "stock": 6, "description": "Túi da màu nâu, phom dáng cổ điển cho nhu cầu hằng ngày.", "art": "bag"},
    {"id": "P07", "name": "Red Sports T-Shirt", "category": "Clothing", "color": "Red", "price": 35, "stock": 20, "description": "Áo thun thể thao màu đỏ, thoải mái khi vận động.", "art": "shirt"},
    {"id": "P08", "name": "Black Running Shorts", "category": "Clothing", "color": "Black", "price": 40, "stock": 14, "description": "Quần short chạy bộ màu đen, nhẹ và linh hoạt.", "art": "shorts"},
    {"id": "P09", "name": "Grey Cotton Hoodie", "category": "Clothing", "color": "Grey", "price": 65, "stock": 9, "description": "Áo hoodie cotton màu xám, ấm áp và dễ mặc.", "art": "hoodie"},
    {"id": "P10", "name": "Black Leather Wallet", "category": "Accessories", "color": "Black", "price": 30, "stock": 11, "description": "Ví da màu đen thiết kế nhỏ gọn với nhiều ngăn tiện dụng.", "art": "wallet"},
)

# Derived image representations are indexed separately from product facts.
VECTORS = {
    "P01": (0.98, 0.08, 0.03), "P02": (0.96, 0.05, 0.08),
    "P03": (0.92, 0.09, 0.12), "P04": (0.88, 0.04, 0.18),
    "P05": (0.07, 0.98, 0.05), "P06": (0.05, 0.94, 0.10),
    "P07": (0.08, 0.08, 0.97), "P08": (0.13, 0.06, 0.93),
    "P09": (0.04, 0.11, 0.96), "P10": (0.02, 0.65, 0.52),
}

# Example order records support Search Order and View Order from the use case model.
ORDERS = {
    "O001": {"id": "O001", "customer": "Nguyễn Minh Anh", "date": "2026-09-18", "status": "Đã giao", "items": ({"product_id": "P01", "quantity": 1, "unit_price": 120}, {"product_id": "P08", "quantity": 1, "unit_price": 40})},
    "O002": {"id": "O002", "customer": "Trần Gia Huy", "date": "2026-09-26", "status": "Đang vận chuyển", "items": ({"product_id": "P05", "quantity": 1, "unit_price": 85}, {"product_id": "P10", "quantity": 2, "unit_price": 30})},
    "O003": {"id": "O003", "customer": "Lê Thu Hà", "date": "2026-10-02", "status": "Đang xử lý", "items": ({"product_id": "P04", "quantity": 1, "unit_price": 60},)},
}


class ProductRepository:
    def search_products(self):
        return deepcopy(PRODUCTS)

    def find_by_id(self, product_id):
        return next((deepcopy(item) for item in PRODUCTS if item["id"] == product_id), None)


class VectorIndex:
    def find(self, product_id):
        return VECTORS.get(product_id)

    def search(self, query_vector):
        """Return candidate IDs with a positive raw vector signal."""
        return [
            (product_id, sum(a * b for a, b in zip(query_vector, stored)))
            for product_id, stored in VECTORS.items()
            if sum(a * b for a, b in zip(query_vector, stored)) > 0
        ]


class OrderRepository:
    def __init__(self, products):
        self.products = products

    def find_by_id(self, order_id):
        record = ORDERS.get(order_id)
        if record is None:
            return None
        items = [
            {
                "product_id": line["product_id"],
                "product": self.products.find_by_id(line["product_id"]),
                "quantity": line["quantity"],
                "unit_price": line["unit_price"],
            }
            for line in record["items"]
        ]
        return {
            "id": record["id"], "customer": record["customer"],
            "date": record["date"], "status": record["status"],
            "items": items,
            "total": sum(item["quantity"] * item["unit_price"] for item in items),
        }
