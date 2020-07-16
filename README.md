# Hilan Payslip
![Build](https://github.com/talsalmona/hilan/workflows/Build/badge.svg)

Download your Hilan payslip from CLI.
Bonus: it will compare the last two salaries to see there are no large gaps and will alert you if there is.


## Usage

Choose one of the two methods below to download your payslip for the last month.


### Binary for MacOS
1. Download the [latest release](https://github.com/talsalmona/hilan/releases/latest)
2. Rename conf-example.yaml to conf.yaml and fill in your credential and other settings.
3. Run ``` ./hilan ```

* You may need to go to the "Security & Privacy" settings on your mac and allow the app to run. This is usually a one time step.
* You may need to ``` chmod +x ``` the executable before running.

### From Source
1. Install python 3.6+ and pip
2. Clone this repo
3. Optionally, create a virtualenv
4. Install the depenencies
``` pip install -r requirements.txt ```
5. Rename conf-example.yaml to conf.yaml and fill in your credential and other settings.
6. Run
``` python src/hilan.py ```
