# -*- coding: utf-8 -*-
import os, sys, glob, traceback, io

# 控制台中文 UTF-8 输出
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import PhotoScan

def log(s):
    print(s, flush=True)

def ensure_dir(p):
    if not os.path.isdir(p):
        os.makedirs(p, exist_ok=True)
    return p

def collect_images(images_dir):
    exts = (".jpg", ".jpeg", ".tif", ".tiff", ".png")
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

    log("[STEP] 对齐（HighAccuracy）...")
    chunk.matchPhotos(
        accuracy=PhotoScan.HighAccuracy,
        generic_preselection=True,
        reference_preselection=False,
        keypoint_limit=40000,
        tiepoint_limit=10000
    )
    chunk.alignCameras()
    try:
        chunk.optimizeCameras()
    except Exception as e:
        log("[WARN] optimizeCameras 跳过：{}".format(e))
    log("[OK] 对齐完成")

    log("[STEP] 深度图 + 稠密点云（High, Mild）...")
    chunk.buildDepthMaps(quality=PhotoScan.HighQuality, filter=PhotoScan.MildFiltering)
    chunk.buildDenseCloud()
    log("[OK] 稠密点云完成")

    log("[STEP] 网格（Arbitrary / DenseCloudData）...")
    chunk.buildModel(
        surface=PhotoScan.Arbitrary,
        source=PhotoScan.DataSource.DenseCloudData,
        interpolation=PhotoScan.EnabledInterpolation
    )
    log("[OK] 网格完成")

    log("[STEP] 保存工程（.psx）：{}".format(project_path))
    doc.save(project_path)
    PhotoScan.app.update()
    log("[OK] 工程已保存")

def export_orthotif_from_chunk(chunk, out_path):
    exported = False

    # 1) chunk.exportOrthomosaic(...)
    if hasattr(chunk, "exportOrthomosaic"):
        try:
            if hasattr(PhotoScan, "ImageFormatTIFF"):
                chunk.exportOrthomosaic(out_path, image_format=PhotoScan.ImageFormatTIFF)
            else:
                chunk.exportOrthomosaic(out_path)  # 依扩展名判断
            exported = True
        except Exception as e:
            log("[INFO] exportOrthomosaic 失败：{}".format(e))

    # 2) chunk.exportOrthophoto(...)
    if (not exported) and hasattr(chunk, "exportOrthophoto"):
        try:
            if hasattr(PhotoScan, "ImageFormatTIFF"):
                chunk.exportOrthophoto(out_path, image_format=PhotoScan.ImageFormatTIFF)
            else:
                try:
                    chunk.exportOrthophoto(out_path, format=PhotoScan.ImageFormatTIFF)
                except TypeError:
                    chunk.exportOrthophoto(out_path)
            exported = True
        except Exception as e:
            log("[INFO] exportOrthophoto 失败：{}".format(e))

    # 3) 正射对象导出：chunk.orthomosaic.export(...)
    if (not exported) and hasattr(chunk, "orthomosaic") and chunk.orthomosaic:
        try:
            if hasattr(chunk.orthomosaic, "export"):
                if hasattr(PhotoScan, "ImageFormatTIFF"):
                    chunk.orthomosaic.export(out_path, image_format=PhotoScan.ImageFormatTIFF)
                else:
                    chunk.orthomosaic.export(out_path)
                exported = True
        except Exception as e:
            log("[INFO] orthomosaic.export 失败：{}".format(e))

    if not exported:
        raise RuntimeError("未找到可用的正射导出 API（TIFF）。")

def reopen_and_build_products(project_path, export_dir, images_dir):
    app = PhotoScan.app
    app.document.clear(); app.update()
    app.document.open(project_path)
    doc = app.document
    chunk = doc.chunk
    log("[OK] 已重新打开：{}".format(project_path))

    # 确保区域有效
    try:
        chunk.resetRegion()
    except Exception:
        pass

    # DEM
    log("[STEP] 构建 DEM …")
    chunk.buildDem(source=PhotoScan.DataSource.DenseCloudData)
    log("[OK] DEM 完成")

    # 正射：优先 DEM，失败则改 Mesh
    log("[STEP] 构建正射（优先 DEM）…")
    try:
        chunk.buildOrthomosaic(surface=PhotoScan.DataSource.ElevationData)
        log("[OK] 正射完成（DEM）")
    except RuntimeError as e:
        if "Empty extent" in str(e):
            log("[WARN] 正射报 Empty extent，改用网格表面重试 …")
            try:
                try: chunk.resetRegion()
                except Exception: pass
                chunk.buildOrthomosaic(surface=PhotoScan.DataSource.ModelData)
                log("[OK] 正射完成（Mesh）")
            except Exception as e2:
                raise
        else:
            raise

    base = os.path.basename(os.path.normpath(images_dir))
    orth_tif = os.path.join(export_dir, base + "_orth.tif")
    log("[STEP] 导出正射 TIFF：{}".format(orth_tif))
    export_orthotif_from_chunk(chunk, orth_tif)
    log("[OK] 导出完成 -> {}".format(orth_tif))

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
