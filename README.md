# Imgcompress

一款本地图片批量压缩工具，支持 JPG、PNG、GIF、WebP。默认无损压缩，可切换有损并自定义质量。

## 功能
- 批量压缩，按目录递归处理
- 无损与有损模式切换
- PNG 有损优先使用 pngquant
- GIF 支持动图压缩
- WebP、JPG、PNG、GIF 格式支持

## 环境准备
- Python 3.10+
- 依赖安装：pip install -r requirements.txt
- 可选：安装 pngquant 以获得更好的 PNG 有损压缩效果

## 运行
python main.py

## 使用说明
1. 选择输入目录或选择图片文件
2. 选择输出目录
3. 选择压缩模式（无损或有损）
4. 有损模式下调整质量滑块
5. 勾选需要处理的图片格式
6. 点击开始压缩

## 打包
已提供 PyInstaller 配置文件 imgcompress.spec，并封装了一键打包脚本：
- 安装打包工具：pip install pyinstaller
- 构建当前平台可执行文件：python build.py
- macOS 生成 dmg：python build_mac.py
- Windows 生成 exe：python build_windows.py

Windows 打包必须在 Windows 上运行，macOS 打包必须在 macOS 上运行。

为保证所有用户压缩效果与性能一致，建议把以下工具二进制放到项目根目录的 vendor/ 目录中并随包发布（程序会优先使用 vendor 内的工具，不依赖用户电脑是否安装）：
- pngquant（PNG 有损）
- oxipng 或 optipng（PNG 无损优化）
- cjpeg 或 mozjpeg（JPG 有损）
- jpegtran（JPG 无损优化）
- gifsicle（GIF 压缩）
- cwebp（WebP 有损/无损）

说明：
- 这些工具通常不是系统自带的，需要你准备对应平台的可执行文件（macOS/Windows 需要分别准备）
- 工具体积与平台/构建方式有关，一般单个在几百 KB 到数 MB 级别；若要同时内置多平台版本，总体会变大

## vendor 获取
已提供自动拉取脚本（本地执行一次即可，打包时直接复用 vendor）：
- 一键拉取 Windows + macOS（x64/arm64）：python fetch_vendor_all.py
- 多平台预拉取：python fetch_vendor.py --all --platforms=windows,macos --archs=x64,arm64
脚本默认使用 npm 国内镜像源（registry.npmmirror.com）下载各工具的 npm 包（tgz），再从包内的 vendor/ 目录解压出对应平台的二进制；若包内缺失，会尝试从国内二进制镜像补齐（cdn.npmmirror.com/binaries）。可通过环境变量 NPM_REGISTRY 与 BINARY_MIRROR 覆盖镜像源。
如果某个平台缺少二进制，可使用 --allow-missing 跳过（程序会回退到 Pillow 或系统 PATH 工具）。
Windows arm64 若当前版本缺失，会在失败后按优先级回退到 x64 版本。

vendor 目录结构：
- vendor/<platform>/<arch>/<tool>
- platform：windows | macos | linux
- arch：x64 | arm64

## 目录结构
- imgcompress/app.py 桌面界面
- imgcompress/compress.py 压缩逻辑
- imgcompress/models.py 数据模型
- main.py 程序入口
