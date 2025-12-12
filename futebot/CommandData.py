import SubManager
import Scheduler
import Redditor
import AdminTools

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
        "alts": ["encerrar", "parar", "interromper"]
    },
    "cancelar": {
        "action": Scheduler.cancel_match_thread,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["anular", "apagar", "deletar"]
    },
    "resumir": {
        "action": Scheduler.set_thread_to_hub_only,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["reduzir", "diminuir", "simplificar", "sohub", "apenashub", "somentehub"]
    },
    "bloquear": {
        "action": SubManager.block_user,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["bloqueio", "mutar", "banir"]
    },
    "reiniciar": {
        "action": Scheduler.restart_match,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": ["recomecar", "arrumar"]
    },
    "pedidos": {
        "action": Scheduler.view_requests,
        "options": {
            "registered_sub": True,
            "allow_locked": False,
            "mod_only": True,
            "mod_only_by_options": False
        },
        "alts": []
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
    },
    "dbfix": {
        "action": AdminTools.update_follow_names,
        "options": {
            "registered_sub": True,
            "allow_locked": True,
            "admin_only": True,
            "mod_only": False,
            "mod_only_by_options": False
        },
        "alts": []
    }
}
