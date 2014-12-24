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

            'time_completed': gm.time_completed.strftime("%m/%d/%y %H:%M")
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
