from database import db
from service import Service
from sklearn.feature_extraction.text import CountVectorizer


class SearchCoincidende(db.Model):
    __table_name__ = 'search_coincidences'

    id = db.Column(db.Integer, primary_key='True')
    word = db.Column(db.Text, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    @classmethod
    def tokenize(cls, s: str):
        cv = CountVectorizer(stop_words='spanish')
        cv_matrix = cv.fit_transform(s.lower())
        return zip(cv.get_feature_names(), cv_matrix[0])

    @classmethod
    def put_service(cls, s: Service):
        db.session.query(cls).filter(cls.service_id == s.id).delete()
        db.session.commit()

        for word, count in cls.tokenize(s.title + ' ' + s.description):
            coincidence = cls(word=word, count=count)
            coincidence.service = s
            db.session.add(coincidence)
            db.session.commit()
            yield coincidence.id


class SearchTerm(db.Model):
    __table_name__ = 'search_terms'

    word = db.Column(db.Text, primary_key=True)
    search_ids = db.Column(db.ARRAY(db.Integer), nullable=False, default=[])

    @classmethod
    def get_coincidences(cls, word):
        indices = cls.query.get(word)
        return [SearchCoincidende.query.get(idx) for idx in indices]

    @classmethod
    def put_service(cls, s: Service):
        for word, idx in SearchCoincidende.put_service(s):
            term = cls.query.get(word)

            if not term:
                term = cls(word=word)

            term.search_ids.append(idx)
            db.session.add(term)

        db.session.commit()
