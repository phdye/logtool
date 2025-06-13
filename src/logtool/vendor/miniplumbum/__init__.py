import os
import subprocess
import sys
import tempfile
from shutil import which
from typing import List, Iterable, Optional, Tuple


class ProcessExecutionError(Exception):
    def __init__(self, retcode: int, stdout: str = "", stderr: str = ""):
        super().__init__(f"Command returned {retcode}")
        self.retcode = retcode
        self.stdout = stdout
        self.stderr = stderr


class ExecutionModifier:
    """Base class for execution modifiers invoked via ``cmd & modifier``."""

    def __rand__(self, cmd):
        raise NotImplementedError


class Command:
    def __init__(self, argv: Iterable[str]):
        self.argv = list(argv)
        self.stdout_file: Optional[str] = None
        self.stdout_append: bool = False

    def __getitem__(self, args):
        if isinstance(args, (list, tuple)):
            return Command(self.argv + list(args))
        else:
            return Command(self.argv + [str(args)])

    def __or__(self, other):
        if isinstance(other, Command):
            return Pipeline([self, other])
        elif isinstance(other, Pipeline):
            return Pipeline([self] + other.commands)
        else:
            raise TypeError("Unsupported operand type for |")

    def __ior__(self, other):
        return self.__or__(other)

    def __and__(self, modifier: ExecutionModifier):
        return modifier.__rand__(self)

    def __str__(self):
        return " ".join(self.argv)

    def __rshift__(self, filename):
        cmd = Command(self.argv)
        cmd.stdout_file = filename
        cmd.stdout_append = True
        return cmd

    def run(self, retcode: Optional[int] = 0) -> Tuple[int, str, str]:
        stdout_target = subprocess.PIPE
        stderr_target = subprocess.PIPE
        out_file = None
        if self.stdout_file:
            mode = "ab" if self.stdout_append else "wb"
            out_file = open(self.stdout_file, mode)
            stdout_target = out_file
        argv = list(self.argv)
        exe = argv[0]
        if os.path.islink(exe) and not os.path.exists(exe):
            target = os.readlink(exe)
            if target.startswith("#!/"):
                tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".py")
                tmp.write(target)
                tmp.close()
                argv = [sys.executable, tmp.name] + argv[1:]
        proc = subprocess.run(
            argv,
            stdin=None,
            stdout=stdout_target,
            stderr=stderr_target,
            text=True,
        )
        if out_file:
            out_file.close()
            stdout = ""
        else:
            stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if retcode is not None and proc.returncode != retcode:
            raise ProcessExecutionError(proc.returncode, stdout, stderr)
        return proc.returncode, stdout, stderr

    def bgrun(
        self,
        retcode: Optional[int] = 0,
        stdin=None,
        stdout=None,
        stderr=None,
        timeout=None,
    ):
        argv = list(self.argv)
        exe = argv[0]
        if os.path.islink(exe) and not os.path.exists(exe):
            target = os.readlink(exe)
            if target.startswith("#!/"):
                tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".py")
                tmp.write(target)
                tmp.close()
                argv = [sys.executable, tmp.name] + argv[1:]
        proc = subprocess.Popen(
            argv,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        return BGProcess(proc, retcode)


class Pipeline(Command):
    def __init__(self, commands: List[Command]):
        self.commands = list(commands)
        self.stdout_file: Optional[str] = None
        self.stdout_append: bool = False

    def __or__(self, other):
        if isinstance(other, Command):
            return Pipeline(self.commands + [other])
        elif isinstance(other, Pipeline):
            return Pipeline(self.commands + other.commands)
        else:
            raise TypeError("Unsupported operand type for |")

    def __ior__(self, other):
        if isinstance(other, Command):
            self.commands.append(other)
        elif isinstance(other, Pipeline):
            self.commands.extend(other.commands)
        else:
            raise TypeError("Unsupported operand type for |=")
        return self

    def __and__(self, modifier: ExecutionModifier):
        return modifier.__rand__(self)

    def __rshift__(self, filename):
        self.stdout_file = filename
        self.stdout_append = True
        return self

    def run(self, retcode: Optional[int] = 0) -> Tuple[int, str, str]:
        procs = []
        prev_stdout = None
        for i, cmd in enumerate(self.commands):
            stdin = prev_stdout
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
            if i == len(self.commands) - 1 and self.stdout_file:
                stdout = open(self.stdout_file, "ab" if self.stdout_append else "wb")
            argv = list(cmd.argv)
            exe = argv[0]
            if os.path.islink(exe) and not os.path.exists(exe):
                target = os.readlink(exe)
                if target.startswith("#!/"):
                    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".py")
                    tmp.write(target)
                    tmp.close()
                    argv = [sys.executable, tmp.name] + argv[1:]
            proc = subprocess.Popen(argv, stdin=stdin, stdout=stdout, stderr=stderr, text=True)
            if prev_stdout and prev_stdout is not subprocess.PIPE:
                prev_stdout.close()
            prev_stdout = proc.stdout
            procs.append(proc)
        # collect
        stdout_data, stderr_data = procs[-1].communicate()
        for p in procs[:-1]:
            p.wait()
        if isinstance(procs[-1].stdout, (os.FileIO,)):
            procs[-1].stdout.close()
            stdout_data = ""
        if retcode is not None and procs[-1].returncode != retcode:
            raise ProcessExecutionError(procs[-1].returncode, stdout_data, stderr_data)
        return procs[-1].returncode, stdout_data or "", stderr_data or ""

    def bgrun(
        self,
        retcode: Optional[int] = 0,
        stdin=None,
        stdout=None,
        stderr=None,
        timeout=None,
    ):
        # Build pipeline connecting stdout to stdin
        processes = []
        prev_proc = None
        for i, cmd in enumerate(self.commands):
            p_stdin = prev_proc.stdout if prev_proc else stdin
            p_stdout = subprocess.PIPE if i < len(self.commands) - 1 else stdout
            argv = list(cmd.argv)
            exe = argv[0]
            if os.path.islink(exe) and not os.path.exists(exe):
                target = os.readlink(exe)
                if target.startswith("#!/"):
                    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".py")
                    tmp.write(target)
                    tmp.close()
                    argv = [sys.executable, tmp.name] + argv[1:]
            p = subprocess.Popen(argv, stdin=p_stdin, stdout=p_stdout, stderr=stderr)
            if prev_proc and prev_proc.stdout:
                prev_proc.stdout.close()
            processes.append(p)
            prev_proc = p
        return BGProcess(processes[-1], retcode, extra=processes[:-1])


