# Hilan Payslip
![Build](https://github.com/talsalmona/hilan/workflows/Build/badge.svg)

Download your Hilan payslip from CLI


## Usage

Choose one of the two methods below to download your payslip for the last month.


### Precompiled for MacOS
1. Download the [latest release](https://github.com/talsalmona/hilan/releases/latest)
2. Create a conf.yaml file in the same folder as the downloaded executable
3. Run ``` ./hilan ```

* You may need to go to the "Security & Privacy" settings on your mac and allow the app to run. This is usually a one time step.
* You may need to ``` chmod +x ``` the executable before running.

### From Source
1. Install python 3.6+ and pip
2. Clone this repo
3. Optionally, create a virtualenv
4. Install the depenencies
``` pip install -r requirements.txt ```
5. Enter your credentials and other configurations in conf.yaml
6. Run
``` python src/hilan.py ```
