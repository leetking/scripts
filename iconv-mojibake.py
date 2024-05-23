#!/usr/bin/env python3

# Author: alpha0x00
# Date: 2022-09-06

import re
import os
import sys
import argparse
import contextlib


# 按照如下编码尝试
TRY_CHARSETS = [
    'ascii', # 全英文
    'gb2312',
    'utf-8',
    #'gbk',   # use gbk not gb18030
]

"""
自动识别并转换乱码文档到指定编码
- 支持 utf-8 和 gbk 混合导致的编码

思路：
- 按行解析并尝试不同编码转换，保证转换后的字符在常见字符范围
- 识别不同的换行符
"""

def iconv_mojibake(byte :bytes, tocharset='utf-8', newline='\n'):
    """
    转换数据为 tocharset 编码的字符串
    """
    newlines = [
        b'\n',  # Unix/Linux
        b'\r',  # Mac OS <= OS 9
        b'\r\n' # Windows
    ]
    newlines.sort(key=len, reverse=True)
    ret = []
    for line in re.split(b'|'.join(newlines), byte):
        for charset in TRY_CHARSETS:
            try:
                text = line.decode(charset)
            except UnicodeDecodeError:
                continue
            break
        ret.append(text.encode(tocharset))
    newline = newline.encode(tocharset)
    return newline.join(ret)


def detect_charsets(byte: bytes):
    ret = []
    newlines = [
        b'\n',  # Unix/Linux
        b'\r',  # Mac OS <= OS 9
        b'\r\n' # Windows
    ]
    newlines.sort(key=len, reverse=True)
    ret = set()
    for line in re.split(b'|'.join(newlines), byte):
        for charset in TRY_CHARSETS:
            try:
                text = line.decode(charset)
            except UnicodeDecodeError:
                continue
            if text not in (None, 'ascii'):
                ret.add(charset)
            break
    return list(ret)


def file_readable(path):
    return os.path.isfile(path) and os.access(path, os.R_OK)

def parse_args():
    parser = argparse.ArgumentParser(prog='iconv-mojibake', epilog='Author: alpha0x00', description="自动识别并转换乱码文档到指定编码")
    parser.add_argument('-t', '--to', type=str, default='utf-8', choices=TRY_CHARSETS,
            help="保存编码，默认 utf-8，支持 " + ', '.join(TRY_CHARSETS))
    parser.add_argument('--style', type=str, default='unix', choices=['unix', 'mac', 'windows'],
            help="保存的换行风格，默认 unix，支持 unix、mac、windows")
    parser.add_argument('-k', '--only-check', action='store_true', default=False, help="检查文件编码，不进行转换")
    parser.add_argument('input_fname', nargs='?', type=str, default='-', help="乱码文件，未指定使用标准输入")
    parser.add_argument('output_fname', nargs='?', type=str, default='-', help="保存到文件，未指定使用标准输出")
    return parser.parse_args()


@contextlib.contextmanager
def smart_open(fname=None, mode='r'):
    is_stdfile = fname is None or fname == '-'
    write = 'w' in mode
    if is_stdfile:
        fp = sys.stdout if write else sys.stdin
        if 'b' in mode:     # binary mode
            fp = fp.buffer
    else:
        fp = open(fname, mode)

    try:
        yield fp
    finally:
        if not is_stdfile:
            fp.close()


def main():
    args = parse_args()
    newlines = {
        'windows': '\r\n',
        'unix': '\n',
        'mac': '\r',
    }
    ifname = args.input_fname
    ofname = args.output_fname
    tocharset = args.to
    newline = newlines.get(args.style, '\n')

    if args.only_check:
        with smart_open(ifname, 'rb') as input_:
            context = input_.read()     # read all
            charsets = detect_charsets(context)
            if len(charsets) > 1:
                print("file {} mixs encodings: {}".format(ifname, ', '.join(charsets)))
            else:
                print("file {} encoding: {}".format(ifname, ', '.join(charsets)))
        return 0

    with smart_open(ifname, 'rb') as input_:
        with smart_open(ofname, 'wb') as output:
            context = input_.read()     # read all
            conved_bytes = iconv_mojibake(context, tocharset, newline)
            output.write(conved_bytes)


if __name__ == '__main__':
    main()

