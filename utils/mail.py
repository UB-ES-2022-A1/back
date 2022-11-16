from flask_mail import Message, Mail
from flask import url_for

mail = Mail()

mail_type = ['REGISTER', 'RECOVER']


def send_email(m_type, message="", recipient=None):
    """
    This method sends en email.
    :param m_type: Type of the email, used to redirect the method.
    :param message: The message.
    :param recipient: Who receives the email.
    :return:
    """
    if recipient is None:
        recipient = []
    if m_type == "REGISTER":
        send_register(message, recipient)
    if m_type == "RECOVER":
        send_reset_password(message, recipient)


def send_register(message, recipient):
    """
    This method sends an email with a confirmation link
    :param message: It's the user token used later to change its status of validation
    :param recipient: User mail
    :return: None
    """
    email = recipient
    msg = Message('AtYourService', sender="atyourservice.noreply@gmail.com", recipients=[email])
    link = url_for('users.confirm_email', token=message, _external=True)
    msg.html = '<p>Verifica tu correo clicando en el siguiente <a href=' + link + '>enlace</a>.</p> ' \
                                                                                  '<img src="https://d226aj4ao1t61q.cloudfront.net/ai2shais_blog_confirmationmail.png", alt="Imagen con mail" width="500" height="300">'

    mail.send(msg)


def send_reset_password(message, recipient):
    """
    This method sends an email with reset password link
    :param message: It's the user token used later to change its status of validation
    :param recipient: User mail
    :return: None
    """
    email = recipient
    msg = Message('AtYourService', sender="atyourservice.noreply@gmail.com", recipients=[email])
    link = url_for('users.back_reset_mail', token=message, _external=True)
    msg.html = '<p>Cambia la contraseña des del siguiente enlace <a href=' + link + '>enlace</a>.</p> '
    mail.send(msg)
