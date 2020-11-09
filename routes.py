from flask import render_template, flash, abort, redirect, url_for, request, session
from flask_login import current_user, login_required
from app import csrf, db

from . import bp
from .forms import LiveAssessmentCreationForm
from .models import LiveAssessmentAssignment, LiveAssessmentFeedback, AssessmentForm, get_live_assessment_info

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
		form.peer_review_form_id.choices = [(peer_review_form.id, peer_review_form.title) for peer_review_form in AssessmentForm.query.all()]
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
		form_data = AssessmentForm.query.get(peer_review_form_id).serialised_form_data

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


# Admin page to manage assessment forms
@bp.route("/forms/admin")
@login_required
def assessment_form_admin():
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		forms = AssessmentForm.query.all()
		return render_template(
			'manage_assessment_forms.html', 
			forms=forms)
	abort (403)


############# Assessment forms builder routes

# Route to redirect to form builder, after some security checks
@bp.route("/forms/add", methods=['GET', 'POST'])
@login_required
def add_assessment_form():
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		return (redirect(url_for('live-assessment.form_builder')))
	abort(403)

from flask_talisman import Talisman, ALLOW_FROM
from app import talisman
# Build temporary expanded content security policy
temp_csp = {
        'default-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'cdnjs.cloudflare.com',
            'fonts.googleapis.com',
            'fonts.gstatic.com',
            '*.w3.org',
            'kit-free.fontawesome.com'
        ],
        'img-src': '*',
        'style-src': [
            '*',
            '\'self\'',
            '\'unsafe-inline\'',
            '\'unsafe-eval\'',
        ],
        'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',
			'\'unsafe-eval\'',
            'ajax.googleapis.com',
            'code.jquery.com',
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ]
    }
@talisman(content_security_policy=temp_csp)
@bp.route("/form/builder")
def form_builder():
	return render_template('assessment_form_builder.html')

@bp.route('/form/save', methods=['POST'])
@csrf.exempt
def save_new_assessment_form():
	if request.method == 'POST':
		form_data = request.form.get('formData')
		if form_data == 'None':
			return 'Error processing request'
		else:
			json_string = r'''{}'''.format(form_data)
			json_data = json.loads(json_string)
			
			peer_review_form = AssessmentForm()
			peer_review_form.title = json_data['title']
			peer_review_form.created_by_id = current_user.id
			peer_review_form.description = json_data['description']
			peer_review_form.serialised_form_data = json.dumps(json_data)
			db.session.add(peer_review_form)
			db.session.commit()
		session['form_data'] = form_data
		
	return 'True'

from flask_talisman import Talisman, ALLOW_FROM
from app import talisman
# Build temporary expanded content security policy
temp_csp = {
        'default-src': [
			'*',
			'\'self\'',
            '\'unsafe-inline\'',
            'cdnjs.cloudflare.com',
            'fonts.googleapis.com',
            'fonts.gstatic.com',
            '*.w3.org',
            'kit-free.fontawesome.com'
        ],
        'img-src': '*',
		'connect-src': '*',
		'font-src': [
			'*',
			'\'self\'',
            'data:',
			'\'unsafe-inline\'',
			'\'unsafe-eval\'',
            'ajax.googleapis.com',
            '*.fontawesome.com'
			'code.jquery.com',
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ],
		'child-src': '*',
        'style-src': [
            '*',
            '\'self\'',
            '\'unsafe-inline\'',
            '\'unsafe-eval\'',
        ],
        'script-src': [
            '*',
			'\'self\'',
            '\'unsafe-inline\'',
			'\'unsafe-eval\'',
            'ajax.googleapis.com',
            'code.jquery.com',
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ]
    }
@talisman(content_security_policy=temp_csp)
@bp.route('/form/render')
@bp.route('/form/render/<form_id>')
def render_assessment_form(form_id = False):
	if form_id:
		form_data = AssessmentForm.query.get(form_id).serialised_form_data
	elif not session['form_data']:
		redirect(url_for('main.index'))
	else:
		form_data = session['form_data']
		session['form_data'] = None

	form_loader = app.assignments.formbuilder.formLoader(form_data, 'nosubmit')
	render_form = form_loader.render_form()
	
	return render_template('form_builder_render.html', render_form=render_form)

@bp.route('/form/delete/<form_id>')
def delete_assessment_form(form_id):
	# Check if the form is in use by any assignments, and refuse to delete
	assessment_forms_in_use = LiveAssessmentAssignment.query.filter_by (assessment_form_id = form_id).all()
	if (len(assessment_forms_in_use) > 0):
		flash ('This form is currently being used by an assessment, and can not be deleted.', 'info')	
		return (redirect(url_for('assignments.peer_review_form_admin')))
	AssessmentForm.query.filter(AssessmentForm.id == form_id).delete()
	db.session.commit()
	flash ('Assessment form deleted successfully.', 'success')
	return (redirect(url_for('live-assessment.assessment_form_admin')))

# !FIXME is this only shown when clicking submit at the demo form?
@bp.route('/form/builder/submit', methods=['POST'])
def submit():
	if request.method == 'POST':
		form = json.dumps(request.form)
		return form
