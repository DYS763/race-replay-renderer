import json
import sys
from race_data import CHARACTERS


def load_replay(filepath):
    """加载并校验回放 JSON 文件"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件不存在: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败: {e}")
        sys.exit(1)

    # 校验版本
    version = data.get("version")
    if version != 1:
        print(f"错误: 不支持的版本号 {version}，当前仅支持 version 1")
        sys.exit(1)

    # 校验必要字段
    required_fields = ["track_length", "characters", "turns"]
    for field in required_fields:
        if field not in data:
            print(f"错误: 缺少必要字段 '{field}'")
            sys.exit(1)

    track_length = data["track_length"]
    characters = data["characters"]
    turns = data["turns"]

    if not turns:
        print("错误: 回合数据为空")
        sys.exit(1)

    # 补全角色信息（如果 JSON 中的角色缺少 name/icon）
    for char in characters:
        char_id = char.get("id")
        if char_id and char_id in CHARACTERS:
            if not char.get("name"):
                char["name"] = CHARACTERS[char_id]["name"]
            if not char.get("icon"):
                char["icon"] = CHARACTERS[char_id]["icon"]

    return {
        "track_length": track_length,
        "characters": characters,
        "turns": turns,
        "terrains": data.get("terrains"),
        "terrain_fair": data.get("terrain_fair", True),
    }
