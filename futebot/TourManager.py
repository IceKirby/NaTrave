from TournamentSources.TournamentGE import TournamentGE
from TournamentSources.Tournament365Scores import Tournament365Scores

ongoing_tours = {}

def get_tour_data(tour_name):
    if not tour_name in ongoing_tours:
        ongoing_tours[tour_name] = { "ge": None, "365scores": None }

    tour_data = ongoing_tours[tour_name]
    
    if not tour_data["ge"]:
        tourGE = TournamentGE(tour_name)
        tour_data["ge"] = tourGE
    
    if not tour_data["365scores"]:
        tour365s = Tournament365Scores(tour_name)
        tour_data["365scores"] = tour365s

    if tour_data["ge"]:
        tour_data["ge"].update_tour_data()
        return tour_data["ge"]
    elif tour_data["365scores"]:
        tour_data["365scores"].update_tour_data()
        return tour_data["365scores"]
    
    return None
