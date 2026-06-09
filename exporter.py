"""GIF/MP4 导出器"""

import os
import sys
import shutil
import subprocess
import tempfile
from PIL import Image


def _rgba_to_rgb(frame, bg_color=(26, 26, 46)):
    """将 RGBA 帧转为 RGB，用指定背景色替换透明区域"""
    if frame.mode == "RGBA":
        bg = Image.new("RGB", frame.size, bg_color)
        bg.paste(frame, mask=frame.split()[3])
        return bg
    return frame.convert("RGB")


def _progress_bar(current, total, width=30):
    """生成进度条字符串"""
    pct = current / total
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {pct*100:.0f}% ({current}/{total})"


def check_ffmpeg():
    """检查系统是否安装了 ffmpeg"""
    return shutil.which("ffmpeg") is not None


def export_gif(frames, output_path, fps=15, loop=True, progress_callback=None):
    """
    导出 GIF

    Args:
        frames: PIL.Image 帧列表
        output_path: 输出文件路径
        fps: 帧率
        loop: 是否循环播放
        progress_callback: 进度回调 callback(current, total)
    """
    frame_list = list(frames)
    if not frame_list:
        print("错误: 没有帧可导出")
        return

    total = len(frame_list)
    print(f"正在导出 GIF: {output_path} ({total} 帧, {fps}fps)")

    # 转换为 RGB 模式
    rgb_frames = []
    for i, f in enumerate(frame_list):
        rgb_frames.append(_rgba_to_rgb(f))
        if progress_callback:
            progress_callback(i + 1, total)
        elif (i + 1) % 50 == 0 or i + 1 == total:
            print(f"\r  转换帧: {_progress_bar(i + 1, total)}", end="", flush=True)

    if not progress_callback:
        print()  # 换行

    # 量化为 256 色调色板模式（P 模式）
    print("  量化调色板...")
    palette_frame = rgb_frames[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)

    p_frames = []
    for i, f in enumerate(rgb_frames):
        pf = f.quantize(palette=palette_frame, dither=Image.Dither.FLOYDSTEINBERG)
        p_frames.append(pf)
        if progress_callback:
            progress_callback(i + 1, total)
        elif (i + 1) % 50 == 0 or i + 1 == total:
            print(f"\r  量化: {_progress_bar(i + 1, total)}", end="", flush=True)

    if not progress_callback:
        print()

    duration_ms = int(1000 / fps)

    print("  保存 GIF 文件...")
    p_frames[0].save(
        output_path,
        save_all=True,
        append_images=p_frames[1:],
        duration=duration_ms,
        loop=0 if loop else 1,
        optimize=False,
        disposal=2,
    )

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"GIF 导出完成: {size_mb:.1f} MB")


def export_mp4(frames, output_path, fps=15, progress_callback=None):
    """
    导出 MP4（优先使用内嵌 imageio，否则使用系统 ffmpeg）
    """
    # 优先尝试 imageio（完整版自带）
    try:
        import imageio.v2 as imageio
        import numpy as np
        _export_mp4_imageio(frames, output_path, fps, progress_callback, imageio, np)
        return
    except ImportError:
        pass

    # 回退到系统 ffmpeg
    _export_mp4_ffmpeg(frames, output_path, fps, progress_callback)


def _export_mp4_imageio(frames, output_path, fps, progress_callback, imageio, np):
    """使用内嵌 imageio-ffmpeg 导出 MP4"""
    frame_list = list(frames)
    if not frame_list:
        print("错误: 没有帧可导出")
        return

    total = len(frame_list)
    print(f"正在导出 MP4: {output_path} ({total} 帧, {fps}fps)")

    video_frames = []
    for i, frame in enumerate(frame_list):
        rgb = _rgba_to_rgb(frame)
        video_frames.append(np.array(rgb))
        if progress_callback:
            progress_callback(i + 1, total)
        elif (i + 1) % 50 == 0 or i + 1 == total:
            print(f"\r  转换帧: {_progress_bar(i + 1, total)}", end="", flush=True)

    if not progress_callback:
        print()

    print("  编码视频...")
    writer = imageio.get_writer(output_path, fps=fps, codec="libx264",
                                 output_params=["-crf", "23", "-preset", "medium"])
    for vf in video_frames:
        writer.append_data(vf)
    writer.close()

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"MP4 导出完成: {size_mb:.1f} MB")


def _export_mp4_ffmpeg(frames, output_path, fps, progress_callback):
    """使用系统 ffmpeg 导出 MP4"""
    if not check_ffmpeg():
        print("错误: 需要安装 ffmpeg 才能导出 MP4")
        print("  下载地址: https://ffmpeg.org/download.html")
        print("  或使用: winget install ffmpeg")
        return

    frame_list = list(frames)
    if not frame_list:
        print("错误: 没有帧可导出")
        return

    total = len(frame_list)
    print(f"正在导出 MP4: {output_path} ({total} 帧, {fps}fps)")

    # 将帧保存为临时 PNG 序列
    tmp_dir = tempfile.mkdtemp(prefix="race_replay_")
    try:
        for i, frame in enumerate(frame_list):
            rgb = _rgba_to_rgb(frame)
            rgb.save(os.path.join(tmp_dir, f"frame_{i:06d}.png"))
            if progress_callback:
                progress_callback(i + 1, total)
            elif (i + 1) % 50 == 0 or i + 1 == total:
                print(f"\r  保存帧: {_progress_bar(i + 1, total)}", end="", flush=True)

        if not progress_callback:
            print()

        # 调用 ffmpeg 合成 MP4
        print("  调用 ffmpeg 合成视频...")
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", os.path.join(tmp_dir, "frame_%06d.png"),
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg 错误: {result.stderr[:500]}")
            return

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"MP4 导出完成: {size_mb:.1f} MB")

    finally:
        # 清理临时文件
        shutil.rmtree(tmp_dir, ignore_errors=True)
