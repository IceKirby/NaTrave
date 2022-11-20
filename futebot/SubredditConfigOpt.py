from Models import SuggestedSort

config_options = {
    "post_match": {
        "title": "Pós-Jogo",
        "desc": "Criar tópico de Pós-Jogo",
        "alts": ["posjogo", "postmatch"],
        "type": "Boolean"
    },
    "match_hub": {
        "title": "HUB Thread",
        "desc": "Criar tópico diário com link para todos os jogos",
        "alts": ["hub", "hubthread", "matchhub", "hubmatch"],
        "type": "Boolean"
    },
    "pre_match_time": {
        "title": "Pré-Jogo",
        "desc": "Criar Match Thread quando faltar X minutos para o começo do jogo",
        "alts": ["prejogo", "prematch"],
        "type": "Number",
        "min": 0
    },
    
    "match_title": {
        "title": "Título da Match Thread",
        "desc": "Título para a Match Thread",
        "alts": ["titulo", "matchtitulo", "titulopartida", "titlematch", "matchtitle"],
        "type": "String",
        "max_length": 500
    },
    "post_title": {
        "title": "Título do Pós-Jogo",
        "desc": "Título para o tópico de Pós-Jogo",
        "alts": ["titulopos", "postmatchtitulo", "tituloposjogo", "titlepostmatch", "postmatchtitle"],
        "type": "String",
        "max_length": 500
    },
    "hub_title": {
        "title": "Título de tópicos de HUB",
        "desc": "Título para HUB Thread",
        "alts": ["titulohub", "hubtitulo", "titlehub", "hubtitle"],
        "type": "String",
        "max_length": 500
    },
    
    "match_flair": {
        "title": "Flair da Match Thread",
        "desc": "Flair para a Match Thread",
        "alts": ["flairmatch", "matchflair"],
        "type": "String",
        "max_length": 255
    },
    "post_match_flair": {
        "title": "Flair do Pós-Jogo",
        "desc": "Flair para o tópico de Pós-Jogo",
        "alts": ["posjogoflair", "flairposjogo", "postmatchflair", "flairpostmatch"],
        "type": "String",
        "max_length": 255
    },
    "hub_flair": {
        "title": "Flair do HUB",
        "desc": "Flair para tópicos de HUB",
        "alts": ["hubflair", "flairhub"],
        "type": "String",
        "max_length": 255
    },
    
    "pin_match": {
        "title": "Fixar Match Thread",
        "desc": "Fixar tópicos de Match Thread no topo do sub",
        "alts": ["fixarmatchthread", "pinmatchthread"],
        "type": "Boolean"
    },
    "pin_post": {
        "title": "Fixar Pós-Jogo",
        "desc": "Fixar tópicos de Pós-Jogo no topo do sub",
        "alts": ["fixarposjogo", "pinpostmatch"],
        "type": "Boolean"
    },
    "pin_hub": {
        "title": "Fixar HUB",
        "desc": "Fixar tópicos de HUB no topo do sub",
        "alts": ["fixarhub", "pinhub"],
        "type": "Boolean"
    },
    
    "unpin_match": {
        "title": "Desfixar Match Thread",
        "desc": "Desfixar Match Thread após X horas de seu término.",
        "alts": ["desfixarmatch", "desfixarmatchthread", "unpinmatchthread"],
        "type": "Number",
        "min": 0
    },
    "unpin_post": {
        "title": "Desfixar Pós-Jogo",
        "desc": "Desfixar tópico de Pós-Jogo após X horas de sua criação",
        "alts": ["desfixarpost", "desfixarpostmatch", "unpinpostmatch"],
        "type": "Number",
        "min": 0
    },
    "unpin_hub": {
        "title": "Desfixar HUB",
        "desc": "Desfixar tópicos de HUB X horas após meia-noite.",
        "alts": ["desfixarhub"],
        "type": "Number",
        "min": 0
    },
    
    # "match_template": {
    #     "title": "Template de Match Thread",
    #     "desc": "Template selecionado para Match Thread",
    #     "alts": ["jogotemplate", "templatejogo", "partidatemplate", "templatepartida"],
    #     "type": "Number",
    #     "min": 0
    # },
    # "post_template": {
    #     "title": "Template de Pós-Jogo",
    #     "desc": "Template selecionado para tópicos de Pós-Jogo",
    #     "alts": ["posjogotemplate", "templateposjogo", "pospartidatemplate", "templatepospartida", "postmatchtemplate"],
    #     "type": "Number",
    #     "min": 0
    # },
    # "hub_template": {
    #     "title": "Template de HUB",
    #     "desc": "Template selecionado para tópicos de HUB",
    #     "alts": ["hubtemplate", "templatehub"],
    #     "type": "Number",
    #     "min": 0
    # },
    
    "match_sort": {
        "title": "Ordem sugerida para Match Threads",
        "desc": "Suggested Sort para Match Threads",
        "alts": ["matchsort", "sortmatch", "sortjogo", "jogosort", "sortpartida", "partidasort", "ordempartida", "ordemjogo", "jogoordem", "partidaordem"],
        "type": "Enum",
        "enum": SuggestedSort
    },
    "post_sort": {
        "title": "Ordem sugerida para Post-Match Threads",
        "desc": "Suggested Sort para Post-Match Threads",
        "alts": ["postsort", "sortpost", "sortposjogo", "posjogosort", "sortpospartida", "pospartidasort", "ordempospartida", "pospartidaordem", "ordemposjogo", "posjogoordem"],
        "type": "Enum",
        "enum": SuggestedSort
    },
    "hub_sort": {
        "title": "Ordem sugerida para HUB Threads",
        "desc": "Suggested Sort para HUB Threads",
        "alts": ["sorthub", "hubsort", "ordemhub", "hubordem"],
        "type": "Enum",
        "enum": SuggestedSort
    },
    
    "half_time_stats": {
        "title": "Estatísticas no Intervalo",
        "desc": "Posta as estatísticas do jogo durante o intervalo",
        "alts": ["estatisticas", "estatisticasintervalo", "estatisticasintervalo"],
        "type": "Boolean"
    },
    "mod_only_request": {
        "title": "Restringir Jogos para Mods",
        "desc": "Permitir que apenas moderadores do subreddit requisitem partidas",
        "alts": ["jogosomod", "somodpartida", "somoderadorjogo", "somoderatorpartida", "restringiragendar", "agendarrestrito"],
        "type": "Boolean"
    },
    "instructions_link": {
        "title": "Link de Instruções",
        "desc": "Link para um tópico ou página de Wiki explicando como usar o bot. Esse link aparecerá no rodapé dos tópicos de HUB",
        "alts": ["linkinstrucoes", "instrucoeslink", "urlinstrucoes", "instrucoesurl"],
        "type": "String",
        "max_length": 500,
        "reddit_url": True
    }
}
