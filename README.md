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

- **Trình duyệt ẩn (Headless):** Ở Giai đoạn 1 & 2, trình duyệt sẽ hiện lên (không được đóng!). Nhưng sang Giai đoạn 3, kịch bản sẽ mở 4 luồng chạy ngầm (không hiện trình duyệt) để tăng tốc độ. Các bạn chỉ cần theo dõi tiến độ trên Terminal/Console.
- **Lưu dữ liệu:** Dữ liệu chỉ được lưu vào file CSV **SAU KHI** cào xong toàn bộ 1 thể loại. Nếu bị crash hoặc mất điện giữa chừng khi đang chạy Phase 3, các bạn sẽ phải chạy lại thể loại đó từ đầu.
- Thời gian chạy có thể kéo dài từ 2-3 tiếng mỗi thể loại — hãy cắm sạc và tắt chế độ Sleep/Ngủ của máy tính.
Once you make those minor adjustments, push it to GitHub and let your team loose on it!
