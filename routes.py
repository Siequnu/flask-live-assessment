from flask import render_template, flash, abort, redirect, url_for, request
from flask_login import current_user, login_required

from . import bp
from .forms import LiveAssessmentCreationForm
from .models import LiveAssessmentAssignment, LiveAssessmentFeedback, get_live_assessment_info

import app.models 

from datetime import datetime
import json


# Live assessment index
@bp.route("/", methods=['GET', 'POST'])
@login_required
def live_assessment_index():
	if app.models.is_admin(current_user.username):
		live_assessments = app.live_assessment.models.get_live_assessment_assignments_from_teacher_id(current_user.id)

		form = LiveAssessmentCreationForm()
		form.peer_review_form_id.choices = [(peer_review_form.id, peer_review_form.title) for peer_review_form in app.models.PeerReviewForm.query.all()]
		form.target_turma.choices = [(turma.id, turma.turma_label) for turma in app.classes.models.get_teacher_classes_from_teacher_id (current_user.id)]

		return render_template (
			'live_assessment_index.html',
			form = form,
			live_assessments = live_assessments)
	else:
		live_assessments = app.live_assessment.models.get_student_live_assessments(current_user.id)
		return render_template (
			'live_assessment_index.html',
			live_assessments = live_assessments)


# Toggle live assessment status
@bp.route("/toggle/<int:live_assessment_id>", methods=['GET', 'POST'])
@login_required
def toggle_live_assessment_status(live_assessment_id):
	if app.models.is_admin(current_user.username):
		live_assessment = LiveAssessmentAssignment.query.get(live_assessment_id)
		live_assessment.toggle_status ()
		
		return redirect (url_for ('live-assessment.live_assessment_index'))


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


# The assessment form
@bp.route("/<live_assessment_id>/", methods=['GET', 'POST'])
@login_required
def submit_live_assessment(live_assessment_id):

	live_assessment = LiveAssessmentAssignment.query.get(live_assessment_id)
	if live_assessment is None: abort (404)

	peer_review_form = app.models.PeerReviewForm.query.get(live_assessment.assessment_form_id)
	if peer_review_form is None: abort (404)
	
	# Only students in this class or teachers managing this class can submit reviews
	if app.classes.models.check_if_student_is_in_class (current_user.id, live_assessment.turma_id) is True or current_user.is_admin is True:
		
		# Security check for teacher
		if app.models.is_admin(current_user.username) and current_user.is_superintendant == False:
			if app.classes.models.check_if_turma_id_belongs_to_a_teacher (live_assessment.turma_id, current_user.id) is False: 
				abort (403)
		
		form_data = app.models.PeerReviewForm.query.get(live_assessment.assessment_form_id).serialised_form_data
		form_loader = app.assignments.formbuilder.formLoader(
			form_data, 
			(url_for('live-assessment.submit_live_assessment', live_assessment_id=live_assessment_id)))
		render_form = form_loader.render_form()

		if request.method == 'POST':
			# Submit the review comment form 
			form_contents = json.dumps(request.form)
			new_comment = LiveAssessmentFeedback (
				live_assessment_assignment_id = live_assessment_id,
				comment = form_contents,
				timestamp = datetime.now (),
				student_id = current_user.id
			)
			new_comment.add ()

			flash('Your test was submitted succesfully!', 'success')
			return redirect(url_for('live-assessment.live_assessment_index', live_assessment_id = live_assessment_id))
		
		return render_template('live_assessment_form.html', title='Live assessment', render_form=render_form)
	abort (403)


# View assessment submissions
@bp.route("/view/all/<int:live_assessment_id>")
@login_required
def view_assessment_submissions(live_assessment_id):
	if app.models.is_admin(current_user.username):
		info_array = get_live_assessment_info(live_assessment_id)
		
		return render_template(
			'view_live_assessment_submissions.html', 
			info_array = info_array)
	abort (403)


# View a assessment submission
@bp.route("/view/submission/<submission_id>")
@login_required
def view_completed_submission(submission_id):
	live_assessment_feedback = LiveAssessmentFeedback.query.get(submission_id)
	if live_assessment_feedback is None: abort (404)

	live_assessment = LiveAssessmentAssignment.query.get(live_assessment_feedback.live_assessment_assignment_id)
	if live_assessment is None: abort (404)
	
	if app.models.is_admin(current_user.username) or current_user.id == live_assessment_feedback.student_id:
		
		# Get the peer review form ID
		peer_review_form_id = live_assessment.assessment_form_id
		
		# JSON load the form contents
		form_contents = json.loads(live_assessment_feedback.comment)

		# Load the form (fields)
		form_data = app.models.PeerReviewForm.query.get(peer_review_form_id).serialised_form_data

		# Populate the form fields with the serialised data
		form_loader = app.assignments.formbuilder.formLoader(
			form_data,
			(url_for('live-assessment.live_assessment_index')),
			submit_label = 'Return',
			form_method = 'POST',
			data_array = form_contents)
		render_form = form_loader.render_form()
		
		# Assign the correct form action
		# If we are the comment author, redirect to assignments
		if current_user.is_admin:
			form_action = url_for('live-assessment.live_assessment_index')
		# If we are the file owner redirect to view our other comments
		else:
			form_action = url_for('live-assessment.live_assessment_index')
		
		return render_template(
			'live_assessment_form.html',
			render_form=render_form, 
			title = 'View submission',
			do_not_display_csrf_token = True, # As we are sharing this form with other methods which will POST, and need it
			form_method = 'GET',
			form_action = form_action)
		
	else: abort (403)