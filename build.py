#!/usr/bin/env python3
"""Build the portfolio site assets from manifest.json + downloaded source videos.

Usage:
    python3 build.py            # transcode missing/outdated videos + posters, write data/projects.json
    python3 build.py --force    # re-transcode everything
    python3 build.py --only SLUG

Source videos live in _src/<slack-file-id> (downloaded from Slack). Output goes to
assets/videos/<slug>.mp4 and assets/posters/<slug>.jpg. Nothing is deleted.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "_src")
VOUT = os.path.join(ROOT, "assets", "videos")
POUT = os.path.join(ROOT, "assets", "posters")
DATA = os.path.join(ROOT, "data", "projects.json")

MAX_W = 1280          # downscale only if wider
CRF = 27
PRESET = "medium"
AUDIO_KBPS = 96


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])}... failed:\n{p.stderr[-800:]}")
    return p.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", path])
    j = json.loads(out)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    info = {
        "duration": float(j["format"].get("duration") or 0),
        "size": int(j["format"].get("size") or 0),
        "has_audio": a is not None,
    }
    if v:
        info.update(width=int(v.get("width") or 0), height=int(v.get("height") or 0),
                    codec=v.get("codec_name"))
        # honour rotation metadata (portrait screen recordings)
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd and abs(float(sd["rotation"])) in (90.0, 270.0):
                info["width"], info["height"] = info["height"], info["width"]
    return info


def newer(a, b):
    return os.path.exists(a) and os.path.exists(b) and os.path.getmtime(b) >= os.path.getmtime(a)


def transcode(src, dst, has_audio, force):
    if not force and newer(dst, src):
        return False
    vf = f"scale='min({MAX_W},iw)':-2"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src,
           "-vf", vf, "-c:v", "libx264", "-crf", str(CRF), "-preset", PRESET,
           "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    cmd += (["-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ac", "2"] if has_audio else ["-an"])
    cmd.append(dst)
    run(cmd)
    return True


def poster(src, dst, duration, force):
    if not force and newer(dst, src):
        return False
    ts = max(0.5, duration * 0.15)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{ts:.2f}",
         "-i", src, "-frames:v", "1", "-vf", "scale='min(760,iw)':-2",
         "-q:v", "4", dst])
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", action="append", default=[])
    args = ap.parse_args()

    os.makedirs(VOUT, exist_ok=True)
    os.makedirs(POUT, exist_ok=True)
    os.makedirs(os.path.dirname(DATA), exist_ok=True)

    man = json.load(open(os.path.join(ROOT, "manifest.json"), encoding="utf8"))
    bilibili = {
        "starling-2019": "https://www.bilibili.com/video/BV11R4y1T7Kr/",
        "defects-2020": "https://www.bilibili.com/video/BV1yi4y1g7vw/",
        "xiaochenai-2021": "https://www.bilibili.com/video/BV1Zh411h79w/",
    }

    ready = pending = 0
    for v in man["videos"]:
        if args.only and v["slug"] not in args.only:
            pass
        src = os.path.join(SRC, v["id"])
        slug = v["slug"]
        if not os.path.exists(src) or os.path.getsize(src) < 1024:
            v["status"] = "pending"
            v.pop("file", None)
            v.pop("poster", None)
            v.pop("duration", None)
            pending += 1
            print(f"PENDING  {slug:<28} ({v['id']} not downloaded)")
            continue
        try:
            info = probe(src)
        except Exception as e:
            v["status"] = "pending"
            v.pop("file", None)
            pending += 1
            print(f"PENDING  {slug:<28} probe failed: {e}")
            continue

        out_mp4 = os.path.join(VOUT, slug + ".mp4")
        out_jpg = os.path.join(POUT, slug + ".jpg")
        try:
            enc = transcode(src, out_mp4, info["has_audio"], args.force)
            poster(src, out_jpg, info["duration"], args.force)
        except Exception as e:
            v["status"] = "pending"
            v.pop("file", None)
            pending += 1
            print(f"PENDING  {slug:<28} transcode failed: {e}")
            continue

        v["status"] = "ready"
        v["file"] = slug + ".mp4"
        v["poster"] = "assets/posters/" + slug + ".jpg"
        v["duration"] = round(info["duration"], 2)
        v["width"], v["height"] = info["width"], info["height"]
        v["src_bytes"] = info["size"]
        v["out_bytes"] = os.path.getsize(out_mp4)
        if slug in bilibili:
            v["bilibili"] = bilibili[slug]
        ready += 1
        ratio = v["out_bytes"] / max(1, info["size"])
        print(f"READY    {slug:<28} {info['width']}x{info['height']} {info['duration']:6.1f}s  "
              f"{info['size']/1e6:6.1f}MB -> {v['out_bytes']/1e6:5.1f}MB ({ratio*100:.0f}%)"
              + ("  [transcoded]" if enc else "  [cached]"))

    man["meta"]["counts"] = {"ready": ready, "pending": pending, "total": len(man["videos"])}
    with open(DATA, "w", encoding="utf8") as f:
        json.dump(man, f, ensure_ascii=False, indent=1)
    total = sum(v.get("out_bytes", 0) for v in man["videos"])
    print(f"\nready={ready} pending={pending} published video bytes={total/1e6:.1f} MB")
    print("wrote", DATA)


if __name__ == "__main__":
    sys.exit(main())
