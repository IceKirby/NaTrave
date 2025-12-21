title_template = "[jogo] {Campeonato}: {TimeCasa} x {TimeFora}"
post_title_template = "[pós-jogo] {Campeonato}: {TimeCasa} {PlacarCasa} x {PlacarFora} {TimeFora}"

# ################################### #
# Thread Template for ongoing matches #
# ################################### #
match_template = """
# [{MomentoPartida}] {TimeCasa} {PlacarFinal} {TimeFora}{PlacarAgregado}  
**Gols {TimeCasa}:** *{TimeCasaGols}*  
**Gols {TimeFora}:** *{TimeForaGols}*  
  
---  
  
**{Campeonato} - {CampeonatoFase}**  
**Estádio:** {Estadio}  
**Data:** {Data}, {Horario}  
**Transmissão:** {Transmissao}  
[Link para Live Match Thread]({RedditStream})  
{PostMatchThread}  
  
---  
  
Escalações{EscalacaoTemporaria}:  
  
| {TimeCasa} ({TimeCasaEsquema}) | {TimeFora} ({TimeForaEsquema}) |  
| :-- | :-- |  
| {TimeCasaTitulares} | {TimeForaTitulares} |  
| **Suplentes:** | **Suplentes:** |  
| {TimeCasaReservas} | {TimeForaReservas} |  
| **Técnico:** {TimeCasaTreinador} | **Técnico:** {TimeForaTreinador} |  
  
  
**Arbitragem:** {Arbitragem}  
  
---  
  
# Lances  
{Lances}  
  
---  
  
Gosta do NaTrave? [Seja um apoiador no Catarse!](https://www.catarse.me/natrave)
"""

aggregated_score_template = """ (Agregado: {CasaAgregado} x {ForaAgregado})"""

# #################################### #
# Thread Template for upcoming matches
# #################################### #
match_no_info = """
# {TimeCasa} x {TimeFora}  
## **{Campeonato}**  
**Data:** {Data}, {Horario}  
"""

# ################################################ #
# Thread Template for matches without GE reporting
# ################################################ #
simple_match_template = """
# {TimeCasa} {PlacarCasa} x {PlacarFora} {TimeFora}  
  
---  
  
**{Campeonato}**  
**Data:** {Data}, {Horario}  
[Link para Live Thread]({RedditStream})  
  
*(Detalhes da partida não disponíveis)*
"""

# ###################################### #
# Thread Template for Post-Match threads
# ###################################### #
post_match_template = """
# [Encerrado] {TimeCasa} {PlacarFinal} {TimeFora}{PlacarAgregado}  
**Gols {TimeCasa}:** *{TimeCasaGols}*  
**Gols {TimeFora}:** *{TimeForaGols}*  
  
---  
  
Escalações:  
  
| {TimeCasa} ({TimeCasaEsquema}) | {TimeFora} ({TimeForaEsquema}) |  
| :-- | :-- |  
| {TimeCasaTitulares} | {TimeForaTitulares} |  
| **Suplentes:** | **Suplentes:** |  
| {TimeCasaReservas} | {TimeForaReservas} |  
| **Técnico:** {TimeCasaTreinador} | **Técnico:** {TimeForaTreinador} |  
  
  
**Arbitragem:** {Arbitragem}  
  
---  
  
Estatísticas  
  
{Estatitiscas}  
  
---  

### Vídeos  
  
{Videos}
  
{MatchThreadUrl}  
  
---  
### Próximos Jogos  
  
### {TimeCasa}

{FixturesHome}

### {TimeFora}

{FixturesAway}
  
---  
  
Gosta do NaTrave? [Seja um apoiador no Catarse!](https://www.catarse.me/natrave)
"""

# ################################################ #
# Thread Template for Post-Match without GE reporting
# ################################################ #
simple_post_match_template = """
# [Encerrado] {TimeCasa} {PlacarCasa} x {PlacarFora} {TimeFora}  
**{Campeonato}**  
  
  
(Detalhes da partida não disponíveis)  
---  
{MatchThreadUrl}  
"""

# ###################################### #
# Comment Template for Half-Time Stats
# ###################################### #
half_time_stats_template = """
### {Periodo}  
  
{Estatisticas}  
  
---  
  
Gosta do NaTrave? [Seja um apoiador no Catarse!](https://www.catarse.me/natrave)
"""

# ###################################### #
# Thread Template for HUB threads
# ###################################### #
hub_template = """
Partidas de hoje que terão Match Threads em r/{Sub}:  
  
{Torneios}  
  
&nbsp;  

{HubAnterior}  
Quer requisitar uma partida? Leia como aqui: {InstructionsLink}
  
---  
  
Gosta do NaTrave? [Seja um apoiador no Catarse!](https://www.catarse.me/natrave)
  
"""

hub_tour_group_template = """
# {Torneio}  
  
{Partidas}  
  
"""

hub_match_template = "- [{Estado}] {Mandante} {Placar} {Visitante} ({Links})"
hub_match_creation_template = "Tópico será criado às {Horario}"
hub_match_postponed_template = "Partida foi adiada"
hub_match_link_untracked = "Partida sem tópico próprio"
hub_previous_link = "[Link para a Match HUB do dia {Data}]({Link})"

# ################################ #
# Icons used in match descriptions
# ################################ #
match_icons = {
    "goal": "⚽",
    "own_goal": "⚽",
    "subs": "🔃",
    "yellow_card": "🟨",
    "red_card": "🟥",
    "penalty_scored": "⚽",
    # "penalty_scored": "✔️",
    "penalty_missed": "❌",
    "time_over": "⏱️"
}
