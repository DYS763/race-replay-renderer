"""PyInstaller 打包脚本

用法:
  python build.py              # 同时打包轻量版和完整版
  python build.py --lite-only  # 仅打包轻量版
"""

import PyInstaller.__main__
import os
import sys
from PIL import Image

# 项目根目录
project_dir = os.path.dirname(os.path.abspath(__file__))


def generate_icon():
    """从 1f3c1.png 生成 icon.ico"""
    ico_path = os.path.join(project_dir, "icon.ico")
    if os.path.exists(ico_path):
        return ico_path

    png_path = os.path.join(project_dir, "emoji_icons", "1f3c1.png")
    if not os.path.exists(png_path):
        print(f"警告: 找不到 {png_path}，跳过图标生成")
        return None

    print("生成 icon.ico...")
    img = Image.open(png_path).convert("RGBA")

    # 生成多尺寸 ICO
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon_images = []
    for size in icon_sizes:
        resized = img.resize(size, Image.LANCZOS)
        icon_images.append(resized)

    # 保存为 ICO
    icon_images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s.width, s.height) for s in icon_images],
        append_images=icon_images[1:],
    )
    print(f"  已生成: {ico_path}")
    return ico_path


def build_lite(icon_path):
    """打包轻量版（不含 ffmpeg）"""
    print("\n=== 打包轻量版 ===")
    name = "race-replay-renderer"

    args = [
        os.path.join(project_dir, "main.py"),
        "--onefile",
        "--name", name,
        "--clean",
        # 嵌入 emoji 图标目录
        "--add-data", f"{os.path.join(project_dir, 'emoji_icons')};emoji_icons",
        # 排除不需要的模块
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "numpy",
        "--exclude-module", "imageio",
        "--exclude-module", "imageio_ffmpeg",
        "--exclude-module", "IPython",
        "--exclude-module", "jupyter",
        "--exclude-module", "notebook",
        "--exclude-module", "sphinx",
        "--exclude-module", "unittest",
        "--exclude-module", "xml",
        "--exclude-module", "pydoc",
        "--exclude-module", "difflib",
        "--exclude-module", "email",
        "--exclude-module", "html",
        "--exclude-module", "http",
        "--exclude-module", "xmlrpc",
        # 隐藏导入
        "--hidden-import", "PIL",
        # 输出目录
        "--distpath", os.path.join(project_dir, "dist"),
        "--workpath", os.path.join(project_dir, "build_lite"),
        "--specpath", project_dir,
    ]

    if icon_path:
        args.extend(["--icon", icon_path])

    PyInstaller.__main__.run(args)
    print(f"\n轻量版打包完成: dist/{name}.exe")


def build_full(icon_path):
    """打包完整版（自带 ffmpeg）"""
    print("\n=== 打包完整版（自带 ffmpeg） ===")
    name = "race-replay-renderer-full"

    args = [
        os.path.join(project_dir, "main.py"),
        "--onefile",
        "--name", name,
        "--clean",
        # 嵌入 emoji 图标目录
        "--add-data", f"{os.path.join(project_dir, 'emoji_icons')};emoji_icons",
        # 排除不需要的模块（保留 numpy/imageio/imageio_ffmpeg）
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "cv2",
        "--exclude-module", "lxml",
        "--exclude-module", "psutil",
        "--exclude-module", "IPython",
        "--exclude-module", "jupyter",
        "--exclude-module", "notebook",
        "--exclude-module", "sphinx",
        # 收集 imageio-ffmpeg 的二进制
        "--collect-binaries", "imageio_ffmpeg",
        # 隐藏导入
        "--hidden-import", "PIL",
        "--hidden-import", "imageio",
        "--hidden-import", "imageio_ffmpeg",
        "--hidden-import", "imageio.v2",
        # 输出目录
        "--distpath", os.path.join(project_dir, "dist"),
        "--workpath", os.path.join(project_dir, "build_full"),
        "--specpath", project_dir,
    ]

    if icon_path:
        args.extend(["--icon", icon_path])

    PyInstaller.__main__.run(args)
    print(f"\n完整版打包完成: dist/{name}.exe")


if __name__ == "__main__":
    lite_only = "--lite-only" in sys.argv

    # 生成图标
    icon_path = generate_icon()

    # 打包轻量版
    build_lite(icon_path)

    # 默认也打包完整版，除非指定 --lite-only
    if not lite_only:
        build_full(icon_path)

    # 显示结果
    dist_dir = os.path.join(project_dir, "dist")
    if os.path.exists(dist_dir):
        print("\n=== 打包结果 ===")
        for f in os.listdir(dist_dir):
            if f.endswith(".exe"):
                size_mb = os.path.getsize(os.path.join(dist_dir, f)) / (1024 * 1024)
                print(f"  {f}: {size_mb:.1f} MB")
