#!/usr/bin/env python3
"""Explicit-target Android test runner; Python standard library only."""
import argparse, json, os, pathlib, re, subprocess, sys, time

ADB = os.getenv("ANDROID_ADB", "adb")
KEYS = {"BACK":"4","HOME":"3","ENTER":"66","TAB":"61","DPAD_UP":"19","DPAD_DOWN":"20","DPAD_LEFT":"21","DPAD_RIGHT":"22"}
PACKAGE_RE = re.compile(r"^[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+$")

def run(cmd, timeout=60, check=True):
    try: p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e: raise RuntimeError(f"Command timed out after {timeout}s: {' '.join(map(str,,cmd))}") from e
    if check and p.returncode: raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(map(str,cmd))}\n{(p.stderr or p.stdout).strip()}")
    return p.stdout.strip()

def adb(serial,*args,timeout=60,check=True):
    if not serial or not serial.strip(): raise ValueError("An explicit device serial is required; run 'devices' first.")
    return run([ADB,"-s",serial.strip(),*map(str,args)],timeout,check)

def package_id(v):
    if not PACKAGE_RE.fullmatch(v): raise ValueError(f"Invalid Android package ID: {v!r}")
    return v

def encode_input_text(v):
    if not v or len(v)>500: raise ValueError("Text must contain 1–500 characters.")
    if not re.fullmatch(r"[A-Za-z0-9 .,_@+:-]+",v): raise ValueError("Text accepts letters, digits, spaces, and . , _ @ + : -. Use Appium for Unicode or other characters.")
    return v.replace(" ","%s")

def devices(_): print(run([ADB,"devices","-l"],check=False))
def verify(a):
    pkgs=adb(a.serial,"shell","pm","list","packages")
    d={"serial":a.serial,"android_release":adb(a.serial,"shell","getprop","ro.build.version.release"),"api_level":adb(a.serial,"shell","getprop","ro.build.version.sdk"),"play_store":"com.android.vending" in pkgs,"google_play_services":"com.google.android.gms" in pkgs,"boot_completed":adb(a.serial,"shell","getprop","sys.boot_completed")}
    print(json.dumps(d,indent=2))
    if not (d["play_store"] and d["google_play_services"]): sys.exit(2)
def wait_boot(a):
    end=time.monotonic()+a.timeout; adb(a.serial,"wait-for-device",timeout=a.timeout)
    while time.monotonic()<end:
        if adb(a.serial,"shell","getprop","sys.boot_completed",timeout=10,check=False)=="1": print(f"{a.serial}: boot completed"); return
        time.sleep(2)
    raise RuntimeError(f"{a.serial}: boot not confirmed within {a.timeout}s")
def install(a):
    f=pathlib.Path(a.apk).expanduser().resolve()
    if not f.is_file() or f.suffix.lower()!=".apk": raise ValueError(f"APK does not exist or is not .apk: {f}")
    print(adb(a.serial,"install","-r",str(f),timeout=180))
def launch(a): print(adb(a.serial,"shell","monkey","-p",package_id(a.package),"1"))
def app_info(a):
    pkg=package_id(a.package); raw=adb(a.serial,"shell","dumpsys","package",pkg,timeout=30,check=False)
    if not raw: raise RuntimeError(f"No package information for {pkg}; is it installed?")
    out={"serial":a.serial,"package":pkg}
    for key,pat in {"version_name":r"versionName=([^\\s]+)","version_code":r"versionCode=(\\d+)","first_install_time":r"firstInstallTime=([^\\n]+)","last_update_time":r"lastUpdateTime=([^\\n]+)"}.items():
        m=re.search(pat,raw)
        if m: out[key]=m.group(1).strip()
    print(json.dumps(out,indent=2))
def force_stop(a): print(adb(a.serial,"shell","am","force-stop",package_id(a.package)) or "Force-stop sent.")
def tap(a):
    if min(a.x,a.y)<0 or max(a.x,a.y)>10000: raise ValueError("Coordinates must be between 0 and 10000.")
    print(adb(a.serial,"shell","input","tap",a.x,a.y) or "Tap sent.")
def swipe(a):
    c=(a.x1,a.y1,a.x2,a.y2)
    if min(c)<0 or max(c)>10000: raise ValueError("Coordinates must be between 0 and 10000.")
    if not 100<=a.duration_ms<=10000: raise ValueError("Duration must be 100–10000 ms.")
    print(adb(a.serial,"shell","input","swipe",*c,a.duration_ms) or "Swipe sent.")
def type_text(a): print(adb(a.serial,"shell","input","text",encode_input_text(a.text)) or "Text input sent.")
def keyevent(a): print(adb(a.serial,"shell","input","keyevent",KEYS[a.key]) or "Key event sent.")
def capture(a):
    out=pathlib.Path(a.output).expanduser(); out.parent.mkdir(parents=True,exist_ok=True); remote="/sdcard/android-lab-capture.png"
    adb(a.serial,"shell","screencap","-p",remote); run([ADB,"-s",a.serial,"pull",remote,str(out.resolve())]); print(out.resolve())
def dump_ui(a):
    adb(a.serial,"shell","uiautomator","dump","/sdcard/window.xml"); print(adb(a.serial,"shell","cat","/sdcard/window.xml"))
def logs(a):
    if not 1<=a.lines<=10000: raise ValueError("--lines must be 1–10000.")
    raw=adb(a.serial,"logcat","-d","-t",a.lines,timeout=60)
    if a.filter: raw="\n".join(x for x in raw.splitlines() if a.filter.lower() in x.lower())
    out=pathlib.Path(a.output).expanduser(); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(raw,encoding="utf-8"); print(f"Wrote {len(raw.splitlines())} lines to {out.resolve()}")

def main():
    p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(required=True)
    q=s.add_parser("devices"); q.set_defaults(fn=devices)
    commands={"verify":verify,"wait-boot":wait_boot,"install":install,"launch":launch,"app-info":app_info,"force-stop":force_stop,"tap":tap,"swipe":swipe,"type":type_text,"keyevent":keyevent,"screenshot":capture,"ui-dump":dump_ui,"logcat":logs}
    for name,fn in commands.items():
        q=s.add_parser(name); q.add_argument("--serial",required=True); q.set_defaults(fn=fn)
        if name=="wait-boot": q.add_argument("--timeout",type=int,default=180)
        if name=="install": q.add_argument("--apk",required=True)
        if name in ("launch","app-info","force-stop"): q.add_argument("--package",required=True)
        if name=="tap":
            q.add_argument("--x",type=int,required=True); q.add_argument("--y",type=int,required=True)
        if name=="swipe":
            for k in ("x1","y1","x2","y2"): q.add_argument("--"+k,type=int,required=True)
            q.add_argument("--duration-ms",type=int,default=400)
        if name=="type": q.add_argument("--text",required=True)
        if name=="keyevent": q.add_argument("--key",choices=sorted(KEYS),required=True)
        if name=="screenshot": q.add_argument("--output",default="artifacts/screenshot.png")
        if name=="logcat":
            q.add_argument("--lines",type=int,default=3000); q.add_argument("--filter",default=""); q.add_argument("--output",default="artifacts/logcat.txt")
    a=p.parse_args()
    try: a.fn(a)
    except Exception as e: print(f"ERROR: {e}",file=sys.stderr); sys.exit(1)
if __name__=="__main__": main()
