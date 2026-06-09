# 赛马回放视频生成器

将赛马系统导出的 JSON 回放数据转换为 GIF / MP4 动画视频。

## 功能特性

- 复刻前端 Canvas 渲染效果，包含赛道、角色、地形、天气、技能连线等全部视觉元素
- 支持 GIF 和 MP4 两种输出格式
- 平滑缓动动画（easeInOutCubic），技能连线实时显示
- 事件日志面板，按类型着色（移动/技能/天气/地形）
- TUI 交互模式：双击或拖拽文件即可使用
- CLI 命令行模式：支持批量处理和参数自定义
- 实时进度显示

## 快速开始

### 使用打包好的 EXE（推荐）

无需安装 Python，直接运行即可。

1. 下载对应的 EXE 文件
2. **双击** `race-replay-renderer.exe` → 进入 TUI 交互模式，手动输入文件路径
3. **拖拽** JSON 文件到 EXE 上 → 自动加载文件，进入 TUI 选择输出选项

### 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# TUI 模式（拖拽或双击）
python main.py

# CLI 模式
python main.py replay.json
```

## 两个版本

| 版本 | 文件名 | 大小 | MP4 支持 |
|------|--------|------|----------|
| 轻量版 | `race-replay-renderer.exe` | ~10 MB | 需要系统安装 ffmpeg |
| 完整版 | `race-replay-renderer-full.exe` | ~54 MB | 内置 ffmpeg，无需额外安装 |

- 轻量版输出 MP4 时会调用系统 `ffmpeg`，需提前安装：`winget install ffmpeg`
- 完整版内置 imageio-ffmpeg，MP4 导出开箱即用

## 使用方式

### TUI 交互模式

双击 EXE 或拖拽 JSON 文件到 EXE 图标上，按提示操作：

```
==================================================
  赛马回放视频生成器
==================================================

输入文件: replay.json

参赛角色:
  1号: 🕷 阿布
  2号: 🔔 铃铛铛
  ...

--- 输出格式 ---
  1. GIF + MP4 (两者都输出)
  2. 仅 GIF
  3. 仅 MP4
请选择 [1/2/3] (默认1): 1

--- 播放速度 ---
  1. 0.5x (慢速)
  2. 1.0x (正常)
  3. 1.5x (稍快)
  4. 2.0x (快速)
  5. 3.0x (极速)
请选择 [1/2/3/4/5] (默认2): 2

--- 事件日志 ---
是否显示事件日志面板? [Y/n] (默认Y): y

确认开始渲染? [Y/n] (默认Y): y
```

### CLI 命令行模式

当传入参数包含 `-` 开头的选项时，自动进入 CLI 模式：

```bash
# 同时输出 GIF 和 MP4
race-replay-renderer replay.json

# 仅输出 GIF
race-replay-renderer replay.json -o output.gif

# 仅输出 MP4
race-replay-renderer replay.json -o output.mp4

# 2倍速播放
race-replay-renderer replay.json --speed 2

# 仅渲染前10回合
race-replay-renderer replay.json --max-turns 10

# 不显示事件日志
race-replay-renderer replay.json --no-log

