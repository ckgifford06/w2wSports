import sqlite3, smtplib, os
from email.mime.text import MIMEText

DB_PATH = "emails.db"

def send_daily_email():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email FROM subscribers WHERE verified = 1")
    subscribers = [row[0] for row in c.fetchall()]
    conn.close()

    if not subscribers:
        return

    msg = MIMEText("Good morning Eagles! Here’s your daily update.")
    msg["Subject"] = "Daily W2W Sports / BC Textbook Update"
    msg["From"] = "you@yourdomain.com"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
        for email in subscribers:
            msg["To"] = email
            server.send_message(msg)
            print(f"Sent to {email}")

if __name__ == "__main__":
    send_daily_email()
