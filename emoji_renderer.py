"""Emoji 渲染器 - 从本地 emoji_icons 目录加载 Twemoji PNG 图标"""

import os
import sys
from PIL import Image

# emoji 图标目录（优先从项目目录加载，打包后从 sys._MEIPASS 加载）
def _get_icons_dir():
    """获取图标目录路径（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，从 _MEIPASS 目录加载
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "emoji_icons")


_ICONS_DIR = _get_icons_dir()

# 内存缓存
_memory_cache = {}


def _emoji_to_codepoint(emoji_str):
    """将 emoji 字符转为 Twemoji 文件名格式的 codepoint"""
    # 去除变体选择器 (U+FE0F)
    chars = [c for c in emoji_str if ord(c) != 0xFE0F]
    return "-".join(f"{ord(c):04x}" for c in chars)


def render_emoji(emoji_str, size):
    """
    渲染一个 emoji 为 Pillow Image（使用本地 Twemoji 图标）

    Args:
        emoji_str: emoji 字符串，如 '🕷'
        size: 目标尺寸（正方形边长）

    Returns:
        PIL.Image (RGBA) 或 None（渲染失败时）
    """
    cache_key = (emoji_str, size)
    if cache_key in _memory_cache:
        return _memory_cache[cache_key]

    result = _render_twemoji(emoji_str, size)
    if result is None:
        result = _render_emoji_fallback(emoji_str, size)

    _memory_cache[cache_key] = result
    return result


def _render_twemoji(emoji_str, size):
    """从本地 emoji_icons 目录加载 Twemoji PNG"""
    codepoint = _emoji_to_codepoint(emoji_str)
    filepath = os.path.join(_ICONS_DIR, f"{codepoint}.png")

    if not os.path.exists(filepath):
        return None

    try:
        img = Image.open(filepath).convert("RGBA")
        if img.size[0] != size or img.size[1] != size:
            img = img.resize((size, size), Image.LANCZOS)
        return img
    except Exception:
        return None


def _render_emoji_fallback(emoji_str, size):
    """回退方案：使用 Pillow 渲染单色 emoji"""
    try:
        from renderer import get_font
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        font = get_font(int(size * 0.8))
        draw.text((size // 2, size // 2), emoji_str, fill=(255, 255, 255, 255),
                  font=font, anchor="mm")
        has_content = any(
            img.getpixel((x, y))[3] > 0
            for x in range(size) for y in range(size)
        )
        if has_content:
            return img
    except Exception:
        pass
    return None
