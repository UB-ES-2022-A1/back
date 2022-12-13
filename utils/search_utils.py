from collections import defaultdict
from math import log

from flask import g
from sqlalchemy import or_, asc, desc, func
from sqlalchemy.sql import alias
from sqlalchemy.orm import Query
from werkzeug.exceptions import NotFound, BadRequest

from models.contracted_service import ContractedService
from models.search import term_frequency
from models.service import Service
from models.user import User


def filter_query(q: Query, ser_table: Service, filters):
    for filter_name in filters:

        if filter_name == 'price':
            filter_quantity = ser_table.price
            query_filtering = q.filter

        elif filter_name == 'creation_date':
            filter_quantity = ser_table.created_at
            query_filtering = q.filter

        elif filter_name == 'popularity':

            cs = alias(ContractedService)
            brothers = alias(Service)
            q = q.join(brothers, ser_table.masterID == brothers.c.masterID). \
                outerjoin(cs, brothers.c.id == cs.c.service_id). \
                filter(cs.c.state == 2)

            filter_quantity = func.count(cs.c.id)
            q = q.group_by(ser_table.id)
            query_filtering = q.having

        elif filter_name == 'rating':

            master = alias(Service)
            q = q.join(master, ser_table.masterID == master.c.id)
            filter_quantity = master.c.service_grade
            query_filtering = q.filter

        else:
            raise BadRequest('filter ' + filter_name + ' not yet implemented')

        if 'min' in filters[filter_name] and filters[filter_name]['min'] != -1:
            q = query_filtering(filter_quantity >= filters[filter_name]['min'])

        if 'max' in filters[filter_name] and filters[filter_name]['max'] != -1:
            q = query_filtering(filter_quantity <= filters[filter_name]['max'])

    return q


def sort_query_services(q, ser_table, passed_arguments):
    if 'by' not in passed_arguments:
        raise BadRequest('Specify what to sort by!')

    if passed_arguments['by'] == 'price':
        sort_criterion = ser_table.price

    elif passed_arguments['by'] == 'creation_date':
        sort_criterion = ser_table.created_at

    elif passed_arguments['by'] == 'rating':

        master = alias(Service)
        q = q.join(master, ser_table.masterID == master.c.id)
        sort_criterion = master.c.service_grade

    elif passed_arguments['by'] == 'popularity':

        cs = alias(ContractedService)
        brothers = alias(Service)

        q = q.outerjoin(brothers, ser_table.masterID == brothers.c.masterID).\
            outerjoin(cs, brothers.c.id == cs.c.service_id)
        sort_criterion = func.count(cs.c.id)
        q = q.group_by(ser_table.id)

    else:
        raise NotImplementedError('This sorting method is not supported!')

    if 'reverse' in passed_arguments:
        reverse = passed_arguments['reverse']

        if reverse not in [True, False]:
            raise BadRequest('reverse parameter must be True or False!')

    else:
        reverse = False

    if reverse:
        return q.order_by(desc(sort_criterion))
    else:
        return q.order_by(asc(sort_criterion))


def sort_services(list_to_sort, passed_arguments):
    if 'by' not in passed_arguments:
        raise BadRequest('Specify what to sort by!')

    if passed_arguments['by'] == 'price':
        def sort_criterion(s: Service):
            return s.price

    elif passed_arguments['by'] == 'creation_date':
        def sort_criterion(s: Service):
            return s.created_at

    elif passed_arguments['by'] == 'rating':
        def sort_criterion(s: Service):
            return s.master_service.service_grade

    elif passed_arguments['by'] == 'popularity':

        def sort_criterion(s: Service):
            return sum(
                (len([c for c in b.contracts if c.state == 2]) for b in s.master_service.child_services)
            )

    else:
        raise NotImplementedError('This sorting method is not supported!')

    if 'reverse' in passed_arguments:
        reverse = passed_arguments['reverse']

        if reverse not in [True, False]:
            raise BadRequest('reverse parameter must be True or False!')

    else:
        reverse = False

    list_to_sort.sort(key=sort_criterion, reverse=reverse)


def get_matches_text(q, ser_table, search_text, search_order, threshold=0.9):

    coincidences_queries, hashtag_query = term_frequency.search_text(search_text)

    if len(coincidences_queries) == 0:
        scores = {c: 1 for c in q.join(hashtag_query.subquery()).all()}

    else:

        scores = defaultdict(float)
        total_documents = Service.get_count()

        for word, coincidences_query in coincidences_queries:

            merged_query = coincidences_query.join(q.join(hashtag_query.subquery()).subquery())
            coincidences_word = merged_query.all()

            if len(coincidences_word) > 0:

                idf = log(1 + total_documents / len(coincidences_word))
                partial_counts = defaultdict(float)

                for coincidence in coincidences_word:
                    count = int.from_bytes(coincidence.count, "little")
                    partial_counts[coincidence.service] += \
                        count / (len(coincidence.service.description) + len(coincidence.service.title)) * \
                        len(word) / len(coincidence.word)

                for service, total_count in partial_counts.items():

                    if search_order:
                        tf = log(1 + total_count)
                        scores[service] += tf * idf

                    else:
                        scores[service] += idf

    all_scored = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if not search_order:

        if len(all_scored) == 0:
            return []

        n = 0
        while n < len(all_scored) and all_scored[n][1] >= all_scored[0][1] * threshold:
            n += 1

        return [scored[0] for scored in all_scored[:n]]

    else:
        return [scored[0] for scored in all_scored]


def filter_email_state(q, ser_table, user_email=None):
    q_final = q

    if user_email:

        user = User.get_by_id(user_email)
        if not user:
            raise NotFound('User not found')

        q_final = q_final.filter(ser_table.user == user)

        if g.user.email == user_email and not g.user.access >= 8:
            q_final = q_final.filter(or_(ser_table.state == 0, ser_table.state == 1))
        elif not g.user.access >= 8:
            q_final = q_final.filter(ser_table.state == 0)
    else:
        if not g.user.access >= 8:
            q_final = q_final.filter(ser_table.state == 0)

    return q_final
