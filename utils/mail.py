from flask_mail import Message, Mail
from flask import url_for

mail = Mail()

mail_type = ['REGISTER']


def send_email(m_type, message="", recipient=[]):
    if m_type == "REGISTER":
        send_register(message, recipient)


def send_register(message, recipient):
    email = recipient
    msg = Message('Verificar Mail', sender="atyourservice.noreply@gmail.com", recipients=[email])
    link = url_for('users.confirm_email', token=message, _external=True)
    msg.body = 'Verifica tu correo clicando en el siguiente enlace {}'.format(link)
    mail.send(msg)
