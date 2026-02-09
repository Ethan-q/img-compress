# Imgcompress（C++/Qt 原生版）

## 功能介绍
本工具以 C++/Qt 原生版为发行目标，提供本地批量图片压缩与格式转换能力，覆盖 JPG/PNG/GIF/WebP，面向专业压缩流程设计：
- 目录递归与文件列表两种批量模式
- 无损/有损模式切换，质量与强度可控
- 输出格式真正转换，不是改后缀
- 输出尺寸支持三态：原尺寸 / 宽高等比 / 强制裁剪
- 引擎状态可见，方便排查工具缺失

## 组合算法与调参维度（专业说明）
整体流程由“输入判断 → 尺寸处理 → 临时输出 → 专业引擎压缩 → 结果守护”组成，强调可控性与可追踪性：
1. 输入与输出判定  
   - 默认保持原格式，也可指定输出为 JPG/PNG/WebP/GIF  
   - WebP 编码使用 cwebp，WebP 解码使用 dwebp  
   - GIF 仅支持压缩，不支持从其他格式转换  
   - 引擎优先从应用目录与 vendor 目录查找，必要时回退系统 PATH  
   - 扩展名与实际格式不一致时会提示并按实际格式输出  
2. 尺寸处理策略  
   - 原尺寸：不做几何处理  
   - 宽高等比：等比缩放，保留完整画面  
   - 强制裁剪：等比放大后居中裁剪，保证目标宽高  
   - 启用尺寸裁剪/缩放时，WebP 需要 Qt WebP 插件，否则会提示不支持  
3. 引擎组合策略  
   - JPG 有损：mozjpeg(cjpeg)  
   - JPG 无损：jpegtran  
   - PNG 有损：pngquant  
   - PNG 无损：oxipng/optipng  
   - GIF：gifsicle  
   - WebP 编码：cwebp  
   - WebP 解码：dwebp  
   - WebP 转 JPG：dwebp 解码为 PPM，再交给 mozjpeg 编码  
   - WebP 转 PNG：dwebp 直接输出 PNG  
4. 调参维度（有损场景）  
   - 质量等级（quality）用于控制目标码率  
   - 强度档位（高/均衡/强）用于二次调整质量区间与速度  
   - JPG：quality 会按强度进一步下调，输出 progressive + optimize  
   - PNG：最大化 zlib/滤波组合（按强度选择滤波策略与压缩级别），结合哈夫曼表优化  
   - PNG：quality 影响质量区间，区间与 speed 联动（压缩率与速度平衡）  
   - GIF：轻度抖动与色彩收敛控制，减少色带与块状噪点  
   - 调色与色板：以可见色为基准进行颜色聚类与量化，兼顾体积与视觉一致性  
   - GIF：lossy 值与 colors 上限联动（清晰度与体积权衡）  
   - GIF：有损输出未减小体积时，会自动提高 lossy/降低 colors 再尝试一次  
   - PNG：pngquant 在体积无收益时会跳过输出  
5. 调参维度（无损/优化场景）  
   - JPG：jpegtran 优化元数据与扫描  
   - PNG：oxipng/optipng 按强度选择压缩级别  
   - WebP：cwebp lossless 模式并禁用元数据  
   - PNG：pngquant 输出会剥离元数据  
6. 临时输出与再压缩  
   - 需要改格式或尺寸时，会先临时导出，再交给对应引擎二次压缩  
   - 临时文件在输出目录生成，压缩完成后自动清理  
7. 结果守护  
   - 若压缩后体积变大，自动保留原图输出  

## 打包说明（C++/Qt 发行版）
### 依赖与工具
- CMake 3.20+
- Qt 6（含 Widgets）
- macOS 需要 macdeployqt，Windows 需要 windeployqt

### vendor 工具随包发布
为保证一致的压缩效果，建议将二进制工具放入项目根目录 vendor/ 并随包发布：
- pngquant（PNG 有损）
- oxipng 或 optipng（PNG 无损优化）
- cjpeg 或 mozjpeg（JPG 有损）
- jpegtran（JPG 无损优化）
- gifsicle（GIF 压缩）
- cwebp（WebP 编码）
- dwebp（WebP 解码）

vendor 目录结构：
- vendor/<platform>/<arch>/<tool>
- platform：windows | macos | linux
- arch：x64 | arm64

### vendor 获取
已提供自动拉取脚本（本地执行一次即可，打包时直接复用 vendor）：
- 一键拉取 Windows + macOS（x64/arm64）：python fetch_vendor_all.py
- 多平台预拉取：python fetch_vendor.py --all --platforms=windows,macos --archs=x64,arm64
脚本默认使用国内镜像源下载 npm 包并解压 vendor 二进制，包内缺失会尝试镜像补齐。可通过 NPM_REGISTRY 与 BINARY_MIRROR 覆盖镜像源。

### macOS 打包
- 执行：python native/build_mac.py
- 产物：native/dist/ImgcompressNative.app 与 native/dist/ImgcompressNative.dmg
- vendor 会被复制到 app/Contents/Resources/vendor

### Windows 打包
- 执行：python native/build_windows.py
- 产物：native/dist/ImgcompressNative.exe 与 native/dist/vendor/
- windeployqt 会自动部署 Qt 运行库

## Python 版本（学习用）
Python 目录仅用于学习与对比实现，不作为发行版。发行与交付以 C++/Qt 原生版为准。
