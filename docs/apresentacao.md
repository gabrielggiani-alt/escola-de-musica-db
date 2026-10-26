# Apresentação da Etapa 2 — passo a passo completo

**Quando:** 23/11/2026, aula 17 · **Duração:** 15 minutos · **Formato:** demonstração AO VIVO
(o professor não quer slides; quer ver a aplicação e o banco funcionando).

Este documento tem 4 partes:

- **A.** Instalar no notebook que vai apresentar (uma vez, dias antes)
- **B.** No dia, 15 minutos antes
- **C.** O roteiro dos 15 minutos, com o que clicar, digitar e falar
- **D.** Se algo der errado

> Escolham **um notebook** para apresentar e façam a parte A nele **antes** do dia.
> Ensaiem a parte C inteira pelo menos uma vez.

---

## A. Instalar (uma vez, no notebook da apresentação)

### A1. Programas

| Programa | Onde baixar | Observação |
|---|---|---|
| **MySQL 8** (Server + Workbench) | dev.mysql.com/downloads/installer | Na instalação, **anote a senha do root**. |
| **Python 3.10 ou mais novo** | python.org/downloads | No Windows, marque **"Add Python to PATH"** na primeira tela. |
| **Git** (opcional) | git-scm.com | Dá para baixar o ZIP pelo GitHub em vez de usar git. |

### A2. Baixar o projeto

GitHub → https://github.com/gabrielggiani-alt/escola-de-musica-db → botão verde **Code → Download ZIP** →
extrair numa pasta (ex.: `C:\escola-de-musica-db`).

### A3. Criar o arquivo `.env`

Na pasta do projeto, copiar o arquivo `.env.example` e renomear a cópia para **`.env`**.
Abrir o `.env` no Bloco de Notas e:

- na linha `# DB_ROOT_PASSWORD=` **apagar o `# `** e escrever a senha do root do MySQL depois do `=`;
- as outras senhas podem ficar como estão (são senhas do ambiente de demonstração).

> O `.env` nunca vai para o GitHub (está no `.gitignore`). É isso que o item B2 pede.

### A4. Instalar as bibliotecas e preparar o banco

