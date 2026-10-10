# 个人作品集 · Personal Portfolio

GitHub Pages 站点：[https://wannatwo-weizhou.github.io/portfolio/](https://wannatwo-weizhou.github.io/portfolio/)

把「可在线试玩的 Demo」和历年项目的「试玩录像」集中到一个页面上，用于对外展示（求职 / 合作 / 存档）。

## 页面结构

- **在线试玩** — 目前 1 项：`ShieldCore` 主分支 demo（`gh-pages` 部署的 WebGL 构建），浏览器直接运行。
- **试玩视频** — 卡片墙 + 标签筛选，点击卡片在弹出的播放器里播放；每张卡片带年份、项目归属、标签与说明。

## 目录

```
index.html            单页站点（无外部依赖、无 CDN）
manifest.json         数据源：每条视频的标题/年份/标签/说明 + Slack 文件 ID
build.py              读取 _src/ 里的源视频 → 转码 + 抽封面 + 生成 data/projects.json
data/projects.json    构建产物，页面运行时 fetch 读取
assets/videos/*.mp4   发布用的转码后视频
assets/posters/*.jpg  视频封面
_src/<slack-file-id>  源视频（.gitignore 忽略，不入库）
```

## 本地构建

```bash
python3 build.py            # 增量：只处理缺失/更新的视频
python3 build.py --force    # 全量重转
python3 build.py --only starling-2019
```

预览（`index.html` 用 `fetch` 读 JSON，需要 http 而非 file://）：

```bash
python3 -m http.server 8080   # 然后打开 http://localhost:8080/
```

## 新增一段试玩视频

1. 把源视频放到 `_src/<slack-file-id>`（或改 `manifest.json` 里的 `id` 与 `_src` 文件名对应）。
2. 在 `manifest.json` 的 `videos` 里加一条：`slug`（输出文件名）、`title`、`year`、`tags`、`desc`。
3. 跑 `python3 build.py` —— 有源文件的条目会变成 `ready` 并生成封面；没有源文件的保持 `pending`，页面显示「视频待补充」。
4. 提交 `manifest.json` + `data/projects.json` + `assets/`。

## 转码参数

`libx264 -crf 27 -preset medium -pix_fmt yuv420p -movflags +faststart`，宽度超过 1280 才缩放；有声则 `aac 96k`。
原始录音多为 640–960 宽的录屏，转码后约为原体积的 15–35%。

## 待办

- `manifest.json` 中标记 `"inferred": true` 的条目是**按录制时间与项目周期推断**的归属，需要人工确认。
- `tags` 里含「待补充」的条目（`IMG_0816` / `5128` / `IMG_1518` / `3198` / `2025-01-26`）需要补标题与说明。
- 若源视频文件缺失（Slack 里读不到），条目会停在 `pending`。
