
import requests
import datetime
from dateutil.relativedelta import relativedelta
import yaml
import os
from bs4 import BeautifulSoup
import re
import click

class Hilan:

    def __init__(self, lookback, private):
        self.month_delta = lookback if lookback else 0
        self.private = private
        self.session = requests.Session()
        self.config = {}

    def execute(self):
        if self.load_config(yaml.load(open('conf.yaml', 'r'), Loader=yaml.FullLoader)):
            self.orgId = self.fetch_orgId()
            if (self.orgId > 0):
                if self.login():
                    (file_name, success) = self.download()
                    if success:
                        self.compare_months()

    def load_config(self, config):
        if all (key in config for key in ("subdomain", "username", "password", "folder", "format")):
            self.config = config
            return True
        else:
            print("Some config keys are missing")
        return False

    def fetch_orgId(self):
        url = f'https://{self.config["subdomain"]}.hilan.co.il'
        response = requests.get(url)
        num = re.findall(r'{\\"OrgId\\":\\"(\d+)\\"', response.text)
        if len(num) == 1: return int(num[0])
        return -1



    def login(self):
        post_data = {key: self.config[key] for key in ('username','password') if key in self.config}
        post_data['orgId'] = self.orgId
        response = self.session.post(f'https://{self.config["subdomain"]}.hilan.co.il/HilanCenter/Public/api/LoginApi/LoginRequest', data=post_data)

        json_data = response.json()
        failure = json_data.get('IsFail', False)
        captcha = json_data.get('IsShowCaptcha', False)
        temp_error = json_data.get('Code', 0) == 18 # Temporary login errror. Hilan says: "Try again later"
        change_password = json_data.get('Code', 0) == 6 # Need to change password
        error_message = json_data.get('ErrorMessage', '')
        if failure:
            if captcha:
                print("Login failed. You need to go to the Hilan website and solve a captcha challenge before trying again.")
            elif temp_error:
                print("There was a temporary login error. Please try again in a few minutes.")
            elif change_password:
                print("You need to change your password. Please do so on the Hilan website.")
            else:
               print("Login failed. Please make sure the credentails in conf.yaml are correct and try again.")
               print("Hilan Message:")
               self.rtl_print(error_message)

            return False
        return True

    def download(self):
        last_month = self.get_last_month()
        print(last_month.strftime('Getting salary for %B %Y'))

        request_date = last_month.strftime("%m/%Y")
        pdf_url = f'https://{self.config["subdomain"]}.hilan.co.il/Hilannetv2/PersonalFile/PdfPaySlip.aspx?Date=01/{request_date}&UserId={self.orgId}{self.config["username"]}'
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
        response = self.session.post(f'https://{self.config["subdomain"]}.hilan.co.il/Hilannetv2/PersonalFile/SalaryAllSummary.aspx', data=post_data)
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
            two_months_salary = self.extract_number_from_cell(table[0][1])
            last_month_salary = self.extract_number_from_cell(table[0][2])
            diff = 100 * abs(last_month_salary - two_months_salary) / two_months_salary
            if (diff > 1):
                print("There is a large gap from the previous salary, please check your payslip.")
                print("The %s sallary was %s while %s was %s" % (
                    two_months_ago.strftime("%B"),
                    self.mask_salary("{:,}".format(two_months_salary)),
                    last_month.strftime("%B"),
                    self.mask_salary("{:,}".format(last_month_salary))))
                return (last_month_salary, False)
            else:
                print("The %s salary was %s" % (last_month.strftime("%B"), self.mask_salary("{:,}".format(last_month_salary))))
            return (last_month_salary, True)
        else:
            print("Could not fetch the salary summary")
            return (-1, False)

    def rtl_print(self, message):
        print(message[::-1])

    def is_not_valid_pdf(self, content):
        pdf_magic = bytearray(b'\x25\x50\x44\x46') #%PDF in ascii
        file_magic = content[0:4]
        if (file_magic != pdf_magic):
            return True
        return False

    def extract_number_from_cell(self, str):
        if str == '': return 1
        num = re.findall(r'\d+', str)[0]
        return int(num)


    def get_last_month(self, delta=1):
        delta += self.month_delta
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_month = first_day - relativedelta(months=delta)
        return last_month

    def mask_salary(self, salary):
        if self.private:
            return re.sub(r'[0-9]+,', '**,', salary)
        return salary


@click.command()
@click.argument('lookback', default=0, type=click.INT)
@click.option('-p', '--private', default=False, is_flag=True, help='If added, the salary sums will not be printed to console.')
def execute(lookback, private):
    """Download the salary file for the past <LOOKBACK> months.

    LOOKBACK is an optional parameter you can provide to download older months.
    For example running 'hilan 3' will download the salary file for 3 months ago.
    """
    h = Hilan(lookback, private)
    h.execute()

if __name__ == "__main__":
    execute()
