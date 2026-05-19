import pandas as pd
import json
import re
from langdetect import detect

# =====================================================
# 1. BỘ TỪ ĐIỂN CHUẨN HÓA CỦA BẠN
# =====================================================
STRUCTURAL_VOCAB = {
    "type_fiction": ["fiction", "generalfiction", "novel", "novella", "contemporaryfiction","realisticfiction"],
    "type_nonfiction": ["nonfiction"],
    "audience_childrens": ["children", "childrens", "picturebook", "middlegrade", "kid"],
    "audience_juvenile": ["teen", "comingofage", "highschool"],
    "audience_young_adult": ["youngadult", "ya", "newadult"],
    "audience_adult": ["adult"]
}

GENRE_TOPIC_VOCAB = {
    "fantasy": ["fantasy", "highfantasy", "epicfantasy", "urbanfantasy", "darkfantasy", "swordandsorcery","fairytale","scififantasy"],
    "science_fiction": ["scifi", "sciencefiction", "sf", "cyberpunk", "spaceopera", "steampunk", "postapocalyptic", "apocalyptic", "timetravel", "aliens","dystopian", "dystopia","scififantasy"],
    "romance": ["romance", "contemporaryromance", "historicalromance", "paranormalromance", "chicklit"],
    "thriller": ["thriller", "suspense", "crime", "mystery", "detective", "cozymystery", "espionage", "spy", "noir", "mysterythriller"],
    "horror": ["horror", "vampire", "zombie", "ghost", "werewolf", "demon"],
    "historical_fiction": ["historicalfiction", "regency", "victorian", "tudor"],
    "humor": ["humor", "humour", "comedy"],
    "western": ["western", "cowboy"],
    "history": ["history", "war", "military", "ww2", "wwii"],
    "science": ["science", "physics", "biology", "math", "psychology", "medical", "health"],
    "technology": ["technology", "computer", "software", "programming", "coding"],
    "business": ["business", "economics", "finance", "management", "leadership", "productivity"],
    "literary_fiction": ["literaryfiction","literature"],
    "classic": ["classic", "classics"],
    "poetry": ["poetry", "poem"],
    "drama": ["play", "drama"],
    "essay": ["essay"],
    "anthology": ["anthology"],
    "religion": ["religion", "christian", "theology", "bible", "faith", "buddhism","spirituality"],
    "philosophy": ["philosophy", "ethic", "logic", "metaphysics"],
    "biography_memoir": ["biography", "memoir", "autobiography"],
    "self_help": ["selfhelp", "personaldevelopment", "motivation", "selfimprovement", "selfdevelopment"],
    "politics": ["politics", "political", "currentevents","politic"],
    "art_music": ["art", "music", "photography", "design"],
    "cooking": ["cookbook", "food", "cooking", "baking"],
    "sports": ["sport", "football", "baseball"],
    "travel": ["travel", "travelogue", "roadtrip"],
    "comics_graphic_novels": ["comic", "graphicnovel", "manga", "manhwa"]
}

# Tạo bảng tra ngược (Reverse Lookup)
CANONICAL_MAP = {}
for vocab_dict in [STRUCTURAL_VOCAB, GENRE_TOPIC_VOCAB]:
    for canonical, variants in vocab_dict.items():
        for v in variants:
            CANONICAL_MAP.setdefault(v, []).append(canonical)

# =====================================================
# 2. HÀM CHUẨN HÓA DỮ LIỆU
# =====================================================
def normalize_tag(text):
    if not isinstance(text, str): return text
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', '', text)
    if text.endswith('ies'): text = text[:-3] + 'y'
    elif text.endswith('s') and not text.endswith('ss'): text = text[:-1]
    return text

def process_clawed_genres(genre_string):
    """Tách chuỗi CSV, chuẩn hóa và đưa về nhãn ML của bạn."""
    if not isinstance(genre_string, str): return []
    raw_genres = [g.strip() for g in genre_string.split(',')]
    final_labels = set()
    for g in raw_genres:
        norm = normalize_tag(g)
        mapped_targets = CANONICAL_MAP.get(norm, [])
        for target in mapped_targets:
            final_labels.add(target)
    return list(final_labels)

# =====================================================
# 3. LANGDETECT: LỌC SÁCH TIẾNG ANH
# =====================================================
print("Đang chuẩn bị bộ lọc ngôn ngữ...")

