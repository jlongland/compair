import json

from data.fixtures.test_data import CriterionTestData
from acj.tests.test_acj import ACJAPITestCase


class CriterionAPITests(ACJAPITestCase):
    def setUp(self):
        super(CriterionAPITests, self).setUp()
        self.data = CriterionTestData()

    def _verify_critera(self, criterion_expected, criterion_actual):
        self.assertEqual(
            criterion_expected.name, criterion_actual['name'],
            'Expected criterion name does not match actual.')
        self.assertEqual(
            criterion_expected.description, criterion_actual['description'],
            'Expected criterion description does not match actual')

    def _build_assignment_criterion_url(self, course_id, assignment_id, criterion_id = None):
        if criterion_id == None:
            return '/api/courses/' + str(course_id) + '/assignments/' + str(assignment_id) + '/criteria'
        else:
            return '/api/courses/' + str(course_id) + '/assignments/' + str(assignment_id) + '/criteria/' + str(criterion_id)

    def test_create_criterion(self):
        criterion_api_url = '/api/criteria'

        criterion_expected = {
            'name': 'Which is more accurate?',
            'description': 'Please answer honestly.'
        }

        # Test login required
        rv = self.client.post(
            criterion_api_url,
            data=json.dumps(criterion_expected),
            content_type='application/json')
        self.assert401(rv)

        with self.login(self.data.get_authorized_instructor().username):
            # Test successful criterion creation
            rv = self.client.post(
                criterion_api_url,
                data=json.dumps(criterion_expected),
                content_type='application/json')
            self.assert200(rv)
            criterion_actual = rv.json
            self.assertEqual(criterion_expected['name'], criterion_actual['name'])
            self.assertEqual(criterion_expected['description'], criterion_actual['description'])

        # Test fail criterion creation - student
        with self.login(self.data.get_authorized_student().username):
            rv = self.client.post(
                criterion_api_url,
                data=json.dumps(criterion_expected),
                content_type='application/json')
            self.assert403(rv)

    def test_get_criterion(self):
        criterion_api_url = '/api/criteria/' + str(self.data.get_criterion().id)

        # Test login required
        rv = self.client.get(criterion_api_url)
        self.assert401(rv)

        # Test author access
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(criterion_api_url)
            self.assert200(rv)
            self._verify_critera(self.data.get_criterion(), rv.json)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(criterion_api_url)
            self.assert403(rv)

        # Test admin access
        with self.login('root'):
            rv = self.client.get(criterion_api_url)
            self.assert200(rv)
            self._verify_critera(self.data.get_criterion(), rv.json)

            # Test invalid criterion id
            rv = self.client.get('/api/criteria/999')
            self.assert404(rv)

    def test_edit_criterion(self):
        criterion_api_url = '/api/criteria/' + str(self.data.get_criterion().id)
        criterion_expected = {
            'id': self.data.get_criterion().id,
            'name': 'Which is more correct?',
            'description': 'Please answer more honestly.'
        }

        # Test login required
        rv = self.client.post(
            criterion_api_url,
            data=json.dumps(criterion_expected),
            content_type='application/json')
        self.assert401(rv)

        # Test unauthorized user
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.post(
                criterion_api_url,
                data=json.dumps(criterion_expected),
                content_type='application/json')
            self.assert403(rv)

        # Test invalid criterion id
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.post(
                '/api/criteria/999',
                data=json.dumps(criterion_expected),
                content_type='application/json')
            self.assert404(rv)

            # Test author access
            rv = self.client.post(
                criterion_api_url,
                data=json.dumps(criterion_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(criterion_expected['name'], rv.json['name'])
            self.assertEqual(criterion_expected['description'], rv.json['description'])

        # Test admin access
        # admin_criterion_expected = self.data.get_criterion()
        admin_criterion_expected = {
            'id': self.data.get_criterion().id,
            'name': 'Which one uses the correct formula?',
            'description': 'Hint: Law of Physics.'
        }
        with self.login('root'):
            rv = self.client.post(
                criterion_api_url,
                data=json.dumps(admin_criterion_expected),
                content_type='application/json')
            self.assert200(rv)
            self.assertEqual(admin_criterion_expected['name'], rv.json['name'])
            self.assertEqual(admin_criterion_expected['description'], rv.json['description'])


    def test_get_available_criterion(self):
        criterion_api_url = '/api/criteria'

        # Test login required
        rv = self.client.get(criterion_api_url)
        self.assert401(rv)

        # Test authorized instructor
        with self.login(self.data.get_authorized_instructor().username):
            rv = self.client.get(criterion_api_url)
            self.assert200(rv)
            # one public + two authored
            self.assertEqual(len(rv.json['objects']), 3)
            self._verify_critera(self.data.get_default_criterion(), rv.json['objects'][0])
            self._verify_critera(self.data.get_criterion(), rv.json['objects'][1])

        # Test unauthorized instructor
        with self.login(self.data.get_unauthorized_instructor().username):
            rv = self.client.get(criterion_api_url)
            self.assert200(rv)
            # one public + one authored
            self.assertEqual(len(rv.json['objects']), 2)
            self._verify_critera(self.data.get_default_criterion(), rv.json['objects'][0])
            self._verify_critera(self.data.get_secondary_criterion(), rv.json['objects'][1])

        # Test admin
        with self.login('root'):
            rv = self.client.get(criterion_api_url)
            self.assert200(rv)
            # return all
            self.assertEqual(len(rv.json['objects']), 4)
            self._verify_critera(self.data.get_default_criterion(), rv.json['objects'][0])
            self._verify_critera(self.data.get_criterion(), rv.json['objects'][1])
            self._verify_critera(self.data.get_secondary_criterion(), rv.json['objects'][2])