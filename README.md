# Crawl — Goodreads Data Scraper

Script cào dữ liệu từ Goodreads Listopia để cân bằng dataset cho model phân loại sách.

---

## 1. Chuẩn bị dữ liệu ban đầu

Tải file data gốc tại đây: [Link Google Drive](https://drive.google.com/file/d/1T2jEGioE9M4TSj8CSrPTwqUP5pCQr99p/view?usp=sharing)

Sau khi tải về, đặt file vào **cùng thư mục** với `claw.py`.

---

## 2. Cài đặt môi trường

```bash
pip install playwright pandas langdetect
python -m playwright install chromium
```

---

## 3. Cách dùng

Mở `claw.py`, sửa dòng theo phân công của mình:

```python
# Thể loại được phân công (chọn một trong các giá trị bên dưới)
priority_order = []   # essay | anthology | technology | sports | western | self_help
```

Sau đó chạy:

```bash
python claw.py
```

Kết quả sẽ được lưu vào file `balanced_dataset_additions.csv`. Gửi file này lên nhóm sau khi chạy xong.

---

## 4. Phân công

| Thành viên | Thể loại          |
|------------|-------------------|
| Dũng       | anthology         |
| Chức       | technology        |
| Tú         | sports            |
| Quý        | western, self_help |

---

## 5. Lưu ý

- **Không đóng** cửa sổ trình duyệt khi script đang chạy.
- Thời gian chạy có thể kéo dài — để máy ở trạng thái hoạt động, không cho ngủ.
- Nếu script bị lỗi giữa chừng, chạy lại từ đầu — dữ liệu đã cào sẽ được ghi tiếp vào file cũ, không bị mất.
