# PhotoScan 1.4.5 自动化拼图脚本

基于 Agisoft PhotoScan 1.4.5 的自动化航拍影像处理脚本，可批量处理照片并生成高质量的正射影像（Orthomosaic）。

## 项目简介

本项目提供了一套完整的 PhotoScan 自动化工作流脚本，能够自动执行从照片导入到正射影像导出的全部流程，大幅提高摄影测量工作效率。

## 功能特点

- **全自动处理流程**：从照片对齐到正射影像导出一键完成
- **高质量输出**：支持高精度对齐（High Accuracy）和高质量点云生成
- **多格式支持**：支持 JPG/JPEG、TIF/TIFF、PNG 等常见影像格式
- **双版本脚本**：提供 JPEG 和 TIFF 两种输出格式的脚本版本
- **异常处理**：自动处理常见错误（如 Empty frame path）并重试
- **中文支持**：完善的中文编码处理，避免控制台乱码
- **批处理集成**：提供 Windows 批处理文件，方便快速启动

## 项目结构

```
.
├── README.md                           # 项目说明文档
├── 白老师自动化拼图工作流.txt            # 手动操作工作流参考
├── 自动化拼图脚本/
│   ├── PhotoScan1.4.5 - jpg.py        # JPEG 输出版本脚本
│   ├── PhotoScan1.4.5 - tiff.py       # TIFF 输出版本脚本
│   ├── Auto_run_photoscan.bat         # 自动运行批处理文件
│   ├── 乱码解决.bat                    # 控制台乱码解决方案
│   └── PhotoScan 1.4.5 自动化.txt      # 脚本使用说明
```

## 环境要求

- **操作系统**：Windows 7/10/11
- **软件依赖**：Agisoft PhotoScan Professional 1.4.5
- **Python**：PhotoScan 内置 Python 环境
- **影像要求**：
  - 格式：JPG、JPEG、TIF、TIFF、PNG
  - 建议具有 GPS/EXIF 信息以提高对齐精度

## 使用方法

### 方法一：命令行直接运行

```batch
"C:\Program Files\Agisoft\PhotoScan Pro\photoscan.exe" -r "PhotoScan1.4.5 - jpg.py" "G:\影像文件夹路径"
```

### 方法二：指定项目文件和输出目录

```batch
"C:\Program Files\Agisoft\PhotoScan Pro\photoscan.exe" -r "PhotoScan1.4.5 - jpg.py" "G:\影像文件夹" "G:\项目文件.psx" "G:\输出目录"
```

### 方法三：使用批处理文件

1. 编辑 `Auto_run_photoscan.bat` 文件
2. 修改以下参数：
   - PhotoScan 安装路径
   - Python 脚本路径
   - 影像文件夹路径
3. 双击运行批处理文件

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `images_dir` | 是 | 影像文件夹路径 |
| `project.psx` | 否 | PhotoScan 项目文件路径（默认：影像文件夹下生成） |
| `export_dir` | 否 | 输出目录（默认：影像文件夹/outputs） |

## 处理流程

脚本自动执行以下步骤：

1. **添加照片**：扫描并导入影像文件夹中的所有照片
2. **照片对齐**：使用高精度（High Accuracy）进行特征匹配和相机对齐
3. **生成稠密点云**：构建高质量深度图和稠密点云（High Quality, Mild Filtering）
4. **生成网格**：基于稠密点云数据构建三角网格模型
5. **保存项目**：将工程保存为 .psx 文件
6. **重新打开项目**：解决 "Empty frame path" 问题
7. **构建 DEM**：生成数字高程模型（Digital Elevation Model）
8. **构建正射影像**：生成正射影像（Orthomosaic）
9. **导出结果**：导出为 JPEG 或 TIFF 格式

## 脚本版本对比

| 脚本版本 | 输出格式 | 文件大小 | 质量 | 适用场景 |
|---------|---------|---------|------|---------|
| `PhotoScan1.4.5 - jpg.py` | JPEG | 小 | 有损压缩 | 快速预览、网页展示 |
| `PhotoScan1.4.5 - tiff.py` | TIFF | 大 | 无损压缩 | 专业测量、后续处理 |

## 常见问题

### 1. 控制台中文乱码

运行 `乱码解决.bat` 或在脚本中已包含 UTF-8 编码处理：

```python
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
```

### 2. Empty frame path 错误

脚本已自动处理此错误：
- 保存项目后重新打开
- 重新初始化 frame path
- 如仍失败会自动重试一次

### 3. API 兼容性问题

脚本兼容多种 PhotoScan API 版本：
- 优先尝试 `exportOrthomosaic()`
- 备选 `exportOrthophoto()`
- 最后尝试 `orthomosaic.export()`

### 4. 内存不足

建议设置：
- 增加 PhotoScan 内存限制
- 降低质量参数（High → Medium）
- 分批处理大量照片

## 输出文件

处理完成后会在输出目录生成以下文件：

```
输出目录/
├── <影像文件夹名>.psx              # PhotoScan 项目文件
├── <影像文件夹名>_orth.jpg/tiff   # 正射影像（根据脚本版本）
└── outputs/                        # 默认输出目录（可自定义）
```

## 技术参数

### 对齐参数
- 精度：High Accuracy
- 关键点限制：40,000
- 连接点限制：10,000
- 通用预选：启用
- 参考预选：禁用

### 点云参数
- 质量：High Quality
- 深度滤波：Mild Filtering
- 数据源：Dense Cloud Data

### 网格参数
- 表面类型：Arbitrary
- 插值：Enabled

## 注意事项

1. **照片质量**：确保照片清晰、重叠率足够（建议 60-80%）
2. **文件路径**：避免使用包含特殊字符的路径
3. **磁盘空间**：预留足够空间（处理过程中会生成大量临时文件）
4. **处理时间**：根据照片数量和电脑配置，处理时间从数小时到数天不等
5. **授权许可**：需要 PhotoScan Professional 版本授权

## 手动操作流程参考

如需手动操作，请参考 `白老师自动化拼图工作流.txt`：

1. 工作流程 → 添加图片 → 添加照片 → 打开
2. 工作流程 → 对齐图片 → 精度：高 → 确定并等待
3. 工作流程 → 建立密集点云 → 质量：高 → 确定并等待
4. 工作流程 → 生成网格 → 确定
5. 点击保存 → 保存到源文件
6. 工作流程 → Build DEM → 确定
7. 工作流程 → Build Orthomosaic → 确定
8. 展开工作区 → 右击正射影像 → 导出 → 选择格式并命名

## 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 许可证

本项目仅供学习和研究使用。请确保您拥有 Agisoft PhotoScan 的合法授权。

## 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

**最后更新**：2025-11-12
