# Comandos do pacotes-discord-bot

- `/adiciona <nome> <código>`
  - 
  - Adiciona um pacote de nome `nome` e de código `código` à lista de rastreio do bot. Após alguma atualização de pacote, o bot poderá te avisar nos servidores inscritos.
  - Caso o pacote ficar com o estado de "não encontrado" durante um tempo, será automaticamente deletado.
- `/remove <nome> `
  - 
  - Remove um pacote de nome `[nome]` da lista de rastreio do bot. Somente pacotes adicionados irão aparecer na lista.
- `/rastreia [nome] [código] [visivel]`
  - 
  - Mostra as atualizações de um pacote por `nome` ou por `código`. Somente pacotes adicionados irão aparecer na lista de `nome`, e qualquer pacote pode ser visualizado com o seu `código`.
  - O comando é privado por padrão, mas é possível deixar ele visível com o argumento `visivel`.
- `/me_atualize_aqui`
  - 
  - Após alguma atualização de algum pacote cadastrado, o bot irá te avisar no servidor em que este comando for enviado, caso ele estiver configurado.
- `/nao_me_atualize_aqui`
  - 
  - Após alguma atualização de algum pacote cadastrado, o bot não irá te avisar no servidor em que este comando for enviado, caso ele estiver configurado.
- `/lista [mostrar_entregues=Sim]`
  - 
  - O bot irá enviar uma lista pública com todos os seus pacotes cadastrados. Você pode deletar a mensagem facilmente com um clique, caso necessário.
  - Caso `mostrar_entregues` for Sim, também irá mostrar os pacotes entregues que foram adicionados.
- `/mostrar_codigo_rastreio`
  - 
  - O bot irá mostrar o código de rastreio dos seus pacotes quando aplicável. Além disso, também irá mudar a visibilidade de alguns comandos por padrão.
- `/nao_mostrar_codigo_rastreio`
  - 
  - O bot irá esconder o código de rastreio dos seus pacotes quando aplicável. Além disso, também irá mudar a visibilidade de alguns comandos por padrão. Esse é o comportamento padrão para quem valoriza a sua privacidade.
- `/canal_de_pacotes`
  - 
  - Define o canal atual como o canal padrão para recebimento de atualização de pacotes.
  - Caso esse comando não for enviado, **nenhuma atualização** será enviada ao servidor.
  - Somente administradores podem usar este comando.