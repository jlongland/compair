import unittest
import mock

from compair import db
from compair.models import User, Comparison, Score, \
    LTIOutcome
from compair.models.comparison import update_scores
from test_compair import ComPAIRTestCase
from compair.algorithms import ComparisonPair
from compair.algorithms.score import calculate_score
from data.fixtures.test_data import TestFixture, LTITestData

class TestUsersModel(ComPAIRTestCase):
    user = User()

    def setUp(self):
        self.user.firstname = "John"
        self.user.lastname = "Smith"

    def test_fullname(self):
        self.assertEqual(self.user.fullname, "John Smith")

    def test_avatar(self):
        self.user.email = "myemailaddress@example.com"
        self.assertEqual(self.user.avatar, '0bc83cb571cd1c50ba6f3e8a78ef1346')
        self.user.email = " myemailaddress@example.com "
        self.assertEqual(
            self.user.avatar, '0bc83cb571cd1c50ba6f3e8a78ef1346',
            'Email with leading and trailing whilespace')
        self.user.email = "MyEmailAddress@example.com"
        self.assertEqual(
            self.user.avatar, '0bc83cb571cd1c50ba6f3e8a78ef1346',
            'Email with upper case letters')

    def test_set_password(self):
        self.user.password = '123456'
        self.assertTrue(self.user.verify_password('123456'))


class TestUtils(ComPAIRTestCase):
    def test_update_scores(self):

        criterion_comparison_results = {
            1: calculate_score(comparison_pairs=[
                ComparisonPair(1,2, winning_key=1)
            ])
        }
        scores = update_scores([], 1, criterion_comparison_results)
        self.assertEqual(len(scores), 2)
        for score in scores:
            self.assertIsNone(score.id)

        score = Score(answer_id=1, criterion_id=1, id=2)
        scores = update_scores([score], 1, criterion_comparison_results)
        self.assertEqual(len(scores), 2)
        self.assertEqual(scores[0].id, 2)
        self.assertIsNone(scores[1].id)


        criterion_comparison_results = {
            1: calculate_score(comparison_pairs=[
                   ComparisonPair(1,2, winning_key=1)
            ]),
            2: calculate_score(comparison_pairs=[
               ComparisonPair(1,2, winning_key=1)
            ])
        }
        score = Score(answer_id=1, criterion_id=1, id=2)
        scores = update_scores([score], 1, criterion_comparison_results)
        self.assertEqual(len(scores), 4)

class TestLTIOutcome(ComPAIRTestCase):

    def setUp(self):
        super(TestLTIOutcome, self).setUp()
        self.fixtures = TestFixture().add_course(num_students=30, num_groups=2, with_draft_student=True)
        self.lti_data = LTITestData()
        self.lti_consumer = self.lti_data.lti_consumer

        self.lis_outcome_service_url = "TestUrl.com"
        self.lis_result_sourcedid = "SomeUniqueSourcedId"
        self.grade = 0.8

    def mocked_requests_post(*args, **kwargs):
        class MockResponse:
            def __init__(self, content, status_code):
                self.content = content
                self.status_code = status_code

        content = """<imsx_POXEnvelopeResponse xmlns = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
        <imsx_POXHeader>
            <imsx_POXResponseHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>4560</imsx_messageIdentifier>
            <imsx_statusInfo>
                <imsx_codeMajor>success</imsx_codeMajor>
                <imsx_severity>status</imsx_severity>
                <imsx_description>Score for {lis_result_sourcedid} is now {grade}</imsx_description>
                <imsx_messageRefIdentifier>999999123</imsx_messageRefIdentifier>
                <imsx_operationRefIdentifier>replaceResult</imsx_operationRefIdentifier>
            </imsx_statusInfo>
            </imsx_POXResponseHeaderInfo>
        </imsx_POXHeader>
        <imsx_POXBody>
            <replaceResultResponse/>
        </imsx_POXBody>
        </imsx_POXEnvelopeResponse>
        """.format(lis_result_sourcedid="SomeUniqueSourcedId", grade=0.8)

        return MockResponse(content, 200)

    @mock.patch('requests.post', mock.Mock(side_effect = mocked_requests_post))
    def test_post_replace_result(self):
        # no lis_outcome_service_url
        result = LTIOutcome.post_replace_result(self.lti_consumer, self.lis_result_sourcedid, self.grade)
        self.assertFalse(result)

        # add lis_outcome_service_url
        self.lti_consumer.lis_outcome_service_url = self.lis_outcome_service_url
        db.session.commit()

        # no lis_result_sourcedid
        result = LTIOutcome.post_replace_result(self.lti_consumer, "", self.grade)
        self.assertFalse(result)

        # garde < 0.0
        result = LTIOutcome.post_replace_result(self.lti_consumer, self.lis_result_sourcedid, -0.1)
        self.assertFalse(result)

        # garde > 1.0
        result = LTIOutcome.post_replace_result(self.lti_consumer, self.lis_result_sourcedid,  30.0)
        self.assertFalse(result)

        # success
        result = LTIOutcome.post_replace_result(self.lti_consumer, self.lis_result_sourcedid, self.grade)
        self.assertTrue(result)