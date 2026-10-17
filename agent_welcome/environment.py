"""Read-only observations of the current process environment."""

import os
import platform
import re
import sys


def _architecture(value):
    text = value.lower()
    return {
        'arm64': 'aarch64',
        'armv8l': 'armv8l',
        'amd64': 'x86_64',
        'x64': 'x86_64',
        'i386': 'i686',
        'i686': 'i686',
    }.get(text, text)


def observe():
    system = platform.system().lower()
    if sys.platform == 'ios' or system in {'ios', 'iphoneos'}:
        kernel_os = 'darwin'
        host_os = 'ios'
        host_method = 'python_ios_platform'
    elif system == 'darwin':
        kernel_os = 'darwin'
        host_os = 'macos'
        host_method = 'darwin_kernel'
    elif system == 'windows':
        kernel_os = 'windows'
        host_os = 'windows'
        host_method = 'windows_kernel'
    elif system == 'linux':
        kernel_os = 'linux'
        android_api = getattr(sys, 'getandroidapilevel', None)
        if os.environ.get('PROOT_TMP_DIR') or os.environ.get('PROOT_LOADER'):
            host_os = None
            host_method = 'guest_host_unknown'
        elif callable(android_api):
            host_os = 'android'
            host_method = 'android_api_level'
        elif 'microsoft' in platform.release().lower():
            host_os = None
            host_method = 'wsl_host_unknown'
        else:
            host_os = 'linux'
            host_method = 'native_linux_kernel'
    else:
        kernel_os = system
        host_os = None
        host_method = 'unrecognized_platform'
    libc_name, libc_version = platform.libc_ver()
    family = 'glibc' if libc_name.lower() in {'glibc', 'gnu libc'} else (
        'musl' if 'musl' in libc_name.lower() else None
    )
    if libc_version and not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', libc_version):
        libc_version = None
    runtime_kind = 'proot' if os.environ.get('PROOT_TMP_DIR') or os.environ.get('PROOT_LOADER') else (
        'linux_userland' if kernel_os == 'linux' else 'native'
    )
    return {
        'kernel_os': kernel_os,
        'host_os': host_os,
        'architecture': _architecture(platform.machine()),
        'runtime_kind': runtime_kind,
        'libc': {'family': family, 'version': libc_version or None},
        'capabilities': {},
        'auth': {'failure_stage': None},
        'provenance': {
            'kind': 'process_observation',
            'python': platform.python_version(),
            'platform': platform.platform(),
            'host_os_method': host_method,
            'runtime_tested': False,
        },
    }
