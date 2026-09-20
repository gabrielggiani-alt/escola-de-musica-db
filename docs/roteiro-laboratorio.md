# Rodar o projeto no computador do laboratório — passo a passo

Apresentação: 21/09/2026, aula 8. 12 minutos por equipe.
Repositório: https://github.com/gabrielggiani-alt/escola-de-musica-db

Este roteiro serve para qualquer computador com MySQL 8, não só o do laboratório.
Os scripts não dependem de nada instalado na máquina do Gabriel.

---

## Antes de sair de casa

- [ ] Conferir que o repositório abre **numa aba anônima** (sem login). Se abrir, o computador da faculdade também abre.
- [ ] Levar um pendrive com a pasta `sql/` copiada, caso a internet da UCB falhe.
- [ ] Opcional (plano B): levar no pendrive a pasta inteira `D:\ferramentas\mysql` (1,4 GB), que roda sem instalar nada.
- [ ] Chegar com **pelo menos 20 minutos** de antecedência. Todo o risco desta apresentação está no ambiente, não no conteúdo.

---

## Passo 1 — Baixar o projeto na máquina da UCB

1. Abrir o navegador em `https://github.com/gabrielggiani-alt/escola-de-musica-db`
2. Clicar no botão verde **Code** e depois em **Download ZIP**
3. O arquivo cai em `Downloads` como `escola-de-musica-db-main.zip`
4. Clicar com o botão direito → **Extrair tudo** → **Extrair**

Guardar o caminho da pasta extraída. Costuma ser algo como:
`C:\Users\<usuario>\Downloads\escola-de-musica-db-main\escola-de-musica-db-main\`

> **Sem internet?** Copiar a pasta `sql` do pendrive para a Área de Trabalho e seguir do Passo 2.

---

## Passo 2 — Abrir o MySQL Workbench e conectar

1. Abrir o **MySQL Workbench** (menu Iniciar, digitar "workbench")
2. Na tela inicial aparecem as conexões salvas. Provavelmente já existe uma, chamada
   **Local instance MySQL80** ou parecida. Clicar nela.
3. Se pedir senha, é a senha do `root` **daquele laboratório** (perguntar ao professor ou ao técnico).
   A senha do computador do Gabriel não vale aqui.

### Se não existir nenhuma conexão salva

1. Clicar no **`+`** ao lado de "MySQL Connections"
2. Preencher:
   - **Connection Name:** `local`
   - **Hostname:** `127.0.0.1` · **Port:** `3306`
   - **Username:** `root`
3. **Test Connection** → tem que dizer que conectou → **OK**

### Como saber se o servidor está ligado

No menu da esquerda, em **Administration → Server Status**, o indicador precisa estar
verde ("Running"). Se estiver vermelho, o servidor MySQL da máquina está parado:
abrir o menu Iniciar, procurar **Serviços**, achar **MySQL80** na lista, botão direito → **Iniciar**.

---

## Passo 3 — Executar os três scripts, nesta ordem

Para cada arquivo, sempre a mesma sequência:

1. **File → Open SQL Script...** (ou `Ctrl+Shift+O`)
2. Escolher o arquivo dentro da pasta `sql` do projeto
3. Clicar no **raio ⚡** da barra de cima (ou `Ctrl+Shift+Enter`) — isso executa o arquivo inteiro
4. Olhar o painel **Output**, embaixo: cada comando vira uma linha. Todas com ✓ verde = deu certo

| Ordem | Arquivo | O que faz | Quanto demora |
|---|---|---|---|
| 1º | `01_ddl.sql` | Apaga o banco se existir e cria as 15 tabelas | alguns segundos |
| 2º | `02_carga.sql` | Insere os dados (a maior tabela tem 901 linhas) | até uns 30 segundos |
| 3º | `03_consultas.sql` | Roda as 15 consultas e abre 15 abas de resultado | alguns segundos |

**A ordem importa.** A carga depende das tabelas, e as consultas dependem dos dados.

Depois do 2º script, clicar no ícone de **atualizar** no painel **Schemas** (esquerda).
O banco `escola_musica` aparece, e dentro dele as 15 tabelas.

---

## Passo 4 — O que mostrar na apresentação

Para rodar **uma consulta só**: selecionar o texto dela com o mouse e apertar **`Ctrl+Enter`**.
(O raio ⚡ roda o arquivo inteiro; o `Ctrl+Enter` roda só o que está selecionado.)

**Sugestão de sequência, na parte de 2 minutos de scripts:**

1. **Mostrar que o banco nasceu do zero:** rodar o `01_ddl.sql` na frente do professor e mostrar o Output sem erro. É exatamente o teste eliminatório do enunciado.
2. **C11 — aprovação:** mostra os alunos de 2026/1 com média, frequência e o resultado APROVADO ou REPROVADO. É a consulta que responde a regra RN29.
3. **C15 — auditoria:** volta uma linha por regra que o banco não consegue garantir sozinho, todas com **0 violações**. É a prova de que os dados respeitam as regras de negócio.

Se sobrar tempo, a **C07** é boa: usa LEFT JOIN e mostra o nível de flauta com 0 turmas,
o que prova que o LEFT JOIN está fazendo o trabalho dele.

---

## Erros comuns e o que fazer

| Mensagem na tela | O que é | Solução |
|---|---|---|
| `Can't connect to MySQL server on '127.0.0.1'` | O servidor não está rodando | Serviços → MySQL80 → Iniciar |
| `Access denied for user 'root'@'localhost'` | Senha errada | Pedir a senha do laboratório. Não é a de casa |
| `Access denied; you need CREATE privilege` | O usuário não pode criar banco | Pedir um usuário com permissão ao técnico, ou usar o plano B (pendrive) |
| `Unknown database 'escola_musica'` | Rodou a carga antes do DDL | Rodar o `01_ddl.sql` primeiro |
| `Table 'x' already exists` | Rodou o DDL pela metade | Rodar o `01_ddl.sql` inteiro de novo: ele começa com DROP DATABASE |
| `Error Code: 1406 Data too long` | Não deve acontecer; foi corrigido | Conferir se está rodando a versão baixada hoje do GitHub |
| Caracteres estranhos (Ã§, Ã£) | Problema de acentuação na exibição | Não afeta a nota. O banco está em utf8mb4 |

---

## Se nada funcionar: plano C

O arquivo **`docs/resultados-consultas.txt`**, que também está no repositório, tem a saída
das 15 consultas já executada, com os resultados reais. Abrir esse arquivo e mostrar na tela.

Não é o ideal, mas é melhor do que ficar sem demonstração. E o enunciado da Etapa 1 não
exige demonstração ao vivo: isso só vira obrigatório na Etapa 2.
