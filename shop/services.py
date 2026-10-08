"""Query conversion, retrieval and ranking specified by the assignment."""

from dataclasses import dataclass
from math import isfinite, sqrt
import re
import unicodedata

from .data import OrderRepository, ProductRepository, VectorIndex


class InputError(ValueError):
    """A readable error caused by invalid customer input."""


def normalize(text):
    folded = unicodedata.normalize("NFD", text.casefold()).replace("đ", "d")
    return "".join(char for char in folded if unicodedata.category(char) != "Mn")


STOPWORDS = {"find", "show", "me", "a", "an", "the", "for", "please", "tim", "kiem", "cho", "toi", "cai", "mot"}


def tokens_of(text):
    return tuple(dict.fromkeys(word for word in re.findall(r"[a-z0-9]+", normalize(text)) if word not in STOPWORDS))


@dataclass(frozen=True)
class Query:
    type: str
    tokens: tuple[str, ...]
    vector: tuple[float, ...] | None
    interpreted: str

    def as_dict(self):
        return {"type": self.type, "tokens": list(self.tokens), "vector": list(self.vector) if self.vector else None, "interpreted": self.interpreted}


class SpeechService:
    def transcribe(self, supplied_transcript):
        if not isinstance(supplied_transcript, str) or not supplied_transcript.strip():
            raise InputError("Hãy nhập lời nói đã chuyển thành văn bản.")
        return supplied_transcript.strip()


class ImageService:
    def encode(self, values):
        if not isinstance(values, (list, tuple)) or len(values) != 3:
            raise InputError("Vector ảnh phải có đúng 3 số không âm.")
        try:
            vector = tuple(float(value) for value in values)
        except (TypeError, ValueError):
            raise InputError("Vector ảnh phải có đúng 3 số không âm.") from None
        if any(not isfinite(value) or value < 0 for value in vector) or not any(vector):
            raise InputError("Vector ảnh phải có 3 số không âm và ít nhất một số lớn hơn 0.")
        return vector


class QueryService:
    def text_query(self, text):
        if not isinstance(text, str) or not tokens_of(text):
            raise InputError("Hãy nhập từ khóa sản phẩm.")
        return Query("text", tokens_of(text), None, text.strip())

    def voice_query(self, transcript):
        query = self.text_query(transcript)
        return Query("voice", query.tokens, None, transcript.strip())

    def image_query(self, vector):
        return Query("image", (), vector, f"({', '.join(f'{value:g}' for value in vector)})")


class SearchService:
    def __init__(self, products, vectors):
        self.products = products
        self.vectors = vectors

    def retrieve(self, query):
        if query.type == "image":
            # The index selects IDs; the product repository supplies their records.
            return [
                self.products.find_by_id(product_id)
                for product_id, _signal in self.vectors.search(query.vector)
            ]
        candidates = []
        for product in self.products.search_products():
            words = set(tokens_of(f"{product['name']} {product['category']} {product['color']}"))
            if any(token in words for token in query.tokens):
                candidates.append(product)
        return candidates


class RankingService:
    def __init__(self, vectors):
        self.vectors = vectors

    def rank(self, query, candidates):
        # A product ID is the deterministic tie breaker for both score types.
        scored = []
        for product in candidates:
            if query.type == "image":
                stored = self.vectors.find(product["id"])
                dot = sum(a * b for a, b in zip(query.vector, stored))
                norm_query = sqrt(sum(value * value for value in query.vector))
                norm_stored = sqrt(sum(value * value for value in stored))
                score = dot / (norm_query * norm_stored)
            else:
                words = set(tokens_of(f"{product['name']} {product['category']} {product['color']}"))
                score = sum(token in words for token in query.tokens)
            scored.append({"product": product, "score": score})
        return sorted(scored, key=lambda item: (-item["score"], item["product"]["id"]))


class ShopService:
    def __init__(self):
        self.products = ProductRepository()
        self.vectors = VectorIndex()
        self.orders = OrderRepository(self.products)
        self.speech = SpeechService()
        self.images = ImageService()
        self.queries = QueryService()
        self.searcher = SearchService(self.products, self.vectors)
        self.ranker = RankingService(self.vectors)

    def all_products(self):
        return [{"product": product, "score": None} for product in self.products.search_products()]

    def product(self, product_id):
        return self.products.find_by_id(product_id.upper())

    def order(self, order_id):
        if not isinstance(order_id, str) or not order_id.strip():
            raise InputError("Hãy nhập mã đơn hàng.")
        return self.orders.find_by_id(order_id.strip().upper())

    def search(self, mode, value):
        if mode == "text":
            query = self.queries.text_query(value)
        elif mode == "voice":
            query = self.queries.voice_query(self.speech.transcribe(value))
        elif mode == "image":
            query = self.queries.image_query(self.images.encode(value))
        else:
            raise InputError("Phương thức tìm kiếm không hợp lệ.")
        candidates = self.searcher.retrieve(query)
        return {"query": query.as_dict(), "results": self.ranker.rank(query, candidates)}
