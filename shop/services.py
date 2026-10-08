"""Query conversion, retrieval and ranking specified by the assignment."""

from dataclasses import dataclass
from io import BytesIO
from math import isfinite, sqrt
import re
from statistics import median
import unicodedata

from PIL import Image, ImageOps, UnidentifiedImageError

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
    MAX_BYTES = 5_000_000
    MAX_PIXELS = 12_000_000

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

    def encode_image(self, image_bytes):
        """Estimate the assignment's shoe/bag/clothing vector from one image.

        This small local baseline uses the foreground silhouette, not a trained
        recognition model. It works best for one item on a plain background.
        """
        if not image_bytes:
            raise InputError("Hãy chọn một ảnh sản phẩm.")
        if len(image_bytes) > self.MAX_BYTES:
            raise InputError("Ảnh quá lớn. Hãy chọn ảnh dưới 5 MB.")
        try:
            with Image.open(BytesIO(image_bytes)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise InputError("Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP.")
                if source.width * source.height > self.MAX_PIXELS:
                    raise InputError("Ảnh có độ phân giải quá lớn.")
                oriented = ImageOps.exif_transpose(source)
                if "A" in oriented.getbands():
                    rgba = oriented.convert("RGBA")
                    background = Image.new("RGBA", rgba.size, "white")
                    background.alpha_composite(rgba)
                    image = background.convert("RGB")
                else:
                    image = oriented.convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as error:
            raise InputError("Không đọc được ảnh. Hãy chọn tệp JPG, PNG hoặc WebP hợp lệ.") from error

        image.thumbnail((256, 256))
        width, height = image.size
        if width < 24 or height < 24:
            raise InputError("Ảnh quá nhỏ để tìm kiếm.")
        pixels = image.load()
        step = max(1, min(width, height) // 32)
        border = ([pixels[x, 0] for x in range(0, width, step)]
                  + [pixels[x, height - 1] for x in range(0, width, step)]
                  + [pixels[0, y] for y in range(0, height, step)]
                  + [pixels[width - 1, y] for y in range(0, height, step)])
        background = tuple(median(pixel[channel] for pixel in border) for channel in range(3))
        foreground = []
        for y in range(height):
            for x in range(width):
                color = pixels[x, y]
                if sum(abs(color[channel] - background[channel]) for channel in range(3)) > 105:
                    foreground.append((x, y))
        if len(foreground) < max(30, width * height // 200):
            raise InputError("Không nhận ra sản phẩm trong ảnh. Hãy thử ảnh có nền đơn giản.")

        left = min(x for x, _ in foreground)
        right = max(x for x, _ in foreground)
        top = min(y for _, y in foreground)
        bottom = max(y for _, y in foreground)
        box_width, box_height = right - left + 1, bottom - top + 1
        aspect = box_width / box_height
        fill = len(foreground) / (box_width * box_height)
        top_pixels = [x for x, y in foreground if y < top + box_height * 0.35]
        bottom_pixels = [x for x, y in foreground if y > bottom - box_height * 0.35]
        top_span = (max(top_pixels) - min(top_pixels) + 1) / box_width if top_pixels else 0
        bottom_span = (max(bottom_pixels) - min(bottom_pixels) + 1) / box_width if bottom_pixels else 0
        shoulder = max(0.0, top_span - bottom_span)

        shoe = max(0.01, min(1.0, (aspect - 1.2) / 0.8))
        bag = max(0.01, min(1.0, (1.15 - aspect) / 0.55))
        clothing = max(0.01, 1.0 - abs(aspect - 1.05) / 0.65) * (1.0 + shoulder)
        if aspect > 1.5 and fill > 0.78:  # A flat, rectangular wallet.
            bag = max(bag, 0.85)
            shoe *= 0.2
        return self.encode((shoe, bag, clothing))


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
        return self._search_query(query)

    def search_image_bytes(self, image_bytes):
        vector = self.images.encode_image(image_bytes)
        return self._search_query(self.queries.image_query(vector))

    def _search_query(self, query):
        candidates = self.searcher.retrieve(query)
        return {"query": query.as_dict(), "results": self.ranker.rank(query, candidates)}
