import ctypes
import ctypes.wintypes
import os
import platform
import shutil
import socket
import sys
import threading
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")
STARTED_AT = time.time()
_CPU_LOCK = threading.Lock()
_LAST_CPU_TIMES = None

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


def _filetime_to_int(filetime):
    return (filetime.dwHighDateTime << 32) + filetime.dwLowDateTime


def _cpu_percent():
    if platform.system() != "Windows":
        load = os.getloadavg()[0] if hasattr(os, "getloadavg") else None
        cpu_count = os.cpu_count() or 1
        return round(min((load / cpu_count) * 100, 100), 1) if load is not None else None

    idle_time = ctypes.wintypes.FILETIME()
    kernel_time = ctypes.wintypes.FILETIME()
    user_time = ctypes.wintypes.FILETIME()
    ctypes.windll.kernel32.GetSystemTimes(
        ctypes.byref(idle_time),
        ctypes.byref(kernel_time),
        ctypes.byref(user_time),
    )

    current = (
        _filetime_to_int(idle_time),
        _filetime_to_int(kernel_time),
        _filetime_to_int(user_time),
    )

    global _LAST_CPU_TIMES
    with _CPU_LOCK:
        previous = _LAST_CPU_TIMES
        _LAST_CPU_TIMES = current

    if previous is None:
        return None

    idle_delta = current[0] - previous[0]
    total_delta = (current[1] - previous[1]) + (current[2] - previous[2])
    if total_delta <= 0:
        return None
    return round(max(0, min(100, (1 - idle_delta / total_delta) * 100)), 1)


def _memory_status():
    if platform.system() != "Windows":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(MemoryStatus)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    used = status.ullTotalPhys - status.ullAvailPhys
    return {
        "total": status.ullTotalPhys,
        "available": status.ullAvailPhys,
        "used": used,
        "percent": round(status.dwMemoryLoad, 1),
    }


def _disk_status():
    root = os.path.abspath(os.sep)
    if platform.system() == "Windows":
        root = os.path.splitdrive(os.getcwd())[0] + "\\"
    usage = shutil.disk_usage(root)
    return {
        "mount": root,
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "percent": round((usage.used / usage.total) * 100, 1) if usage.total else None,
    }


def _host_addresses():
    try:
        return sorted(set(socket.gethostbyname_ex(socket.gethostname())[2]))
    except socket.gaierror:
        return []


def _system_uptime_seconds():
    if platform.system() == "Windows":
        return int(ctypes.windll.kernel32.GetTickCount64() / 1000)
    return None


@app.get("/api/cluster/health")
def cluster_health():
    now = time.time()
    return {
        "status": "healthy",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "cluster": {
            "name": "local-cluster",
            "node_count": 1,
            "healthy_nodes": 1,
        },
        "node": {
            "hostname": socket.gethostname(),
            "addresses": _host_addresses(),
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "cpu_count": os.cpu_count(),
            "system_uptime_seconds": _system_uptime_seconds(),
        },
        "metrics": {
            "cpu_percent": _cpu_percent(),
            "memory": _memory_status(),
            "disk": _disk_status(),
            "process": {
                "pid": os.getpid(),
                "thread_count": threading.active_count(),
                "uptime_seconds": int(now - STARTED_AT),
            },
        },
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
