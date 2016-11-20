#!/usr/bin/env python2

from __future__ import print_function

import os
import sys
import datetime
import time
from collections import namedtuple

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.header import Header
from email.Utils import formatdate
import smtplib

import requests

BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)

import conf

TRANSFERWISE_URL='https://api.transferwise.com/v1/rates?source={from_currency}&target={to_currency}&from={from_date}&to={to_date}&group=day'
TRANSFERWISE_DATE_FORMAT='%Y-%m-%dT%H:%M:%S+0000'

# https://google-developers.appspot.com/chart/image/docs/chart_params
GOOGLE_CHART_URL='http://chart.googleapis.com/chart?cht=lc&chs={size}&chxt=x,y&chm=N*c{currency}4z*,000000,00000,-1,11&chxt=x,y&chds={rate_min},{rate_max}&chxr=1,{rate_min},{rate_max}&chxl=0:|{x_labels}&chd=t:{data}'

EMAIL_DATE_FORMAT='%B %d, %Y'
EMAIL_BODY_TEMPLATE="""<html><body>
<table>
<tr><td>Start rate ({start_rate_date}):</td><td>1 {from_currency} = {start_rate} {to_currency}</td></tr>
<tr><td>Period start rate ({period_start_date}):</td><td>1 {from_currency} = {period_start_rate} {to_currency}</td></tr>
<tr><td>Period minimum rate ({min_rate_date}):</td><td>1 {from_currency} = {min_rate} {to_currency}</td></tr>
<tr><td>Period maximum rate ({max_rate_date}):</td><td>1 {from_currency} = {max_rate} {to_currency}</td></tr>
<tr><td>Yesterday's rate ({yesterday_rate_date}):</td><td>1 {from_currency} = {yesterday_rate} {to_currency}</td></tr>
<tr><td>Today's rate ({today_rate_date}):</td><td>1 {from_currency} = {today_rate} {to_currency}</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td>Rate change since start</td><td>{rate_change_since_start} {to_currency}</td></tr>
<tr><td>Rate change since period start</td><td>{rate_change_since_period_start} {to_currency}</td></tr>
<tr><td>Rate change compared with minimum</td><td>{rate_change_compared_with_min} {to_currency}</td></tr>
<tr><td>Rate change compared with maximum</td><td>{rate_change_compared_with_max} {to_currency}</td></tr>
<tr><td>Rate change since yesterday&nbsp;</td><td>{rate_change_since_yesterday} {to_currency}</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td>Amount</td><td>{amount} {from_currency}</td></tr>
<tr><td>Start value</td><td>{start_value} {to_currency}</td></tr>
<tr><td>Period start value</td><td>{period_start_value} {to_currency}</td></tr>
<tr><td>Period minimum value</td><td>{min_value} {to_currency}</td></tr>
<tr><td>Period maximum value</td><td>{max_value} {to_currency}</td></tr>
<tr><td>Yesterday's value</td><td>{yesterday_value} {to_currency}</td></tr>
<tr><td>Today's value</td><td>{today_value} {to_currency}</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td>Gain/loss since start</td><td>{gain_since_start} {to_currency}</td></tr>
<tr><td>Gain/loss since period start</td><td>{gain_since_period_start} {to_currency}</td></tr>
<tr><td>Gain/loss compared with minimum</td><td>{gain_compared_with_min} {to_currency}</td></tr>
<tr><td>Gain/loss compared with maximum</td><td>{gain_compared_with_max} {to_currency}</td></tr>
<tr><td>Gain/loss since yesterday</td><td>{gain_since_yesterday} {to_currency}</td></tr>
</table>
<br />
<img src="cid:image1"><br />
</body></html>
"""

Rate = namedtuple('Rate', ('rate', 'date'))

