# Assault Fire Server Emulator

**Idioma:** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | [简体中文](README-ZH-CN.md) | [Mais idiomas](README-LANGUAGES.md)

Projeto não oficial de preservação do **Assault Fire PH** e emulação do servidor. Este projeto e servidores operados por terceiros não são afiliados, patrocinados nem endossados pela Tencent, pela Level Up! Games ou pelos titulares originais dos direitos. Servidores da comunidade são independentes.

> **Única versão compatível e testada:** Assault Fire PH **v1.0.0.24**. Este repositório não inclui os arquivos do jogo. Você precisa ter seus próprios arquivos.

## Jeito mais fácil de começar

1. Coloque a pasta inteira `af-emulator` dentro da pasta do jogo Assault Fire PH.
2. Clique com o botão direito em `START_ASSAULT_FIRE.ps1` e escolha **Run with PowerShell**. Autorize o acesso de Administrador se o Windows solicitar.
3. O inicializador verifica a versão e a configuração, prepara as chaves locais e inicia o servidor, o auxiliar de inicialização e o cliente do jogo.
4. Entre no cliente. Quando o botão **START** aparecer, clique nele para continuar.

No fluxo normal de um clique, você não precisa iniciar manualmente o servidor nem as ferramentas de patch. O script não baixa nem redistribui arquivos do jogo; usa apenas os seus arquivos locais. Se a versão não corresponder ou não for possível verificar a assinatura de `TGame.exe` ou `TCLS.dll`, pare e não force o patch.

## Configuração manual e desenvolvimento

Consulte o [guia completo em inglês](README.md) para todas as etapas e comandos exatos. Você precisa de Windows, Python 3.10 ou mais recente e da sua própria cópia da versão compatível do jogo. Na configuração manual, espere o preflight mostrar `UNLOCKED`. Se iniciar o jogo manualmente, não clique em **START** antes de o auxiliar mostrar `TCLS ARMED`. A opção `--server-only` é apenas para hospedar o servidor; ela não libera a inicialização local do jogo.

## Status e ajuda

A base estável pública atual é a **v143b**. Os fluxos VERSION, AUTH, DIR, ROLE e ZONE, o gerenciamento de salas e as partidas PvE estão funcionando. A criação inicial de apelido/conta e alguns recursos sociais/de progressão continuam em desenvolvimento. A sincronização inicial de AP no cliente ainda usa uma solução local temporária.

Ao pedir ajuda, envie uma captura do erro, a etapa em que estava, o comando exato, `server/af_server_live.log` e a versão do jogo. **Não envie** `PRIVATE.PEM`, senhas, credenciais de conta, tokens ou arquivos originais do jogo.

- [Status do projeto](docs/STATUS.md) · [Erros do inicializador](docs/LAUNCHER_ERRORS.md) · [Notas importantes de configuração](docs/VITAL_SETUP_NOTES.md) · [Índice da documentação](docs/README.md)
- [Todos os READMEs por idioma](README-LANGUAGES.md)

**Licença:** MIT.
