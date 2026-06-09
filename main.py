"""赛马回放视频生成器 - CLI 入口"""

import argparse
import os
import sys

from data_loader import load_replay
from animator import generate_frames
from exporter import export_gif, export_mp4, check_ffmpeg


def _progress_bar(current, total, prefix="", width=30):
    """打印单行进度条"""
    pct = current / total if total > 0 else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    print(f"\r{prefix}[{bar}] {pct*100:.0f}% ({current}/{total})", end="", flush=True)


def run_tui(input_file=None):
    """TUI 交互模式"""
    print()
    print("=" * 50)
    print("  赛马回放视频生成器")
    print("=" * 50)
    print()

    # 1. 选择文件
    if input_file:
        filepath = input_file
        print(f"输入文件: {filepath}")
    else:
        filepath = input("请输入 JSON 回放文件路径: ").strip().strip('"').strip("'")
        if not filepath:
            print("错误: 未指定文件路径")
            input("按回车退出...")
            return

    if not os.path.exists(filepath):
        print(f"错误: 文件不存在: {filepath}")
        input("按回车退出...")
        return

    # 加载数据
    print(f"\n加载回放数据: {filepath}")
    try:
        replay_data = load_replay(filepath)
    except SystemExit:
        input("按回车退出...")
        return

    print(f"  赛道长度: {replay_data['track_length']}")
    print(f"  参赛角色: {len(replay_data['characters'])} 名")
    print(f"  总回合数: {len(replay_data['turns'])}")

    # 显示角色列表
    print("\n参赛角色:")
    for char in replay_data["characters"]:
        print(f"  {char['track']}号: {char['icon']} {char['name']}")

    # 检测 ffmpeg
    has_ffmpeg = check_ffmpeg()
    if not has_ffmpeg:
        print("\n注意: 未检测到 ffmpeg，将无法输出 MP4 格式")
        print("  安装方法: winget install ffmpeg")
        print("  或者请下载完整版生成器，其内置了ffmpeg，无需额外安装")

    # 2. 选择输出格式
    print("\n--- 输出格式 ---")
    if has_ffmpeg:
        print("  1. GIF + MP4 (两者都输出)")
        print("  2. 仅 GIF")
        print("  3. 仅 MP4")
        format_choice = input("请选择 [1/2/3] (默认1): ").strip() or "1"
    else:
        print("  1. 仅 GIF (未安装 ffmpeg，无法输出 MP4)")
        format_choice = "2"

    input_basename = os.path.splitext(os.path.basename(filepath))[0]
    if format_choice == "2":
        outputs = [f"{input_basename}.gif"]
    elif format_choice == "3":
        outputs = [f"{input_basename}.mp4"]
    else:
        outputs = [f"{input_basename}.gif", f"{input_basename}.mp4"]

    # 3. 选择播放速度
    print("\n--- 播放速度 ---")
    print("  1. 0.5x (慢速)")
    print("  2. 1.0x (正常)")
    print("  3. 1.5x (稍快)")
    print("  4. 2.0x (快速)")
    print("  5. 3.0x (极速)")
    speed_choice = input("请选择 [1/2/3/4/5] (默认2): ").strip() or "2"
    speed_map = {"1": 0.5, "2": 1.0, "3": 1.5, "4": 2.0, "5": 3.0}
    speed = speed_map.get(speed_choice, 1.0)

    # 4. 是否显示日志
    print("\n--- 事件日志 ---")
    show_log_input = input("是否显示事件日志面板? [Y/n] (默认Y): ").strip().lower()
    show_log = show_log_input != "n"

    # 5. 确认
    print("\n--- 确认 ---")
    print(f"  输入文件: {filepath}")
    print(f"  输出格式: {', '.join(os.path.splitext(o)[1][1:].upper() for o in outputs)}")
    print(f"  播放速度: {speed}x")
    print(f"  事件日志: {'显示' if show_log else '隐藏'}")
    confirm = input("\n确认开始渲染? [Y/n] (默认Y): ").strip().lower()
    if confirm == "n":
        print("已取消")
        input("按回车退出...")
        return

    # 执行渲染
    _do_render(replay_data, filepath, outputs, speed=speed, show_log=show_log)

    print("\n渲染完成!")
    for o in outputs:
        if os.path.exists(o):
            size_mb = os.path.getsize(o) / (1024 * 1024)
            print(f"  {o}: {size_mb:.1f} MB")

    input("\n按回车退出...")


