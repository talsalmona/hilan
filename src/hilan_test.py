import unittest
import requests
import responses
import sys
import os
from contextlib import contextmanager
from io import StringIO
import hilan

class TestHilan(unittest.TestCase):

    @contextmanager
    def captured_output(self):
        new_out, new_err = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = new_out, new_err
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    def tearDown(self):
        responses.reset()

    @responses.activate
    def test_login_success(self):
        responses.add(responses.POST, 'https://nextage.net.hilan.co.il/HilanCenter/Public/api/LoginApi/LoginRequest', json={'IsFail': False})
        h = hilan.Hilan()
        self.assertTrue(h.login())


    @responses.activate
    def test_login_failure(self):
        responses.add(responses.POST, 'https://nextage.net.hilan.co.il/HilanCenter/Public/api/LoginApi/LoginRequest', json={'IsFail': True})
        h = hilan.Hilan()
        with self.captured_output() as (out, err):
            self.assertFalse(h.login())
        output = out.getvalue().strip()
        self.assertEqual(output, 'Login failed. Please make sure the credentails in conf.yaml are correct and try again.')


    @responses.activate
    def test_login_failure_captcha(self):
        responses.add(responses.POST, 'https://nextage.net.hilan.co.il/HilanCenter/Public/api/LoginApi/LoginRequest', json={'IsFail': True, 'IsShowCaptcha': True})
        h = hilan.Hilan()
        with self.captured_output() as (out, err):
            self.assertFalse(h.login())
        output = out.getvalue().strip()
        self.assertEqual(output, 'Login failed. You need to go to the Hilan website and solve a captcha challenge before trying again.')

    @responses.activate
    def test_login_failure_temporary(self):
        responses.add(responses.POST, 'https://nextage.net.hilan.co.il/HilanCenter/Public/api/LoginApi/LoginRequest', json={'IsFail': True, 'Code': 18})
        h = hilan.Hilan()
        with self.captured_output() as (out, err):
            self.assertFalse(h.login())
        output = out.getvalue().strip()
        self.assertEqual(output, 'There was a temporary login error. You should try again in a few minutes.')

    @responses.activate
    def test_download(self):
        h = hilan.Hilan()
        h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.', 'format': '%Y-%d'})
        last_month = h.get_last_month()
        request_date = last_month.strftime("%m/%Y")
        mock_url = f'https://nextage.net.hilan.co.il/Hilannetv2/PersonalFile/PdfPaySlip.aspx?Date=01/{request_date}&UserId=123abc'
        responses.add(responses.GET, mock_url)

        file_name = h.download()

        self.assertTrue(os.path.exists(file_name))
        os.remove(file_name)

    @responses.activate
    def test_compare_months_large_gap(self):
        h = hilan.Hilan()
        h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.', 'format': '%Y-%d'})
        mock_url = f'https://nextage.net.hilan.co.il/Hilannetv2/PersonalFile/SalaryAllSummary.aspx'
        responses.add(responses.POST, mock_url, body="<table><tr class='RSGrid'><td>sum</td><td class='ARSGrid'>1</td><td class='RSGrid'>2</td></tr></table>")

        with self.captured_output() as (out, err):
            result = h.compare_months()
        output = out.getvalue().strip()
        self.assertEqual(result, 2)
        self.assertEqual(output, 'There is a large gap from the previous salary, please check your payslip.\nLast month\'s sallary was 1, this month is 2')

    @responses.activate
    def test_compare_months_ok(self):
        h = hilan.Hilan()
        h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.', 'format': '%Y-%d'})
        mock_url = f'https://nextage.net.hilan.co.il/Hilannetv2/PersonalFile/SalaryAllSummary.aspx'
        responses.add(responses.POST, mock_url, body="<table><tr class='RSGrid'><td>sum</td><td class='ARSGrid'>1</td><td class='RSGrid'>1</td></tr></table>")

        with self.captured_output() as (out, err):
            result = h.compare_months()
        output = out.getvalue().strip()
        self.assertEqual(output, 'This months salary was 1')

    @responses.activate
    def test_compare_months_fail_fetch(self):
        h = hilan.Hilan()
        h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.', 'format': '%Y-%d'})
        mock_url = f'https://nextage.net.hilan.co.il/Hilannetv2/PersonalFile/SalaryAllSummary.aspx'
        responses.add(responses.POST, mock_url, body="")

        with self.captured_output() as (out, err):
            result = h.compare_months()
        output = out.getvalue().strip()
        self.assertEqual(result, 0)
        self.assertEqual(output, 'Could not fetch the salary summary.')


    def test_load_config(self):
        h = hilan.Hilan()
        self.assertTrue(h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.', 'format': '%d%Y'}))
        self.assertFalse(h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.'}))


if __name__ == '__main__':
    unittest.main()
