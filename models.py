from app import db
from datetime import datetime


class LiveAssessmentAssignment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(250))
	description = db.Column(db.String(500))
	created_timestamp = db.Column(db.DateTime, default=datetime.now())
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	turma_id = db.Column(db.Integer, db.ForeignKey('turma.id'))
	assessment_form_id = db.Column(db.Integer, db.ForeignKey('peer_review_form.id'))
	
	def __repr__(self):
		return '<Live Assessment Assignment {}>'.format(self.id)

	def add (self):
		db.session.add(self)
		db.session.commit()

	def save (self):
		db.session.commit()

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
	comment = db.Column(db.String(5000))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
	assessor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	assessed_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Live Assessment Feedback {}>'.format(self.id)

	def delete (self):
		db.session.delete(self)
		db.session.commit()