def _do_render(replay_data, filepath, outputs, speed=1.0, fps=15, max_turns=None,
               show_log=True, width=800, height=350, log_height=208):
    """执行渲染"""
    # 保存渲染器尺寸参数（供 animator 使用）
    import renderer as _renderer
    _renderer._render_width = width
    _renderer._render_height = height
    _renderer._render_log_height = log_height

    # 进度回调
    def on_frame_progress(current, total):
        _progress_bar(current, total, prefix="生成动画帧: ")

    # 生成帧
    print(f"\n生成动画帧 (速度: {speed}x, FPS: {fps})...")
    frames = generate_frames(
        replay_data,
        speed=speed,
        fps=fps,
        max_turns=max_turns,
        show_log=show_log,
        progress_callback=on_frame_progress,
    )

    # 收集帧（带进度）
    frame_list = list(frames)
    print(f"\n共 {len(frame_list)} 帧")

    for out_path in outputs:
        ext = os.path.splitext(out_path)[1].lower()
        if ext == ".gif":
            export_gif(frame_list, out_path, fps=fps)
        elif ext == ".mp4":
            export_mp4(frame_list, out_path, fps=fps)


def main():
    # 检测是否进入 TUI 模式
    # 双击 exe: sys.argv = ['xxx.exe']
    # 拖拽文件: sys.argv = ['xxx.exe', 'replay.json']
    if len(sys.argv) <= 2 and not any(a.startswith("-") for a in sys.argv[1:]):
        # TUI 模式
        input_file = sys.argv[1] if len(sys.argv) == 2 else None
        run_tui(input_file)
        return

    # CLI 模式
    parser = argparse.ArgumentParser(
        description="赛马回放视频生成器 - 将导出的 JSON 回放数据转为 GIF/MP4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  race-replay-renderer replay.json                    # 同时输出 GIF 和 MP4
  race-replay-renderer replay.json -o output.gif      # 仅输出 GIF
  race-replay-renderer replay.json -o output.mp4      # 仅输出 MP4
  race-replay-renderer replay.json --speed 2          # 2倍速播放
  race-replay-renderer replay.json --max-turns 10     # 仅渲染前10回合
  race-replay-renderer replay.json --no-log           # 不显示事件日志
        """
    )

    parser.add_argument("input", help="JSON 回放文件路径")
    parser.add_argument("-o", "--output", action="append", default=None,
                        help="输出文件路径（.gif 或 .mp4，可多次指定）")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="播放速度倍率（默认 1.0，支持 0.5/1.0/1.5/2.0/3.0）")
    parser.add_argument("--max-turns", type=int, default=None,
                        help="最大渲染回合数（默认全部）")
    parser.add_argument("--fps", type=int, default=15,
                        help="帧率（默认 15）")
    parser.add_argument("--no-log", action="store_true",
                        help="不渲染事件日志面板")
    parser.add_argument("--width", type=int, default=800,
                        help="画布宽度（默认 800）")
    parser.add_argument("--height", type=int, default=350,
                        help="赛道区域高度（默认 350）")
    parser.add_argument("--log-height", type=int, default=208,
                        help="日志区域高度（默认 208）")

    args = parser.parse_args()

    # 加载数据
    print(f"加载回放数据: {args.input}")
    replay_data = load_replay(args.input)
    print(f"  赛道长度: {replay_data['track_length']}")
    print(f"  参赛角色: {len(replay_data['characters'])} 名")
    print(f"  总回合数: {len(replay_data['turns'])}")

    # 确定输出格式
    input_basename = os.path.splitext(os.path.basename(args.input))[0]
    outputs = args.output

    if not outputs:
        outputs = [f"{input_basename}.gif", f"{input_basename}.mp4"]

    # 验证输出格式
    valid_extensions = {".gif", ".mp4"}
    for out_path in outputs:
        ext = os.path.splitext(out_path)[1].lower()
        if ext not in valid_extensions:
            print(f"错误: 不支持的输出格式 '{ext}'，仅支持 .gif 和 .mp4")
            sys.exit(1)

    # 检查 MP4 是否需要 ffmpeg
    if any(os.path.splitext(o)[1].lower() == ".mp4" for o in outputs):
        if not check_ffmpeg():
            print("警告: 未检测到 ffmpeg，MP4 输出将不可用")
            print("  安装方法: winget install ffmpeg")
            outputs = [o for o in outputs if os.path.splitext(o)[1].lower() != ".mp4"]
            if not outputs:
                print("错误: 没有可用的输出格式")
                sys.exit(1)

    _do_render(replay_data, args.input, outputs,
               speed=args.speed, fps=args.fps, max_turns=args.max_turns,
               show_log=not args.no_log, width=args.width, height=args.height,
               log_height=args.log_height)

    print("完成!")


if __name__ == "__main__":
    main()
