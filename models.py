from app import db
from flask_login import current_user
from datetime import datetime

import app.classes.models
from app.assignments.models import get_user_enrollment_from_id

from app.models import Turma, User


class LiveAssessmentAssignment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(250))
	description = db.Column(db.String(500))
	created_timestamp = db.Column(db.DateTime, default=datetime.now())
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'))
	is_open = db.Column(db.Boolean, default=False)
	assessment_form_id = db.Column(db.Integer, db.ForeignKey('peer_review_form.id'))
	
	def __repr__(self):
		return '<Live Assessment Assignment {}>'.format(self.id)

	def add (self):
		db.session.add(self)
		db.session.commit()

	def save (self):
		db.session.commit()

	def toggle_status (self):
		self.is_open = not self.is_open
		db.session.commit ()

	def delete (self):
		# Find any associated feedback and delete it
		for live_assessment_feedback in LiveAssessmentFeedback.query.filter_by(live_assessment_assignment_id = self.id).all():
			live_assessment_feedback.delete()

		for live_assessment_registration in LiveAssessmentRegistration.query.filter_by(live_assessment_assignment_id = self.id).all():
			live_assessment_registration.delete()

		db.session.delete(self)
		db.session.commit()


class LiveAssessmentRegistration(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	live_assessment_assigment_id = db.Column(db.Integer, db.ForeignKey('live_assessment_assignment.id'))

	def __repr__(self):
		return '<Live Assessment Registration {}>'.format(self.id)

	def delete (self):
		db.session.delete(self)
		db.session.commit()


class LiveAssessmentFeedback(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	live_assessment_assignment_id = db.Column(db.Integer, db.ForeignKey('live_assessment_assignment.id'))
	comment = db.Column(db.String(20000))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
	student_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Live Assessment Feedback {}>'.format(self.id)

	def add (self):
		db.session.add(self)
		db.session.commit()

	def delete (self):
		db.session.delete(self)
		db.session.commit()


class AssessmentForm(db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(140))
	description = db.Column(db.String(280))
	serialised_form_data = db.Column(db.String(20000))
	created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
	
	def __repr__(self):
		return '<Assessment form {}>'.format(self.title)


def get_live_assessment_assignments_from_teacher_id (teacher_id):
	live_assessments = []
	for assessment in LiveAssessmentAssignment.query.all():
		if app.classes.models.check_if_turma_id_belongs_to_a_teacher (assessment.turma_id, teacher_id) is True:
			assessment_dict = assessment.__dict__
			assessment_dict['turma'] = Turma.query.get(assessment.turma_id)
			live_assessments.append (assessment_dict)

	return live_assessments

def get_student_live_assessments (student_id):
	live_assessments = []
	user_enrollment = get_user_enrollment_from_id (student_id)
	for enrollment, user, turma in user_enrollment:
		# Get all the open assessments
		for assessment in LiveAssessmentAssignment.query.filter_by (turma_id = turma.id).all():
			assessment_dict = assessment.__dict__
			assessment_dict['turma'] = Turma.query.get(assessment.turma_id)
			assessment_dict['completed'] = LiveAssessmentFeedback.query.filter_by(live_assessment_assignment_id = assessment.id).filter_by (student_id = current_user.id).first()
			print (assessment_dict['completed'])
			live_assessments.append (assessment_dict)

	return live_assessments

def get_live_assessment_info (live_assessment_id):
	info = {}

	live_assessment = LiveAssessmentAssignment.query.get(live_assessment_id)
	info['assessment_object'] = live_assessment

	info ['turma'] = Turma.query.get(live_assessment.turma_id)
	
	submissions = []
	for assessment in LiveAssessmentFeedback.query.filter_by(live_assessment_assignment_id = live_assessment.id):
		assessment_dict = assessment.__dict__
		assessment_dict['student'] = User.query.get(assessment.student_id)
		submissions.append (assessment_dict)

	info['submissions'] = submissions
	
	return info