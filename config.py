# ── Màn hình ──
SCREEN_W = 1280
SCREEN_H = 720
FPS      = 60
TITLE    = "Victoria 3 — Simple Engine"

# ── Camera ──
ZOOM_MAX = 6.0

# ── Màu UI ──
C_BG          = (18, 16, 15)
C_PANEL       = (28, 25, 23)
C_BORDER      = (58, 54, 50)
C_GOLD        = (212, 175,  55)
C_GOLD_DIM    = (145, 118,  47)
C_SEA         = (18,  30,  43)
C_LAKE        = (35,  65,  85)
C_WHITE       = (235, 230, 220)
C_GREY        = (150, 155, 165)
C_GREEN       = (46,  176, 105)
C_RED         = (200,  68,  68)
C_LAND_EMPTY  = (180, 175, 160)   # đất vô chủ
# Vic3 decentralized / unrecognized / colonial — tô gần trắng, viền dày trên bản đồ gốc
C_COLONIZABLE = (252, 250, 246)

# ── Game ──
START_YEAR  = 1836
START_MONTH = 1

# ── Kinh tế (mỗi lượt = 1 tháng) ──
BASE_TAX_RATE    = 0.15
BASE_GDP_GROWTH  = 0.002

# ── Dân số ──
BASE_POP_GROWTH = 0.001   # 0.1% mỗi tháng

# ── Quân sự ──
ARMY_UPKEEP_PER_1000 = 5   # gold/tháng cho mỗi 1000 quân

# ── Loại quốc gia có thể thuộc địa hóa ──
COLONIZABLE_TYPES = ('decentralized', 'unrecognized', 'colonial')