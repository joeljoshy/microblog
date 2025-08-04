from threading import Thread

from flask import render_template, url_for, current_app

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from twilio.rest import Client

from app import Config as config

sms_client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def send_async_email(app, msg):
    with app.app_context():
        print("Sending email...")
        try:
            sg = SendGridAPIClient(api_key=config.SENDGRID_API_KEY)
            sg.send(msg)
        except Exception as e:
            app.logger.error(f"Error sending email: {e}")


def send_email(subject, sender, recipients, html_body):
    msg = Mail(
        from_email=sender,
        to_emails=recipients,
        subject=subject,
        html_content=html_body
    )
    app = current_app._get_current_object()
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    reset_url = url_for('reset_password', token=token, _external=True)

    html_context = render_template(
        'email/reset_password_email.html',
        user=user,
        reset_url=reset_url
    )

    subject = "Reset Your Password | Micro Blog"
    sender = config.MAIL_DEFAULT_SENDER
    recipients = user.email

    try:
        send_email(subject, sender, recipients, html_context)
        print(f"Password Reset Email Sent to {user.email}")
    except Exception as e:
        print(f"Failed to send email to {user.email}: {e}")


def send_email_otp(to_email, otp):
    html_content = f"""
      <html>
      <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
          <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
              <h2 style="color: #333;">🔐 OTP Verification</h2>
              <p>Use the following One-Time Password (OTP) to log in:</p>
              <div style="font-size: 24px; font-weight: bold; margin: 20px 0; background-color: #f0f0f0; padding: 15px; text-align: center; border-radius: 6px;">
                  {otp}
              </div>
              <p>This OTP will expire in 5 minutes. If you didn’t request this, you can ignore this email.</p>
              <p style="margin-top: 30px;">Thanks,<br><strong>Your App Team</strong></p>
          </div>
      </body>
      </html>
      """
    sender = config.MAIL_DEFAULT_SENDER

    send_email("OTP | Blog App", sender, to_email, html_content)


def send_sms_otp(contact, otp):
    sms_client.messages.create(
        body=f"Your OTP is: {otp}",
        from_=config.TWILIO_PHONE_NUMBER,
        to=contact
    )