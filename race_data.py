# 赛马系统配置数据（从 race_skills.json / race_weather.json / race_terrains.json 提取）

# 16个角色 {id: {name, icon}}
CHARACTERS = {
    1:  {"name": "阿布",      "icon": "🕷"},
    2:  {"name": "铃铛铛",    "icon": "🔔"},
    3:  {"name": "龙包包",    "icon": "🍙"},
    4:  {"name": "Ryu邪道长", "icon": "🚧"},
    5:  {"name": "三千宫魔王", "icon": "😈"},
    6:  {"name": "12dora",    "icon": "🚬"},
    7:  {"name": "陆夫人",    "icon": "🚩"},
    8:  {"name": "奶茶",      "icon": "🥤"},
    9:  {"name": "烤鱼",      "icon": "🐟"},
    10: {"name": "Api",       "icon": "🍍"},
    11: {"name": "yommyko",   "icon": "🐇"},
    12: {"name": "小肉包",    "icon": "🌻"},
    13: {"name": "巴老师",    "icon": "🦁"},
    14: {"name": "鹿头",      "icon": "🦌"},
    15: {"name": "雪绘",      "icon": "❄️"},
    16: {"name": "胡桃",      "icon": "✝️"},
    17: {"name": "乌拉拉",    "icon": "🍆"},
}

# 9种地形 {type: {color, name, desc}}
TERRAIN_CONFIG = {
    "bush":     {"color": "#90EE90", "name": "🌿 草丛",  "desc": "无法被他人技能选中"},
    "wetland":  {"color": "#87CEEB", "name": "💧 湿地",  "desc": "基础移动速度-1"},
    "rift":     {"color": "#8B4513", "name": "🏔 裂谷",  "desc": "移动≤2格则停留"},
    "swamp":    {"color": "#006400", "name": "🍂 沼泽",  "desc": "无法释放技能"},
    "mountain": {"color": "#808080", "name": "⛰ 山地",  "desc": "技能效果加倍"},
    "barrier":  {"color": "#FFD700", "name": "🚧 路障",  "desc": "首次到达必停"},
    "blackhole":{"color": "#1a1a1a", "name": "🕳 黑洞",  "desc": "朝向+1/背向-1"},
    "ice":      {"color": "#E0F0FF", "name": "❄ 冰面",  "desc": "停留时前滑1格"},
    "conveyor": {"color": "#4A4A00", "name": "⏪ 传送带", "desc": "停留时后滑1格"},
}

# 12种天气 {key: {name, icon}}
WEATHER_CONFIG = {
    "none":        {"name": "无天气",     "icon": "🌤"},
    "sunny":       {"name": "晴天",       "icon": "☀️"},
    "very_sunny":  {"name": "大晴天",     "icon": "🔥"},
    "rainy":       {"name": "雨天",       "icon": "🌧"},
    "heavy_rain":  {"name": "暴雨",       "icon": "⛈"},
    "sandstorm":   {"name": "沙尘暴",     "icon": "🌪"},
    "tailwind":    {"name": "大风(顺风)",  "icon": "💨"},
    "headwind":    {"name": "大风(逆风)",  "icon": "🌬"},
    "typhoon":     {"name": "台风",       "icon": "🌀"},
    "hail":        {"name": "冰雹",       "icon": "🧊"},
    "light_snow":  {"name": "小雪",       "icon": "🌨"},
    "heavy_snow":  {"name": "大雪",       "icon": "❄️"},
    "boulder_rain":{"name": "巨石雨",     "icon": "🪨"},
}

# 深色主题配色（与前端一致）
COLORS = {
    "bg_primary":    "#1a1a2e",   # 主背景
    "bg_card":       "#16213e",   # 卡片背景（偶数赛道）
    "bg_input":      "#0f3460",   # 输入框背景（奇数赛道）
    "text_primary":  "#e0e0e0",   # 主文字
    "text_secondary":"#a0a0a0",   # 次要文字
    "border":        "#333355",   # 边框线
    "border_light":  "#444466",   # 格点颜色
    "skill_buff":    "#448aff",   # 增益技能线
    "skill_debuff":  "#ff5252",   # 减益技能线
    "skill_reflect": "#ab47bc",   # 钢板反弹连线（紫色）
    "skill_deploy":  "#ff9800",   # 浮游炮部署连线（橙色）
    "log_move":      "#a0a0a0",   # 移动日志颜色
    "log_skill":     "#ffd54f",   # 技能日志颜色
    "log_weather":   "#4fc3f7",   # 天气日志颜色
    "log_terrain":   "#81c784",   # 地形日志颜色
    "log_finish":    "#ff7043",   # 完赛日志颜色
    "medal_gold":    "#ffd700",
    "medal_silver":  "#c0c0c0",
    "medal_bronze":  "#cd7f32",
    "finish_line":   "#dc3545",   # 终点线颜色
}

# 赛道长度对应的名称
TRACK_NAMES = {
    12: ("短距离", "💨"),
    16: ("中距离", "🏃"),
    20: ("长距离", "🏇"),
    24: ("超长距离", "🛤"),
}
