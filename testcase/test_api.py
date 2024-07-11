#!/usr/bin/env python
# _*_ coding:utf-8 _*_
__author__ = 'YinJia'

import ast
import configparser
import logging
import os
from run import MyConfig
import unittest, requests, ddt
from utils.my_requests import MyRequests
from utils.excel_testcase_processor import ExcelTestCaseProcessor


@ddt.ddt
class TestAPI(unittest.TestCase):
    """读取testdata/auto_test_case.xlsx执行用例"""

    # 创建ConfigParser对象
    configParser = configparser.ConfigParser()

    # 读取配置文件
    config_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
    configParser.read(config_file_path, encoding='UTF-8')
    status_codes_str = configParser.get('request', 'status_code')
    # 将字符串分割成列表，并转换为整数
    config_status_codes = [int(code) for code in status_codes_str.split(',')]

    def setUp(self):
        self.session = requests.session()

    def tearDown(self):
        pass

    logger = logging.getLogger()

    # testData = XlrdExcel(MyConfig.TESTDATA_FILE).read_data()
    @ddt.data(*ExcelTestCaseProcessor(MyConfig.TESTDATA_FILE).read_data())
    def test_api(self, excel_data: dict):
        """excel_data为sheet页中的一行数据，key为每一列的首行数据，value为这一行中的值"""
        # 发送请求
        response = MyRequests().send_request(self.session, excel_data=excel_data)
        # 校验http响应的状态码
        if response.status_code not in self.config_status_codes:
            raise RuntimeError(
                f"{excel_data['casetitle']} {excel_data['url']} {response.status_code} not in {self.config_status_codes}")

        code_key = "code"
        if code_key in excel_data:
            code = excel_data[code_key]
        else:
            code_key = self.next_key(excel_data, "body")
            code = excel_data[code_key]

        msg_key = "msg"
        if msg_key in excel_data:
            msg = excel_data[msg_key]
        else:
            msg_key = self.next_key(excel_data, code_key)
            msg = excel_data[code_key]
        result = "PASS"

        # 检查响应的Content-Type是否为JSON
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            self.result = response.json()
            self.logger.debug(f"用例数据：{excel_data}")
            self.logger.info("响应数据：%s" % response.content.decode("utf-8"))

            try:
                self.assertEqual(ast.literal_eval(code), response.json()[code_key], "响应的code不相等！")
                self.assertIn(msg, response.json()[msg_key], "响应的消息不在里面！")
            except Exception as e:
                result = "FAIL"
                raise e
            finally:
                ExcelTestCaseProcessor(MyConfig.TESTDATA_FILE).write_data(excel_data, value=result)
        else:
            # 如果Content-Type不是JSON，处理非JSON响应
            try:
                self.assertIn(ast.literal_eval(code), response.text, "响应的code不在里面！")
                self.assertIn(msg, response.text, "响应的消息不在里面！")
            except Exception as e:
                result = "FAIL"
                raise e
            finally:
                ExcelTestCaseProcessor(MyConfig.TESTDATA_FILE).write_data(excel_data, value=result)

    def next_key(self, my_dict, current_key):
        keys = list(my_dict.keys())
        if current_key not in keys:
            return None  # 如果当前键不在字典中，返回None
        current_index = keys.index(current_key)
        if current_index + 1 < len(keys):
            return keys[current_index + 1]  # 返回下一个键
        else:
            return None  # 如果当前键是最后一个，返回None


if __name__ == '__main__':
    unittest.main()
