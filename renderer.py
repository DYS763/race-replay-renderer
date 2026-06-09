"""核心渲染器 - 复刻前端 Canvas drawTrack() 逻辑，使用 Pillow 绘图"""

from PIL import Image, ImageDraw, ImageFont
from race_data import TERRAIN_CONFIG, COLORS, TRACK_NAMES
from emoji_renderer import render_emoji

# 尝试加载支持 emoji 的字体
def _load_font(size):
    """尝试加载支持中文和 emoji 的字体"""
    font_paths = [
        "C:/Windows/Fonts/segoeuiemoji.ttf",   # Windows Emoji
        "C:/Windows/Fonts/msyh.ttc",            # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",          # 黑体
        "C:/Windows/Fonts/seguiemj.ttf",        # Segoe UI Emoji
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# 预加载字体
_font_cache = {}

def get_font(size):
    if size not in _font_cache:
        _font_cache[size] = _load_font(size)
    return _font_cache[size]


def _hex_to_rgb(hex_color):
    """十六进制颜色转 RGB 元组"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _hex_to_rgba(hex_color, alpha=1.0):
    """十六进制颜色转 RGBA 元组"""
    r, g, b = _hex_to_rgb(hex_color)
    return (r, g, b, int(alpha * 255))


# 渲染器默认尺寸（可由 main.py 覆盖）
_render_width = 800
_render_height = 350
_render_log_height = 208


class RaceRenderer:
    """赛马赛道渲染器"""

    def __init__(self, width=None, track_height=None, log_height=None):
        self.width = width or _render_width
        self.track_height = track_height or _render_height
        self.info_bar_height = 24  # 信息栏高度
        self.log_height = log_height or _render_log_height
        self.total_height = self.track_height + self.info_bar_height + self.log_height

        # 渲染参数（与前端 drawTrack 一致）
        self.margin = 60
        self.right_margin = 30

    def render_frame(self, characters, track_length, positions, terrains=None,
                     rankings=None, skill_lines=None, turn_number=None,
                     total_turns=None, events=None, weather_name=None,
                     terrain_fair=True):
        """
        渲染一帧画面

        Args:
            characters: 角色列表 [{track, id, name, icon}, ...]
            track_length: 赛道长度 (12/16/20/24)
            positions: 位置列表 [pos1, pos2, ...]，值从 track_length 到 1
            terrains: 地形数据 {mode, cells/tracks, removed_barriers}
            rankings: 排名列表 [{track, position, rank}, ...]
            skill_lines: 技能连线 [{from, to, type, isSelf}, ...]
            turn_number: 当前回合号
            total_turns: 总回合数
            events: 当前回合事件列表 [{action, text, track, effects?}, ...]
            weather_name: 天气名称
            terrain_fair: 是否公平地形
        """
        num_tracks = len(characters) or 7
        track_h = min(50, self.track_height / num_tracks)

        # 创建画布（赛道区域 + 日志区域）
        img = Image.new("RGBA", (self.width, self.total_height), _hex_to_rgb(COLORS["bg_primary"]))
        self._current_img = img  # 供 _draw_emoji 粘贴图片
        draw = ImageDraw.Draw(img)

        # 绘制赛道区域
        self._draw_tracks(draw, characters, track_length, positions, terrains,
                          rankings, skill_lines, num_tracks, track_h)

        # 绘制顶部信息栏
        self._draw_info_bar(draw, track_length, turn_number, total_turns,
                            weather_name, terrain_fair, num_tracks, track_h)

        # 绘制日志区域
        if events is not None:
            self._draw_log_panel(draw, events, num_tracks, track_h)

        return img

    def _draw_tracks(self, draw, characters, track_length, positions, terrains,
                     rankings, skill_lines, num_tracks, track_h):
        """绘制赛道区域"""
        colors = COLORS
        track_span = self.width - self.margin - self.right_margin

        for i in range(num_tracks):
            y = i * track_h

            # 交替背景
            bg_color = _hex_to_rgb(colors["bg_card"] if i % 2 == 0 else colors["bg_input"])
            draw.rectangle([0, y, self.width, y + track_h], fill=bg_color)

            # 中心线
            draw.line(
                [(self.margin, y + track_h / 2), (self.width - self.right_margin, y + track_h / 2)],
                fill=_hex_to_rgb(colors["border"]),
                width=1
            )

            # 格点
            for step in range(track_length):
                x = self.margin + step * track_span / (track_length - 1)
                draw.ellipse(
                    [x - 2, y + track_h / 2 - 2, x + 2, y + track_h / 2 + 2],
                    fill=_hex_to_rgb(colors["border_light"])
                )

            # 地形渲染
            if terrains:
                self._draw_terrains(draw, terrains, i + 1, track_length, y, track_h, track_span)

            # 角色渲染
            char_data = characters[i] if i < len(characters) else None
            pos = positions[i] if i < len(positions) else track_length
            progress = (track_length - pos) / (track_length - 1)
            char_x = self.margin + progress * track_span
            char_y = y + track_h / 2

            # 角色 emoji
            icon = char_data["icon"] if char_data else "🏃"
            self._draw_emoji(draw, icon, char_x, char_y, 22)

            # 奖牌
            if rankings:
                rank_info = next((r for r in rankings if r["track"] == i + 1), None)
                if rank_info and rank_info["rank"] <= 3:
                    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                    self._draw_emoji(draw, medals[rank_info["rank"]], char_x + 18, char_y - 12, 14)

            # 赛道号
            font_small = get_font(13)
            draw.text((8, char_y), f"{i + 1}", fill=_hex_to_rgb(colors["text_secondary"]),
                      font=font_small, anchor="lm")

            # 角色名
            if char_data:
                font_name = get_font(11)
                draw.text((self.margin - 5, char_y), char_data["name"],
                          fill=_hex_to_rgb(colors["text_secondary"]),
                          font=font_name, anchor="rm")

        # 终点标记
        self._draw_emoji(draw, "🏁", self.margin, 14, 16)

        # 技能连线
        if skill_lines:
            self._draw_skill_lines(draw, skill_lines, characters, positions,
                                   track_length, num_tracks, track_h, track_span)

    def _draw_terrains(self, draw, terrains, track_num, track_length, y, track_h, track_span):
        """绘制地形色块"""
        cells = self._get_terrain_cells(terrains, track_num)
        step_width = track_span / (track_length - 1)

        for cell in cells:
            pos = cell.get("pos", 0)
            cell_type = cell.get("type", "")
            if pos < 1 or pos > track_length:
                continue
            cfg = TERRAIN_CONFIG.get(cell_type)
            if not cfg:
                continue

            progress = (track_length - pos) / (track_length - 1)
            x = self.margin + progress * track_span
            half_step = step_width / 2
            left = self.margin if pos == track_length else x - half_step
            right = self.width - self.right_margin if pos == 1 else x + half_step

            # 半透明色块
            color_rgb = _hex_to_rgb(cfg["color"])
            # 用 overlay 方式模拟半透明
            overlay_color = (*color_rgb, 90)  # ~35% alpha
            # Pillow ImageDraw 不直接支持半透明矩形，用实色近似
            # 混合底色和地形色
            bg_color = _hex_to_rgb(COLORS["bg_card"] if (track_num - 1) % 2 == 0 else COLORS["bg_input"])
            blended = self._blend_colors(bg_color, color_rgb, 0.35)
            draw.rectangle([left, y + 2, right, y + track_h - 2], fill=blended)

    def _draw_skill_lines(self, draw, skill_lines, characters, positions,
                          track_length, num_tracks, track_h, track_span):
        """绘制技能连线（实线箭头，增大可见性）"""
        import math

        for line in skill_lines:
            from_idx = line["from"] - 1
            to_idx = line["to"] - 1
            if from_idx < 0 or from_idx >= num_tracks:
                continue

            from_y = from_idx * track_h + track_h / 2
            from_pos = positions[from_idx] if from_idx < len(positions) else track_length
            from_progress = (track_length - from_pos) / (track_length - 1)
            from_x = self.margin + from_progress * track_span

            line_color = _hex_to_rgb(COLORS["skill_debuff"] if line["type"] == "debuff"
                                      else COLORS["skill_buff"])
            line_width = 3  # 增大线宽

            if line.get("isSelf") and line["type"] == "buff":
                # 自身增益：环形箭头
                r = 12
                draw.ellipse(
                    [from_x - r, from_y - r, from_x + r, from_y + r],
                    outline=line_color, width=line_width
                )
                # 小箭头指向右
                draw.polygon([
                    (from_x + r + 6, from_y),
                    (from_x + r - 2, from_y - 5),
                    (from_x + r - 2, from_y + 5),
                ], fill=line_color)
            elif line.get("isSelf") and line["type"] == "debuff":
                # 自身减益：X 标记
                r = 8
                draw.line([(from_x - r, from_y - r), (from_x + r, from_y + r)],
                          fill=line_color, width=line_width)
                draw.line([(from_x - r, from_y + r), (from_x + r, from_y - r)],
                          fill=line_color, width=line_width)
            elif not line.get("isSelf"):
                if to_idx < 0 or to_idx >= num_tracks:
                    continue
                to_y = to_idx * track_h + track_h / 2
                to_pos = positions[to_idx] if to_idx < len(positions) else track_length
                to_progress = (track_length - to_pos) / (track_length - 1)
                to_x = self.margin + to_progress * track_span

                # 从施法者到目标画线
                draw.line([(from_x, from_y), (to_x, to_y)], fill=line_color, width=line_width)

                # 箭头在目标端
                angle = math.atan2(to_y - from_y, to_x - from_x)
                arrow_len = 12  # 增大箭头
                # 箭头尖端在目标位置偏移一点
                tip_x = to_x - 10 * math.cos(angle)
                tip_y = to_y - 10 * math.sin(angle)
                draw.polygon([
                    (tip_x, tip_y),
                    (tip_x - arrow_len * math.cos(angle - math.pi / 6),
                     tip_y - arrow_len * math.sin(angle - math.pi / 6)),
                    (tip_x - arrow_len * math.cos(angle + math.pi / 6),
                     tip_y - arrow_len * math.sin(angle + math.pi / 6)),
                ], fill=line_color)

    def _draw_info_bar(self, draw, track_length, turn_number, total_turns,
                       weather_name, terrain_fair, num_tracks, track_h):
        """绘制信息栏（赛道下方独立区域）"""
        info_y = num_tracks * track_h
        info_h = self.info_bar_height
        # 信息栏背景（向下延伸，不覆盖赛道）
        draw.rectangle([0, info_y, self.width, info_y + info_h], fill=_hex_to_rgb(COLORS["bg_primary"]))

        # 分隔线
        draw.line([(0, info_y), (self.width, info_y)], fill=_hex_to_rgb(COLORS["border"]), width=1)

        font_info = get_font(12)
        parts = []

        # 赛道信息
        track_info = TRACK_NAMES.get(track_length, (f"{track_length}格", "🏃"))
        parts.append(f"{track_info[1]} {track_info[0]}")

        # 回合信息
        if turn_number is not None:
            turn_text = f"第{turn_number}回合"
            if total_turns:
                turn_text += f"/{total_turns}"
            parts.append(turn_text)

        # 天气
        if weather_name:
            parts.append(f"天气: {weather_name}")

        # 地形模式
        terrain_mode = "公平地形" if terrain_fair else "随机地形"
        parts.append(terrain_mode)

        text = "  |  ".join(parts)
        draw.text((10, info_y + info_h // 2), text, fill=_hex_to_rgb(COLORS["text_secondary"]),
                  font=font_info, anchor="lm")

    def _draw_log_panel(self, draw, events, num_tracks, track_h):
        """绘制底部日志面板"""
        log_top = num_tracks * track_h + self.info_bar_height
        log_bottom = self.total_height

        # 日志区域背景
        draw.rectangle([0, log_top, self.width, log_bottom], fill=_hex_to_rgb("#0d1117"))

        # 分隔线
        draw.line([(0, log_top), (self.width, log_top)], fill=_hex_to_rgb(COLORS["border"]), width=1)

        if not events:
            return

        font_log = get_font(11)
        x = 10
        y = log_top + 8
        line_height = 16
        max_lines = int((log_bottom - log_top - 10) / line_height)

        for i, ev in enumerate(events[:max_lines]):
            text = ev.get("text", "")
            if not text:
                continue

            # 根据事件类型选择颜色
            action = ev.get("action", "")
            if action == "move_log":
                color = _hex_to_rgb(COLORS["log_move"])
            elif action == "paused_log":
                color = _hex_to_rgb(COLORS["log_move"])
            elif action == "skill":
                color = _hex_to_rgb(COLORS["log_skill"])
            elif action == "weather":
                color = _hex_to_rgb(COLORS["log_weather"])
            elif action.startswith("terrain_"):
                color = _hex_to_rgb(COLORS["log_terrain"])
            else:
                color = _hex_to_rgb(COLORS["text_primary"])

            # 清理 {c:xxx}...{/c} 标记
            clean_text = self._clean_skill_colors(text)

            # 截断过长文本
            max_chars = (self.width - 20) // 7  # 大约每字符7px
            if len(clean_text) > max_chars:
                clean_text = clean_text[:max_chars - 3] + "..."

            draw.text((x, y), clean_text, fill=color, font=font_log)
            y += line_height

    def _draw_emoji(self, draw, emoji, x, y, size):
        """绘制 emoji（使用 Twemoji 彩色图标）"""
        emoji_img = render_emoji(emoji, size)
        if emoji_img is not None:
            # 粘贴到画布上（需要获取底层 img 对象）
            # draw 对象有 im 属性指向底层 Image
            paste_x = int(x - size / 2)
            paste_y = int(y - size / 2)
            # 使用 alpha 合成
            if hasattr(self, '_current_img'):
                self._current_img.paste(emoji_img, (paste_x, paste_y), emoji_img)
        else:
            # 回退：用文字渲染
            try:
                font = get_font(size - 4)
                draw.text((x, y), "?", fill=_hex_to_rgb(COLORS["text_primary"]),
                          font=font, anchor="mm")
            except Exception:
                pass

    @staticmethod
    def _get_terrain_cells(terrains, track_num):
        """获取指定赛道的地形格子"""
        mode = terrains.get("mode", "fair")
        if mode == "fair":
            cells = terrains.get("cells", [])
        else:
            cells = (terrains.get("tracks", {})).get(str(track_num), [])

        # 过滤已移除的路障
        removed = terrains.get("removed_barriers", {})
        if mode == "fair":
            removed_positions = removed.get("all", [])
        else:
            removed_positions = removed.get(str(track_num), [])

        if not removed_positions:
            return cells
        return [c for c in cells if not (c.get("type") == "barrier" and c.get("pos") in removed_positions)]

    @staticmethod
    def _blend_colors(bg, fg, alpha):
        """混合两种颜色（模拟半透明）"""
        return tuple(int(bg[i] * (1 - alpha) + fg[i] * alpha) for i in range(3))

    @staticmethod
    def _clean_skill_colors(text):
        """清理 {c:xxx}...{/c} 标记，保留内容"""
        import re
        return re.sub(r"\{c:\w+\}(.*?)\{/c\}", r"\1", text)
