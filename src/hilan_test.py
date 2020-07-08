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
        self.assertEqual(output, 'Login failed. Please make sure the credentails in conf.yaml are correct and try again.\nYou also need to go to the Hilan website and solve a captcha challenge.')

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



    def test_load_config(self):
        h = hilan.Hilan()
        self.assertTrue(h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.', 'format': '%d%Y'}))
        self.assertFalse(h.load_config({'orgId': 123, 'username': 'abc', 'password': 'xyz', 'folder': '.'}))


if __name__ == '__main__':
    unittest.main()
