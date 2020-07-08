
import requests
import datetime
import yaml
import os

class Hilan:

    def __init__(self):
        self.session = requests.Session()
        self.config = {}

    def execute(self):
        if self.load_config(yaml.load(open('conf.yaml', 'r'), Loader=yaml.FullLoader)):
            if self.login():
                self.download()
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
        if failure:
            print("Login failed. Please make sure the credentails in conf.yaml are correct and try again.")
            if captcha:
                print("You also need to go to the Hilan website and solve a captcha challenge.")
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

    def get_last_month(self):
        today = datetime.date.today()
        first = today.replace(day=1)
        return first - datetime.timedelta(days=1)


if __name__ == "__main__":
    h = Hilan()
    h.execute()
