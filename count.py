
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

print("Đang đọc và đếm dữ liệu...")
file_path = "goodreads_final_training_dataset.json"

# Khởi tạo bộ đếm
genre_counts = Counter()

# Đọc file theo từng chunk (10,000 dòng một lần) để chống tràn RAM
chunks = pd.read_json(file_path, lines=True, chunksize=10000)
for chunk in chunks:
    # Lấy cột genres và đếm
    for genres_list in chunk['genres'].dropna():
        if isinstance(genres_list, list):
            genre_counts.update(genres_list)

# Chuyển kết quả đếm được thành DataFrame để dễ vẽ
df_counts = pd.DataFrame.from_dict(genre_counts, orient='index', columns=['Count'])
# Sắp xếp tăng dần để cột lớn nhất nằm trên cùng của biểu đồ
df_counts = df_counts.sort_values(by='Count', ascending=False).reset_index()
df_counts.columns = ['Genre', 'Count']

print(f"Đã đếm xong {len(df_counts)} thể loại. Đang vẽ biểu đồ...")

# Thiết lập phong cách và kích thước biểu đồ
plt.figure(figsize=(14, 12))
sns.set_style("whitegrid")

# Vẽ biểu đồ cột ngang (Horizontal Bar Chart)
ax = sns.barplot(x='Count', y='Genre', data=df_counts, palette='viridis')

# Thêm tiêu đề và nhãn
plt.title('Phân bố số lượng sách theo 33 thể loại trong tập dữ liệu Goodreads', fontsize=18, fontweight='bold', pad=20)
plt.xlabel('Số lượng sách', fontsize=14, fontweight='bold')
plt.ylabel('Tên thể loại', fontsize=14, fontweight='bold')

# Gắn số liệu trực tiếp lên đuôi mỗi cột cho chuyên nghiệp
for i, v in enumerate(df_counts['Count']):
    ax.text(v + 1000, i, f"{v:,}", color='black', va='center', fontsize=11)

# Chỉnh lề và lưu thành file ảnh
plt.tight_layout()
plt.savefig('genre_distribution.png', dpi=300) # Lưu ảnh nét căng (300 dpi)
plt.show()

print("Đã lưu ảnh biểu đồ thành công vào Google Drive!")