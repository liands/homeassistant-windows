# Home Assistant Core no Windows

Porta experimental do Home Assistant Core **2026.10.4** para Windows x64 e Python **3.14.4**. Roda diretamente em um ambiente virtual Python. Inclui as adaptações para Windows, o tema Smart Glass, o Dashboard Smart com cinco abas, o coletor Xiaomi BLE e a integração opcional da JBL PartyLight Stick. Esta revisão foi preparada em 21/11/2026 com os arquivos ativos do servidor. O Core original é baixado do PyPI. Esta instalação não inclui Supervisor nem a loja de apps e tem limitações para voz local e integrações dependentes do sistema operacional. [Código do Core](https://github.com/home-assistant/core/tree/2026.10.4) · [Métodos de instalação mantidos pelo Home Assistant](https://www.home-assistant.io/installation/)

## 1. Instalar

1. Instale o **Python 3.14.4 x64 convencional** para Windows com `pip` e o lançador `py`. Abra uma nova janela do PowerShell. Use uma pasta gravável com caminho curto, como `C:\HA-Windows`. [Download oficial do Python 3.14.4](https://www.python.org/downloads/release/python-3144/)
2. Entre na pasta deste projeto, onde estão `readme.md` e `scripts`, e rode os comandos abaixo. Se você tiver várias instalações de Python e `py -3.14` não selecionar a versão desejada, chame o `python.exe` dela pelo caminho completo.

```powershell
Set-Location C:\HA-Windows
py -3.14 --version
py -3.14 .\scripts\install.py
```

O instalador baixa o [pacote oficial do Core](https://pypi.org/project/homeassistant/2026.10.4/), confere o SHA-256, cria `runtime\venv`, instala as dependências do PyPI com `pip` e aplica as adaptações em `patches\windows-port.json`. Ele preenche os arquivos ausentes em `runtime\config` com os exemplos. Use o mesmo comando se a instalação for interrompida. O Core pode baixar bibliotecas adicionais via `uv` ao configurar cada integração. Para incluir o coletor Xiaomi e suas dependências, adicione `--with-ble` ao comando.

## 2. Iniciar e acessar

Execute estes comandos a partir da raiz do projeto. Pare a instância com **Ctrl+C** na janela de execução. Para validar o YAML local, use `--check`.

```powershell
$ha = '.\runtime\venv\Scripts\python.exe'
& $ha .\scripts\start.py --check
& $ha .\scripts\start.py
```

Abra [http://127.0.0.1:8123](http://127.0.0.1:8123) na máquina que roda o serviço. Crie um novo administrador no assistente e selecione sua localização, unidade de medidas e fuso horário. As preferências podem ser ajustadas depois em **Configurações → Sistema → Geral**. O primeiro início pode demorar enquanto as dependências do painel são baixadas.

Para acessar pela intranet, use `http://IP-DO-SERVIDOR:8123`. Se o firewall bloquear o acesso, execute a regra abaixo em um PowerShell administrativo. Antes do primeiro início, outra porta pode ser escolhida com `$env:SETUP_PORT = '18123'`. Depois do primeiro início, use **Configurações → Sistema → Rede → Servidor HTTP** para alterá-la e confirme a configuração no novo endereço quando solicitado. Use a mesma porta na regra de firewall. [Configuração HTTP](https://www.home-assistant.io/integrations/http/)

```powershell
New-NetFirewallRule -DisplayName 'Home Assistant LAN TCP 8123' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8123 -Profile Private -RemoteAddress LocalSubnet
```

Para câmeras e integrações multimídia que pedem FFmpeg, obtenha um binário Windows x64 pelas opções da página oficial, extraia numa pasta local e adicione a pasta que contém `ffmpeg.exe` ao `PATH` da conta que inicia o Core. Confira com `Get-Command ffmpeg` em um PowerShell novo. [Download do FFmpeg](https://ffmpeg.org/download.html#build-windows)

Para iniciar no logon, crie uma tarefa no Agendador de Tarefas com o caminho absoluto de `runtime\venv\Scripts\python.exe` no campo **Programa**, o caminho absoluto de `scripts\start.py` entre aspas em **Argumentos** e a raiz do projeto em **Iniciar em**. Use a conta local que tem acesso à pasta. Encerre a instância manual antes de iniciar a tarefa. Para iniciar antes do logon, configure os direitos da conta e teste a tarefa, especialmente se usar Bluetooth.

## 3. Onde ficam os arquivos

| Caminho relativo à raiz | Conteúdo |
| --- | --- |
| `integrations/jbl_partylight/` | Código da integração local JBL. O instalador opcional copia para `runtime/config/custom_components/jbl_partylight/`. |
| `integrations/frontend/` | Módulos de reconexão JBL e ícone do controle infravermelho. Os arquivos usados no navegador são copiados para `runtime/config/www/`. |
| `scripts/install.py` | Instala o Core, as dependências e o patch no ambiente isolado. |
| `scripts/start.py` | Inicia o Core a partir da pasta de configuração e trata o código de reinício. |
| `patches/` | Versão, URLs e SHA-256 das distribuições. O patch registra os trechos de código alterados e os hashes antes e depois. |
| `examples/config/` | Modelos públicos copiados para a configuração local durante a instalação. |
| `runtime/venv/` | Ambiente Python gerado, incluindo os módulos do Core. |
| `runtime/downloads/`, `runtime/pip-cache/`, `runtime/uv-cache/` | Pacotes baixados e caches recriáveis. |
| `runtime/config/configuration.yaml` | Configuração principal, painel e inclusão de temas e pacotes. O servidor HTTP é configurado em Sistema → Rede e salvo em `.storage/http`. |
| `runtime/config/automations.yaml`, `scripts.yaml`, `scenes.yaml` | Automações, scripts e cenas. Os três arquivos ficam dentro de `runtime/config/`. |
| `runtime/config/custom_components/` | Uma pasta por componente manual, como `sonoff/`, `tuya_local/` ou `positivo/`. |
| `runtime/config/packages/` | YAMLs opcionais, incluindo o do coletor Xiaomi BLE. |
| `runtime/config/dashboards/` e `themes/` | Layout do Dashboard Smart e tema Smart Glass. As duas pastas ficam dentro de `runtime/config/`. |
| `runtime/config/.storage/` | Conta, integrações cadastradas na interface, registros de dispositivos e entidades, pareamentos e outros dados privados. Use a interface para gerenciar esses dados. |
| `runtime/config/secrets.yaml` | Arquivo local para valores referenciados por `!secret` em YAML. [Sintaxe do Home Assistant](https://www.home-assistant.io/docs/configuration/secrets/) |
| `runtime/config/home-assistant.log` e `home-assistant_v2.db` | Log e banco SQLite do histórico. Dependendo das configurações de registro, o log também aparece no PowerShell. |
| `runtime/xiaomi_ble/` | `sensors.json` guarda as bindkeys e os MACs. `latest.json` guarda a última coleta técnica. |
| `runtime/config/xiaomi_ble/latest.json` | Leituras exportadas para o Core. Contém MACs e medições, sem bindkeys. |

Todas as credenciais do novo ambiente ficam em `runtime/`, ignorado pelo Git. Para integrações configuradas pela interface, faça login ou cole a chave no próprio fluxo de instalação. Use `secrets.yaml` somente quando o componente aceitar configuração YAML com `!secret`. Há um modelo em `examples/config/secrets.yaml.example`.

## 4. Cadastrar integrações nativas

Abra **Configurações → Dispositivos e serviços → Adicionar integração**. Procure pelo nome da integração e siga o assistente. Confira as entradas já criadas pelo cadastro inicial antes de repetir a configuração. Se a descoberta automática não listar o aparelho, informe o endereço local quando o assistente oferecer essa opção.

- **Tuya (Smart Life)**. No app, abra **Eu → Configurações → Conta e segurança** e copie o **Código do usuário**. Informe-o no Home Assistant e escaneie o QR que o Home Assistant exibir usando o scanner do app. A conta precisa ter os aparelhos cadastrados. Tuya Smart e Smart Life usam contas e listas de aparelhos separadas. Para aparelhos nos dois apps, adicione uma entrada Tuya para cada conta com o código e o scanner do app correspondente. Depois de acrescentar um aparelho no app, recarregue sua entrada no Home Assistant. [Tuya](https://www.home-assistant.io/integrations/tuya/)
- **Android TV Remote**. Deixe a TV ligada e alcançável pela intranet. Selecione a TV descoberta ou informe seu endereço IP e digite o código apresentado na tela. O fluxo pode criar uma entidade `remote.*` e uma `media_player.*`. [Android TV Remote](https://www.home-assistant.io/integrations/androidtv_remote/)
- **Meteorologisk institutt (Met.no)**. Escolha a localização no fluxo ou use a zona Casa. A entidade `weather.*` fornece previsão, temperatura e umidade externas. [Met.no](https://www.home-assistant.io/integrations/met/)
- **Shopping List e Radio Browser**. Adicione pela interface e verifique a lista ou o catálogo de rádio na barra lateral e em Mídia. Radio Browser requer acesso à internet e um reprodutor compatível. [Shopping List](https://www.home-assistant.io/integrations/shopping_list/) · [Radio Browser](https://www.home-assistant.io/integrations/radio_browser/)
- **Google Translate text-to-speech**. Adicione pela interface e escolha o idioma. O serviço sintetiza fala e precisa de acesso à internet. Para reproduzir, selecione o reprodutor de mídia no serviço `tts.speak`. [Google Translate TTS](https://www.home-assistant.io/integrations/google_translate/)
- **Alterar o tipo de dispositivo de um interruptor**. Use a aba **Ajudantes → Criar ajudante** em **Dispositivos e serviços**. Selecione o interruptor existente e o tipo desejado, como ventilador ou luz. [Switch as X](https://www.home-assistant.io/integrations/switch_as_x/)
- **Backup e Analytics**. Para habilitar a integração de backup, adicione `backup:` na raiz do seu `configuration.yaml`, reinicie e abra **Configurações → Sistema → Backups**. Para disponibilizar as preferências de telemetria, adicione `analytics:` na raiz e gerencie o compartilhamento em **Configurações → Sistema → Analytics**. [Backup](https://www.home-assistant.io/integrations/backup/) · [Analytics](https://www.home-assistant.io/integrations/analytics/)
- **Outros componentes do Core**. Consulte o catálogo antes de instalar. Alguns exigem hardware, serviços ou bibliotecas sem suporte nesta porta para Windows. [Catálogo de integrações](https://www.home-assistant.io/integrations/)

## 5. Instalar componentes manuais

Com o Core parado, rode os comandos abaixo para os componentes que você usa. Cada comando baixa a versão indicada e verifica o SHA-256 antes de instalar em `runtime\config\custom_components`. Depois inicie o Core e cadastre a integração pela interface.

```powershell
$ha = '.\runtime\venv\Scripts\python.exe'
& $ha .\scripts\install_component.py sonoff
& $ha .\scripts\install_component.py tuya-local
```

- **SonoffLAN 3.13.3 (eWeLink)**. Procure **Sonoff** no menu de integrações. Use sua própria conta eWeLink conforme o modo local, nuvem ou automático documentado pelo projeto. [Versão usada](https://github.com/AlexxIT/SonoffLAN/releases/tag/v3.13.3) · [Configuração](https://github.com/AlexxIT/SonoffLAN#configuration)
- **Tuya Local 2026.10.0**. Procure **Tuya Local**. No modo manual, informe o IP local, o ID do dispositivo e a chave local quando solicitados. Consulte o seu aparelho e o perfil compatível na documentação. Links de compartilhamento de aplicativos de marca não fornecem a chave local. [Versão usada](https://github.com/make-all/tuya-local/releases/tag/2026.10.0) · [Configuração](https://github.com/make-all/tuya-local#configuration)

Para componentes distribuídos como ZIP, o download costuma conter uma pasta extra do repositório. O nível a instalar deve ser o que contém `manifest.json`, ficando em `runtime/config/custom_components/<domínio>/manifest.json`. As dependências ficam no manifesto do componente e normalmente são instaladas no primeiro carregamento. Evite instalar bibliotecas no Python global.

### Positivo Casa Inteligente

A integração de origem é **homeassistant-positivo**, de **rgsilva**, criada por engenharia reversa do app Positivo Casa Inteligente. O README do autor informa que o projeto deixou de ser mantido e convida explicitamente os usuários a criar forks, com a frase “Feel free to fork it if you want”. Preserve os créditos e a nota do autor ao manter uma adaptação. [Projeto original e nota do autor](https://github.com/rgsilva/homeassistant-positivo)

O componente usa a conta do app Positivo e o backend de nuvem. Os aparelhos precisam estar cadastrados e acessíveis nessa conta. Na implementação que serviu de referência a este projeto, a versão adaptada **1.1.1** foi usada para tomadas e controle infravermelho, com ajustes de compatibilidade para Core 2026.10.4. A disponibilidade dos controles depende do modelo e dos comandos cadastrados no app.

#### Obter e instalar o componente

Com o Home Assistant parado, coloque os arquivos da integração em `runtime/config/custom_components/positivo/`. O nível correto contém diretamente `manifest.json`, `__init__.py`, `config_flow.py`, `switch.py`, `remote.py` e a pasta `tuya/`. Preserve as traduções e demais arquivos que acompanhem a versão escolhida.

Para obter o código original, use **Code → Download ZIP** no repositório do autor ou faça o clone abaixo. O comando requer Git para Windows. A pasta `runtime/` fica ignorada pelo Git deste projeto.

```powershell
New-Item -ItemType Directory -Path .\runtime\downloads -Force | Out-Null
git clone https://github.com/rgsilva/homeassistant-positivo.git .\runtime\downloads\homeassistant-positivo
New-Item -ItemType Directory -Path .\runtime\config\custom_components\positivo -Force | Out-Null
Get-ChildItem .\runtime\downloads\homeassistant-positivo -Force |
    Where-Object { $_.Name -ne '.git' } |
    Copy-Item -Destination .\runtime\config\custom_components\positivo -Recurse
```

Esses comandos são para uma instalação nova. Ao atualizar, guarde a pasta existente antes de copiar os arquivos. O repositório original foi arquivado em 2022 e a versão adaptada deste ambiente recebeu alterações posteriores. Para reproduzir o comportamento validado no Core 2026.10.4, use a pasta completa da versão adaptada obtida de um fork compatível ou de um backup da instalação. Ao usar diretamente o upstream antigo, confira os imports, o fluxo de configuração e as APIs do Core antes de iniciar.

A versão adaptada 1.1.1 declara `requests==2.34.2` e `pycryptodome==3.23.0` em `manifest.json`. O Core instala as dependências declaradas quando carrega a integração. Para conferir ou reparar essas bibliotecas na versão adaptada, use o Python isolado do projeto.

```powershell
$ha = '.\runtime\venv\Scripts\python.exe'
& $ha -m pip install requests==2.34.2 pycryptodome==3.23.0
& $ha -c "import requests; from Crypto.Cipher import AES; from Crypto.PublicKey import RSA; print('Dependencias Positivo carregadas')"
& $ha .\scripts\start.py --check
& $ha .\scripts\start.py
```

#### Cadastrar a conta e os aparelhos

1. No Home Assistant, abra **Configurações → Dispositivos e serviços → Adicionar integração** e procure **Positivo Casa Inteligente**.
2. Informe o e-mail e a senha da sua própria conta do app Positivo. Os aparelhos devem aparecer após o login e a atualização da integração.
3. Abra **Entidades** e copie os IDs das tomadas e dos controles que serão usados no dashboard. Cada instalação pode gerar nomes diferentes.

Na versão adaptada, as credenciais são informadas no fluxo da interface e guardadas pelo Core em `runtime/config/.storage/core.config_entries`. Para trocar a conta, use as opções da entrada quando disponíveis ou remova e cadastre novamente a integração, conferindo as automações que dependem dela. Mantenha o conteúdo de `.storage` no ambiente privado.

#### Tomadas e controle infravermelho

As tomadas expõem entidades `switch.*`. Teste ligar e desligar pela interface e use o ID criado no lugar de `switch.tomada_secundaria_exemplo` ou `switch.luminaria_exemplo` nos cartões públicos.

Para o controlador IR, cadastre e teste o controle da TV no app Positivo primeiro. No Home Assistant, abra **Ferramentas do desenvolvedor → Ações**, selecione `remote.send_command` e use o ID da entidade IR e o nome exato do comando cadastrado. O exemplo abaixo usa um ID fictício.

```yaml
action: remote.send_command
target:
  entity_id: remote.televisao_ir_exemplo
data:
  command: 'On/Off'
```

O comando de energia pode alternar entre ligado e desligado. O estado mostrado pelo controle IR é estimado pelos comandos enviados, pois o controle remoto físico da TV pode alterar o estado sem informar o Home Assistant. Ajuste os comandos do painel ao controle efetivamente cadastrado. O módulo opcional `integrations/frontend/office-tv-power.js`, explicado na seção JBL, personaliza o ícone do popup da entidade IR.

#### Arquivos e diagnóstico

`config_flow.py` trata o login, `__init__.py` coordena a integração, `switch.py` expõe tomadas, `remote.py` expõe o infravermelho e `tuya/` contém o cliente de comunicação com a nuvem. Esses caminhos são relativos a `runtime/config/custom_components/positivo/`.

Se a integração não aparecer, confira a localização de `manifest.json`, reinicie o Core e recarregue o navegador. Para falhas de login ou aparelhos indisponíveis, confirme o funcionamento no app Positivo e consulte **Configurações → Sistema → Registros** ou `runtime/config/home-assistant.log`. Erros em `Crypto` devem ser investigados no ambiente virtual e nas dependências da versão instalada. Guarde uma cópia privada da pasta adaptada antes de substituí-la numa atualização.

## 6. Xiaomi BLE com o Bluetooth do Windows

Este coletor usa Bleak/WinRT para o termômetro Xiaomi **LYWSD03MMC** (MiBeacon `0x055B`). Ele escuta os anúncios locais e, quando faltam leituras, tenta obter temperatura e umidade via GATT. Use uma máquina com adaptador Bluetooth ligado e ao alcance do sensor. As chaves precisam pertencer ao pareamento atual. Se o sensor foi resetado, execute o cadastro novamente com a nova bindkey.

```powershell
py -3.14 .\scripts\install.py --with-ble
$ha = '.\runtime\venv\Scripts\python.exe'
& $ha .\scripts\xiaomi_ble.py --self-test
& $ha .\scripts\xiaomi_ble.py --discover --seconds 60
# Endereço fictício para demonstrar a sintaxe. Troque pelo MAC do sensor.
& $ha .\scripts\xiaomi_ble.py --enroll '00:11:22:33:44:55' 'Escritorio'
& $ha .\scripts\xiaomi_ble.py --seconds 120 --publish .\runtime\config\xiaomi_ble\latest.json
```

Digite a bindkey de 32 caracteres hexadecimais no prompt oculto. O coletor grava a chave em `runtime\xiaomi_ble\sensors.json` e mostra apenas o final do MAC no resultado padrão da coleta. Na saída, `not_seen` significa que nenhum anúncio compatível foi recebido, `bindkey_mismatch` indica falha na descriptografia e `gatt_ok` indica leitura pelo enlace Bluetooth. A descoberta imprime MACs. Mantenha sua saída local.

Depois do primeiro snapshot, habilite o modelo de entidades:

```powershell
Copy-Item .\examples\config\packages\xiaomi_ble_windows.yaml.example .\runtime\config\packages\xiaomi_ble_windows.yaml
```

Abra `runtime\config\packages\xiaomi_ble_windows.yaml`. Substitua `MAC_ESCRITORIO`, `MAC_QUARTO` e `MAC_BANHEIRO` pelos MACs correspondentes com 12 caracteres, em maiúsculas e sem `:`. Remova os dois blocos de entidade de cada cômodo que não for usado. Para adicionar outros cômodos, duplique um par de sensores e altere o MAC, o nome, o `unique_id` e o `default_entity_id`. Rode `start.py --check` e reinicie. Os sensores restauram as últimas medições válidas até 2h30 após a coleta. Depois desse período ficam indisponíveis até chegar uma leitura nova.

Para atualizar a cada hora, crie uma tarefa como a da seção 2, com o mesmo `python.exe` e a raiz do projeto em **Iniciar em**. Use os argumentos `scripts\xiaomi_ble.py --seconds 120 --publish runtime\config\xiaomi_ble\latest.json`. Configure repetição de 1 hora e a opção de ignorar uma nova execução se outra estiver ativa. Execute a tarefa manualmente uma vez e confira `collected_at` em `runtime\config\xiaomi_ble\latest.json`. Se o Windows não permitir BLE na sessão em segundo plano da sua conta, use a opção de executar quando o usuário estiver conectado.

## 7. JBL PartyLight Stick

A integração incluída usa Bluetooth direto com Bleak/WinRT. Disponibiliza luz RGB, liga/desliga, brilho, efeitos, um slider de velocidade e o botão Reconectar Bluetooth. Foi verificada com PartyLight Stick firmware 0.5.0. A detecção de som está funcional na luminária, conforme validação de uso. O microfone integrado sincroniza os efeitos com o som ambiente. A ativação e a desativação dessa opção são feitas no app JBL.

A implementação usa como base de referência o trabalho de engenharia reversa do projeto **PartyBox for Home Assistant**, de **BaggaBruh**, especialmente a documentação dos canais Bluetooth e do protocolo de comandos. O projeto original é distribuído sob licença MIT. A adaptação desta distribuição acrescenta suporte à PartyLight Stick no Windows e verificação do número de série durante a redescoberta Bluetooth. [Projeto original](https://github.com/BaggaBruh/jbl-partybox-ha) · [Documentação do protocolo](https://github.com/BaggaBruh/jbl-partybox-ha/blob/main/PROTOCOL.md)

Com o Core parado, instale o componente público.

```powershell
$ha = '.\runtime\venv\Scripts\python.exe'
& $ha .\scripts\install_component.py jbl
Copy-Item .\examples\config\packages\jbl_partylight.yaml.example .\runtime\config\packages\jbl_partylight.yaml
# Se secrets.yaml já existe, acrescente apenas as duas chaves JBL nele.
if (!(Test-Path .\runtime\config\secrets.yaml)) {
    Copy-Item .\examples\config\secrets.yaml.example .\runtime\config\secrets.yaml
}
```

Abra `runtime/config/secrets.yaml`, remova o `#` inicial das duas linhas JBL e informe seu endereço Bluetooth e o número de série da etiqueta. O endereço mostrado abaixo é fictício. O número de série permite confirmar a identidade quando o endereço BLE mudar.

```yaml
jbl_bluetooth_address: '00:11:22:33:44:55'
jbl_serial: 'SUBSTITUA_PELO_SERIAL_DA_ETIQUETA'
```

Para descobrir o endereço, ligue a JBL, feche os apps JBL e rode este comando no PowerShell da máquina que contém o adaptador Bluetooth.

```powershell
& $ha -c "import asyncio; from bleak import BleakScanner; print(asyncio.run(BleakScanner.discover(timeout=15)))"
```

O resultado contém identificadores Bluetooth. Mantenha-o local. Se Bleak ainda não estiver instalado, rode `& $ha -m pip install bleak==3.0.2` dentro do ambiente deste projeto. O `manifest.json` também solicita a dependência quando o Core carrega a integração.

O pacote `jbl_partylight.yaml` registra também o módulo `/local/jbl-partylight-reconnect.js?v=1` em `frontend.extra_module_url`. Se houver outro pacote com essa mesma lista, reúna as URLs em um único local. Valide e inicie o Core.

```powershell
& $ha .\scripts\start.py --check
& $ha .\scripts\start.py
```

As entidades esperadas são `light.jbl_partylight_stick`, `number.jbl_partylight_velocidade` e `button.jbl_partylight_reconectar_bluetooth`. Consulte os IDs efetivos em **Configurações → Dispositivos e serviços → Entidades**, pois o Core pode acrescentar sufixos se existirem nomes repetidos.

O módulo do frontend acrescenta o botão à janela original da luz, inclusive quando ela está indisponível. Se os IDs efetivos mudarem, ajuste `lightId` e `buttonId` em `runtime/config/www/jbl-partylight-reconnect.js`. Depois incremente `v` na URL do módulo, reinicie o Core quando necessário e recarregue o navegador com Ctrl+F5. Esse complemento depende da estrutura do frontend da versão usada pelo projeto. A entidade `button.*` permite reconectar também por automações ou cartões caso o popup mude numa atualização.

A integração consulta o estado aproximadamente a cada 90 segundos. O botão inicia uma nova consulta imediatamente, pode aguardar uma operação já em andamento e permanece disponível quando a luz está indisponível. A JBL precisa estar ligada e ao alcance. Feche o app JBL se estiver ocupando a conexão. A descoberta pode levar dezenas de segundos.

Quando o endereço conhecido não responde, a integração procura anúncios PartyLight Stick e consulta o número de série antes de aceitar uma conexão. O último endereço confirmado fica em memória e será redescoberto após reinício se necessário. O endereço original da configuração continua como identificador das entidades. Assim, a troca de endereço BLE não recria as entidades. Preencha sempre o serial para habilitar essa verificação. Sem ele, a conexão utiliza somente o endereço configurado.

As sessões Bluetooth são temporárias e consultam a resposta da luminária após escrever os ajustes. A reconexão consulta o estado sem enviar comandos de luz. O percentual de brilho do Home Assistant segue a escala reportada pelo firmware, que pode diferir do percentual apresentado no app JBL.

Para manutenção, os arquivos ativos ficam em `runtime/config/custom_components/jbl_partylight/`. `protocol.py` trata descoberta, confirmação do serial e comandos. `coordinator.py` compartilha a conexão e as consultas entre as entidades. `light.py`, `number.py` e `button.py` expõem os controles. `__init__.py` lê o YAML. Atualize a pasta inteira com o Core parado e preserve `runtime/config/secrets.yaml`. O código público de origem fica em `integrations/jbl_partylight/`.

### Ícone opcional do controle infravermelho

O módulo `integrations/frontend/office-tv-power.js` personaliza o ícone de energia da janela de uma entidade remote. Copie para `runtime/config/www/office-tv-power.js`, ajuste `entityId` para o controle IR que cadastrou e acrescente `/local/office-tv-power.js?v=1` à lista `frontend.extra_module_url`. O valor público inicial é `remote.televisao_ir_exemplo`. Os comandos e o estado estimado dependem da integração IR usada.

## 8. Dashboard Smart

Abra **Dashboard Smart** no menu lateral. O tema Smart Glass e as abas de visão geral, TV, dispositivos, clima e clima interno estão em `runtime\config\themes\smart_glass.yaml` e `runtime\config\dashboards\dashboard-smart.yaml`. O arquivo do painel usa sintaxe JSON, válida no YAML do Home Assistant. A revisão inclui cartões da luz JBL e da velocidade dos efeitos. Pode ser editado em um editor de texto.

Os cartões usam entidades de exemplo, como `weather.previsao_exemplo`, `switch.luminaria_exemplo` e `remote.televisao_ir_exemplo`. Copie os IDs reais em **Configurações → Dispositivos e serviços → Entidades** e substitua os exemplos nos cartões e em seus alvos de ação. Remova os cartões dos aparelhos que você não usa. O botão de TV e os comandos IR dependem das ações aceitas pelo controle registrado. Teste `remote.turn_on`, `remote.turn_off` e `remote.send_command` em **Ferramentas do desenvolvedor → Ações** antes de ligar os botões à sua TV. Se o controle oferece só um comando alternado, o estado físico da TV pode divergir do estado visual.

Se editar o modelo público em `examples/`, uma instalação existente continuará usando sua cópia local. Leve a mudança desejada para `runtime\config\dashboards\` ou `themes\` e recarregue o painel. [Configuração de painéis em YAML](https://www.home-assistant.io/dashboards/dashboards/)

## 9. Atualizações, diagnóstico e publicação

- **Antes de atualizar**. Pare o Core e guarde uma cópia privada de `runtime/config/` e `runtime/xiaomi_ble/`. O ambiente Python e os caches podem ser recriados. Trate o backup como privado porque a configuração inclui contas, tokens, pareamentos e chaves.
- **Core e Python**. O patch é vinculado aos bytes da distribuição 2026.10.4. Nesta revisão, os nove arquivos alterados foram comparados com os arquivos ativos do servidor. Os ajustes registram caminho, hashes antes e depois e alterações textuais com índices de linha iniciados em zero. Para atualizar o Core, revise os trechos em `patches/windows-port.json` contra o código upstream novo, atualize as versões e hashes e teste em uma pasta separada. Evite usar `pip install -U homeassistant` sobre o ambiente original. Para reinstalar a versão deste projeto, pare o Core, renomeie apenas `runtime/venv/`, rode o instalador e preserve `runtime/config/`.
- **Componente manual**. Pare o Core. Mova a pasta anterior do componente inteira para fora de `custom_components`, guarde-a em backup privado e instale o componente novo. Com os provedores suportados pelo instalador, revise versão, URL, pasta interna e SHA-256 em `patches/components.json` antes de trocar a versão. Se der erro, restaure a pasta anterior e, se houve migração da integração, restaure também o backup compatível da configuração.
- **Erros de integração**. Consulte **Configurações → Sistema → Registros** e `runtime/config/home-assistant.log`. Se houver erro de resolução DNS na sua rede Windows, tente iniciar o Core com `$env:HASS_WINDOWS_DNS_SERVER = 'IP_DO_SEU_DNS'` no mesmo PowerShell. Use um servidor DNS válido e acessível da sua rede. A variável é opcional e, quando vazia, é usada a configuração padrão do resolvedor.
- **GitHub**. Esta pasta contém a adaptação pronta para um repositório independente com os créditos do upstream em `NOTICE.md` e `LICENSE.md`. Se quiser que o GitHub mostre a relação formal de fork com `home-assistant/core`, crie o fork na página do upstream e adicione esta pasta em um subdiretório dedicado de uma branch. Antes do primeiro commit, rode `git status --short --ignored` e `git diff --cached --name-only` para conferir os arquivos. Mantenha `runtime/`, o ZIP de origem e os dados da sua casa fora do repositório.
