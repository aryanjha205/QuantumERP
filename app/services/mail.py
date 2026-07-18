import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_otp_email(to_email: str, otp: str) -> None:
    """
    Send OTP verification email using standard library smtplib (No external Node.js nodemailer wrapper needed,
    since we are in a Python FastAPI backend environment).
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be configured to send OTP emails")

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = f"QuantURP — {otp} is your Sign Up verification code"

    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #FAFAFA; color: #212121; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; background-color: #FFFFFF; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #EEEEEE;">
          <h2 style="color: #00C853; text-align: center; margin-top: 0; font-family: 'Outfit', sans-serif;">QuantURP</h2>
          <hr style="border: 0; border-top: 1px solid #EEEEEE; margin: 20px 0;">
          <p>Hello,</p>
          <p>Thank you for choosing QuantURP. Use the following One-Time Password (OTP) to verify your signup request:</p>
          <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 32px; font-weight: bold; color: #00C853; letter-spacing: 6px; background-color: #e8f5e9; padding: 12px 24px; border-radius: 8px; display: inline-block; border: 1px solid #c8e6c9;">{otp}</span>
          </div>
          <p style="font-size: 13px; color: #757575;">This OTP is valid for 10 minutes. If you did not request this, please ignore this email.</p>
          <hr style="border: 0; border-top: 1px solid #EEEEEE; margin: 20px 0;">
          <p style="font-size: 11px; color: #9E9E9E; text-align: center;">QuantURP — AI-Native Voice ERP Platform</p>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
      server.starttls()
      server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
      server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
