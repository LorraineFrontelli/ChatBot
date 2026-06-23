# Assessor.IA

Assistente pessoal de finanças e agenda. Conversa em linguagem natural, registra transações financeiras no banco de dados e responde dúvidas com base em um FAQ oficial.

---

## Como funciona

O usuário digita uma mensagem no terminal. Um **Roteador** classifica a intenção e encaminha para o agente correto. O agente **Especialista** processa e retorna um JSON estruturado. O **Orquestrador** transforma esse JSON em uma resposta final legível para o usuário.

```
Usuário
  └─► Roteador
        ├─► Agente Financeiro ──► Orquestrador ──► Usuário
        ├─► Agente Agenda     ──► Orquestrador ──► Usuário
        ├─► Agente FAQ        ──────────────────── Usuário
        └─► Resposta direta (saudações / fora de escopo)
```

---

## Agentes

### Roteador
Classifica a mensagem do usuário e decide para onde encaminhar. Responde diretamente em casos de saudação, small talk ou perguntas fora de escopo. Para os demais casos emite um protocolo `ROUTE=[financeiro|agenda|faq]` e repassa a mensagem original.

### Orquestrador
Recebe o JSON retornado pelo agente especialista e gera a resposta final formatada para o usuário. Nunca inventa informações — apenas transforma o que o especialista retornou.

### Agente Financeiro (Especialista)
Responsável por tudo relacionado a finanças: registrar gastos e receitas, consultar transações, calcular saldo. Tem acesso a tools que interagem com o banco de dados PostgreSQL.

**Tools disponíveis:**
- `add_transaction` — registra uma transação (INCOME, EXPENSES ou TRANSFER)
- `query_transactions` — busca transações com filtros por data, tipo, categoria e descrição
- `total_balance` — retorna o saldo acumulado de todo o histórico
- `daily_balance` — retorna o saldo acumulado até uma data específica
- `update_transaction` — atualiza uma transação existente por ID ou por texto/data

### Agente FAQ (Consultor)
Responde dúvidas sobre o funcionamento do sistema, políticas, regras e privacidade. Usa RAG (busca em documento) sobre o FAQ oficial em PDF. Não passa pelo Orquestrador — responde diretamente ao usuário.

### Agente Agenda (Especialista)
Gerencia compromissos, eventos e lembretes. Passa pelo Orquestrador para formatar a resposta final.

---

## Banco de dados

PostgreSQL com 4 tabelas:

- **`transaction_types`** — tipos de transação: `INCOME`, `EXPENSES`, `TRANSFER`
- **`categories`** — categorias: comida, transporte, moradia, saúde, lazer, etc.
- **`transactions`** — transações financeiras com valor, tipo, categoria, data e texto original
- **`events`** — eventos de agenda com título, horário de início/fim, local e notas

---

## Modelos de linguagem

| Variável           | Modelo                                     | Uso                         |
|---                 |---                                         |---                          |
| `llm_especialista` | Gemini 2.5 Flash (fallback: LLaMA 3.3 70B) | Agentes financeiro e agenda |
| `llm_rapido`       | GPT-OSS 120B via Groq                      | Roteador e orquestrador     |

---

## Configuração

### 1. Instalar dependências

```bash
pip install langchain langchain-google-genai langchain-groq langchain-community
pip install langgraph psycopg2-binary pydantic-settings python-dotenv
pip install faiss-cpu pypdf langchain-text-splitters rich pymongo
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY=sua_chave_aqui
GROQ_API_KEY=sua_chave_aqui

PGUSER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=nome_do_banco
DB_PORT=5432

MONGODB_URI=mongodb+srv://usuario:senha@cluster.mongodb.net/?retryWrites=true&w=majority
```

### 3. Criar o banco de dados

```bash
psql -U seu_usuario -d nome_do_banco -f sql/ScriptBancoDeDados.sql
```

### 4. Executar

```bash
python -m src.main
```

---

## Encerrando

Digite qualquer um dos comandos abaixo para sair:

```
sair | exit | tchau | bye | end | fim
```
