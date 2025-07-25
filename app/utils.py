from threading import Thread

from flask import render_template, url_for, current_app

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email

from app import Config as config


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