Abrir o **Prompt de Comando** (ou PowerShell) **dentro da pasta do projeto** e rodar:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python ferramentas/preparar_banco.py
```

O último comando deve terminar mostrando:

```
ok  01_ddl.sql
ok  02_carga.sql
ok  04_seguranca.sql
ok  05_auditoria.sql
ok  06_otimizacao.sql
ok  app_login       -> r_login
...
PRONTO. Agora rode:  python app/app.py   e abra http://127.0.0.1:5000
```

### A5. Testar

```
python app/app.py
```

Abrir **http://127.0.0.1:5000** no navegador e entrar com `secretaria` / `Secretaria@2026`.
Se abriu, está tudo certo. Para parar a aplicação: **Ctrl + C** no terminal.

---

## B. No dia, 15 minutos antes

1. Ligar o notebook e confirmar que o **MySQL está rodando** (no Windows ele sobe sozinho como serviço).
2. Abrir o Prompt de Comando na pasta do projeto e rodar:
   ```
   .venv\Scripts\activate
   python ferramentas/preparar_banco.py
   ```
   **Isso volta o banco ao estado inicial** e apaga o que foi cadastrado nos ensaios. Sem isso, a
   matrícula de demonstração dá erro de "já matriculado".
3. Subir a aplicação e **deixar este terminal aberto**:
   ```
   python app/app.py
   ```
4. Navegador em **http://127.0.0.1:5000**, ainda **sem logar**.
5. **MySQL Workbench:** abrir a conexão local **duas vezes**. Clique no bloco da conexão na tela
   inicial, volte para a tela inicial (ícone da casinha, no canto superior esquerdo) e clique no
   bloco de novo. Ficam duas abas de conexão, que são **duas sessões diferentes**: a "sessão A" e
   a "sessão B" do experimento de concorrência. Atenção: abrir uma nova aba de consulta dentro da
   mesma conexão **não** cria outra sessão.
6. Na primeira aba do Workbench, deixar aberto o arquivo `sql/08_demo_explain.sql`
   (*File → Open SQL Script*).
7. Deixar à mão o relatório `docs/relatorio-final.pdf`, para mostrar números, se o professor pedir.

---

## C. Roteiro dos 15 minutos

Sugestão de divisão: 5 integrantes, cada um fala uma parte. O professor pode perguntar
qualquer coisa a qualquer um. Leiam o `docs/guia-etapa2.md` (perguntas e respostas).

### 1. Contexto — 2 min (integrante 1)

**Falar:** "Nosso domínio é uma escola de música. Pessoa se especializa em aluno e professor.
Instrumentos têm níveis com pré-requisito. A turma é de um nível, o aluno se matricula,
tem aulas, frequência, avaliações e paga mensalidades. Desde a Etapa 1 acrescentamos duas
tabelas: USUARIO_APP, para o login com senha em hash, e AUDITORIA. Também criamos três
visões, perfis de acesso e índices."

### 2. CRUD e consultas — 4 min (integrante 2)

Entrar com **`secretaria`** / **`Secretaria@2026`**.

1. **Alunos → Novo aluno.** Preencher:
   - Nome: `Maria Teste Apresentação` · CPF: `11122233344` · Nascimento: `15/03/2001`
   - Clicar **Salvar** → aparece "Aluno salvo."
   - **Falar:** "O cadastro grava em PESSOA e ALUNO na mesma transação."
2. Na busca de alunos, digitar `Maria` → **Buscar** → o aluno aparece. Clicar **editar**,
   mudar o e-mail, **Salvar**. Isso mostra o criar, consultar e alterar.
3. **Consulta: inadimplência** → deixar as datas como estão → **Consultar**.
   - **Falar:** "Consulta parametrizada: junção de mensalidade, matrícula e pessoa, com SUM e
     HAVING. Os filtros vão como parâmetro, nunca colados no SQL."
4. **Relatório** → mostrar as duas tabelas.
   - **Falar:** "Este relatório lê de duas visões criadas no banco:
     vw_relatorio_financeiro e vw_ocupacao_turma."

### 3. Transação — 3 min (integrante 3)

**Matrícula:**

1. **Sucesso.** Aluno: **Wagner Rocha Siqueira** · Turma: **VIO-B1-26C** · Valor: `320` → **Matricular**
   → aparece "Matricula ... criada ... (COMMIT)".
   - **Falar:** "Numa transação só, gravou a matrícula, o histórico de situação e a primeira
     mensalidade. Antes, a transação travou a linha da turma com SELECT ... FOR UPDATE para
     contar as vagas."
2. **Falha provocada.** Aluno: **Rafael Nogueira Almeida** · Turma: **VIO-B1-26C** · Valor: `0`
   → **Matricular** → aparece "O valor da mensalidade deve ser maior que zero ... (ROLLBACK)".
   - **Falar:** "O terceiro INSERT violou o CHECK da mensalidade. A matrícula e o histórico já
     tinham sido inseridos, e o ROLLBACK desfez os dois. Detalhe do MySQL: o erro desfaz só o
     comando que falhou. Se não chamássemos ROLLBACK, a matrícula ficaria pendente."
   - **Provar** que nada ficou: **Relatório → Ocupação das turmas**. A VIO-B1-26C tem 7 ocupadas:
     6 antes da demonstração, mais o Wagner. O Rafael não entrou.

### 4. Restrições em ação — 2 min (integrante 4)

Ainda logado como secretaria:

1. **Alunos → Novo aluno** com CPF `68045717847`, que já é do Arthur Gomes Lima → aparece
   "Já existe uma pessoa cadastrada com este CPF (RN01)."
2. **Alunos** → no **Arthur Gomes Lima** clicar **excluir** → aparece "Não é possível excluir:
   o aluno ou a turma tem matrículas (RN16)."
3. **Matrícula** → qualquer aluno na turma **BAT-B2-26B** → aparece "Turma sem vagas".
- **Falar:** "O usuário nunca vê a exceção do driver. Lemos o nome da restrição violada e
  mostramos a regra de negócio. Por isso nomeamos todas as restrições na Etapa 1."

### 5. Desempenho e acesso — 3 min (integrante 5)

**Desempenho (Workbench, primeira aba):**

1. Executar `sql/08_demo_explain.sql` com o raio (⚡).
2. Mostrar os dois resultados de EXPLAIN:
   - **Antes:** `type = ALL`, `key = NULL`, `rows = 54`, "Using filesort": leu a tabela inteira e ordenou.
   - **Depois:** `type = range`, `key = idx_pessoa_nome`, `rows = 5`, sem filesort.
   - **Falar:** "Com 50 mil pessoas, medimos 12,3 ms antes e 0,18 ms depois. Os três estudos
     estão no relatório."

**Acesso, o mesmo sistema sob dois perfis:**

3. No navegador: **sair** → entrar com **`prof.julia`** / **`Professor@2026`**.
4. O menu mostra só Turmas, Consulta de desempenho e Relatório.
5. Digitar na barra de endereço **http://127.0.0.1:5000/alunos** → aparece "Seu perfil não tem
   permissão (o banco recusou)".
   - **Falar:** "Não foi a tela que bloqueou, foi o MySQL. O professor conecta com um usuário de
     banco sem SELECT na tabela PESSOA. Ele vê os alunos só pela visão vw_aluno_contato, sem CPF."
6. **Consulta: desempenho** → Violão, média `6` → **Consultar** → funciona para o professor.

**Concorrência, se der tempo ou se o professor pedir.** Precisa das duas abas do Workbench:

| Aba 1 (sessão A) | Aba 2 (sessão B) |
|---|---|
| `USE escola_musica;` | `USE escola_musica;` |
| `START TRANSACTION;` | |
| `SELECT vagas FROM turma WHERE id_turma=7 FOR UPDATE;` | |
| | `START TRANSACTION;` |
| | `SELECT vagas FROM turma WHERE id_turma=7 FOR UPDATE;` ← **fica girando (esperando)** |
| `COMMIT;` | ← **libera na hora** |
| | `ROLLBACK;` |

- **Falar:** "A sessão B ficou bloqueada até a A terminar. É assim que duas secretárias não
  vendem a mesma última vaga. Sem a trava, nosso experimento colocou 9 alunos numa turma de 8."
- Plano B, mais rápido, no terminal: `python ferramentas/experimento_concorrencia.py`. Ele mostra
  as duas sessões e o tempo de espera.

### 6. Arguição — 1 min

O professor sorteia integrantes. As respostas estão no `docs/guia-etapa2.md`, seção 3.

---

## D. Se algo der errado

| Problema | Solução |
|---|---|
| `python` não é reconhecido | Reinstalar o Python marcando "Add Python to PATH", ou usar `py` no lugar de `python`. |
| "Não consegui conectar no MySQL como root" | O MySQL não está ligado (Windows: Serviços → MySQL80 → Iniciar) ou a senha do root no `.env` está errada. |
| "Falta DB_SENHA_... no arquivo .env" | O `.env` não foi criado. Ver passo A3. |
| "Falta FLASK_SECRET_KEY" | Mesmo caso: falta o `.env`. |
| Matrícula do Wagner dá "já está matriculado" | O banco ficou com dados do ensaio. Rodar `python ferramentas/preparar_banco.py` de novo. |
| Login não entra | Se o `preparar_banco.py` não terminou com PRONTO, rodar de novo. |
| A sessão B do Workbench não fica esperando | As duas abas são a mesma conexão. Abrir a conexão de novo pela tela inicial do Workbench. |
| Acentos estranhos (Ã£) | Rodar o `preparar_banco.py` em vez de colar os scripts no terminal. |

### Logins (só demonstração)

| Login | Senha | Perfil |
|---|---|---|
| `admin` | `Admin@2026` | ADMIN — tudo, inclusive a tela de Auditoria |
| `secretaria` | `Secretaria@2026` | SECRETARIA |
| `prof.julia` | `Professor@2026` | PROFESSOR |

Extra para quem quiser mostrar: entrar como **admin → Auditoria** depois de dar baixa numa
mensalidade (tela Mensalidades → **pago**). Aparece quem alterou, quando e os valores antes e depois.
