# plextrac-nessus-import-automation
Simple python setup for automating login, client/report creation, and data imports for nessus XML files.

## Requirements

* Python3+ (Tested with Python 3.8)
* pip
* pipenv


## Usage:

```bash
git clone repository
cd /path/to/repository
pipenv install -r requirements.txt
pipenv shell
python import-nessus-scan.py
```

Once the script runs you'll be prompted for information, upon completion, you should have a successful import.

### Required information:
* PlexTrac Top Level Domain e.g. https://yourapp.plextrac.com
* Username
* Password
* A valid Nessus XML export

### Optional information:
* MFA Token (if enabled)
* Pre-existing clientId from your PlexTrac instance
* Pre-existing reportId from your PlexTrac instance

#### If creating a new client:
* Client description
* Client name
* Client point of contact
* Client point of contact e-mail

#### If creating a new report:
* The nessus filename you specify will be used as the report name

If you opt to create a new client and report, you will simply need to provide values for each of the questions you get asked and a new client/report will be created, then the provided XML data will be imported into the new report.
 