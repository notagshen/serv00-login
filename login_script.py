import asyncio
import json
import os
import random
from datetime import datetime, timedelta

import aiofiles
import requests
from pyppeteer import launch

# 从环境变量中获取 Telegram Bot Token、 Chat ID、PUSH_PLUS_TOKEN、WECOM_BOT_TOKEN。
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PUSH_PLUS_TOKEN = os.getenv('PUSH_PLUS_TOKEN')
WECOM_BOT_TOKEN = os.getenv('WECOM_BOT_TOKEN')


def format_to_iso(date):
    return date.strftime('%Y-%m-%d %H:%M:%S')


async def delay_time(ms):
    await asyncio.sleep(ms / 1000)


# 全局浏览器实例
browser = None

# telegram消息
message = 'serv00&ct8自动化脚本运行\n'


async def login(username, password, panel):
    global browser

    page = None  # 确保 page 在任何情况下都被定义
    serviceName = 'ct8' if 'ct8' in panel else 'serv00'
    try:
        if not browser:
            browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])

        page = await browser.newPage()
        url = f'https://{panel}/login/?next=/'
        await page.goto(url)

        username_input = await page.querySelector('#id_username')
        if username_input:
            await page.evaluate('''(input) => input.value = ""''', username_input)

        await page.type('#id_username', username)
        await page.type('#id_password', password)

        login_button = await page.querySelector('#submit')
        if login_button:
            await login_button.click()
        else:
            raise Exception('无法找到登录按钮')

        await page.waitForNavigation()

        is_logged_in = await page.evaluate('''() => {
            const logoutButton = document.querySelector('a[href="/logout/"]');
            return logoutButton !== null;
        }''')

        return is_logged_in

    except Exception as e:
        print(f'{serviceName}账号 {username} 登录时出现错误: {e}')
        return False

    finally:
        if page:
            await page.close()


async def main():
    global message
    message = 'serv00&ct8自动化脚本运行\n'

    try:
        async with aiofiles.open('accounts.json', mode='r', encoding='utf-8') as f:
            accounts_json = await f.read()
        accounts = json.loads(accounts_json)
    except Exception as e:
        print(f'读取 accounts.json 文件时出错: {e}')
        return

    message += f'{len(accounts)}个账号执行结果如下：\n'
    for account in accounts:
        username = account['username']
        password = account['password']
        panel = account['panel']

        serviceName = 'ct8' if 'ct8' in panel else 'serv00'
        is_logged_in = await login(username, password, panel)

        if is_logged_in:
            now_utc = format_to_iso(datetime.utcnow())
            now_beijing = format_to_iso(datetime.utcnow() + timedelta(hours=8))
            success_message = f'{serviceName}账号 {username} 于北京时间 {now_beijing}（UTC时间 {now_utc}）登录成功！'
            message += success_message + '\n'
            print(success_message)
        else:
            message += f'{serviceName}账号 {username} 登录失败，请检查{serviceName}账号和密码是否正确。\n'
            print(f'{serviceName}账号 {username} 登录失败，请检查{serviceName}账号和密码是否正确。')

        delay = random.randint(1000, 8000)
        await delay_time(delay)

    message += f'所有任务已完成！'
    await send_message(message)
    print(f'所有{serviceName}账号登录完成！')


async def send_message(message):
    if TELEGRAM_CHAT_ID:
        send_telegram_message(message)
    if PUSH_PLUS_TOKEN:
        send_push_plus_message(message)
    if WECOM_BOT_TOKEN:
        send_wecom_bot_message(message)


def send_wecom_bot_message(message):
    wx_headers = {
        'Content-Type': 'application/json',
    }

    json_data = {
        'msgtype': 'text',
        'text': {
            'content': f'{message}',
        },
    }

    try:
        response = requests.post(f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_BOT_TOKEN}', headers=wx_headers,
                             json=json_data)
        if response.status_code != 200:
            print(f"发送消息到WeCom_bot失败: {response.text}")
    except Exception as e:
        print(f"发送消息到WeCom_bot时出错: {e}")


def send_push_plus_message(message):
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSH_PLUS_TOKEN,
        "title": "serv00&ct8自动登录通知",
        "content": message
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"发送消息到PushPlus失败: {response.text}")
    except Exception as e:
        print(f"发送消息到PushPlus时出错: {e}")


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'reply_markup': {
            'inline_keyboard': [
                [
                    {
                        'text': '问题反馈❓',
                        'url': 'https://t.me/yxjsjl'
                    }
                ]
            ]
        }
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"发送消息到Telegram失败: {response.text}")
    except Exception as e:
        print(f"发送消息到Telegram时出错: {e}")


if __name__ == '__main__':
    asyncio.run(main())
