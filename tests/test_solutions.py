import transaction
import datetime
from .base import WebTest
from nthuion.models import Issue, Solution, User, Tag, Comment

from hypothesis import given, strategies as st


class SolutionTest(WebTest):

    def create_issue(self):
        user = User(name='username')
        self.session.add(user)
        issue = Issue(
            title='qtitle',
            content='qcontent',
            tags=Tag.from_names(self.session, ['tag1', 'tag2', 'tag3']),
            is_anonymous=False,
            author=user,
        )
        self.token = user.acquire_token()
        self.token_header = {'Authorization': 'Token {}'.format(self.token)}
        self.session.add(issue)
        self.session.flush()
        self.uid = user.id
        self.qid = issue.id
        transaction.commit()

    def create_solution(self):
        self.create_issue()
        solution = Solution(
            issue_id=self.qid,
            title='stitle',
            content='scontent',
            author_id=self.uid,
            tags=Tag.from_names(self.session, ['a', 'b', 'c'])
        )
        self.session.add(solution)
        self.session.flush()
        self.sid = solution.id
        transaction.commit()


class SolutionListTest(SolutionTest):

    def test_get(self):
        self.create_solution()
        res = self.app.get(
            '/api/solutions'
        )
        self.assertEqual(1, len(res.json['data']))
        sol = res.json['data'][0]
        self.assertEqual('stitle', sol['title'])
        self.assertEqual('scontent', sol['content'])
        self.assertEqual(self.qid, sol['issue']['id'])
        self.assertEqual(self.uid, sol['author']['id'])
        self.assertEqual('username', sol['author']['name'])
        self.assertEqual(0, sol['votes'])

    def test_post(self):
        self.create_issue()
        res = self.app.post_json(
            '/api/solutions',
            {
                'title': 'mytitle',
                'content': 'mycontent',
                'issue_id': self.qid,
                'tags': ['a', 'b', 'c']
            },
            headers=self.token_header
        )
        assert 'id' in res.json
        assert res.json['id'] is not None
        assert 'mytitle' == res.json['title']
        assert 'mycontent' == res.json['content']
        assert self.qid == res.json['issue']['id']
        assert set('abc') == set(res.json['tags'])
        assert 0 == res.json['user_vote']
        assert 'views' in res.json
        assert 'popularity' in res.json

    def test_post_anon(self):
        self.create_issue()
        self.app.post_json(
            '/api/solutions',
            {
                'title': 'mytitle',
                'content': 'mycontent',
                'issue_id': self.qid
            },
            status=401
        )

    def test_solution_pagination(self):
        for i in range(10):
            self.create_solution()

        jobj = self.app.get(
            '/api/solutions',
            {'limit': 4}
        ).json
        assert 4 == len(jobj['data'])

        jobj = self.app.get(
            '/api/solutions',
            {'offset': 7}
        ).json
        assert 3 == len(jobj['data'])

        jobj = self.app.get(
            '/api/solutions',
            {'offset': 6, 'limit': 5}
        ).json
        assert 4 == len(jobj['data'])

        jobj = self.app.get(
            '/api/solutions',
            {'offset': 6, 'limit': 2}
        ).json
        assert 2 == len(jobj['data'])


class SolutionSingleTest(SolutionTest):

    def test_get(self):
        self.create_solution()
        res = self.app.get(
            '/api/solutions/{}'.format(self.sid)
        )
        jobj = res.json
        assert self.sid == jobj['id']
        assert 'stitle' == jobj['title']
        assert 'scontent' == jobj['content']
        assert set('abc') == set(jobj['tags'])

    @given(
        st.booleans(),
        st.lists(
            st.text(
                st.characters(
                    blacklist_characters='\x00',
                    blacklist_categories=('Cs',)),
                max_size=25)),
        st.text(
            st.characters(
                blacklist_characters='\x00',
                blacklist_categories=('Cs',)),
            max_size=80),
        st.text(
            st.characters(
                blacklist_characters='\x00',
                blacklist_categories=('Cs',)),
            max_size=30000, average_size=100),
    )
    def test_put(self, has_issue, tags, title, content):
        self.create_solution()
        issue_id = self.qid if has_issue else None
        res = self.app.put_json(
            '/api/solutions/{}'.format(self.sid),
            {
                'issue_id': issue_id,
                'tags': tags,
                'title': title,
                'content': content
            },
            headers=self.token_header
        )
        jobj = res.json
        assert 'id' in jobj
        assert (issue_id is None) == (jobj['issue'] is None)
        if issue_id is not None:
            assert issue_id == jobj['issue']['id']
        assert set(tags) == set(jobj['tags'])
        assert title == jobj['title']
        assert content == jobj['content']


