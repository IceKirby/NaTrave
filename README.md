# Sobre o NaTrave

NaTrave é um bot para Reddit que cria e gerencia Match Threads para partidas de futebol.  
Você pode vê-lo em ação através dos posts do usuário [u/NaTrave](https://www.reddit.com/user/NaTrave) no Reddit.

---
  
# Funções do Bot

- Subreddits podem se registrar com o bot para habilitá-lo
- Cria e atualiza várias Match Threads e Post-Match Threads ao mesmo tempo
- Match Threads podem ser requisitadas manualmente enviando uma mensagem para o bot, ou podem ser agendadas automaticamente usando o sistema de seguir times e/ou competições
- Cria HUB Threads com links para todas as Match Threads do dia para aquele subreddit
- Mais detalhes sobre a utilização do bot podem ser encontradas em https://www.reddit.com/r/NaTrave/wiki/index

---

# Desenvolvendo localmente

Antes de tudo, você irá precisar ter instalado em seu computador:

- [Docker e Docker Compose](https://www.docker.com) 
- [Git](https://git-scm.com)

Para rodar esse projeto localmente, siga os passos a seguir:

1. Clone este repositório

    ```
    $ git clone https://github.com/IceKirby/NaTrave.git
    ```
2. Entre no diretório do projeto
    ```
    $ cd NaTrave
    ```

3. Copie `.env.sample` como `.env`
    ```
    $ cp .env.sample .env
    ```

4. Siga as instruções [deste link](https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps) para obter um `client_id` e `client_secret` da sua conta do Reddit
5. No arquivo `.env`, preencha os campos relacionados ao Reddit com as informações da sua conta
6. Ainda no arquivo `.env`, preencha o campo `POSTGRES_PASSWORD` com uma senha de sua preferência.
7. Execute o Docker Compose:
    ```
    $ docker-compose up
    ```

O Docker Compose para este projeto utiliza o [Watchdog](https://pypi.org/project/watchdog/), que automaticamente recarrega o bot quando há alterações no código.

---
