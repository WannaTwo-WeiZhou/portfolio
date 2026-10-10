# 个人作品集 · Personal Portfolio

GitHub Pages 站点：[https://wannatwo-weizhou.github.io/portfolio/](https://wannatwo-weizhou.github.io/portfolio/)

把「可在线试玩的 Demo」和历年项目的「试玩录像」集中到一个页面上，用于对外展示（求职 / 合作 / 存档）。

## 页面结构

- **在线试玩** — 目前 1 项：`ShieldCore` 主分支 demo（`gh-pages` 部署的 WebGL 构建），浏览器直接运行。
- **试玩视频** — 卡片墙 + 标签筛选，点击卡片在弹出的播放器里播放；每张卡片带年份、项目归属、标签与说明。

## 目录

```
index.html            单页站点（无外部依赖、无 CDN）
manifest.json         数据源：每条视频的标题/年份/标签/说明 + Slack 文件 ID + 源文件名
build.py              读取 _src/ 里的源视频 → 转码 + 抽封面 + 生成 data/projects.json
data/projects.json    构建产物，页面运行时 fetch 读取
assets/videos/*.mp4   发布用的转码后视频
assets/posters/*.jpg  视频封面
_src/<slack-file-id>  源视频（.gitignore 忽略，不入库；键为 manifest 里的 id）
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

1. 把源视频放到 `_src/<manifest 里的 id>`（或在 Slack 里把文件发到 Hermes DM —— gateway 会把附件缓存到
   `~/.hermes/profiles/prod/cache/videos/`，按 `files.list` 拿到的真实文件名与大小把它对应回文件 ID 即可）。
   仅存在于本地的文件（从未发过 Slack）没有 file ID，用 `local-<名称>` 当 id（例：`local-1214`）。
2. 在 `manifest.json` 的 `videos` 里加一条：`id`、`slug`（输出文件名）、`title`、`year`、`tags`、`desc`。
3. 跑 `python3 build.py` —— 有源文件的条目会变成 `ready` 并生成封面；没有源文件的保持 `pending`，页面显示「视频待补充」。
4. 提交 `manifest.json` + `data/projects.json` + `assets/`。

## 转码参数

`libx264 -crf 27 -preset medium -pix_fmt yuv420p -movflags +faststart`，长边超过 1280 才缩放（竖屏同样按长边裁）；
有声则 `aac 96k`。原始录音多为 600–1560 宽的录屏，转码后约为原体积的 15–35%。

## 待办

- 源视频已齐：16 条条目全部有 `_src/` 源文件；本地汇总目录为 `~/Documents/Pictures/作品`。
- 全部条目的标题与说明已于 2026-10-10 按项目事实校对：原 8 条占位的「试玩录像 <编号>」已改写，
  `clip-*` 占位 slug 也一并改成语义化 slug（`merge-ugc-2026` / `tiaohe-2019` / `eye-tracking-2016` …）。
- 已删除 6 段重复录屏（2019-01 的 `ScreenRecording_*`）：三段分别与 Theater / AvocadoReborn /
  TungstenAvocado 重复；另三段为 Doodle 联机对战、Boxygeon 联机菜单与对战、网格滚球物理解谜原型，
  与已有卡片重复。源文件仍留在 `_src/`，需要时可重新收录。
- Slack 只能读到「出现在 Hermes 所在会话里的文件」：只贴 permalink 而文件本身在别处时，`files.info` 返回
  `file_not_found`。缺件时请把文件重新发到 DM（见 `hermes-slack-gateway` 技能的 `fetch-slack-file.py`）。
