# Hieu Ecommerce Shop — bản Python

Web localhost dựa trên tài liệu bài tập `A6_V2_04_HieuBT.150.docx`. Logic tìm kiếm và dữ liệu nằm trong Python; HTML/CSS/JavaScript chỉ phụ trách giao diện trình duyệt.

## Chạy trên Windows

Máy cần Python 3.10 trở lên. Cài thư viện xử lý ảnh một lần:

```powershell
py -m pip install -r requirements.txt
```

Sau đó có thể nhấp đúp `Chay-Hieu-Shop.cmd`, hoặc mở PowerShell trong thư mục project và chạy:

```powershell
py app.py
```

Mở **http://localhost:4173**. Giữ cửa sổ PowerShell mở khi dùng web; nhấn `Ctrl+C` để dừng. Không cần chạy `npm`.

Nếu máy dùng macOS/Linux, chạy `python3 app.py`. Có thể đổi cổng bằng biến môi trường `PORT`.

## Kiểm tra

```powershell
py -m unittest discover -s tests -v
```

## Đối chiếu tài liệu

| Nội dung trong tài liệu | Mã nguồn |
| --- | --- |
| Presentation: SearchUI, VoiceInput, ImageUpload, SearchResultView | `index.html`, `styles.css`, `ui.js`; ảnh được tải lên và xem trước trong trình duyệt |
| Application: SpeechService, ImageService, QueryService | `shop/services.py` |
| Application: SearchService, RankingService | `shop/services.py` |
| Data: ProductRepository, OrderRepository, VectorIndex | `shop/data.py` |
| Giao tiếp giữa web và Python | `app.py` |

- Mười sản phẩm P01–P10, giá và tồn kho lấy từ bảng sản phẩm trong tài liệu.
- Tìm từ khóa hoặc bản ghi lời nói bằng số từ trùng chính xác trong tên, loại và màu sản phẩm.
- Tải ảnh JPG/PNG/WebP (tối đa 5 MB). Python đọc ảnh, tách hình sản phẩm khỏi nền đơn giản, ước lượng vector 3 chiều giày/túi/trang phục, rồi xếp hạng bằng cosine. Đây là thuật toán hình dạng thử nghiệm, chưa phải mô hình AI nhận dạng sản phẩm; ảnh nền phức tạp có thể cho kết quả chưa chính xác.
- API vẫn hỗ trợ vector 3 chiều nhập trực tiếp để kiểm tra bản mẫu trong tài liệu.
- Cùng truy vấn cho cùng thứ tự kết quả; khi bằng điểm thì sắp theo mã sản phẩm.
- Xem chi tiết sản phẩm; tra cứu và xem đơn hàng mẫu O001–O003 theo phần use case mở rộng. Dữ liệu đơn hàng là ví dụ bổ sung, không có trong bảng sản phẩm gốc.
- Hiển thị rõ lỗi đầu vào rỗng, ảnh hỏng/quá lớn, vector sai và mã đơn hàng không tồn tại.

Ứng dụng dùng dữ liệu trong bộ nhớ, không có thanh toán hoặc đăng nhập. Giá giữ nguyên số trong bảng mẫu; giao diện dùng ký hiệu `$` để trình bày.
