#!/usr/bin/env python3
"""Small, agent-friendly local Android test runner. Python standard library only."""
import argparse, json, os, pathlib, subprocess, sys

def run(cmd, timeout=60, check=True):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(map(str, cmd))}\n{p.stderr.strip()}")
    return p.stdout.strip()

def adb(serial, *args, timeout=60, check=True):
    return run([os.getenv("ANDROID_ADB", "adb"), "-s", serial, *args], timeout, check)

def devices(_):
    print(run([os.getenv("ANDROID_ADB", "adb"), "devices", "-l"], check=False))

def verify(args):
    packages = adb(args.serial, "shell", "pm", "list", "packages")
    props = {
        "serial": args.serial,
        "android_release": adb(args.serial, "shell", "getprop", "ro.build.version.release"),
        "api_level": adb(args.serial, "shell", "getprop", "ro.build.version.sdk"),
        "play_store": "com.android.vending" in packages,
        "google_play_services": "com.google.android.gms" in packages,
        "boot_completed": adb(args.serial, "shell", "getprop", "sys.boot_completed"),
    }
    print(json.dumps(props, indent=2))
    if not (props["play_store"] and props["google_play_services"]):
        sys.exit(2)

def install(args):
    print(adb(args.serial, "install", "-r", str(pathlib.Path(args.apk).resolve()), timeout=180))

def launch(args):
    print(adb(args.serial, "shell", "monkey", "-p", args.package, "1"))

def capture(args):
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = "/sdcard/android-lab-capture.png"
    adb(args.serial, "shell", "screencap", "-p", tmp)
    run([os.getenv("ANDROID_ADB", "adb"), "-s", args.serial, "pull", tmp, str(out.resolve())])
    print(str(out.resolve()))

def dump_ui(args):
    adb(args.serial, "shell", "uiautomator", "dump", "/sdcard/window.xml")
    print(adb(args.serial, "shell", "cat", "/sdcard/window.xml"))

def logs(args):
    raw = adb(args.serial, "logcat", "-d", "-t", str(args.lines), timeout=60)
    if args.filter:
        raw = "\n".join(x for x in raw.splitlines() if args.filter.lower() in x.lower())
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(raw, encoding="utf-8")
    print(f"Wrote {len(raw.splitlines())} lines to {out}")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(required=True)
    d = sub.add_parser("devices"); d.set_defaults(fn=devices)
    for name, fn in (("verify", verify), ("install", install), ("launch", launch),
                     ("screenshot", capture), ("ui-dump", dump_ui), ("logcat", logs)):
        q = sub.add_parser(name); q.add_argument("--serial", required=True); q.set_defaults(fn=fn)
        if name == "install": q.add_argument("--apk", required=True)
        if name == "launch": q.add_argument("--package", required=True)
        if name == "screenshot": q.add_argument("--output", default="artifacts/screenshot.png")
        if name == "logcat":
            q.add_argument("--lines", type=int, default=3000)
            q.add_argument("--filter", default="")
            q.add_argument("--output", default="artifacts/logcat.txt")
    args = p.parse_args()
    try: args.fn(args)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__": main()
