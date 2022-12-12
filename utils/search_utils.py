from collections import defaultdict
from math import log

from flask import g
from sqlalchemy import or_, asc, desc
from werkzeug.exceptions import NotFound, BadRequest

from models.search import term_frequency
from models.service import Service
from models.user import User


def filter_query(q, ser_table, filters):
    for filter_name in filters:

        if filter_name == 'price':
            filter_quantity = ser_table.price
        elif filter_name == 'creation_date':
            filter_quantity = ser_table.created_at
        elif filter_name == 'popularity':

            """

            cs = aliased(ContractedService)
            s2 = aliased(Service)

            filter_quantity = func.count(cs.id)
            q = q.add_column(filter_quantity)

            q = q.join(s2, ser_table.masterID == s2.masterID).join(cs, cs.service_id == s2.id).group_by(s2.id)
            filter_quantity = ser_table.price
            """
            raise NotImplementedError

        elif filter_name == 'rating':
            raise BadRequest('filter by rating not implemented yet')
        else:
            raise BadRequest('filter ' + filter_name + ' not yet implemented')

        if 'min' in filters[filter_name] and filters[filter_name]['min'] != -1:
            q = q.filter(filter_quantity >= filters[filter_name]['min'])

        if 'max' in filters[filter_name] and filters[filter_name]['max'] != -1:
            q = q.filter(filter_quantity <= filters[filter_name]['max'])

    return q


def sort_query_services(q, ser_table, passed_arguments):
    if 'by' not in passed_arguments:
        raise BadRequest('Specify what to sort by!')

    if passed_arguments['by'] == 'price':
        sort_criterion = ser_table.price

    elif passed_arguments['by'] == 'creation_date':
        sort_criterion = ser_table.created_at

    elif passed_arguments['by'] == 'rating':
        raise NotImplementedError('This sorting method is not supported!')

    elif passed_arguments['by'] == 'popularity':
        raise NotImplementedError('This sorting method is not supported!')

        # q = q.join(ContractedService).group_by(Service.masterID)
        # sort_criterion = func.count(ContractedService.id)

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
        raise NotImplementedError('This sorting method is not supported!')

    elif passed_arguments['by'] == 'popularity':
        raise NotImplementedError('This sorting method is not supported!')
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
    scores = defaultdict(float)

    total_documents = Service.get_count()

    coincidences_queries, hashtag_query = term_frequency.search_text(search_text)

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
            q_final = q_final.filter(or_(Service.state == 0, Service.state == 1))
        elif not g.user.access >= 8:
            q_final = q_final.filter(Service.state == 0)
    else:
        if not g.user.access >= 8:
            q_final = q_final.filter(Service.state == 0)

    return q_final
