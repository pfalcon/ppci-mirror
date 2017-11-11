
if False:
    import sys
    from IPython.core import ultratb
    sys.excepthook = ultratb.FormattedTB(mode='Verbose', call_pdb=1)

import argparse
import logging
import os
import sys
from ppci import api
from ppci.common import CompilerError
from ppci.utils.reporting import HtmlReportGenerator
from ppci.lang.c.options import COptions, coptions_parser

this_dir = os.path.abspath(os.path.dirname(__file__))
libc_includes = os.path.join(this_dir, '..', 'librt', 'libc')

parser = argparse.ArgumentParser(parents=[coptions_parser])
parser.add_argument('fatfs_path')
parser.add_argument('-v', action='count', default=0)
args = parser.parse_args()

coptions = COptions.from_args(args)
coptions.add_include_path(libc_includes)
fatfs_path = args.fatfs_path
report_html = os.path.join(fatfs_path, 'compilation_report.html')
if args.v > 0:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

arch = api.get_arch('riscv')

with open(report_html, 'w') as rf, HtmlReportGenerator(rf) as reporter:
    def cc(filename):
        logging.info('Compiling %s', filename)
        with open(os.path.join(fatfs_path, filename)) as f:
            try:
                obj = api.cc(f, arch, reporter=reporter, coptions=coptions)
                logging.info('Compiled %s into %s bytes', filename, obj.byte_size)
            except CompilerError as e:
                print(e)
                e.print()
                obj = None
        return obj

    file_list = ['xprintf.c', 'loader.c', 'ff.c', 'sdmm.c']
    objs = [cc(f) for f in file_list]
    print(objs)
