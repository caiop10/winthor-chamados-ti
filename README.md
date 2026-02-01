# Sistema de Chamados TI - WinThor

Sistema de gerenciamento de chamados de TI integrado ao ERP WinThor (TOTVS).

## Funcionalidades

### Para Usuários
- Abrir chamados de suporte técnico
- Anexar arquivos (imagens, documentos)
- Acompanhar status dos chamados
- Responder aos analistas
- Receber notificações de atualizações

### Para Analistas de TI (Setor 10)
- Visualizar todos os chamados abertos
- Assumir chamados para atendimento
- Responder aos usuários
- Mover categoria e prioridade
- Finalizar chamados
- Visualizar anexos de cada etapa
- Receber notificações de novos chamados

### Para Gerência (Matrícula 14)
- Painel com KPIs e métricas
- Análise de SLA (tempo de atendimento)
- Filtros por período, categoria, status
- Visão geral de todos os chamados

## Tecnologias

- **Python 3.11+**
- **CustomTkinter** - Interface gráfica moderna
- **Oracle Database** - Banco de dados WinThor
- **oracledb** - Driver Oracle para Python
- **PyInstaller** - Compilação de executável standalone
- **plyer** - Notificações desktop

## Estrutura do Projeto

```
ROTINA-CHAMADO/
├── config/
│   ├── settings.py      # Configurações do sistema
│   └── database.py      # Pool de conexões Oracle
├── models/
│   └── chamado.py       # Modelo de dados
├── services/
│   ├── chamado_service.py      # Lógica de negócio
│   ├── sla_service.py          # Cálculo de SLA
│   └── notification_service.py # Notificações
├── gui/
│   ├── app.py           # Aplicação principal
│   ├── splash_screen.py # Tela de loading
│   ├── frames/          # Telas da aplicação
│   ├── components/      # Componentes reutilizáveis
│   └── dialogs/         # Diálogos modais
├── utils/
│   ├── logger.py        # Sistema de logs
│   └── helpers.py       # Funções auxiliares
├── sounds/              # Sons de notificação
├── templates/           # Templates Flask (versão web)
├── .env                 # Configurações (não commitado)
├── .env.example         # Template de configuração
├── build_exe.py         # Script de compilação
├── main.py              # Entry point (desenvolvimento)
└── PSAAP9805_LAUNCHER_novo.pyw  # Launcher WinThor
```

## Instalação

### Requisitos
- Python 3.11 ou superior
- Oracle Instant Client 19+
- Acesso ao banco WinThor

### Desenvolvimento

1. Clone o repositório:
```bash
git clone https://github.com/caiop10/winthor-chamados-ti.git
cd winthor-chamados-ti
```

2. Crie o ambiente virtual:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o `.env`:
```bash
copy .env.example .env
# Edite o .env com suas credenciais
```

5. Execute:
```bash
python main.py
```

### Produção (Executável Standalone)

1. Compile o executável:
```bash
python build_exe.py
```

2. O executável será gerado em `C:\winthor\Prod\PSAAP\PSAAP9805_LAUNCHER.exe`

3. Copie para a pasta de deploy:
   - `PSAAP9805_LAUNCHER.exe`
   - `.env`

## Configuração WinThor

### Cadastro da Rotina
- **Código**: 9805
- **Descrição**: Chamados TI
- **Executável**: `P:\ROTINA-CHAMADO\PSAAP9805_LAUNCHER.exe`

### Parâmetros
| Posição | Parâmetro | Descrição |
|---------|-----------|-----------|
| 1 | USUARIOWT | Matrícula do usuário |
| 2 | SENHABD | Senha do banco |
| 3 | ALIASBD | Alias de conexão |
| 4 | USUARIOBD | Usuário do banco |
| 5 | CODROTINA | Código da rotina (9805) |

## Configuração do .env

```env
# Oracle Database
DB_USER=USUARIO
DB_PASSWORD=SENHA
DB_HOST=IP_SERVIDOR
DB_PORT=1521
DB_SERVICE=WINT

# Oracle Client
ORACLE_CLIENT=C:\oracle\instantclient_23_0

# Pool de conexões
DB_POOL_MIN=2
DB_POOL_MAX=10

# Servidor de arquivos (anexos)
SERVIDOR_REDE=\\192.168.0.155\Compartilhamentos
ANEXOS_DIR=\\192.168.0.155\Compartilhamentos\imagens_chamados

# Auto-refresh (segundos)
AUTO_REFRESH_INTERVAL=60
```

## Banco de Dados

### Tabelas Utilizadas
- `PCS_CHAMADOS_TI` - Chamados
- `PCS_CHAMADOS_TI_RESPOSTAS` - Respostas/histórico
- `PCS_CHAMADOS_TI_ANEXOS` - Anexos
- `PCS_CHAMADOS_TI_NOTIF` - Notificações

### Procedures
- `PRC_ABRIR_CHAMADO_TI` - Abrir novo chamado
- `PRC_ASSUMIR_CHAMADO_TI` - Assumir chamado
- `PRC_RESPONDER_CHAMADO_TI` - Responder chamado
- `PRC_MOVER_CHAMADO_TI` - Mover categoria
- `PRC_FINALIZAR_CHAMADO_TI` - Finalizar chamado

### Setup de Notificações
Execute o script para criar tabela e triggers:
```bash
python setup_notificacoes.py
```

## Permissões

| Perfil | Condição | Acesso |
|--------|----------|--------|
| Usuário | Qualquer | Painel Usuário |
| Analista TI | CODSETOR = 10 | Painel TI |
| Gerência | Matrícula = 14 | Painel Gerência |

## Licença

Projeto interno - SOTRIGO

## Autor

Desenvolvido para integração com WinThor ERP.
