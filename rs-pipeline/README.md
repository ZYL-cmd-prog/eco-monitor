# 遥感数据管线（Windows / conda）

从 Microsoft Planetary Computer 在线读取宜宾区域的 Sentinel-2 L2A，计算 NDVI / NDWI，
并导出到前端 `eco-monitor/public/data/`。

## 目录结构

```
rs-pipeline/
├── download.py          # 选景 + 只切宜宾 bbox 读波段
├── ndvi.py              # 计算 NDVI
├── ndwi.py              # 计算 NDWI
├── export_frontend.py   # 汇总统计，导出 ndvi.json + PNG 到前端
├── make_demo.py         # 生成合成演示图（仅供预览）
├── data/                # 下载的波段（red/green/nir/swir.tif）
└── result/              # NDVI.tif / NDWI.tif / NDVI.png / NDWI.png
```

## 第一步：装依赖

```bash
conda activate remote
conda install -c conda-forge rasterio
pip install pystac-client planetary-computer matplotlib numpy
```

## 第二步：依次运行

```bash
python download.py          # 1. 选景 + 下载宜宾波段
python ndvi.py              # 2. 计算 NDVI
python ndwi.py              # 3. 计算 NDWI
python export_frontend.py   # 4. 导出到前端 public/data/
```

跑完后，前端 `eco-monitor/public/data/` 里会出现：
- `ndvi.json`（NDVI/NDWI 统计值，前端 fetch 的就是它）
- `NDVI.png`、`NDWI.png`（结果图）

然后回到前端目录 `npm run build`，把 `dist/` 重新拖到 Netlify 即可。

## 注意

- **反射率缩放**：Sentinel-2 L2A 的反射率是 ×10000 存储的，算指数前必须 `/10000`（脚本里已处理）。
- **只读 bbox**：`download.py` 用 `rasterio.windows.from_bounds` 只读宜宾范围，不会下载几十 GB。
- **时间范围**：`download.py` 里 `datetime` 可改；`timeseries`（NDVI/NDWI 季节变化）需要下载多期影像后，在
  `export_frontend.py` 里按月统计填充。
- **首次预览**：还没跑真实数据前，可先 `python make_demo.py` 生成两张合成图，让前端先有东西可看。
