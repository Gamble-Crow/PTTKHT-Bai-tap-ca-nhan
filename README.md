# Hieu Ecommerce Shop — bản Python

Web localhost dựa trên tài liệu bài tập `A6_V2_04_HieuBT.150.docx`. Logic tìm kiếm và dữ liệu nằm trong Python; HTML/CSS/JavaScript chỉ phụ trách giao diện trình duyệt.

## Chạy trên Windows

Máy cần Python 3.10 trở lên. Có thể nhấp đúp `Chay-Hieu-Shop.cmd`, hoặc mở PowerShell trong thư mục `hieu-ecommerce-shop` và chạy:

```powershell
py app.py
```

Sau đó mở **http://localhost:4173**. Giữ cửa sổ PowerShell mở khi dùng web; nhấn `Ctrl+C` để dừng. Không cần cài thêm thư viện hay chạy `npm`.

Nếu máy dùng macOS/Linux, chạy `python3 app.py`. Có thể đổi cổng bằng biến môi trường `PORT`.

## Kiểm tra

```powershell
py -m unittest discover -s tests -v
```

## Đối chiếu tài liệu

| Nội dung trong tài liệu | Mã nguồn |
| --- | --- |
| Presentation: SearchUI, VoiceInput, ImageUpload, SearchResultView | `index.html`, `styles.css`, `ui.js`; ImageUpload được biểu diễn bằng ô vector ảnh mô phỏng của bản mẫu |
| Application: SpeechService, ImageService, QueryService | `shop/services.py` |
| Application: SearchService, RankingService | `shop/services.py` |
| Data: ProductRepository, OrderRepository, VectorIndex | `shop/data.py` |
| Giao tiếp giữa web và Python | `app.py` |

- Mười sản phẩm P01–P10, giá và tồn kho lấy từ bảng sản phẩm trong tài liệu.
- Tìm từ khóa hoặc bản ghi lời nói bằng số từ trùng chính xác trong tên, loại và màu sản phẩm.
- Tìm ảnh dùng vector mô phỏng 3 chiều và điểm cosine, đúng với bản mẫu Python được mô tả. Chưa phân tích ảnh tải lên bằng mô hình thị giác.
- Cùng truy vấn cho cùng thứ tự kết quả; khi bằng điểm thì sắp theo mã sản phẩm.
- Xem chi tiết sản phẩm; tra cứu và xem đơn hàng mẫu O001–O003 theo phần use case mở rộng. Dữ liệu đơn hàng là ví dụ bổ sung, không có trong bảng sản phẩm gốc.
- Hiển thị rõ lỗi đầu vào rỗng, vector sai và mã đơn hàng không tồn tại.

Ứng dụng dùng dữ liệu trong bộ nhớ, không có thanh toán hoặc đăng nhập. Giá giữ nguyên số trong bảng mẫu; giao diện dùng ký hiệu `$` để trình bày.
