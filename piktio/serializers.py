from sqlalchemy.sql import func
from models import DBSession, Rating

def show_completed_game(gm, request):
    return {'id': gm.id,

            'subject': gm.subject.subject,

            'subject_author': author(gm.subject.author, request),

            'predicate': gm.predicate.predicate,

            'predicate_author': author(gm.predicate.author, request),

            'first_drawing': gm.first_drawing.identifier,

            'first_drawing_author': author(gm.first_drawing.author, request),

            'first_description': gm.first_description.description,

            'first_description_author':
            author(gm.first_description.author, request),

            'second_drawing': gm.second_drawing.identifier,

            'second_drawing_author':
            author(gm.second_drawing.author, request),

            'second_description': gm.second_description.description,

            'second_description_author':
            author(gm.second_description.author, request),

            'time_completed': gm.time_completed.strftime("%m/%d/%y %H:%M"),

            'rating': rating(gm.id, request)
            }


def game_list(games, request):
    if games:
        lst = [show_completed_game(games[0], request)]
    else:
        lst = []
    lst.extend([{'id': gm.id} for gm in games[1:]])
    return lst


def author(author, request):
    return {'id': author.id,
            'display_name': author.display_name,
            'followed': (author in request.user.followees),
            'csrf_token': request.session.get_csrf_token()}


def rating(game_id, request):
    average_score = DBSession.query(func.avg(Rating.rating).label("average_score"))\
        .filter(Rating.game == game_id).one()[0]
    if average_score is None:
        average_score = "0.00"
    else:
        average_score = "%.2f" % average_score

    author_rating = DBSession.query(Rating).filter(
        Rating.rater == request.user.id,
        Rating.game == game_id).first()
    if author_rating is None:
        author_score = None
    else:
        author_score = author_rating.rating

    return {'game_id': game_id,
            'average_score': average_score,
            'author_score': author_score}

_TITLES = {'predicate': 'Enter the predicate of a sentence',
           'first_drawing': 'Draw this sentence',
           'first_description': 'Describe this drawing',
           'second_drawing': 'Draw this sentence',
           'second_description': 'Describe this drawing'}

_INSTRUCTIONS = {'predicate': 'Like "disguised himself as a raincloud ' +
                              'to steal honey from the tree"',
                 'first_drawing': None,
                 'first_description': 'Try to make it fun to draw',
                 'second_drawing': None,
                 'second_description': 'Try to make it fun to draw'}


def step(game, request):
    if game is None:
        return {'error': 'No suitable game for the next step',
                'redirect': request.route_path('invite')}

    csrf = request.session.new_csrf_token()
    step_response = {'title': _TITLES[request.session['step']],
                     'game_id': game.id,
                     'authors': [author(auth, request)
                                 for auth in game.authors],
                     'route': request.route_path(request.session['step']),
                     'csrf_token': csrf}

    if _INSTRUCTIONS[request.session['step']]:
        step_response['instructions'] = _INSTRUCTIONS[request.session['step']]
    else:
        step_response['instructions'] = " ".join([game.subject.subject,
                                                  game.predicate.predicate])

    if request.session['step'] == 'first_description':
        step_response['drawing'] = game.first_drawing.identifier
    if request.session['step'] == 'second_description':
        step_response['drawing'] = game.second_drawing.identifier

    return step_response
