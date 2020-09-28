from flask import render_template, flash, abort, redirect, url_for
from flask_login import current_user, login_required

from . import bp
from .forms import LiveAssessmentCreationForm
from .models import LiveAssessmentAssignment

import app.models 

from datetime import datetime


# Live assessment index
@bp.route("/", methods=['GET', 'POST'])
@login_required
def live_assessment_index():
	if app.models.is_admin(current_user.username):
		live_assessments = app.live_assessment.get_live_assessment_assignments_from_teacher_id(current_user.id)
		return render_template ('live_assessment_index.html')

# Create new live assessment form
@bp.route("/create", methods=['GET', 'POST'])
@login_required
def create_live_assessment():
	if app.models.is_admin(current_user.username):
		
		form = LiveAssessmentCreationForm()
		form.peer_review_form_id.choices = [(peer_review_form.id, peer_review_form.title) for peer_review_form in app.models.PeerReviewForm.query.all()]
		form.target_turma.choices = [(turma.id, turma.turma_label) for turma in app.classes.models.get_teacher_classes_from_teacher_id (current_user.id)]
		
		if form.validate_on_submit():
			new_live_assessment = LiveAssessmentAssignment(
				title = form.title.data,
				description = form.description.data,
				user_id = current_user.id, 
				created_timestamp = datetime.now(),
				turma_id = form.target_turma.data,
				assessment_form_id = form.peer_review_form_id.data
			)
			
			new_live_assessment.add()
			flash ('New live assessment added successfully', 'success')
		
			return redirect (url_for ('live-assessment.live_assessment_index'))

		return render_template(
			'create_live_assessment.html', 
			form = form
		) 
	abort (403)