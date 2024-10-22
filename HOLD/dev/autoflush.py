#
#
#

import sys

# from io import TextIOWrapper


def autoflush(stream, flush=True):

    def autoflush_write(s):
        # if s != "\n" :
        #     stream.pre_autoflush_write(':')
        stream.pre_autoflush_write(s)
        stream.flush()

    def autoflush_writelines(lines):
        stream.pre_autoflush_writelines(lines)
        stream.flush()

    if flush:
        if sys.stdout.write.__name__ != 'autoflush_write':
            stream.pre_autoflush_write = stream.write
            stream.pre_autoflush_writelines = stream.writelines
            stream.write = autoflush_write
            stream.writelines = autoflush_writelines
    else:
        if sys.stdout.write.__name__ == 'autoflush_write':
            stream.write = stream.pre_autoflush_write
            stream.writelines = stream.pre_autoflush_writelines

    return stream

# ------------------------------------------------------------------------------


if __name__ == "__main__":

    from pprint import PrettyPrinter
    pp = PrettyPrinter(indent=4).pprint

    print('')
    print('- start')
    print('')

    print(
        "    sys.stdout.write.__name__ = '{}'".format(
            sys.stdout.write.__name__))
    print('')

    print('- sys.stdout, autoflush - enable')
    print('')
    autoflush(sys.stdout)

    print(
        "    sys.stdout.write.__name__ = '{}'".format(
            sys.stdout.write.__name__))
    print('')

    autoflush(sys.stdout, False)
    print('- sys.stdout, autoflush - disabled')
    print('')

    print(
        "    sys.stdout.write.__name__ = '{}'".format(
            sys.stdout.write.__name__))
    print('')

    print('- done')
    print('')

# ------------------------------------------------------------------------------
