from bouncer.constants import READ, EDIT, CREATE, DELETE, MANAGE
from flask import Blueprint
from flask.ext.login import login_required, current_user
from flask.ext.restful import Resource, marshal
from flask.ext.restful.reqparse import RequestParser
from sqlalchemy import desc, or_
from acj import dataformat, db
from acj.authorization import allow, require
from acj.models import PostsForQuestions, Courses, Posts, CoursesAndUsers, CriteriaAndCourses, UserTypesForCourse, PostsForAnswers, AnswerPairings, Judgements, Users
from acj.util import new_restful_api
from acj.attachment import addNewFile, deleteFile

import datetime, os
import dateutil.parser

questions_api = Blueprint('questions_api', __name__)
api = new_restful_api(questions_api)

new_question_parser = RequestParser()
new_question_parser.add_argument('title', type=str, required=True, help="Question title is required.")
new_question_parser.add_argument('post', type=dict, default={})
new_question_parser.add_argument('answer_start', type=str, required=True)
new_question_parser.add_argument('answer_end', type=str, required=True)
new_question_parser.add_argument('judge_start', type=str, default=None)
new_question_parser.add_argument('judge_end', type=str, default=None)
new_question_parser.add_argument('name', type=str, default=None)
new_question_parser.add_argument('alias', type=str, default=None)
new_question_parser.add_argument('can_reply', type=bool, default=False)
new_question_parser.add_argument('num_judgement_req', type=int, required=True) 

# existing_question_parser = new_question_parser.copy()
existing_question_parser = RequestParser()
existing_question_parser.add_argument('id', type=int, required=True, help="Question id is required.")
existing_question_parser.add_argument('title', type=str, required=True, help="Question title is required.")
existing_question_parser.add_argument('post', type=dict, default={})
existing_question_parser.add_argument('answer_start', type=str, required=True)
existing_question_parser.add_argument('answer_end', type=str, required=True)
existing_question_parser.add_argument('judge_start', type=str, default=None)
existing_question_parser.add_argument('judge_end', type=str, default=None)
existing_question_parser.add_argument('name', type=str, default=None)
existing_question_parser.add_argument('alias', type=str, default=None)
existing_question_parser.add_argument('uploadedFile', type=bool, default=False)
existing_question_parser.add_argument('can_reply', type=bool, default=False)
existing_question_parser.add_argument('num_judgement_req', type=int, required=True)

