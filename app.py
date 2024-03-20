from datetime import datetime
from flask import Flask, render_template, request
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# MySQL configurations
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin',
    'database': 'hospital',
}

# Email configurations
email_config = {
    'smtp_server': 'smtp.gmail.com',  # SMTP server for Gmail
    'smtp_port': 587,  # Port number for TLS encryption
    'sender_email': 'abc@gmail.com',
    'sender_password': 'password your mail',#open mail goto google in security search add app in add name after get password if no get then msg me
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


def create_appointment_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    create_appointment_table_query = ("""
    CREATE TABLE IF NOT EXISTS appointment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        service VARCHAR(255) NOT NULL,
        doctor VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time VARCHAR(255) NOT NULL
    )
    """)
    create_contact_table_query = ("""
    CREATE TABLE IF NOT EXISTS contact (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        subject VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        message TEXT NOT NULL
    )
    """)
    cursor.execute(create_appointment_table_query)
    cursor.execute(create_contact_table_query)
    conn.commit()
    cursor.close()
    conn.close()


create_appointment_tables()


def create_signup():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""create table if not exists signup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL
    )""")

    conn.commit()
    cursor.close()
    conn.close()


create_signup()


def send_email(recipient_email, subject, message):
    msg = MIMEMultipart()
    msg['From'] = email_config['sender_email']
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    # Connect to SMTP server
    server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
    server.starttls()
    server.login(email_config['sender_email'], email_config['sender_password'])

    # Send email
    text = msg.as_string()
    server.sendmail(email_config['sender_email'], recipient_email, text)

    # Quit server
    server.quit()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/appointment', methods=['GET', 'POST'])
def appointments():
    if request.method == 'POST':
        service = request.form['service']
        doctor = request.form['doctor']
        name = request.form['name']
        email = request.form['email']
        appointment_date_str = request.form['appointmentDate']
        appointment_date_obj = datetime.strptime(appointment_date_str, '%m/%d/%Y')

        # Check if the selected date is Sunday
        if appointment_date_obj.weekday() == 6:  # Sunday
            # Send notification email for Sunday appointments
            sunday_subject = "Sunday Appointment Notification"
            sunday_message = f"Dear {name},\n\nWe are closed on Sundays. Please schedule your appointment on a working day (Monday to Saturday).\n\nBest regards,\nThe Hospital Team"
            send_email(email, sunday_subject, sunday_message)

            return "We are closed on Sundays. Please schedule your appointment on a working day (Monday to Saturday)."

        appointment_date = appointment_date_obj.strftime('%Y-%m-%d')

        appointment_time_str = request.form['appointmentTime']
        appointment_time_obj = datetime.strptime(appointment_time_str, '%I:%M %p').time()

        # Define working hours
        working_start_time = datetime.strptime('6:00 AM', '%I:%M %p').time()
        working_end_time = datetime.strptime('10:00 PM', '%I:%M %p').time()

        # Check if the appointment time is within working hours
        if not (working_start_time <= appointment_time_obj <= working_end_time):
            # Send notification email for non-working hours appointments
            non_working_subject = "Non-Working Hours Appointment Notification"
            non_working_message = f"Dear {name},\n\nWe've noticed that your requested appointment time is outside our operational hours, which are from 6:00 AM to 10:00 PM. To better serve you, kindly reschedule your appointment within these hours.\n\nBest regards,\nThe Hospital Team"
            send_email(email, non_working_subject, non_working_message)

            return "We've noticed that your requested appointment time is outside our operational hours, which are from 6:00 AM to 10:00 PM. To better serve you, kindly reschedule your appointment within these hours."

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO appointment (service, doctor, name, email, appointment_date, appointment_time) VALUES (%s, %s, %s, %s, %s, %s)",
                (service, doctor, name, email, appointment_date, appointment_time_obj))

            conn.commit()
            cursor.close()
            conn.close()

            # Send appointment confirmation email to the user
            user_subject = "Appointment Confirmation"
            user_message = f"Dear {name},\n\nYour appointment has been successfully scheduled.\n\nService: {service}\nDoctor: {doctor}\nDate: {appointment_date}\nTime: {appointment_time_obj.strftime('%I:%M %p')}\n\nWe look forward to seeing you.\n\nBest regards,\nThe Hospital Team"
            send_email(email, user_subject, user_message)

            return "Your appointment has been successfully scheduled."
        except mysql.connector.Error as e:
            return "Error inserting data into database: {}".format(str(e))

    return render_template('appointment.html')


@app.route('/contact')
def contact_page():
    return render_template('contact.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/service')
def services():
    return render_template('service.html')


@app.route('/price')
def price():
    return render_template('price.html')


@app.route('/team')
def team():
    return render_template('team.html')


@app.route('/testimonial')
def testimonial():
    return render_template('testimonial.html')


@app.route('/signup', methods=['POST'])
def sign():
    if request.method == 'POST':
        email = request.form['email']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO signup (email) VALUES (%s)", (email,))

            conn.commit()
            cursor.close()
            conn.close()

            # Send notification email to your email address
            your_email = 'abc@gmail.com'  # Replace with your email address
            subject = 'New User Sign-up'
            message = f'A new user has signed up with the email address: {email}'
            send_email(your_email, subject, message)

            return 'Your signup has been successfully'
        except mysql.connector.Error as e:
            return 'Error inserting data into database: {}'.format(str(e))
    return "method not allowed"


@app.route('/contact', methods=['POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO contact (name, email, subject, message) VALUES (%s, %s, %s, %s)",
                           (name, email, subject, message))
            conn.commit()
            cursor.close()
            conn.close()

            # Send acknowledgment email to the user
            user_subject = "Thank you for contacting us!"
            user_message = (
                f"Dear {name},\n\n"
                "Thank you for contacting us. We have received your message and will get back to you as soon as possible.\n\n"
                "Best regards,\n"
                "The Hospital Team"
            )
            send_email(email, user_subject, user_message)

            # Send notification email to admin
            admin_subject = "New Contact Form Submission"
            admin_message = (
                f"New message received from {name} ({email}) with subject: {subject}\n\n"
                f"Message: {message}"
            )
            send_email(email_config['sender_email'], admin_subject, admin_message)

            return 'Form submitted successfully!'
        except mysql.connector.Error as e:
            return 'Error submitting form: {}'.format(str(e))
    return "Method not allowed"


if __name__ == '__main__':
    app.run(debug=True)
