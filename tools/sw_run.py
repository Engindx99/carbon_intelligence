"""Run SolidWorks macros from WSL, on the code in geometry/macros.

    python3 tools/sw_run.py drawings.calciner pid.preheater pid.kiln
    python3 tools/sw_run.py --no-reload drawings.c4

SolidWorks must be running. Each argument is module.procedure of a module
loader.bas (module sw_loader) imports (drawings, pid). First the loader macro
(geometry/output/loader.swp, one-time setup in geometry/macros/loader.bas)
re-imports the .bas files into its project, then each procedure runs there
through the SolidWorks COM object: PowerShell, calling RunMacro2 by
reflection on System.__ComObject (its COM adapter cannot read SolidWorks'
type library, and VBScript cannot pass RunMacro2's by-reference error
code), so a failure comes back as swRunMacroError_e. geometry/output/quiet.flag
is held while running so the macros skip their closing message box; the
build logs carry the result, and the first line of each new one is printed.
"""
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "geometry", "output")
WIN_ROOT = "C:\\Users\\engin\\carbon_intelligence\\"
LOADER = WIN_ROOT + "geometry\\output\\loader.swp"
TIMEOUT = 1200  # [s] one procedure (the calciner sheet takes a few minutes)


# swRunMacroError_e values seen so far
RUN_ERRORS = {6: "procedure not found in the module", 22: "module not found in the macro file"}


def _ps1(module, proc):
    """A PowerShell script that runs one procedure, then closes the documents
    it left open (only those: a drawing still open from the last run made
    the next C1 sheet's left view lose its outlet circle, 16 Nov); prints
    what it closed, then ok and the error code."""
    return (
        "$sw = [Runtime.InteropServices.Marshal]::GetActiveObject('SldWorks.Application')\r\n"
        "$T = [System.__ComObject]; $F = [Reflection.BindingFlags]::InvokeMethod\r\n"
        "function Titles { $d = $T.InvokeMember('GetDocuments', $F, $null, $sw, $null); "
        "if ($d) { $d | ForEach-Object { $T.InvokeMember('GetTitle', $F, $null, $_, $null) } } }\r\n"
        "$before = @(Titles)\r\n"
        f"$a = [object[]]@('{LOADER}', '{module}', '{proc}', [int]0, [int]0)\r\n"
        "$m = New-Object Reflection.ParameterModifier 5; $m[4] = $true\r\n"
        "$ok = $T.InvokeMember('RunMacro2', $F, $null, $sw, $a, [Reflection.ParameterModifier[]]@($m), $null, $null)\r\n"
        # not $t: PowerShell names ignore case, $t would overwrite $T
        "foreach ($doc in @(Titles)) { if ($before -notcontains $doc) { "
        "[void]$T.InvokeMember('CloseDoc', $F, $null, $sw, @($doc)); Write-Output \"closed $doc\" } }\r\n"
        "Write-Output (\"$ok \" + $a[4])\r\n"
    )


def _run(module, proc):
    """(ok, error code, text) of one RunMacro2 call."""
    path = os.path.join(OUT, "sw_run.ps1")
    with open(path, "w", newline="") as f:
        f.write(_ps1(module, proc))
    win = subprocess.run(["wslpath", "-w", path], capture_output=True, text=True).stdout.strip()
    r = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", win],
                       capture_output=True, timeout=TIMEOUT, cwd="/mnt/c/")
    out = (r.stdout + r.stderr).decode("cp1254", "replace").replace("\r", "").strip()
    for line in out.splitlines()[:-1]:
        if line.startswith("closed "):
            print("    " + line)
    last = out.splitlines()[-1].split() if out else []
    if len(last) == 2 and last[0] in ("True", "False") and last[1].lstrip("-").isdigit():
        code = int(last[1])
        return last[0] == "True", code, RUN_ERRORS.get(code, f"swRunMacroError {code}") if last[0] == "False" else "ran"
    return False, None, out


def _new_logs(since):
    logs = glob.glob(os.path.join(OUT, "*", "*_build.log")) + [os.path.join(OUT, "loader.log")]
    return sorted(p for p in logs if os.path.exists(p) and os.path.getmtime(p) >= since)


def _first_line(p):
    with open(p, encoding="cp1254", errors="replace") as f:
        return f.readline().strip()


def main(argv):
    reload = "--no-reload" not in argv
    jobs = [a for a in argv if not a.startswith("--")]
    flag = os.path.join(OUT, "quiet.flag")
    open(flag, "w").close()
    bad = 0
    try:
        if reload:
            t0 = time.time()
            ok, _, why = _run("sw_loader", "reload")
            print("sw_loader.reload:", why)
            log = os.path.join(OUT, "loader.log")
            fresh = os.path.exists(log) and os.path.getmtime(log) >= t0
            text = open(log, encoding="cp1254", errors="replace").read() if fresh else ""
            print(text.rstrip())
            if not ok or "RESULT: OK" not in text:
                print("reload failed: not running anything")
                return 2
        for job in jobs:
            module, proc = job.split(".", 1)
            t0 = time.time()
            ok, _, why = _run(module, proc)
            print(f"{job}: {why}")
            bad += not ok
            logs = [p for p in _new_logs(t0) if not p.endswith("loader.log")]
            for p in logs:
                line = _first_line(p)
                print(f"    {os.path.basename(p)}: {line}")
                bad += "ABORTED" in line
            if not logs:
                print("    no build log written")
                bad += 1
    finally:
        os.remove(flag)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
