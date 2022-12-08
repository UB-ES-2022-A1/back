from database import db
from sklearn.feature_extraction.text import CountVectorizer


class term_frequency(db.Model):
    __table_name__ = 'term_frequency'

    # id = db.Column(db.Integer, primary_key='True')
    word = db.Column(db.Text, nullable=False, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False, primary_key=True)
    count = db.Column(db.Integer, nullable=False)

    @classmethod
    def tokenize(cls, s: str):
        cv = CountVectorizer(stop_words='english')
        cv_matrix = cv.fit_transform([s.lower()])
        return zip(cv.get_feature_names(), cv_matrix.toarray()[0])

    @classmethod
    def put_service(cls, s):
        db.session.query(cls).filter(cls.service_id == s.id).delete()
        # db.session.commit()

        for word, count in cls.tokenize(s.title + ' ' + s.description):
            coincidence = cls(word=word, count=count)
            coincidence.service = s
            db.session.add(coincidence)

        db.session.commit()

    @classmethod
    def get_coincidences(cls, word):
        search_term_regex = f'%{word}%'
        return cls.query.filter(word.like(search_term_regex))

    @classmethod
    def search_text(cls, s: str):
        cv = CountVectorizer(stop_words='english')
        try:
            cv.fit_transform([s.lower()])
        except ValueError:
            return []
        words = cv.get_feature_names()
        return [(word, cls.get_coincidences(word)) for word in words]





"""
class SearchTerm(db.Model):
    __table_name__ = 'search_terms'

    word = db.Column(db.Text, primary_key=True)
    search_ids = db.Column(db.ARRAY(db.Integer), nullable=False, default=[])

    @classmethod
    def get_coincidences(cls, word) -> List[SearchCoincidende]:
        indices = cls.query.get(word)
        return [SearchCoincidende.query.get(idx) for idx in indices]

    @classmethod
    def put_service(cls, s):
        for word, idx in SearchCoincidende.put_service(s):
            term = cls.query.get(word)

            if not term:
                term = cls(word=word)

            term.search_ids.append(idx)
            db.session.add(term)

        db.session.commit()

    @classmethod
    def search_text(cls, s: str) -> List[List[SearchCoincidende]]:

        cv = CountVectorizer(stop_words='spanish')
        cv.fit_transform(s.lower())
        return [cls.get_coincidences(word) for word in cv.get_feature_names()]

"""
