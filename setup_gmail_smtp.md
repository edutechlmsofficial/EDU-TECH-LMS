# Setup Gmail SMTP Server Configuration for Edu Tech LMS

To configure your Edu Tech LMS app to send confirmation emails using Gmail’s SMTP server, follow these steps:

### SMTP Server Settings

- SMTP Server: smtp.gmail.com
- SMTP Port: 587
- Use TLS: Yes
- SMTP Username: thuvask001@gmail.com
- SMTP Password: lobghmsuvowocqwe

### Notes:

1. **App Passwords**:
   - For enhanced security, create an "App Password" in your Google Account settings.
   - To do this, go to your Google Account > Security > App passwords.
   - Generate a new password for “Mail” and use it as the SMTP_PASSWORD.
   
2. **Less Secure Apps**:
   - If not using 2FA and App Passwords, you may need to enable “Less secure app access” in Google Account Security settings.  
   - This is less secure; App Passwords are recommended.

3. **Environment Variables**:
   - Set the following environment variables in your system or in a `.env` file:
     ```
     SMTP_SERVER=smtp.gmail.com
     SMTP_PORT=587
     SMTP_USERNAME=thuvask001@gmail.com

     SMTP_PASSWORD=lobghmsuvowocqwe
     EMAIL_SENDER=thuvask001@gmail.com
     ```
4. **Restart the App**:
   - After setting environment variables, restart the Edu Tech LMS app to apply changes.

### Testing

- After configuration, register a new user and confirm you receive the confirmation email.
- Check the spam/junk folder if you do not see the email in your inbox.

If you want, I can help you set the environment variables or integrate a .env file loader like python-dotenv for better configuration management.

Please let me know how you want to proceed.
