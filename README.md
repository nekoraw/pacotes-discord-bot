# pacotes-discord-bot

pacotes-discord-bot é um bot para Discord com o objetivo de gerenciar e avisar ao usuário sobre atualizações sobre pacotes de várias transportadoras.

### Comandos do bot
Veja: [COMMANDS.md](COMMANDS.md)

### Transportadoras suportadas
- Correios

### Instalação

Primeiro, clone o repositório localmente e mude para o diretório
```shell
git clone https://github.com/nekoraw/pacotes-discord-bot
cd pacotes-discord-bot
```

Após isso, crie um ambiente virtual do Python.
```shell
python3 -m venv pacotes
source pacotes/bin/activate
```

Depois, basta instalar as bibliotecas necessárias para o funcionamento do bot.
```shell
python3 -m pip install -r requirements.txt
```

Para sair do ambiente virtual basta executar:
```shell
deactivate
```

### Configuração
Após clonar o bot e instalar as bibliotecas, você também precisará configurar uma instância do [MongoDB](https://www.mongodb.com/).
Depois de configurado, faça uma cópia do `.env` e edite o seu conteúdo:

```shell
cp .env_EXAMPLE .env
nano .env
```
O arquivo deverá parecer como abaixo:
```dotenv
DISCORD_TOKEN=change_me
MONGODB_CONNECTION_URI=mongodb://localhost:27017
DATABASE_NAME=pacotes_discord_bot
UPDATE_DELAY_MINUTES=5
PARCELS_PER_PAGE=5
UPDATES_PER_PAGE=5
DAYS_TO_TRACK_BEFORE_DELETION=14
```
Você deverá mudar o `DISCORD_TOKEN` para o token do seu bot, assim como o `MONGODB_CONNECTION_URI` caso necessário.

Por fim, você precisará convidar o bot para algum servidor e depois executar
```shell
# dentro do ambiente virtual (pacotes)
python3 main.py emojis
```
para definir os emojis usados no bot.

Após essa primeira execução, para rodar o bot, basta enviar:

```shell
python3 main.py
```