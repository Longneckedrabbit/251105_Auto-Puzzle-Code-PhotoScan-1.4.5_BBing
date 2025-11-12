# -*- coding: utf-8 -*-
import os, sys, glob, traceback, io

# 控制台中文 UTF-8 输出
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import PhotoScan

def log(s): print(s, flush=True)

def ensure_dir(p):
    if not os.path.isdir(p):
        os.makedirs(p, exist_ok=True)
    return p

def collect_images(images_dir):
    exts = (".jpg",".jpeg",".tif",".tiff",".png")
    files = [p for p in sorted(glob.glob(os.path.join(images_dir, "*")))
             if os.path.splitext(p)[1].lower() in exts]
    if not files:
        raise RuntimeError("未在目录中找到影像文件: " + images_dir)
    return files

def to_psx_path(project_path, images_dir):
    if not project_path:
        base = os.path.basename(os.path.normpath(images_dir))
        project_path = os.path.join(images_dir, base + ".psx")
    root, ext = os.path.splitext(project_path)
    if ext.lower() != ".psx":
        project_path = root + ".psx"
    return os.path.abspath(project_path)

def build_pipeline(images_dir, project_path):
    app = PhotoScan.app
    doc = app.document

    photos = collect_images(images_dir)
    log("[STEP] 添加照片：{} 张".format(len(photos)))
    chunk = doc.addChunk() if not doc.chunks else doc.chunk
    chunk.addPhotos(photos)

    # 对齐（High）
    log("[STEP] 对齐（HighAccuracy）...")
    chunk.matchPhotos(
        accuracy=PhotoScan.HighAccuracy,
        generic_preselection=True,
        reference_preselection=False,
        keypoint_limit=40000, tiepoint_limit=10000
    )
    chunk.alignCameras()
    try:
        chunk.optimizeCameras()
    except Exception as e:
        log("[WARN] optimizeCameras 跳过：{}".format(e))
    log("[OK] 对齐完成")

    # 深度图/稠密点云（High, Mild）
    log("[STEP] 深度图 + 稠密点云（High, Mild）...")
    chunk.buildDepthMaps(quality=PhotoScan.HighQuality, filter=PhotoScan.MildFiltering)
    chunk.buildDenseCloud()
    log("[OK] 稠密点云完成")

    # 网格
    log("[STEP] 网格（Arbitrary / DenseCloudData）...")
    chunk.buildModel(surface=PhotoScan.Arbitrary,
                     source=PhotoScan.DataSource.DenseCloudData,
                     interpolation=PhotoScan.EnabledInterpolation)
    log("[OK] 网格完成")

    # 保存为 .psx（为后续 DEM/Orth 准备 frame 路径）
    log("[STEP] 保存工程（.psx）：{}".format(project_path))
    doc.save(project_path)
    PhotoScan.app.update()
    log("[OK] 工程已保存")

def reopen_and_build_products(project_path, export_dir, images_dir):
    # 关闭并重新打开 .psx，规避 Empty frame path
    log("[STEP] 重新打开 .psx 以初始化 frame path …")
    app = PhotoScan.app
    app.document.clear(); app.update()
    app.document.open(project_path)
    doc = app.document
    chunk = doc.chunk
    log("[OK] 已重新打开：{}".format(project_path))

    # DEM
    log("[STEP] 构建 DEM …")
    chunk.buildDem(source=PhotoScan.DataSource.DenseCloudData)
    log("[OK] DEM 完成")

    # 正射
    log("[STEP] 构建正射 …")
    chunk.buildOrthomosaic(surface=PhotoScan.DataSource.ElevationData)
    log("[OK] 正射完成")

    # 导出 JPEG（多种 API 名称的兼容处理）
    base = os.path.basename(os.path.normpath(images_dir))
    orth_jpg = os.path.join(export_dir, base + "_orth.jpg")
    log("[STEP] 导出正射 JPEG：{}".format(orth_jpg))

    exported = False
    # 1) 尝试 chunk.exportOrthomosaic（部分 1.4.x/1.5 具备）
    if hasattr(chunk, "exportOrthomosaic"):
        try:
            if hasattr(PhotoScan, "ImageFormatJPEG"):
                chunk.exportOrthomosaic(orth_jpg, image_format=PhotoScan.ImageFormatJPEG)
            else:
                chunk.exportOrthomosaic(orth_jpg)  # 让它按扩展名判断
            exported = True
        except Exception as e:
            log("[INFO] exportOrthomosaic 不可用/失败：{}".format(e))

    # 2) 尝试 chunk.exportOrthophoto（另一些 1.4.x 具备）
    if (not exported) and hasattr(chunk, "exportOrthophoto"):
        try:
            if hasattr(PhotoScan, "ImageFormatJPEG"):
                chunk.exportOrthophoto(orth_jpg, image_format=PhotoScan.ImageFormatJPEG)
            else:
                # 有时参数名叫 format=
                try:
                    chunk.exportOrthophoto(orth_jpg, format=PhotoScan.ImageFormatJPEG)
                except TypeError:
                    chunk.exportOrthophoto(orth_jpg)
            exported = True
        except Exception as e:
            log("[INFO] exportOrthophoto 不可用/失败：{}".format(e))

    # 3) 尝试在正射对象上导出（老接口常见）
    if (not exported) and hasattr(chunk, "orthomosaic") and chunk.orthomosaic:
        try:
            # 大多数 1.4.x：Raster/Orthomosaic 对象自带 export()
            if hasattr(chunk.orthomosaic, "export"):
                if hasattr(PhotoScan, "ImageFormatJPEG"):
                    chunk.orthomosaic.export(orth_jpg, image_format=PhotoScan.ImageFormatJPEG)
                else:
                    chunk.orthomosaic.export(orth_jpg)
                exported = True
        except Exception as e:
            log("[INFO] orthomosaic.export 不可用/失败：{}".format(e))

    if not exported:
        raise RuntimeError("未找到可用的正射导出 API（已尝试 exportOrthomosaic / exportOrthophoto / orthomosaic.export）。")

    log("[OK] 导出完成 -> {}".format(orth_jpg))

def main(images_dir, project_path=None, export_dir=None):
    images_dir = os.path.abspath(images_dir)
    project_path = to_psx_path(project_path, images_dir)
    export_dir = ensure_dir(export_dir or os.path.join(images_dir, "outputs"))

    log("[INFO] Images dir : {}".format(images_dir))
    log("[INFO] Project psx: {}".format(project_path))
    log("[INFO] Export dir : {}".format(export_dir))

    build_pipeline(images_dir, project_path)
    try:
        reopen_and_build_products(project_path, export_dir, images_dir)
    except RuntimeError as e:
        if "Empty frame path" in str(e):
            log("[RETRY] 捕获 Empty frame path：重存 & 重开一次 …")
            PhotoScan.app.document.save(project_path)
            PhotoScan.app.document.clear(); PhotoScan.app.update()
            PhotoScan.app.document.open(project_path)
            reopen_and_build_products(project_path, export_dir, images_dir)
        else:
            raise

    log("[DONE] 全流程完成。")

if __name__ == "__main__":
    try:
        images_dir = sys.argv[1]
        project_path = sys.argv[2] if len(sys.argv) > 2 else None
        export_dir   = sys.argv[3] if len(sys.argv) > 3 else None
    except Exception:
        print("用法：photoscan.exe -r PhotoScan1.4.5.py <images_dir> [project.psx] [export_dir]")
        sys.exit(1)

    try:
        main(images_dir, project_path, export_dir)
    except Exception as e:
        print("[ERROR]", e)
        traceback.print_exc()
        sys.exit(2)