def detect_english(text):
    if not text or len(text.strip()) < 20:
        return False
    try:
        # Sử dụng thư viện langdetect thay vì fasttext
        return detect(text) == 'en'
    except:
        return False

# =====================================================
# 4. QUÁ TRÌNH GỘP & CLEAN CHÍNH
# =====================================================
# Thay đổi đường dẫn file cho đúng với máy của bạn
existing_json_path = "goodreads_books_cleaned_english.json"
clawed_csv_path = "add.csv"
output_path = "goodreads_final_training_dataset.json"

# Bước 1: Đọc JSON cũ
print("Đang tải dữ liệu JSON cũ...")
existing_data = []
with open(existing_json_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                existing_data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
df_existing = pd.DataFrame(existing_data)
print(f"-> Đã tải {len(df_existing):,} cuốn sách cũ.")

# Bước 2: Đọc CSV mới cào
print("\nĐang tải và làm sạch dữ liệu CSV vừa cào...")
df_clawed = pd.read_csv(clawed_csv_path)
df_clawed = df_clawed.dropna(subset=['title', 'description', 'genre'])

# Bước 3: Lọc ngôn ngữ tiếng Anh
df_clawed['combined_text'] = df_clawed['title'] + " " + df_clawed['description']
df_clawed['is_english'] = df_clawed['combined_text'].apply(detect_english)
df_clawed = df_clawed[df_clawed['is_english'] == True]

# Bước 4: Chuyển đổi chuỗi thể loại thành list chuẩn
df_clawed['genres'] = df_clawed['genre'].apply(process_clawed_genres)
df_clawed = df_clawed[df_clawed['genres'].map(len) > 0] # Bỏ những sách không map được thể loại nào
df_clawed = df_clawed[['title', 'description', 'genres']] # Chỉ giữ lại 3 cột cần thiết

print(f"-> Sẵn sàng gộp {len(df_clawed):,} cuốn sách mới (chuẩn Tiếng Anh, đã map nhãn).")

# Bước 5: Gộp và Xóa trùng lặp
print("\nĐang gộp và xóa trùng lặp...")
df_combined = pd.concat([df_existing, df_clawed], ignore_index=True)

df_combined['dedup_key'] = (
    df_combined['title'].str.lower().str.strip()
    + "||"
    + df_combined['description'].str[:80].str.lower().str.strip().fillna('')
)

# ── AUDIT NÂNG CAO: So sánh cặp giữ vs xóa ──────────────────────────────
df_combined['dedup_key'] = (
    df_combined['title'].str.lower().str.strip()
    + "||"
    + df_combined['description'].str[:80].str.lower().str.strip().fillna('')
)

# Tìm các key bị trùng
dup_keys = df_combined[df_combined.duplicated(subset=['dedup_key'], keep=False)]['dedup_key'].unique()

# Lấy 20 cặp đầu tiên, mỗi cặp hiện cả bản GIỮ lẫn bản XÓA
pairs = []
for key in dup_keys[:20]:
    group = df_combined[df_combined['dedup_key'] == key][['title', 'description']].copy()
    group['status'] = ['GIỮ'] + ['XÓA'] * (len(group) - 1)
    pairs.append(group)

df_pairs = pd.concat(pairs, ignore_index=True)
df_pairs.to_csv("audit_pairs.csv", index=False, encoding='utf-8-sig')
print("Đã lưu 20 cặp vào audit_pairs.csv")

# ── THỰC SỰ XÓA TRÙNG (đang bị thiếu) ───────────────────────────────────
before = len(df_combined)
df_combined = df_combined.drop_duplicates(subset=['dedup_key'], keep='first')
df_combined = df_combined.drop(columns=['dedup_key'])
after = len(df_combined)
print(f"-> Đã xóa {before - after:,} bản trùng, còn lại {after:,} cuốn.")
# ─────────────────────────────────────────────────────────────────────────

# Bước 6: Lưu ra file JSON hoàn chỉnh
print(f"\nĐang lưu {len(df_combined):,} cuốn sách...")
# Bước 6: Lưu ra file JSON hoàn chỉnh
print(f"\nĐang lưu {len(df_combined):,} cuốn sách vào file cuối cùng: {output_path}...")
df_combined.to_json(output_path, orient='records', lines=True, force_ascii=False)
print("Hoàn tất! Dữ liệu đã sạch sẽ và cân bằng, sẵn sàng để train DistilBERT.")