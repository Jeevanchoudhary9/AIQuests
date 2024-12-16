from imports import *


def send_email(to_email, subject, html_content,attachment=None):
    # Gmail SMTP server details
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # Gmail SMTP port

    # Sender's Gmail address and password
    sender_email = 'ai.aiquest@gmail.com' #enter your email
    sender_password = 'stpa vqvq oqog fykk' #enter code > you can get it at https://myaccount.google.com/apppasswords or search for "app password" in google account > create a new app code > format "wxyz wxyz wxyz wxyz" > enter it here

    # Create a MIME multipart message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    if attachment:
        # Attach file
        # part = MIMEBase('application', 'octet-stream')
        # part.set_payload(open(attachment, 'rb').read())
        # encoders.encode_base64(part)
        # part.add_header('Content-Disposition', f'attachment; filename={attachment}')
        # msg.attach(part)

        pdf_part = MIMEApplication(attachment, _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment', filename='report.pdf')
        msg.attach(pdf_part)


    # Attach HTML content
    msg.attach(MIMEText(html_content, 'html','utf-8'))

    

    # Connect to Gmail's SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Start TLS encryption
    server.login(sender_email, sender_password)  # Login to Gmail

    # Send email
    server.sendmail(sender_email, to_email, msg.as_string())

    # Close SMTP connection
    server.quit()




@app.route("/trigger/<string:redirect_url>/<string:message_title>/<string:message_body>")
def trigger_notification(redirect_url, message_title, message_body):
    # Flash the message with the provided title and body
    flash(['Background process completed!', 'success', message_title, message_body])
    try:
        # Redirect to the specified route
        return redirect(url_for(redirect_url))
    except Exception as e:
        # Handle invalid redirect URL gracefully
        return f"Error: {e}", 400

# @app.route('/check_notification/<int:question_id>', methods=['GET'])
# def check_notification(question_id):
#     print("Checking notification for question ID:", question_id)
#     if question_id in notification_data:
#         # Return the notification data and remove it after sending
#         return jsonify(notification_data.pop(question_id))
#     return jsonify({"status": "pending"})

# Simulating notifications
notifications = [
    # {"title": "New Notification", "body": "You have a new message.", "redirect_url": "/"},
    # {"title": "Update Available", "body": "A new update is available for your app."}
]

@app.route('/check_notifications')
def check_notifications():
    if notifications:
        # Pop the first notification from the list
        notification = notifications.pop(0)
        return jsonify({"notifications": [notification]})
    else:
        # If there are no notifications, return an empty list
        return jsonify({"notifications": []})

