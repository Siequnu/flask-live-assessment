from flask import render_template, current_app, session, flash
from flask_login import current_user, login_required

from . import bp
from .forms import LiveAssessmentCreationForm
from .models import LiveAssessmentAssignment

from app import db
from datetime import datetime


# Admin index page
@bp.route("/create", methods=['GET', 'POST'])
@login_required
def create_live_assessment():
	form = LiveAssessmentCreationForm()
	if form.validate_on_submit():
		new_live_assessment = LiveAssessmentAssignment(
			title = form.title.data,
			description = form.description.data,
			user_id = current_user.id, 
			create_timestamp = datetime.now()
		)
		
		new_live_assessment.add()
		flash ('New live assessment added successfully', 'success')
	
		return render_template('check_grammar.html', form = form, api_response = api_response, body = body) 
	return render_template('check_grammar.html', form = form) 