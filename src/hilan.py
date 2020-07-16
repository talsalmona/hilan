
import requests
import datetime
import yaml
import os
from bs4 import BeautifulSoup
import re

class Hilan:

    def __init__(self):
        self.session = requests.Session()
        self.config = {}

    def execute(self):
        if self.load_config(yaml.load(open('conf.yaml', 'r'), Loader=yaml.FullLoader)):
            if self.login():
                self.download()
                self.compare_months()
        else:
            exit(1)

    def load_config(self, config):
        if all (key in config for key in ("orgId", "username", "password", "folder", "format")):
            self.config = config
            return True
        else:
            print("Some config keys are missing")
        return False

    def login(self):
        post_data = {key: self.config[key] for key in ('orgId','username','password') if key in self.config}
        response = self.session.post('https://nextage.net.hilan.co.il/HilanCenter/Public/api/LoginApi/LoginRequest', data=post_data)

        json_data = response.json()
        failure = json_data.get('IsFail', False)
        captcha = json_data.get('IsShowCaptcha', False)
        temp_error = json_data.get('Code', 0) == 18 # Temporary login errror. Hilan says: "Try again later"
        if failure:
            if captcha:
                print("You need to go to the Hilan website and solve a captcha challenge before trying again.")
            elif temp_error:
                print("There was a temporary login error. You should try again in a few minutes.")
            else:
               print("Login failed. Please make sure the credentails in conf.yaml are correct and try again.")

            return False
        return True

    def download(self):
        last_month = self.get_last_month()
        request_date = last_month.strftime("%m/%Y")
        pdf_url = f'https://nextage.net.hilan.co.il/Hilannetv2/PersonalFile/PdfPaySlip.aspx?Date=01/{request_date}&UserId={self.config["orgId"]}{self.config["username"]}'
        response = self.session.get(pdf_url)

        file_name = os.path.join(self.config['folder'], last_month.strftime(self.config['format']))
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print(f'Saved payslip to {file_name}')
        return file_name

    def compare_months(self):
        last_month = self.get_last_month().strftime("%m/%Y")
        two_months_ago = self.get_last_month(2).strftime("%m/%Y")
        request_date = "01/%s,0,30/%s,0" % (two_months_ago, last_month)

        post_data = {'__DatePicker_State': request_date}
        response = self.session.post('https://nextage.net.hilan.co.il/Hilannetv2/PersonalFile/SalaryAllSummary.aspx', data=post_data)
        soup = BeautifulSoup(response.content, "html.parser")
        trs = soup.select('tr[class=RSGrid]') + soup.select('tr[class=ARSGrid]')

        table = []
        for tr in trs:
            tds = tr.find_all('td')
            row = []
            for td in tds:
                row.append(td.text)
            table.append(row)

        last_month_salary = self.extract_number(table[0][1])
        this_month_salary = self.extract_number(table[0][2])
        diff = 100 * abs(this_month_salary - last_month_salary) / last_month_salary
        if (diff > 1):
            print("There is a large gap from the previous salary, please check your payslip.")
            print("Last month's sallary was %s, this month is %s" % ("{:,}".format(last_month_salary), "{:,}".format(this_month_salary)))
        else:
            print("This months salary was %s" % "{:,}".format(this_month_salary))
        return this_month_salary

    def extract_number(self, str):
        num = re.findall(r'\d+', str)[0]
        return int(num)


    def get_last_month(self, delta=1):
        today = datetime.date.today()
        first_day = today.replace(day=1)
        month = today.month-delta
        last_month = today.replace(month=month)
        return last_month


if __name__ == "__main__":
    h = Hilan()
    h.execute()
