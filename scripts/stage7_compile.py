"""Shared helpers of the dada Stage 7 display builders (build-stage7-driver.py, build-dada-legacy-display.py).

compile_command is the replay of XNU's own IOKit compile record from UniXNU-Pagani's build-arm-platform.py. llvm_tool finds
an LLVM binutil on either host: the 13T builders asked Homebrew for it, which a Linux host built with
UniXNU's scripts/linux/setup-toolchain.py does not have.
"""
import os
from pathlib import Path
import shutil
import subprocess


def compile_command(record, source, output):
    args = iter(record['arguments'])
    command = []
    found_source = False
    for value in args:
        if value == record['file']:
            command.append(str(source))
            found_source = True
        elif value == '-o':
            next(args)
            command.extend(['-o', str(output)])
        elif value in ('-MF', '-MJ', '-MT', '-MQ'):
            next(args)
        elif value not in ('-MD', '-MMD', '-MP'):
            command.append(value)
    if not found_source or '-o' not in command:
        raise ValueError('IOKit compile record lacks its source or output argument')
    return command


def llvm_tool(name):
    """The path of an LLVM tool such as llvm-objcopy: Linux toolchain, Homebrew, xcrun, then PATH."""
    candidates = [Path(os.environ.get('UNIXNU_TOOLCHAIN', '/opt/unixnu-linux')) / 'llvm/bin' / name]
    for prefix in ('/opt/homebrew/opt/llvm/bin', '/usr/local/opt/llvm/bin'):
        candidates.append(Path(prefix) / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    try:
        found = subprocess.check_output(['xcrun', '--find', name], text=True, stderr=subprocess.DEVNULL, timeout=30).strip()
        if found and Path(found).is_file():
            return Path(found)
    except (OSError, subprocess.SubprocessError):
        pass
    found = shutil.which(name)
    if found:
        return Path(found)
    raise SystemExit(f'{name} not found: install the UniXNU Linux toolchain or Homebrew LLVM')
