def show_completed_game(gm):
    return {'id': gm.id,

            'subject': gm.subject.subject,

            'subject_author': gm.subject.author.display_name,

            'predicate': gm.predicate.predicate,

            'predicate_author': gm.predicate.author.display_name,

            'first_drawing': gm.first_drawing.identifier,

            'first_drawing_author':
            gm.first_drawing.author.display_name,

            'first_description': gm.first_description.description,

            'first_description_author':
            gm.first_description.author.display_name,

            'second_drawing': gm.second_drawing.identifier,

            'second_drawing_author':
            gm.second_drawing.author.display_name,

            'second_description': gm.second_description.description,

            'second_description_author':
            gm.second_description.author.display_name,

            'time_completed': gm.time_completed.strftime("%m/%d/%y %H:%M")
            }


def game_list(games):
    if games:
        lst = [show_completed_game(games[0])]
    else:
        lst = []
    lst.extend([{'id': gm.id} for gm in games[1:]])
    return lst
