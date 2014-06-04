import json
import unittest
from flask.ext.testing import TestCase
from flask_bouncer import ensure
from flask_login import login_user, logout_user
from werkzeug.exceptions import Unauthorized
from acj import create_app, Users
from acj.manage.database import populate
from acj.core import db
from data.fixtures import DefaultFixture
from tests import test_app_settings
from tests.factories import UserFactory


class ACJTestCase(TestCase):

	def create_app(self):
		return create_app(settings_override=test_app_settings)

	def setUp(self):
		db.create_all()
		populate(default_data=True)

	def tearDown(self):
		db.session.remove()
		db.drop_all()

	def test_unauthorized(self):
		rv = self.client.get('/api/users')
		self.assert401(rv)

	def test_login(self):
		rv = self.login('root', 'password')
		userid = rv.json['userid']
		self.assertEqual(userid, 1, "Logged in user's id does not match!")
		self._verifyPermissions(userid, rv.json['permissions'])

	def test_users_1(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert200(rv)
		root = rv.json
		self.assertEqual(root['username'], 'root')
		self.assertEqual(root['displayname'], 'root')

	def test_users_invalid_id(self):
		self.login('root', 'password')
		rv = self.client.get('/api/users/99999')
		self.assert404(rv)

	def test_users_unauthorized(self):
		user = UserFactory(password='password', usertypeforsystem=DefaultFixture.SYS_ROLE_INSTRUCTOR)
		db.session.commit()

		self.login(user.username, 'password')
		rv = self.client.get('/api/users/' + str(DefaultFixture.ROOT_USER.id))
		self.assert401(rv)

	def login(self, username, password):
		payload = json.dumps(dict(
			username=username,
			password=password
		))
		rv = self.client.post('/login/login', data=payload, content_type='application/json', follow_redirects=True)
		self.assert200(rv)

		return rv

	def logout(self):
		return self.client.get('/login/logout', follow_redirects=True)

	def _verifyPermissions(self, userid, permissions):
		user = Users.query.get(userid)
		with self.app.app_context():
			# can't figure out how to get into logged in app context, so just force a login here
			login_user(user, force=True)
			for model_name, operations in permissions.items():
				for operation, permission in operations.items():
					expected = True
					try:
						ensure(operation, model_name)
					except Unauthorized:
						expected = False
					self.assertEqual(permission, expected,
						"Expected permission " + operation + " on " +  model_name + " to be " + str(expected))
			# undo the forced login earlier
			logout_user()


if __name__ == '__main__':
	unittest.main()