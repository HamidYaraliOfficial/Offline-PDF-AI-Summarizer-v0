from __future__ import annotations

import os
import platform
import shutil
import subprocess
from typing import Any


def hardware_report() -> dict[str, Any]:
    """Return a best-effort local hardware report without making network calls."""
    report: dict[str, Any] = {
        "Operating system": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "CPU": platform.processor() or platform.uname().processor or "Unknown CPU",
        "CPU threads": os.cpu_count() or 1,
        "RAM": "Unknown",
        "GPU": "Not detected (CPU mode is available)",
    }
    try:
        import psutil
        report["RAM"] = f"{psutil.virtual_memory().total / (1024 ** 3):.1f} GB"
    except Exception:
        pass

    # nvidia-smi works even when PyTorch is not installed; it is optional and local-only.
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            result = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3, check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                first = result.stdout.strip().splitlines()[0].split(",")
                report["GPU"] = first[0].strip()
                if len(first) > 1 and first[1].strip().isdigit():
                    report["VRAM"] = f"{int(first[1].strip()) / 1024:.1f} GB"
        except Exception:
            pass

    try:
        import torch  # Optional only; the application does not require PyTorch.
        if torch.cuda.is_available():
            report["GPU"] = torch.cuda.get_device_name(0)
            report["VRAM"] = f"{torch.cuda.get_device_properties(0).total_memory / (1024 ** 3):.1f} GB"
    except Exception:
        pass
    return report
