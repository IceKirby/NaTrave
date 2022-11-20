# GENERAL COMMAND MESSAGES
no_sub_specified = "Seu comando não foi reconhecido porque você não especificou um subreddit."
no_such_sub = "Não foi possível processar seu comando porque ele contém um ou mais subreddits inválidos: {Name}"
mod_only_command = "Não foi possível processar seu comando porque você não é um moderador dos seguintes subreddits: {Name}."
registered_only_command = "Não foi possível processar seu comando porque os seguintes subreddits não estão registrados com o bot: {Name}"

# [COMMAND] REQUEST MATCH
request_match_success = "Você requisitou as seguintes partidas:  \n  \n{Matches}"
request_match_error = "Não foi possível agendar as partidas para {Name}, tente novamente em instantes."
request_match_no_match = "Não foi possível encontrar as partidas na data requisitada."
request_match_invalid_format = "Não foi possível agendar partidas para {Name} porque o formato da mensagem não é válido."

# [COMMAND] ABORT MATCH
abort_match_success = "Você requisitou o cancelamento das seguintes partidas:  \n  \n{Matches}"
abort_match_error = "Não foi possível cancelar as partidas para {Name}, tente novamente em instantes."
abort_match_invalid_format = "Não foi possível cancelar partidas para {Name} porque o formato da mensagem não é válido."

match_listing = "- [{Tour}] {Home} vs {Away} ({Time}) para {Sub}: {Thread}"
aborted_match_listing = "- [{Tour}] {Home} vs {Away} ({Time}) para {Sub}: {Thread}"
match_listing_thread_existing = "[Link do Tópico]({URL})"
match_listing_thread_pending = "Tópico será criado em {Date}"
match_listing_thread_pending_aborted = "Tópico seria criado em {Date}"

# [COMMAND] REGISTER
sub_registered = "Subreddit registrado com sucesso: {Name}"
sub_already_registered = "Subreddit já está registrado: {Name}"
sub_register_error = "Não foi possível registrar {Name}, tente novamente em instantes."

# [COMMAND] UNREGISTER
sub_unregistered = "Subreddit desregistrado desregistrado com sucesso: {Name}"
sub_unregister_error = "Não foi possível desregistrar {Name}, tente novamente em instantes."


# [COMMAND] MOD
mod_accepted = "Convite para moderador de {Name} foi aceito!"
mod_invite_fail = "Não foi possível aceitar o convite para moderador de r/{Name}. Verifique se o convite foi enviado corretamente e tente novamente."

# [COMMAND] SUBSCRIBE
subscribe_success = "Subreddit {Name} está seguindo jogos que atendem aos seguintes critérios:  \n  \n{Follows}"
subscribe_fail = "Não foi possível seguir os times/torneios requisitados, tente novamente mais tarde."
subscribe_invalid_format = "Não foi possível seguir times/torneios para {Name} porque o formato da mensagem não é válido."

subscribe_team_tour = "- **Partidas dos times:** {Teams}  \n- **Nas seguintes competições:** {Tours}"
subscribe_team_only = "- **Partidas dos times:** {Teams}"
subscribe_tour_only = "- **Partidas das competições:** {Tours}"
subscribe_none = "- Nenhum time ou torneio está sendo seguido"

# [COMMAND] UNSUBSCRIBE
unsubscribe_invalid_format = "Formato inválido."
unsubscribe_success = "Subreddit {Name} não está mais seguindo jogos que atendem os seguintes critérios:  \n  \n{Follows}"
unsubscribe_fail = "Não foi possível parar de seguir os times/torneios requisitados, tente novamente mais tarde."

# [COMMAND] GET FOLLOWS
get_follows_fail = "Não foi possível encontrar informações dos jogos seguidos por {Name}."
get_subs_teams = "**Todas as partidas dos times:** {Teams}"
get_subs_tours = "**Todas as partidas das competições:** {Tours}"
get_subs_both = "**Partidas dos times:**  \n  \n{Teams}"
get_subs_both_li = "- {Team} (Competições: {Tours})"

# [COMMAND] CONFIG
config_sub_success = "As seguintes configurações do subreddit {Name} foram modificadas com sucesso:  \n  \n{Config}"
config_sub_invalid_value = "Os seguintes valores não são válidos para as seguintes configurações:  \n  \n{Config}"
config_sub_invalid_option = "Não foi possível identificar as seguintes configurações, verifique se você digitou os nomes corretamente:  \n  \n{Config}"
config_sub_fail = "Não foi possível alterar as configurações, tente novamente mais tarde."
config_sub_list = "As configurações atuais do subreddit {Name} são:  \n  \n{Config}  \n  \nPara modificar as configurações, leia as instruções no seguinte link: https://www.reddit.com/r/NaTrave/wiki/configurar"

# SUB LOCKED WARNING
sub_locked_message = "[Esta é uma mensagem automática do bot {Bot}]  \n  \nO bot {Bot} falhou múltiplas vezes em acessar o subreddit {Name}. Isso provavelmente aconteceu porque o sub está configurado como privado ou restrito, ou o bot foi banido do sub. Como medida de precaução, o bot irá interromper as operações no sub {Name} até que o problema seja solucionado.  \n  \nPara re-estabelecer o funcionamento do bot, certifique-se que o bot possa acessar e postar normalmente no sub, e então envie uma mensagem privada para {Bot} com o título 'Destravar', incluindo também o nome do sub no corpo da mensagem.  \n  \nCaso não queira mais que o bot opere no sub, envie uma mensagem com o título 'Desregistrar', com o nome do sub no corpo da mensagem."
sub_unlocked = "O subreddit {Name} foi destravado com sucesso."
sub_unlocked_error = "Não foi possível destravar o subreddit {Name}. Tente novamente mais tarde."
