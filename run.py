#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'YinJia'

import configparser
import datetime
import logging
import os, sys

from utils.get_new_report import get_latest_file_path
from utils.mail_util import send_mail

sys.path.append(os.path.dirname(__file__))
import unittest, time
from HTMLTestRunner.HTMLTestRunner import HTMLTestRunner, _TestResult


class MyConfig:
    BASE_DIR = os.path.dirname(__file__)
    sys.path.append(BASE_DIR)

    # 配置文件
    CONFIG_INI = os.path.join(BASE_DIR, "config.ini")
    # 测试数据
    TESTDATA_DIR = os.path.join(BASE_DIR, "testdata")
    # 测试用例模板文件
    TESTDATA_FILE = os.path.join(TESTDATA_DIR, "auto_test_case.xlsx")
    # 测试用例报告
    TESTREPORT_DIR = os.path.join(BASE_DIR, "report")
    # 测试用例程序文件
    TEST_CASE = os.path.join(BASE_DIR, "testcase")


def add_case(test_path=MyConfig.TEST_CASE):
    """加载所有的测试用例"""
    discover = unittest.defaultTestLoader.discover(test_path, pattern='test*.py')
    return discover

# logging.basicConfig(level=logging.DEBUG,
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] - [%(filename)s:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d_%H:%M:%S',
                    # stream=sys.stdout,
                    # filename='my.log',
                    # filemode='a',
                    handlers=[
                        # logging.FileHandler(f"{log_name}", encoding="UTF-8", mode='a'),  # 文件日志处理器
                        logging.StreamHandler(sys.stdout)  # 控制台日志处理器
                    ]
                    )


class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        # 定义颜色
        color_codes = {
            logging.DEBUG: '\033[94m',  # 蓝色
            logging.INFO: '\033[92m',  # 绿色
            logging.WARNING: '\033[93m',  # 黄色
            logging.ERROR: '\033[91m',  # 红色
            logging.CRITICAL: '\033[95m'  # 紫色
        }
        # 添加颜色代码
        record.levelname = color_codes.get(record.levelno, '\033[0m') + record.levelname + '\033[0m'
        return super().format(record)


logger = logging.getLogger()
# 获取控制台日志处理器
console_handler = logger.handlers[-1]
# 创建控制台日志格式化器（包含颜色代码）
console_handler.setFormatter(ColoredFormatter(
    fmt='[%(asctime)s] - [%(filename)s:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d_%H:%M:%S'
))


# class MyTestResult(TextTestResult):
class MyTestResult(_TestResult):
    # def __init__(self, stream, descriptions, verbosity):
    #     # 关闭流，这样就不会有任何输出到控制台
    #     # super(QuietTestResult, self).__init__(open(os.devnull, 'w'), descriptions, verbosity)
    #     # 使用传入的流，而不是关闭它
    #     super(QuietTestResult, self).__init__(stream, descriptions, verbosity)

    def addError(self, test, err):
        # 只记录错误到日志文件，不在控制台输出
        logging.getLogger().error("错误：%s", test, exc_info=err)
        super(MyTestResult, self).addError(test, err)

    def addFailure(self, test, err):
        logging.getLogger().error("错误：%s", test, exc_info=err)
        super(MyTestResult, self).addFailure(test, err)

    # def printErrors(self):
    #     print("\r")


class MyHTMLTestRunner(HTMLTestRunner):
    def run(self, test):
        "Run the given test case or test suite."
        # result = _TestResult(self.verbosity)
        result = MyTestResult(self.verbosity)
        test(result)
        self.stopTime = datetime.datetime.now()
        self.generateReport(test, result)
        print(sys.stderr, '\nTime Elapsed: %s' % (self.stopTime - self.startTime))
        return result


def run_case(all_case, result_path=MyConfig.TESTDATA_DIR):
    """执行所有的测试用例"""

    # 初始化接口测试数据
    # test_data.init_data()

    now = time.strftime("%Y%m%d")
    filename = result_path + '/' + f"result-{now}" + '.html'
    with open(filename, 'wb') as fp:
        runner = MyHTMLTestRunner(stream=fp, title='接口自动化测试报告',
                                  description='环境：windows 10 浏览器：chrome',
                                  tester='Jason')
        runner.run(all_case)
    # fp.close()
    latest_file_path = get_latest_file_path(MyConfig.TESTDATA_DIR)  # 调用模块生成最新的报告
    logging.getLogger().info("报告路径：" + latest_file_path)

    # 调用发送邮件模块
    config_p = configparser.ConfigParser()
    config_p.read(MyConfig.CONFIG_INI, encoding='utf-8')
    config_smtp = config_p.items("smtp")
    # 创建一个字典来存储SMTP配置
    smtp_config = {key: value for key, value in config_smtp}
    if "password" in smtp_config and smtp_config["password"] != "":
        send_mail(latest_file_path, smtp_config)


if __name__ == "__main__":
    cases = add_case()
    run_case(cases)
