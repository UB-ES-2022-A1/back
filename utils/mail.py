from flask_mail import Message, Mail
from flask import url_for

mail = Mail()

mail_type = ['REGISTER']


def send_email(m_type, message="", recipient=[]):
    """
    This method sends en email.
    :param m_type: Type of the email, used to redirect the method.
    :param message: The message.
    :param recipient: Who receives the email.
    :return:
    """
    if m_type == "REGISTER":
        send_register(message, recipient)


def send_register(message, recipient):
    """
    This method sends an email with a confirmation link
    :param message: It's the user token used later to change its status of validation.
    :param recipient: User mail
    :return: Response indicating that a confirmation mail has been sent.
    """
    email = recipient
    msg = Message('Verificar Mail', sender="atyourservice.noreply@gmail.com", recipients=[email])
    link = url_for('users.confirm_email', token=message, _external=True)
    msg.body = 'Verifica tu correo clicando en el siguiente enlace {}'.format(link)
    mail.send(msg)
