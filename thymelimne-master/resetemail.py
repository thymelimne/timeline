'''
Drawn from CoreyMSchafer's GitHub:
https://github.com/CoreyMSchafer/code_snippets/tree/master/Python/Flask_Blog/10-Password-Reset-Email/flaskblog
'''
from app import *

class RequestResetForm(FlaskForm):
	email = StringField('Email',
						validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is None:
			raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password',
									 validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Reset Password')
	
#--------------------------------------------

def send_reset_email(user):
	token = user.get_reset_token()
	msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
	msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
	mail.send(msg)


@app.route("/resetpassword", methods=['GET', 'POST'])
@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('create'))
	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('An email has been sent with instructions to reset your password.', 'info')
		return redirect(url_for('create'))
	return render_template('resetemail/reset_request.html', title='Reset Password', form=form)


@app.route("/resetpassword/<token>", methods=['GET', 'POST'])
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('create'))
	user = User.verify_reset_token(token)
	print("reset_token()")
	print(user.username)
	if user is None:
		flash('That is an invalid or expired token', 'warning')
		return redirect(url_for('reset_request'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		#hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		hashed_password = generate_password_hash(form.password.data, method='sha256')
		user.password = hashed_password
		db.session.commit()
		flash('Your password has been updated! You are now able to log in', 'success')
		return redirect(url_for('create'))
	return render_template('resetemail/reset_token.html', title='Reset Password', form=form)