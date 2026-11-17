#!/usr/bin/env python3
"""Compile Stage 7 components with the kernel's own ABI and compiler flags.

From UniXNU-Pagani's fork (IssacL04/UniXNU_Enc3l scripts/build-stage7-driver.py), reduced to the display objects dada links.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess


def c_command(command):
    arguments=iter(command);result=[]
    for value in arguments:
        if value=='-x':
            next(arguments)
        elif value not in ('-fapple-kext','-fno-rtti','-fno-exceptions','-fno-threadsafe-statics',
                           '-fcxx-modules','-fvisibility-inlines-hidden','-fsized-deallocation',
                           '-fno-c++-static-destructors') and not value.startswith(('-x','-std=','-stdlib=','--driver-mode=')):
            result.append(value)
    result[1:1]=['--driver-mode=gcc','-x','c','-std=gnu11']
    return result


root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
# dada: the 13T peripherals (PaganiInput, PaganiS3910, PaganiGeniSpi, PaganiPanel) are not built; DadaDisplayGlue replaces BootProgress.
parser.add_argument('component', choices=['NativeLegacyDisplay', 'NativeGOPPresenter', 'NativeKeyStoreEvents', 'Stage7Probe', 'DadaDisplayGlue'])
component = parser.parse_args().component
directory = root / 'build' / ('native-keystore-events' if component == 'NativeKeyStoreEvents' else 'native-legacy-display')
directory.mkdir(parents=True, exist_ok=True)
source = (root / 'kits/dada/display/Stage7Probe' / (component + '.cpp') if component in ('Stage7Probe', 'DadaDisplayGlue') else
          root / 'kits/dada/display' / ('NativeMobileDisplay' if component in ('NativeLegacyDisplay','NativeGOPPresenter') else component) / (component + '.cpp'))
record = json.loads((root / 'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/iokit/DEVELOPMENT/IOPlatformExpert.cpo.json').read_text().strip().rstrip(','))
obj = directory / (component + '.o')
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage7_compile import compile_command
arguments = iter(compile_command(record, source, obj))
command = []
# Keep XNU's ABI; use the reference driver's warning policy instead of -Weverything.
for value in arguments:
    if value == '-Xclang':
        option = next(arguments)
        if not option.startswith('-W'):
            command += [value, option]
    elif not value.startswith('-W'):
        command.append(value)
if source.suffix == '.c':
    command=c_command(command)
command += ['-mgeneral-regs-only', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
            '-Wno-c99-designator', '-Wno-reorder-init-list', '-Wno-deprecated-enum-enum-conversion', '-Wno-unnecessary-virtual-specifier',
            '-I', str(directory), '-I', str(root / '.cache/xnu-work/osfmk')]
subprocess.run(command, cwd=record['directory'], check=True)
data = obj.read_bytes()
assert struct.unpack_from('<4I', data) == (0xfeedfacf, 0x100000c, 0, 1), 'Require ARM64 Mach-O object'
offset, deployment = 32, None
for _ in range(struct.unpack_from('<I', data, 16)[0]):
    cmd, size = struct.unpack_from('<II', data, offset)
    if cmd == 0x32:
        deployment = struct.unpack_from('<II', data, offset + 8)
    offset += size
assert deployment == (2, 0x110000), 'Require iOS 17 target'
print(component + ': compile and object ABI checks passed')