# 自定义画布尺寸
race-replay-renderer replay.json --width 1200 --height 500 --log-height 300
```

### CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `input` | 必填 | JSON 回放文件路径 |
| `-o, --output` | 自动生成 | 输出文件路径（.gif 或 .mp4，可多次指定） |
| `--speed` | 1.0 | 播放速度倍率（0.5 / 1.0 / 1.5 / 2.0 / 3.0） |
| `--max-turns` | 全部 | 最大渲染回合数 |
| `--fps` | 15 | 帧率 |
| `--no-log` | false | 不渲染事件日志面板 |
| `--width` | 800 | 画布宽度（像素） |
| `--height` | 350 | 赛道区域高度（像素） |
| `--log-height` | 208 | 日志区域高度（像素） |

## 输入数据格式

输入为 JSON 文件，格式如下：

```json
{
  "version": 1,
  "track_length": 16,
  "characters": [
    {"track": 1, "id": 1, "name": "阿布", "icon": "🕷"},
    {"track": 2, "id": 2, "name": "铃铛铛", "icon": "🔔"}
  ],
  "terrains": {
    "mode": "fair",
    "cells": [{"pos": 5, "type": "bush"}, {"pos": 10, "type": "barrier"}],
    "removed_barriers": {}
  },
  "terrain_fair": true,
  "turns": [
    {
      "turn": 1,
      "positions": [14, 12],
      "events": [
        {"action": "move_log", "text": "阿布 前进了2格", "track": 1},
        {"action": "skill", "text": "铃铛铛 使用了 加速", "track": 2,
         "effects": [{"effect": "forward", "track": 2}]}
      ],
      "rankings": [{"track": 1, "position": 2, "rank": 1}]
    }
  ]
}
```

### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | int | 版本号，当前仅支持 `1` |
| `track_length` | int | 赛道长度（12 / 16 / 20 / 24） |
| `characters` | array | 角色列表，每项含 `track`（赛道号）、`id`、`name`、`icon` |
| `turns` | array | 回合数据列表 |

### 回合数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `turn` | int | 回合编号 |
| `positions` | array | 各角色当前位置（从赛道长度倒数到1） |
| `events` | array | 事件列表 |
| `rankings` | array | 排名列表（可选） |
| `terrains` | object | 本回合地形变化（可选，默认使用全局地形） |

### 事件类型

| action | 说明 | 日志颜色 |
|--------|------|----------|
| `move_log` | 移动记录 | 灰色 |
| `paused_log` | 停留记录 | 灰色 |
| `skill` | 技能触发 | 黄色 |
| `weather` | 天气变化 | 蓝色 |
| `terrain_*` | 地形相关 | 绿色 |

### 技能连线

技能事件中的 `effects` 数组用于生成技能连线：

```json
{
  "action": "skill",
  "track": 2,
  "effects": [
    {"effect": "forward", "track": 2},    // 自身增益 → 环形箭头
    {"effect": "backward", "track": 1}     // 他人减益 → 指向箭头
  ]
}
```

- **增益效果**（forward, prob_forward 等）：蓝色连线
- **减益效果**（backward, pause 等）：红色连线
- **自身效果**（`track` 等于施法者）：环形箭头（增益）或 X 标记（减益）
- **跨赛道效果**：从施法者到目标的箭头连线

### 支持的地形

| type | 名称 | 颜色 |
|------|------|------|
| `bush` | 草丛 | 绿色 |
| `wetland` | 湿地 | 蓝色 |
| `rift` | 裂谷 | 棕色 |
| `swamp` | 沼泽 | 深绿 |
| `mountain` | 山地 | 灰色 |
| `barrier` | 路障 | 金色 |
| `blackhole` | 黑洞 | 黑色 |
| `ice` | 冰面 | 浅蓝 |
| `conveyor` | 传送带 | 暗黄 |

### 支持的天气

`none`, `sunny`, `very_sunny`, `rainy`, `heavy_rain`, `sandstorm`, `tailwind`, `headwind`, `typhoon`, `hail`, `light_snow`, `heavy_snow`, `boulder_rain`

## 项目结构

```
race-replay-renderer/
├── main.py            # 入口，TUI/CLI 模式切换
├── renderer.py        # 核心渲染器（Pillow 绘图）
├── animator.py        # 动画帧生成（缓动插值 + 技能连线）
├── exporter.py        # GIF/MP4 导出
├── data_loader.py     # JSON 数据加载与校验
├── race_data.py       # 角色/地形/天气/配色配置
├── emoji_renderer.py  # Twemoji 图标渲染
├── build.py           # PyInstaller 打包脚本
├── requirements.txt   # Python 依赖
├── icon.ico           # EXE 图标（自动生成）
├── emoji_icons/       # 42 个 Twemoji PNG 图标
└── .gitignore
```

## 打包构建

```bash
# 安装打包依赖
pip install pillow pyinstaller imageio imageio-ffmpeg numpy

# 同时打包轻量版和完整版
python build.py

# 仅打包轻量版
python build.py --lite-only
```

输出文件在 `dist/` 目录下：

- `race-replay-renderer.exe` — 轻量版（~10 MB）
- `race-replay-renderer-full.exe` — 完整版（~54 MB）

## 渲染效果说明

动画画面从上到下分为三个区域：

1. **赛道区域** — 显示所有角色的位置、地形色块、技能连线、奖牌标记
2. **信息栏** — 显示赛道类型、回合数、天气、地形模式
3. **日志面板** — 按颜色分类显示当前回合的事件日志

每回合动画分为两个阶段：
- **移动阶段**（40%时长）：角色从上一位置平滑移动到新位置，技能连线全程显示
- **停留阶段**（60%时长）：角色静止，显示事件日志和排名

## 开发依赖

- **运行时**：`pillow>=10.0.0`
- **完整版额外**：`imageio`, `imageio-ffmpeg`, `numpy`（打包时内置）
- **打包工具**：`pyinstaller`
