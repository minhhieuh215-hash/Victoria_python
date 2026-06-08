# ── DỰ ÁN QUỐC GIA (NATIONAL PROJECTS) ──

PROJECTS = {
    "transcontinental_railway": {
        "name": "Đường sắt Xuyên lục địa",
        "cost": 15000,
        "time": 24, # 24 turns (2 years)
        "desc": "Xây dựng mạng lưới đường sắt kết nối các bang, thúc đẩy giao thương.",
        "requirements": {
            "tech": "steam_engine",
            "gdp": 100
        },
        "effects_desc": "+15% GDP, +10 Uy tín, +0.2 CSHT",
        "effects": {
            "gdp_growth_bonus": 0.15,
            "prestige": 10,
            "infrastructure": 0.2
        }
    },
    "suez_canal": {
        "name": "Kênh đào Suez / Panama",
        "cost": 30000,
        "time": 36, # 3 years
        "desc": "Kiến tạo tuyến đường hàng hải chiến lược rút ngắn giao thương thế giới.",
        "requirements": {
            "tech": "steam_engine",
            "gdp": 300
        },
        "effects_desc": "+25 Uy tín, +300 Gold/tháng",
        "effects": {
            "prestige": 25,
            "monthly_income": 300
        }
    },
    "education_reform": {
        "name": "Cải cách Giáo dục toàn diện",
        "cost": 5000,
        "time": 12, # 1 year
        "desc": "Đầu tư vào trường học công lập và chương trình xóa mù chữ quốc gia.",
        "requirements": {},
        "effects_desc": "+0.05% học vấn/tháng, +10% nghiên cứu",
        "effects": {
            "literacy_gain": 0.0005,
            "research_speed": 0.1
        }
    },
    "agricultural_mechanization": {
        "name": "Cơ giới hóa Nông nghiệp",
        "cost": 8000,
        "time": 18, # 1.5 years
        "desc": "Ứng dụng máy móc hơi nước vào canh tác nhằm tăng năng suất nông sản.",
        "requirements": {
            "tech": "steam_engine"
        },
        "effects_desc": "+0.05% dân số/tháng, +5% thuế",
        "effects": {
            "pop_growth_bonus": 0.0005,
            "tax_efficiency": 0.05
        }
    },
    "military_mobilization": {
        "name": "Tổng động viên Quân sự",
        "cost": 10000,
        "time": 12, # 1 year
        "desc": "Tổ chức lại hậu cần và huấn luyện lực lượng trừ bị sẵn sàng chiến đấu.",
        "requirements": {},
        "effects_desc": "+10k quân tức thì, +20% sức chiến đấu",
        "effects": {
            "manpower": 10000,
            "army_combat_modifier": 0.2
        }
    },
    "industrial_subsidies": {
        "name": "Trợ cấp Phát triển Công nghiệp",
        "cost": 12000,
        "time": 18, # 1.5 years
        "desc": "Hỗ trợ vốn để kích thích xây dựng các nhà máy dệt, thép.",
        "requirements": {
            "gdp": 50
        },
        "effects_desc": "+10% CN nhẹ/thép, +8% GDP",
        "effects": {
            "factory_efficiency": 0.1,
            "gdp_growth_bonus": 0.08
        }
    }
}

def ensure_project_attrs(country):
    """Đảm bảo quốc gia có đầy đủ thuộc tính dự án để tránh lỗi lưu/tải."""
    if not hasattr(country, "active_project"):
        country.active_project = None
    if not hasattr(country, "project_progress"):
        country.project_progress = 0
    if not hasattr(country, "project_time_needed"):
        country.project_time_needed = 0
    if not hasattr(country, "completed_projects"):
        country.completed_projects = []

def start_project(country, project_key):
    """Bắt đầu thực hiện một dự án quốc gia."""
    ensure_project_attrs(country)
    if country.active_project:
        return False
    
    proj = PROJECTS.get(project_key)
    if not proj:
        return False
        
    if country.treasury < proj["cost"]:
        return False
        
    # Kiểm tra yêu cầu công nghệ và GDP
    req = proj.get("requirements", {})
    req_tech = req.get("tech")
    if req_tech and req_tech not in getattr(country, "technologies", []):
        return False
        
    req_gdp = req.get("gdp")
    if req_gdp and country.gdp < req_gdp:
        return False
        
    # Trừ ngân khố và kích hoạt
    country.treasury -= proj["cost"]
    country.active_project = project_key
    country.project_progress = 0
    country.project_time_needed = proj["time"]
    return True

def cancel_project(country):
    """Hủy dự án đang thực hiện, hoàn trả 50% chi phí."""
    ensure_project_attrs(country)
    if not country.active_project:
        return False
        
    proj = PROJECTS.get(country.active_project)
    if proj:
        country.treasury += int(proj["cost"] * 0.5)
        
    country.active_project = None
    country.project_progress = 0
    country.project_time_needed = 0
    return True
