from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
from typing import Sequence


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_seconds: int = 30
    memory_bytes: int = 512 * 1024 * 1024
    cpu_seconds: int = 10
    network_allowed: bool = False
    filesystem_root: Path | None = None
    environment: dict[str, str] = field(default_factory=dict)


class SandboxUnavailable(RuntimeError):
    pass


@dataclass
class SandboxRunner:
    """Conservative process sandbox adapter.

    The runner fails closed when the required OS-level isolation backend is not
    available. It does not claim that Python-level policy is a physical sandbox.
    Bubblewrap is used when present to create a restricted Linux process view.
    """

    policy: SandboxPolicy = field(default_factory=SandboxPolicy)

    def _backend(self) -> str:
        if os.name != 'posix':
            raise SandboxUnavailable('no supported OS sandbox backend')
        binary = shutil.which('bwrap')
        if not binary:
            raise SandboxUnavailable('bubblewrap sandbox backend unavailable')
        if self.policy.network_allowed:
            raise SandboxUnavailable('network-enabled sandbox requires explicit hardened backend')
        return binary

    def run(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if not command:
            raise ValueError('empty command')
        bwrap = self._backend()
        root = self.policy.filesystem_root or Path(tempfile.mkdtemp(prefix='manifex-sbx-'))
        root = root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        env = dict(self.policy.environment)
        env['PATH'] = '/usr/bin:/bin'
        wrapped = [
            bwrap,
            '--die-with-parent',
            '--new-session',
            '--unshare-pid',
            '--unshare-uts',
            '--unshare-ipc',
            '--unshare-net',
            '--proc', '/proc',
            '--dev', '/dev',
            '--tmpfs', '/tmp',
            '--ro-bind', '/usr', '/usr',
            '--ro-bind', '/bin', '/bin',
            '--ro-bind', '/lib', '/lib',
            '--ro-bind', '/lib64', '/lib64',
            '--bind', str(root), '/workspace',
            '--chdir', '/workspace',
            '--setenv', 'PATH', env['PATH'],
            '--',
            *command,
        ]
        clean_env = {'PATH': env['PATH']}
        clean_env.update({k: v for k, v in env.items() if k != 'PATH'})
        return subprocess.run(
            wrapped,
            cwd=root,
            env=clean_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.policy.timeout_seconds,
            check=False,
            close_fds=True,
        )
