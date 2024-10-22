from select import select
from subprocess import PIPE
import sys
from dataclasses import dataclass

from plumbum.lib import read_fd_decode_safely

from plumbum.commands.modifiers import ExecutionModifier

KEYBOARD_INTERRUPT_RETCODE = 7

class MULTIPLEX(ExecutionModifier):
    """Run a command, dumping its stdout/stderr to the current process's stdout
    and stderr, but ALSO return them.  Useful for interactive programs that
    expect a TTY but also have valuable output.

    Use as:

        ls["-l"] & MULTIPLEX(keep=False,'/dev/log-recorder'
             ,'/var/log/service/task.log')

    Returns a tuple of (return code, stdout, stderr), just like ``run()``.
    """

    # __slots__ = ("retcode", "buffered", "keep", "append", "timeout", "outputs")

    def __init__(
            self,
            retcode = 0,
            buffered = True,
            keep = True,
            append = False,
            timeout = 15, # 60,
            outputs = None):
        """`retcode` is the return code to expect to mean "success".  Set
        `buffered` to False to disable line-buffering the output, which may
        cause stdout and stderr to become more entangled than usual.

        Default timeout 60 seconds (*** TODO: 7 during testing)
        """
        self.retcode = retcode
        self.buffered = buffered
        self.keep = keep
        self.append = append
        self.timeout = timeout
        self.outputs = outputs or []
        # print(f"[m] {outputs = }")

    def __rand__(self, cmd):

        with cmd.bgrun(
            retcode = self.retcode,
            stdin = PIPE,
            stdout = PIPE,
            stderr = PIPE,
            timeout = self.timeout,
            # new_session = True,		# hangs, does not take input
        ) as bg:

            outbuf = []
            errbuf = []

            mode = 'a' if self.append else 'w'

            @dataclass
            class MultiplexIO:
                in_r = sys.stdin
                in_w = bg.stdin
                out = bg.stdout
                err = bg.stderr
                mout = [open(path, mode) for path in self.outputs]
                tee_to = {out: sys.stdout, err: sys.stderr}
                buffers = {}

            mio = MultiplexIO()

            if self.keep:
                mio.buffers = {mio.out: outbuf, mio.err: errbuf}

            try:
                self.rand_core(bg, mio)
            except KeyboardInterrupt:
                print("*** KeyboardInterrupt")
                bg.returncode = KEYBOARD_INTERRUPT_RETCODE

            for fp_list in [ mio.mout, mio.tee_to.values() ]:
                for fp in fp_list :
                    fp.flush()
	                
            stdout = ''.join([buf.decode('utf-8')
                              for buf in outbuf]) if self.keep else ''

            stderr = ''.join([buf.decode('utf-8')
                              for buf in errbuf]) if self.keep else ''

            return bg.returncode, stdout, stderr

    def rand_core(self, bg, mio):
            while bg.poll() is None:
                ready, _, _ = select((mio.in_r, mio.out, mio.err), (), (), self.timeout)
                for fd in ready:
                    data, text = read_fd_decode_safely(fd, 4096)
                    if not data and not text:
                        continue
                    # print(f"{len(data) = }, {len(text) = }")
                    # Python conveniently line-buffers stdout and stderr for
                    # us, so all we need to do is write to them.
                    # This will automatically add up to three bytes if it
                    # cannot be decoded ? (BOM)
                    if fd == mio.in_r:
                        mio.in_w.write(data)
                        if not self.buffered:
                            mio.in_w.flush()
                    else:
                        mio.tee_to[fd].write(text)
                        for fout in mio.mout:
                            fout.write(text)
                        # And then "unbuffered" is just flushing after each
                        # write
                        if not self.buffered:
                            mio.tee_to[fd].flush()
                            for fout in mio.mout:
                                fout.flush()
                        if self.keep:
                            mio.buffers[fd].append(data)
                