# /id
class QuestionIdAPI(Resource):
	@login_required
	def get(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		if not question_id:
			question_id = 1
		question = PostsForQuestions.query.get_or_404(question_id)
		require(READ, question)
		now = datetime.datetime.utcnow()
		if question.answer_start and not allow(MANAGE, question) and not (question.answer_start <= now):
			return {"error":"The question is unavailable!"}, 403
		restrict_users = not allow(EDIT, CoursesAndUsers(courses_id=course_id))
		criteria = CriteriaAndCourses.query.filter_by(courses_id=course_id).order_by(CriteriaAndCourses.id).all()
		answers = PostsForAnswers.query.filter_by(postsforquestions_id=question.id).join(Posts).filter(Posts.users_id==current_user.id).count()
		judgements = Judgements.query.filter_by(users_id=current_user.id).join(CriteriaAndCourses).filter_by(courses_id=course.id).join(AnswerPairings).filter(AnswerPairings.postsforquestions_id==question.id).count()
		instructors = CoursesAndUsers.query.filter_by(courses_id=course_id).join(UserTypesForCourse).filter(UserTypesForCourse.name.in_([UserTypesForCourse.TYPE_TA, UserTypesForCourse.TYPE_INSTRUCTOR])).all()
		instructor_ids = [u.users_id for u in instructors]
		instructor_answers = PostsForAnswers.query.filter_by(postsforquestions_id=question.id).join(Posts).filter(Posts.users_id.in_(instructor_ids)).all()
		return {
			'question':marshal(question, dataformat.getPostsForQuestions(restrict_users)),
			'criteria':marshal(criteria, dataformat.getCriteriaAndCourses()),
			'instructors':marshal(instructors, dataformat.getCoursesAndUsers()),
			'answers':answers,
			'judged':judgements,
			'instructor_answers':marshal(instructor_answers, dataformat.getPostsForAnswers(restrict_users))
		}
	def post(self, course_id, question_id):
		course = Courses.query.get_or_404(course_id)
		question = PostsForQuestions.query.get_or_404(question_id)
		require(EDIT, question)
		params = existing_question_parser.parse_args()
		# make sure the question id in the url and the id matches
		if params['id'] != question_id:
			return {"error":"Question id does not match URL."}, 400
		# modify question according to new values, preserve original values if values not passed
		question.post.content = params.get("post").get("content")
		uploaded = params.get('uploadedFile')
		name = params.get('name')
		if not (question.post.content or uploaded or name):
			return {"error":"The question content is empty!"}, 400
		question.title = params.get("title", question.title)
		question.answer_start = params.get('answer_start', question.answer_start)
		question.answer_end = params.get('answer_end', question.answer_end)
		question.judge_start = params.get('judge_start', None)
		if question.judge_start is not None:
			question.judge_start = params.get('judge_start', None)
		question.judge_end = params.get('judge_end', None)
		if question.judge_end is not None:
			question.judge_end = params.get('judge_end', None)
		question.can_reply = params.get('can_reply', False)
		question.num_judgement_req = params.get('num_judgement_req', question.num_judgement_req)
		db.session.add(question.post)
		db.session.add(question)
		db.session.commit()
		if name:
			addNewFile(params.get('alias'), name, course_id, question.id, question.post.id)
		return marshal(question, dataformat.getPostsForQuestions())
	@login_required
	def delete(self, course_id, question_id):
		question = PostsForQuestions.query.get_or_404(question_id)
		require(DELETE, question)
		# delete file when question is deleted
		deleteFile(question.post.id)	
		db.session.delete(question)
		db.session.commit()
		return {'id': question.id} 
api.add_resource(QuestionIdAPI, '/<int:question_id>')

# /
class QuestionRootAPI(Resource):
	# TODO Pagination
	@login_required
	def get(self, course_id):
		course = Courses.query.get_or_404(course_id)
		require(READ, course)
		# Get all questions for this course, default order is most recent first
		restrict_users = not allow(EDIT, CoursesAndUsers(courses_id=course_id))
		post = Posts(courses_id=course_id)
		question = PostsForQuestions(post=post)
		if allow(MANAGE, question):
			questions = PostsForQuestions.query.join(Posts).filter(Posts.courses_id==course_id). \
				order_by(desc(Posts.created)).all()
		else:
			now = datetime.datetime.utcnow()
			questions = PostsForQuestions.query.join(Posts).filter(Posts.courses_id==course_id).\
				filter(or_(PostsForQuestions.answer_start==None,now >= PostsForQuestions.answer_start)).\
				order_by(desc(Posts.created)).all()
		judgements = Judgements.query.filter_by(users_id=current_user.id).join(CriteriaAndCourses).filter_by(courses_id=course.id).join(AnswerPairings).all()
		answered = PostsForAnswers.query.join(Posts).filter_by(courses_id=course_id).join(Users).filter_by(id=current_user.id).all()
		return {
			"questions":marshal(questions, dataformat.getPostsForQuestions(restrict_users)),
			"judgements":marshal(judgements, dataformat.getJudgements()),
			"answered": marshal(answered, dataformat.getPostsForAnswers())
		}
	@login_required
	def post(self, course_id):
		course = Courses.query.get_or_404(course_id)
		# check permission first before reading parser arguments
		post = Posts(courses_id=course_id)
		question = PostsForQuestions(post=post)
		require(CREATE, question)
		params = new_question_parser.parse_args()
		post.content = params.get("post").get("content")
		name = params.get('name')
		if not (post.content or name):
			return {"error":"The answer content is empty!"}, 400
		post.users_id = current_user.id
		question.title = params.get("title")
		question.answer_start = dateutil.parser.parse(params.get('answer_start'))
		question.answer_end = dateutil.parser.parse(params.get('answer_end'))
		question.judge_start = params.get('judge_start', None)
		if question.judge_start is not None:
			question.judge_start = dateutil.parser.parse(params.get('judge_start', None))
		question.judge_end = params.get('judge_end', None)
		if question.judge_end is not None:
			question.judge_end = dateutil.parser.parse(params.get('judge_end', None))
		question.can_reply = params.get('can_reply', False)
		question.num_judgement_req = params.get('num_judgement_req') 
		db.session.add(post)
		db.session.add(question)
		db.session.commit()
		if name:
			addNewFile(params.get('alias'), name, course_id, question.id, post.id)	
		return marshal(question, dataformat.getPostsForQuestions())
api.add_resource(QuestionRootAPI, '')