def main():
    to_date = datetime.date.today()
    from_date = to_date - datetime.timedelta(days=conf.DAYS_BACK)
    rates = load_rates(from_date, to_date)
    chart_url = make_chart(rates)
    image = make_mimeimage(chart_url)
    html = create_email_body_html(rates)
    result = send_mail(conf.SMTP_SERVER, conf.EMAIL_FROM, conf.EMAIL_TO,
            conf.EMAIL_SUBJECT, html, image)
    if result:
        for recp in result.keys():
            print("Send mail to {} failed: {}:{}".format(conf.EMAIL_TO,
                    result[recp][0], result[recp][1]), file=sys.stderr)
    # To see the chart in browser:
    # import webbrowser
    # webbrowser.open(chart_url)

def load_rates(from_date, to_date):
    from_currency = conf.FROM_CURRENCY
    to_currency = conf.TO_CURRENCY
    rates = requests.get(TRANSFERWISE_URL.format(**locals())).json()
    return [_make_rate(rate) for rate in rates]

def make_chart(rates):
    data = [rate.rate for rate in rates]
    data.reverse()
    rate_min = min(data)
    rate_max = max(data)
    data = ','.join(str(d) for d in data)
    size = conf.CHART_IMAGE_SIZE
    currency = conf.TO_CURRENCY
    dates = [rate.date.strftime('%d.%m') for rate in rates]
    dates.reverse()
    x_labels = '|'.join(dates)
    return GOOGLE_CHART_URL.format(**locals())

def create_email_body_html(rates):
    amount = conf.AMOUNT
    from_currency = conf.FROM_CURRENCY
    to_currency = conf.TO_CURRENCY

    start_rate = conf.START_RATE
    start_rate_date = _to_datestring(conf.START_RATE_DATE)
    period_start_rate = rates[-1].rate
    period_start_date = _to_datestring(rates[-1].date)
    min_rate = min(rates)
    min_rate_date = _to_datestring(min_rate.date)
    min_rate = min_rate.rate
    max_rate = max(rates)
    max_rate_date = _to_datestring(max_rate.date)
    max_rate = max_rate.rate
    today_rate = rates[0].rate
    today_rate_date = _to_datestring(rates[0].date)
    yesterday_rate = rates[1].rate
    yesterday_rate_date = _to_datestring(rates[1].date)

    rate_change_since_yesterday = today_rate - yesterday_rate
    rate_change_since_start = today_rate - start_rate
    rate_change_since_period_start = today_rate - period_start_rate
    rate_change_compared_with_min = today_rate - min_rate
    rate_change_compared_with_max = today_rate - max_rate

    today_value = today_rate * conf.AMOUNT
    start_value = start_rate * conf.AMOUNT
    yesterday_value = yesterday_rate * conf.AMOUNT
    period_start_value = period_start_rate * conf.AMOUNT
    min_value = min_rate * conf.AMOUNT
    max_value = max_rate * conf.AMOUNT

    gain_since_yesterday = today_value - yesterday_value
    gain_since_start = today_value - start_value
    gain_since_period_start = today_value - period_start_value
    gain_compared_with_min = today_value - min_value
    gain_compared_with_max = today_value - max_value

    return EMAIL_BODY_TEMPLATE.format(**locals())

def send_mail(server, send_from, send_to, subject, html, img):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Subject'] = Header(subject, 'utf-8')
    msg['Date'] = formatdate(time.time(), localtime=True)
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    msg.attach(img)
    smtp = smtplib.SMTP(server)
    result = smtp.sendmail(send_from, [send_to, send_from], msg.as_string())
    smtp.close()
    return result

def make_mimeimage(url):
    image_data = requests.get(url)
    img = MIMEImage(image_data.content)
    img.add_header('Content-ID', '<image1>')
    return img

def _make_rate(rate):
    date = datetime.datetime.strptime(rate['time'], TRANSFERWISE_DATE_FORMAT)
    return Rate(rate['rate'], date)

def _to_datestring(date):
    return date.strftime(EMAIL_DATE_FORMAT)

if __name__ == '__main__':
    main()
