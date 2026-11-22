# Créditos

Home Assistant Core é um projeto da Open Home Foundation e de seus colaboradores. Esta adaptação usa a versão 2026.10.4 e mantém as mudanças de compatibilidade separadas em `patches/windows-port.json`. O código do Core segue a licença Apache 2.0, reproduzida em `LICENSE.md`. As alterações para Windows são distribuídas sob os mesmos termos.

- [Home Assistant Core](https://github.com/home-assistant/core)
- [aiodns](https://github.com/aio-libs/aiodns), distribuído pelo PyPI com sua própria licença. Este repositório contém uma pequena alteração para configurar o DNS no Windows. O aviso original e a licença MIT estão em `licenses/aiodns-MIT.txt`.
- [SonoffLAN](https://github.com/AlexxIT/SonoffLAN) e [Tuya Local](https://github.com/make-all/tuya-local) são projetos independentes. O instalador opcional baixa os arquivos diretamente dos respectivos projetos.

O coletor Xiaomi BLE, a integração local JBL e os módulos de interface desta distribuição são disponibilizados sob Apache 2.0. A base de referência do protocolo Bluetooth vem do projeto **PartyBox for Home Assistant**, de **BaggaBruh**, distribuído sob licença MIT. Créditos ao autor pelo trabalho de engenharia reversa e pela documentação usados na adaptação da JBL PartyLight Stick para Windows. [Projeto original](https://github.com/BaggaBruh/jbl-partybox-ha) · [Documentação do protocolo](https://github.com/BaggaBruh/jbl-partybox-ha/blob/main/PROTOCOL.md). A integração PartyLight é uma implementação local verificada com a luminária. JBL e Harman são marcas de seus respectivos titulares.

- **Positivo Casa Inteligente** tem como origem o projeto **homeassistant-positivo**, de **rgsilva**. O README do autor informa que o projeto não é mais mantido e convida os usuários a criar forks (“Feel free to fork it if you want”). Créditos ao autor pelo cliente de nuvem, pela engenharia reversa e pelo suporte inicial às tomadas e controles infravermelhos. A versão adaptada 1.1.1 usada no ambiente de referência recebeu ajustes para o Core 2026.10.4. [Projeto original e nota do autor](https://github.com/rgsilva/homeassistant-positivo)
