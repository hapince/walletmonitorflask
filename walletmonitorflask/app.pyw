import time
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for
import threading

app = Flask(__name__)

smtp_server = "smtp.gmail.com"
smtp_port = 465
sender_email = "happy.prince.max@gmail.com" #your email
password = "****" # use your own password

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def send_email(token_data, receiver_email):
    try:
        html_content = "<h2>KRC-20 Token 监控通知</h2><table border='1'><tr><th>Token 名称</th><th>数量</th></tr>"
        for token, amount in token_data.items():
            html_content += f"<tr><td>{token}</td><td>{amount}</td></tr>"
        html_content += "</table>"

        msg = MIMEText(html_content, "html")
        msg['Subject'] = 'KRC-20 Token 监控通知'
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"发送邮件时出错: {e}")

def scrape_tokens(address, receiver_email):
    url = f"https://kasplex.org/Currency?address={address}"
    driver.get(url)

    try: 
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ant-table-tbody'))
        )
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tokens_table_body = soup.find('tbody', class_='ant-table-tbody')

        if tokens_table_body:
            token_data = {}
            for row in tokens_table_body.find_all('tr', class_='ant-table-row ant-table-row-level-0'):
                token_name_with_span = row.find('td', class_='ant-table-cell searchCell').get_text(strip=True)
                token_name = token_name_with_span.split('Fair Mint')[0].strip()
                token_amount_str = row.find_all('td', class_='ant-table-cell deployTime')[1].get_text(strip=True)
                token_amount_str = ''.join(filter(str.isdigit, token_amount_str))
                token_amount = int(token_amount_str) / 10**8 if token_amount_str else 0

                token_data[token_name] = token_amount
            send_email(token_data, receiver_email)
            return token_data
        else:
            print("没找到")
            return {}

    except Exception as e:
        print(f"发生错误: {e}")
        return {}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        address = request.form['address']
        receiver_email = request.form['receiver_email']

        thread = threading.Thread(target=start_monitoring, args=(address, receiver_email), daemon=True)
        thread.start()

        return redirect(url_for('index'))

    return render_template('index.html')

def start_monitoring(address, receiver_email):
    while True:
        token_data = scrape_tokens(address, receiver_email)
        time.sleep(60)

if __name__ == '__main__':
    app.run(debug=True)