class SolutionCommentOrderingLimitOffsetTest(SolutionTest):

    def setUp(self):
        super().setUp()
        self.create_solution()
        for i in range(10):
            with transaction.manager:
                self.app.post_json(
                    '/api/solutions/{}/comments'.format(self.sid),
                    {
                        'content': str(i)
                    },
                    headers=self.token_header
                )
        with transaction.manager:
            self.session.query(Comment).filter(Comment.content == '9')\
                .one().ctime -= datetime.timedelta(days=1)

    def test_ordering(self):
        jobj = self.app.get(
            '/api/solutions/{}/comments'.format(self.sid)
        ).json
        assert 10 == len(jobj['data'])
        assert '9' == jobj['data'][0]['content']
        for i, comment in enumerate(jobj['data'][1:]):
            assert str(i) == comment['content']

    def test_limit(self):
        jobj = self.app.get(
            '/api/solutions/{}/comments?limit=1'.format(self.sid)
        ).json

        assert 1 == len(jobj['data'])
        assert '9' == jobj['data'][0]['content']

    def test_offset(self):
        jobj = self.app.get(
            '/api/solutions/{}/comments?offset=2'.format(self.sid)
        ).json

        assert 8 == len(jobj['data'])
        for i, comment in enumerate(jobj['data'], start=1):  # skip 9, 0
            assert str(i) == comment['content']

    def test_limit_and_offset(self):
        jobj = self.app.get(
            '/api/solutions/{}/comments?limit=3&offset=8'.format(self.sid)
        ).json

        assert 2 == len(jobj['data'])
        assert '7' == jobj['data'][0]['content']
        assert '8' == jobj['data'][1]['content']


class ViewsPopularityTest(SolutionTest):

    def test_views_popularity_get_updated(self):
        self.create_solution()
        self.app.get(
            '/api/solutions/{}'.format(self.sid)  # ip is None
        )

        with transaction.manager:
            u1 = User(name='ggg')
            self.session.add(u1)
            t1 = u1.acquire_token()
            t1b = u1.acquire_token()
            u2 = User(name='xxx')
            self.session.add(u2)
            t2 = u2.acquire_token()

        def token_visit(tok):
            return self.app.get(
                '/api/solutions/{}'.format(self.sid),
                headers={'Authorization': 'Token {}'.format(tok)}
            )

        token_visit(t1)
        token_visit(t1b)
        token_visit(t2)

        self.ts.flush_traffic(self.session)

        assert 3 == self.session.query(Solution).first().views
        assert 3 == self.session.query(Solution).first().popularity

        token_visit(t1)
        token_visit(t2)
        token_visit(t2)
        token_visit(t1)

        self.ts.flush_traffic(self.session)
        assert 5 == self.session.query(Solution).first().views
        assert 5 == self.session.query(Solution).first().popularity

        # make sure the change is visible to the end user
        assert 5 == token_visit(t1).json['views']
        assert 5 == token_visit(t1).json['popularity']


class SolutionOrderingTest(WebTest):

    def setUp(self):
        super().setUp()
        with transaction.manager:
            user = User(name='x')
            self.session.add(user)
            now = datetime.datetime.now()
            self.session.add(
                Solution(
                    author=user,
                    title='old',
                    content='popular',
                    popularity=1,
                    ctime=now
                )
            )
            self.session.add(
                Solution(
                    author=user, title='new', content='not-popular',
                    ctime=now + datetime.timedelta(days=1)
                )
            )

    def test_latest_first(self):
        res = self.app.get(
            '/api/solutions',
            {'ordering': 'latest'}
        )
        first, second = res.json['data']
        assert ('new', 'old') == (first['title'], second['title'])

    def test_popular_first(self):
        res = self.app.get(
            '/api/solutions',
            {'ordering': 'popularity'}
        )
        first, second = res.json['data']
        assert 'popular' == first['content']
        assert 'not-popular' == second['content']
        assert first['popularity'] > second['popularity']


# XXX test ctime, mtime
