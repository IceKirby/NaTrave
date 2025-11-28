import SubManager
import Scheduler
import Redditor

command_data = {
    "registrar": {
        "action": SubManager.register_sub,
        "options": {
            "registered_sub": False,
            "allow_locked": True,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["registro", "cadastrar", "cadastro"]
    },
    "desregistrar": {
        "action": SubManager.unregister_sub,
        "options": {
            "registered_sub": True,
            "allow_locked": True,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["desregistro", "descadastrar", "descadastro"]
    },
    "destravar": {
        "action": SubManager.unlock_sub,
        "options": {
            "registered_sub": True,
            "allow_locked": True,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["destrave", "destrava", "unlock"]
    },
    "inscrever": {
        "action": SubManager.subscribe_sub,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["seguir", "acompanhar", "inscricao"]
    },
    "desinscrever": {
        "action": SubManager.unsubscribe_sub,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["desseguir", "desacompanhar", "desinscrição"]
    },
    "abortar": {
        "action": Scheduler.abort_match_thread,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["cancelar", "anular", "interromper"]
    },
    "configurar": {
        "action": SubManager.config_sub,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["config", "configuracoes", "configuracao", "setup", "settings"]
    },
    "lista": {
        "action": SubManager.get_sub_follows,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": False,
            "mod_only_by_options": False
        },
        "alts": []
    },
    "mod": {
        "action": Redditor.accept_mod,
        "options": {
            "registered_sub": False,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["moderador"]
    },
    "jogo": {
        "action": Scheduler.request_match,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": False,
            "mod_only_by_options": True
        },
        "alts": ["partida", "match", "thread", "matchthread", "agendar"]
    },
    "sjogo": {
        "action": Scheduler.request_match_silent,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": False,
            "mod_only_by_options": True
        },
        "alts": ["partidasilencioso", "jogosilencioso", "matchsilencioso", "threadsilencioso", "matchthreadsilencioso", "agendarsilencioso"]
    },
    "tjogo": {
        "action": Scheduler.request_match_threadless,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": False,
            "mod_only_by_options": True
        },
        "alts": ["partidasemtopico", "jogosemtopico", "matchsemtopico", "partidasemmt", "jogosemmt", "matchsemmt"]
    }
}
