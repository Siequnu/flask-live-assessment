from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, SelectMultipleField, BooleanField, FormField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
	
class LiveAssessmentCreationForm(FlaskForm):
	title = StringField('Title:', validators=[DataRequired(), Length(max=250)])
	description = StringField('Description:', validators=[DataRequired(), Length(max=500)])
	peer_review_form_id = SelectField('Feedback form', coerce=int, validators=[DataRequired()])
	create_live_assessment_form_submit = SubmitField('Create')

