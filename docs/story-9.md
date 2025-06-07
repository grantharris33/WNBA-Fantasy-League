# Story 9: Implement Email Service

**Priority**: P2 - Important
**Dependencies**: Story 2 (Notifications)

## Overview
The email service is referenced throughout the codebase but not implemented. This is needed for user verification, password resets, and important notifications.

## Acceptance Criteria
1. Email service can send transactional emails
2. User verification emails work end-to-end
3. Password reset flow implemented
4. Email templates are responsive and branded
5. Email sending is queued and resilient
6. Development uses email preview/logging

## Technical Tasks

### Backend Implementation

#### 1. Create Email Service
```python
# app/services/email.py
class EmailService:
    - [ ] Configure email provider (SendGrid/AWS SES/SMTP)
    - [ ] send_email(to, subject, html, text)
    - [ ] send_verification_email(user)
    - [ ] send_password_reset_email(user, token)
    - [ ] send_welcome_email(user)
    - [ ] send_league_invite_email(email, league, invite_code)
    - [ ] send_trade_notification_email(user, trade)
    - [ ] send_draft_reminder_email(user, draft)
```

#### 2. Create Email Templates
```python
# app/templates/emails/
- [ ] base.html - Base email template with branding
- [ ] verification.html - Email verification
- [ ] password_reset.html - Password reset
- [ ] welcome.html - Welcome new user
- [ ] league_invite.html - League invitation
- [ ] notification.html - Generic notification
```

#### 3. Add Email Queue System
```python
# app/services/email_queue.py
- [ ] Queue email for sending
- [ ] Retry failed emails
- [ ] Track email status
- [ ] Handle rate limiting
```

### Configuration (4 hours)

#### 1. Email Provider Setup
```python
# Environment variables
EMAIL_PROVIDER=smtp  # or ses

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<password>

FROM_EMAIL=noreply@wnbafantasy.com
FROM_NAME=WNBA Fantasy League
```

#### 2. Development Email Setup
```python
# For development - log emails instead of sending
if settings.ENVIRONMENT == "development":
    - [ ] Log emails to console
    - [ ] Save emails to local directory
    - [ ] Use MailHog for local SMTP
```

### API Integration

#### 1. Update User Endpoints
```python
# app/api/users.py
- [ ] Add email verification endpoint
- [ ] Add resend verification endpoint
- [ ] Add password reset request endpoint
- [ ] Add password reset confirm endpoint
```

#### 2. Update Profile Endpoints
```python
# app/api/profile.py
- [ ] Fix email update to send verification
- [ ] Add email preference settings
```

## Email Templates Design

### Base Template Structure
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Responsive email styles */
        .container { max-width: 600px; margin: 0 auto; }
        .header { background: #FF6B6B; color: white; padding: 20px; }
        .content { padding: 20px; }
        .button {
            background: #FF6B6B;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WNBA Fantasy League</h1>
        </div>
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        <div class="footer">
            <p>&copy; 2024 WNBA Fantasy League. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

### Email Types and Triggers

1. **Transactional Emails** (Must Send)
   - Email verification
   - Password reset
   - Email change confirmation

2. **Notification Emails** (User Preference)
   - League invitations
   - Trade offers
   - Draft reminders
   - Weekly summaries

3. **Marketing Emails** (Future)
   - Season start announcements
   - Feature updates
   - Tips and strategies

## Testing Requirements
- [ ] Unit tests for email service
- [ ] Template rendering tests
- [ ] Email queue tests
- [ ] Integration tests for email flows
- [ ] Test email preview in development

## Security Considerations
- [ ] Rate limit email sending
- [ ] Validate email addresses
- [ ] Secure token generation
- [ ] Prevent email enumeration
- [ ] SPF/DKIM configuration

## Error Handling
- [ ] Graceful failure if email service down
- [ ] User notification of email failures
- [ ] Admin alerts for systemic issues
- [ ] Retry logic with backoff

## Development Tools
```bash
# Email preview
/api/v1/admin/email-preview/{template}
```

## Definition of Done
- Email service integrated and configured
- All email templates created and tested
- Verification flow works end-to-end
- Password reset flow works end-to-end
- Emails render correctly on mobile
- Development email preview working
- All tests pass
- Documentation updated