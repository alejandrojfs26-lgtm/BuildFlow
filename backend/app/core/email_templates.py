from app.core.config import settings


def welcome_template(name: str, email: str) -> tuple[str, str]:
    subject = f"Welcome to {settings.app_name}"
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h2>Welcome to {settings.app_name}!</h2>
  <p>Hi {name},</p>
  <p>Your account has been created successfully.</p>
  <p>Email: {email}</p>
  <p>You can now log in and start managing your construction projects.</p>
  <br>
  <p>The {settings.app_name} Team</p>
</body>
</html>
"""
    return subject, body


def password_reset_template(name: str, token: str) -> tuple[str, str]:
    subject = f"{settings.app_name} — Password Reset"
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h2>Password Reset</h2>
  <p>Hi {name},</p>
  <p>Use the token below to reset your password:</p>
  <p><code>{token}</code></p>
  <p>This token expires in 1 hour.</p>
  <br>
  <p>The {settings.app_name} Team</p>
</body>
</html>
"""
    return subject, body


def report_approved_template(worker_name: str, project_name: str, date: str) -> tuple[str, str]:
    subject = f"{settings.app_name} — Daily Report Approved"
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
  <h2>Daily Report Approved</h2>
  <p>Hi {worker_name},</p>
  <p>
    Your daily report for <strong>{project_name}</strong>
    on <strong>{date}</strong> has been approved.
  </p>
  <br>
  <p>The {settings.app_name} Team</p>
</body>
</html>
"""
    return subject, body
