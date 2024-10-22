from select import select
from subprocess import PIPE
import sys

from plumbum.lib import read_fd_decode_safely

from plumbum.commands.modifiers import ExecutionModifier


class _MULTIPLEX(ExecutionModifier):
    """Run a command, dumping its stdout/stderr to the current process's stdout
    and stderr, but ALSO return them.  Useful for interactive programs that
    expect a TTY but also have valuable output.

    Use as:

        ls["-l"] & MULTIPLEX(keep=False,'/dev/log-recorder'
             ,'/var/log/service/task.log')

    Returns a tuple of (return code, stdout, stderr), just like ``run()``.
    """

    __slots__ = ("retcode", "buffered", "keep", "append", "timeout", "outputs")

    def __init__(
            self,
            retcode=0,
            buffered=True,
            keep=True,
            append=False,
            timeout=None,
            outputs=[]):
        """`retcode` is the return code to expect to mean "success".  Set
        `buffered` to False to disable line-buffering the output, which may
        cause stdout and stderr to become more entangled than usual.
        """
        self.retcode = retcode
        self.buffered = buffered
        self.keep = keep
        self.append = append
        self.timeout = timeout
        self.outputs = outputs

        # print('outputs: ')
        # for file in outputs :
        #     print("out:  '%s'" % ( file ))
        # print('')

    def __rand__(self, cmd):
        try:
            return self.rand_core(cmd)
        except KeyboardInterrupt:
            print("*** KeyboardInterrupt")
            sys.exit(1)

    def rand_core(self, cmd):
        with cmd.bgrun(
            retcode=self.retcode,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            timeout=self.timeout,
            # new_session=True,		# hangs, does not take input
        ) as p:

            outbuf = []
            errbuf = []

            in_r = sys.stdin
            in_w = p.stdin
            out = p.stdout
            err = p.stderr
            mode = 'a' if self.append else 'w'
            mout = [open(path, mode) for path in self.outputs]

            if self.keep:
                buffers = {out: outbuf, err: errbuf}
            tee_to = {out: sys.stdout, err: sys.stderr}

            while p.poll() is None:
                ready, _, _ = select((in_r, out, err), (), ())
                for fd in ready:
                    data, text = read_fd_decode_safely(fd, 4096)
                    if not data:  # eof
                        continue
                    # Python conveniently line-buffers stdout and stderr for
                    # us, so all we need to do is write to them
                    # This will automatically add up to three bytes if it
                    # cannot be decoded
                    if fd == in_r:
                        in_w.write(data)
                        if not self.buffered:
                            in_w.flush()
                    else:
                        tee_to[fd].write(text)
                        for fout in mout:
                            fout.write(text)
                        # And then "unbuffered" is just flushing after each
                        # write
                        if not self.buffered:
                            tee_to[fd].flush()
                            for fout in mout:
                                fout.flush()
                        if self.keep:
                            buffers[fd].append(data)

            stdout = ''.join([x.decode('utf-8')
                              for x in outbuf]) if self.keep else ''
            stderr = ''.join([x.decode('utf-8')
                              for x in errbuf]) if self.keep else ''

            return p.returncode, stdout, stderr


MULTIPLEX = _MULTIPLEX()
