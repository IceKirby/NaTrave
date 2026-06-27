import os
import requests
import re
from bs4 import BeautifulSoup, SoupStrainer
from TournamentSources.BaseTournament import BaseTournament
from TournamentSources.TourPageLinksGE import tour_page_links

cached_tour_links = {}

request_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

class TournamentGE(BaseTournament):
    def __init__(self, tour_name):
        super().__init__(tour_name)
        self.page_url = self.find_page_url(tour_name)
        self.api_url = self.find_api_url()
        self.is_valid = self.page_url and self.api_url

    def update_tour_data(self):
        data = self.get_raw_data()

        if not data:
            return
        
        self.reset_tour_data()

        self.current_round = None if not data["rodada"] else data["rodada"]["atual"]
        
        if data["classificacao"]:
            for r in data["classificacao"]:
                self.add_standing_row(
                    r["nome_popular"],
                    r["ordem"],
                    r["pontos"],
                    r["jogos"],
                    r["vitorias"],
                    r["empates"],
                    r["derrotas"],
                    r["gols_pro"],
                    r["gols_contra"],
                    r["saldo_gols"],
                    r["variacao"]
                )

    def find_page_url(self, tour_name):
        for e in tour_page_links:
            if e["name"] == tour_name:
                return e["url"]


    def get_raw_data(self):
        try:
            response = requests.get(self.api_url, headers=request_headers, timeout=10)
            return response.json()
        except requests.RequestException as e:
            pass

        try:
            self.api_url = self.find_api_url()
            response = requests.get(self.api_url, headers=request_headers, timeout=10)
            return response.json()
        except requests.RequestException as e:
            return None

    def find_api_url(self):
        try:
            response = requests.get(self.page_url, headers=request_headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching the URL: {e}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')

        html_tag = soup.find('html')
        hash = html_tag.get("data-bs-resource-id");

        standings_script = soup.find(id='scriptReact')
        match = re.search(r'const\sfase.+"slug":"([^"]+)"', standings_script.string)
        slug = ""
        if match:
            slug = match.group(1)
        else:
            return None
        
        res = f"https://api.globoesporte.globo.com/tabela/{hash}/fase/{slug}/classificacao/"
        return res