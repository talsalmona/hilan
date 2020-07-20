
import requests
import datetime
from dateutil.relativedelta import relativedelta
import yaml
import os
from bs4 import BeautifulSoup
import re
import click

class Hilan:

    def __init__(self, month):
        self.month = month if month else 0
        self.session = requests.Session()
        self.config = {}

    def execute(self):
        if self.load_config(yaml.load(open('conf.yaml', 'r'), Loader=yaml.FullLoader)):
            if self.login():
                (file_name, success) = self.download()
                if success:
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
                print("Login failed. You need to go to the Hilan website and solve a captcha challenge before trying again.")
            elif temp_error:
                print("There was a temporary login error. Please try again in a few minutes.")
            else:
               print("Login failed. Please make sure the credentails in conf.yaml are correct and try again.")

            return False
        return True

    def download(self):
        last_month = self.get_last_month()
        print(last_month.strftime('Getting salary for %B %Y'))

        request_date = last_month.strftime("%m/%Y")
        pdf_url = f'https://nextage.net.hilan.co.il/Hilannetv2/PersonalFile/PdfPaySlip.aspx?Date=01/{request_date}&UserId={self.config["orgId"]}{self.config["username"]}'
        response = self.session.get(pdf_url)
        if (self.is_not_valid_pdf(response.content)):
            print('Could not download a valid PDF file')
            return ('', False)

        file_name = os.path.join(self.config['folder'], last_month.strftime(self.config['format']))
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print(f'Saved payslip to {file_name}')
        return (file_name, True)

    def compare_months(self):
        last_month = self.get_last_month()
        two_months_ago = self.get_last_month(2)
        request_date = "01/%s,0,30/%s,0" % (two_months_ago.strftime("%m/%Y"), last_month.strftime("%m/%Y"))

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

        if (len(table) > 0 and len(table[0]) == 3):
            two_months_salary = self.extract_number(table[0][1])
            last_month_salary = self.extract_number(table[0][2])
            diff = 100 * abs(last_month_salary - two_months_salary) / two_months_salary
            if (diff > 1):
                print("There is a large gap from the previous salary, please check your payslip.")
                print("The %s sallary was %s while %s was %s" % (
                        two_months_ago.strftime("%B"),
                        "{:,}".format(two_months_salary),
                        last_month.strftime("%B"),
                        "{:,}".format(last_month_salary)))
                return (last_month_salary, False)
            else:
                print("The %s salary was %s" % (last_month.strftime("%B"), "{:,}".format(last_month_salary)))
            return (last_month_salary, True)
        else:
            print("Could not fetch the salary summary")
            return (-1, False)

    def is_not_valid_pdf(self, content):
        pdf_magic = bytearray(b'\x25\x50\x44\x46') #%PDF in ascii
        file_magic = content[0:4]
        if (file_magic != pdf_magic):
            return True

        return False

    def extract_number(self, str):
        if str == '': return 1
        num = re.findall(r'\d+', str)[0]
        return int(num)


    def get_last_month(self, delta=1):
        delta += self.month
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_month = first_day - relativedelta(months=delta)
        return last_month


@click.command()
@click.argument('month', default=0, type=click.INT)
def execute(month):
    """Download the salary file for the past month.

    MONTH is an optional parameter you can provide to download older months.
    For example running 'hilan 3' will download the salary file for 3 months ago.
    """
    h = Hilan(month)
    h.execute()

if __name__ == "__main__":
    execute()
