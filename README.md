# Claw — Goodreads Data Scraper

Script cào thêm data từ Goodreads Listopia để cân bằng dataset cho model phân loại sách.

## Cài đặt

```bash
pip install playwright pandas langdetect
python -m playwright install chromium
```

## Cách dùng

Mở `claw.py`, sửa 2 dòng theo phân công:

```python
# Thể loại được phân công
priority_order = ["essay"]   # essay | anthology | technology | sports | western | self_help

# Nếu có file JSON gốc thì điền đường dẫn, không có thì để ""
EXISTING_JSON_PATH = ""
```

Rồi chạy:

```bash
python claw.py
```

Kết quả lưu vào `balanced_dataset_additions.csv`. Gửi file này lên nhóm sau khi chạy xong.

## Phân công

| Thành viên | Thể loại | Cần cào |
|---|---|---|
| Người 1 | essay | ~20,000 |
| Người 2 | anthology | ~15,000 |
| Người 3 | technology | ~10,000 |
| Người 4 | sports | ~10,000 |
| Người 5 | western + self_help | ~8,000 + 5,500 |

## Lưu ý

- Không đóng cửa sổ trình duyệt khi script đang chạy
- Không commit file CSV hoặc JSON lên repo
