from TournamentSources.TournamentGE import TournamentGE

ongoing_tours = {}

def get_tour_data(tour_name):
    if not tour_name in ongoing_tours:
        tourGE = TournamentGE(tour_name)
        ongoing_tours[tour_name] = { "ge": tourGE }
    
    tour_data = ongoing_tours[tour_name]

    if tour_data["ge"]:
        tour_data["ge"].update_tour_data()
        return tour_data["ge"]
    
    return None