class BGProcess:
    def __init__(self, proc: subprocess.Popen, retcode: Optional[int], extra=None):
        self.proc = proc
        self.expected_retcode = retcode
        self.stdin = proc.stdin
        self.stdout = proc.stdout
        self.stderr = proc.stderr
        self._extra = extra or []

    def poll(self):
        return self.proc.poll()

    def wait(self, timeout=None):
        for p in self._extra:
            p.wait(timeout)
        return self.proc.wait(timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.wait()
        return False

    @property
    def returncode(self):
        return self.proc.returncode

    @returncode.setter
    def returncode(self, value):
        self.proc.returncode = value


class RETCODE(ExecutionModifier):
    def __init__(self, FG: bool = False):
        self.FG = FG

    def __rand__(self, cmd):
        ret, _, _ = cmd.run(retcode=None)
        return ret


class _BG(ExecutionModifier):
    def __rand__(self, cmd):
        if isinstance(cmd, (Command, Pipeline)):
            cmd.bgrun()
        else:
            raise TypeError("BG requires a Command or Pipeline")


BG = _BG()


class Local:
    def __getitem__(self, cmd: str) -> Command:
        return Command([cmd])

    def get(self, *cmds: str) -> Command:
        for c in cmds:
            path = which(c)
            if path:
                return Command([path])
        raise FileNotFoundError("command not found")


local = Local()


def read_fd_decode_safely(fd, size: int):
    data = fd.read(size)
    if data is None:
        data = b""
    text = data.decode("utf-8", errors="replace") if isinstance(data, (bytes, bytearray)) else data
    return data, text
