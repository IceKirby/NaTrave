from DB import db_session
from ErrorPrinter import print_error
from Models import Follow
import PMResponse
import NameTranslator

def update_follow_names(author, sub_name, lines, pm):

    with db_session() as s:
        follows = s.query(Follow)\
            .all()
        
        cached_team_names = {}
        cached_tour_names = {}

        for f in follows:
            if f.team == "" and f.tour == "":
                s.delete(f)
                continue
            
            res_team = f.team
            res_tour = f.tour

            if f.team != "":
                if f.team not in cached_team_names:
                    cached_team_names[f.team] = NameTranslator.get_standard_team_name(f.team)
                res_team = cached_team_names[f.team]
            if f.tour != "":
                if f.tour not in cached_tour_names:
                    cached_tour_names[f.tour] = NameTranslator.get_standard_tour_name(f.tour)
                res_tour = cached_tour_names[f.tour]
            
            if res_team != f.team or res_tour != f.tour:
                has_entry = s.query(Follow)\
                    .filter(Follow.sub == f.sub)\
                    .filter(Follow.team == res_team)\
                    .filter(Follow.tour == res_tour)\
                    .first()

                if has_entry:
                    s.delete(f)
                else:
                    f.team = res_team
                    f.tour = res_tour


        result = "Follows found: " + str(len(follows))
    
    if s.success:
        PMResponse.add_response(author, "admin_command_result", result, pm)
        return True
    else:
        print_error(s.error)
        result = "Erro no comando administrativo"
        PMResponse.add_response(author, "admin_command_result", result, pm)
        return True