#coding:utf-8

import os
import sys
from ConfigParser import ConfigParser, ParsingError


def c(s, t=None):
    """
    颜色渲染
    """
    color = {'r': "\033[1;31;1m%s\033[0m" % s,
             'g': "\033[0;32;1m%s\033[0m" % s,
             'y': "\033[0;33;1m%s\033[0m" % s,
             'b': "\033[0;34;1m%s\033[0m" % s,
    }
    return color.get(t) or s


def prog_dir():
    """
    获取程序的根路径
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_abs_path(rel_path=None):
    """
    返回路径的绝对路径，相对程序目录
    :param rel_path:相对路径
    :return:绝对路径
    """
    abs_path = ''
    if rel_path:
        abs_path = os.path.join(prog_dir(), rel_path)
    return abs_path


def read_config(config_file='etc/mtool.conf', ctype="main"):
    """
    @note:解析配置文件，返回字典类型的配置信息
    @config_file:配置文件
    @return:典类型的配置信息
    """
    confparser = ConfigParser()
    opts = {}
    config_file = app_abs_path(config_file)
    if os.path.exists(config_file):
        try:
            confparser.read(config_file)
            opts = {k: v for k, v in confparser.items(ctype)}
        except ParsingError, e:
            print >> sys.stderr, "Error reading config file: %s" % e
            sys.exit(1)
    return opts
