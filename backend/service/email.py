import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    """
    Email service for sending various types of emails.
    Handles SMTP configuration and email templates.
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_APP_PASSWORD")
        self.frontend_url = os.getenv("FE_URL", "http://localhost:3000")
        
        if not self.smtp_email or not self.smtp_password:
            raise ValueError("SMTP credentials not configured")

    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            Exception: If email sending fails
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_email
            message["To"] = to_email

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.sendmail(self.smtp_email, to_email, message.as_string())

            return True

        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    def send_signup_verification(
        self, 
        to_email: str, 
        user_name: str, 
        verification_token: str
    ) -> bool:
        """
        Send signup verification email to new users.
        
        Args:
            to_email: User's email address
            user_name: User's name
            verification_token: Email verification token
            
        Returns:
            bool: True if email sent successfully
        """
        verification_url = f"{self.frontend_url}/verify-email?email={to_email}&token={verification_token}"
        
        subject = "Welcome! Please verify your email address"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #4CAF50; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Guerillafi Ai!</h1>
                </div>
                <div class="content">
                    <h2>Hi {user_name},</h2>
                    <p>Thank you for signing up! To complete your registration, please verify your email address by clicking the button below:</p>
                    
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{verification_url}">{verification_url}</a></p>
                    
                    <p>This verification link will expire in 24 hours for security reasons.</p>
                    
                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Guerillafi Ai. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Guerillafi Ai!
        
        Hi {user_name},
        
        Thank you for signing up! To complete your registration, please verify your email address by visiting:
        
        {verification_url}
        
        This verification link will expire in 24 hours for security reasons.
        
        If you didn't create an account with us, please ignore this email.
        
        © 2025 Guerillafi Ai. All rights reserved.
        """
        
        return self._send_email(to_email, subject, html_content, text_content)

    def send_password_reset(
        self, 
        to_email: str, 
        user_name: str, 
        reset_token: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            to_email: User's email address
            user_name: User's name
            reset_token: Password reset token
            
        Returns:
            bool: True if email sent successfully
        """
        reset_url = f"{self.frontend_url}/reset-password?email={to_email}&token={reset_token}"
        
        subject = "Password Reset Request"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #f44336; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {user_name},</h2>
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    
                    <a href="{reset_url}" class="button">Reset Password</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    
                    <p>This reset link will expire in 1 hour for security reasons.</p>
                    
                    <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Guerillafi Ai. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {user_name},
        
        We received a request to reset your password. Please visit the following link to reset it:
        
        {reset_url}
        
        This reset link will expire in 1 hour for security reasons.
        
        If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        
        © 2025 Guerillafi Ai. All rights reserved.
        """
        
        return self._send_email(to_email, subject, html_content, text_content)

    def send_organization_invite(
        self, 
        to_email: str, 
        inviter_name: str, 
        organization_name: str, 
        invite_token: str
    ) -> bool:
        """
        Send organization invitation email.
        
        Args:
            to_email: Invitee's email address
            inviter_name: Name of person sending invite
            organization_name: Name of organization
            invite_token: Invitation token
            
        Returns:
            bool: True if email sent successfully
        """
        invite_url = f"{self.frontend_url}/join-organization?email={to_email}&token={invite_token}"
        
        subject = f"You're invited to join {organization_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #2196F3; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0; 
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Organization Invitation</h1>
                </div>
                <div class="content">
                    <h2>You're Invited!</h2>
                    <p><strong>{inviter_name}</strong> has invited you to join <strong>{organization_name}</strong> on Guerillafi Ai.</p>
                    
                    <a href="{invite_url}" class="button">Accept Invitation</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{invite_url}">{invite_url}</a></p>
                    
                    <p>This invitation will expire in 7 days.</p>
                    
                    <p>If you don't want to join this organization, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Guerillafi Ai. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Organization Invitation
        
        You're Invited!
        
        {inviter_name} has invited you to join {organization_name} on Guerillafi Ai.
        
        To accept the invitation, please visit:
        {invite_url}
        
        This invitation will expire in 7 days.
        
        If you don't want to join this organization, you can safely ignore this email.
        
        © 2025 Guerillafi Ai. All rights reserved.
        """
        
        return self._send_email(to_email, subject, html_content, text_content)


# Create singleton instance
email_service = EmailService()
