# currency-rate-monitor

Python app for monitoring currency rates and configured amount value changes.
Sends statistics and a graph with rate history to configured email. Fetches
rates from TransferWise.

# Usage

1. Setup requirements and configuration:

        pip install --requirement=requirements.txt
        cp conf-example.py conf.py

2. Change configuration in `conf.py`
3. Launch the script:

        python currency-rate-monitor.py

# Example

Here's how the email looks:

![Screenshot of example email](docs/example-email.png)
