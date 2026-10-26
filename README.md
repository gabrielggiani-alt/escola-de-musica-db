# Escola de Música — Banco de Dados

Projeto final de **Laboratório de Banco de Dados** (UCB, 2026/2, Prof. Samuel Novais).
Banco de dados de uma escola de música: pessoas (alunos e professores), instrumentos,
níveis com pré-requisito, turmas, matrículas com histórico de situação, aulas,
frequência, avaliações e mensalidades.

**Integrantes:**

Gabriel Gomes Giani, Paulo Henrique Barreto da Rocha Dantas, Letícia Paolino, Artur Henrique Caetano e Lucas de Oliveira Faustino.

**SGBD:** MySQL 8.4 · **Notação do MER:** Engenharia da Informação (pé de galinha)

## Estrutura

```
README.md
.env.example                modelo do .env (o .env real NAO vai para o Git)
requirements.txt            bibliotecas Python da aplicacao
docs/
  relatorio-etapa1.pdf      relatório da Etapa 1 (A1 a A5, implementação e uso de IA)
  relatorio-final.pdf       RELATÓRIO CONSOLIDADO PARA ENTREGA: Etapa 2 + Etapa 1 (item B8)
  relatorio-etapa2.pdf      relatório da Etapa 2 (B1 a B8 e uso de IA)
  relatorio-etapa2.md       mesmo relatório em texto (fonte do PDF)
  guia-etapa2.md            explicação da Etapa 2 para a equipe e roteiro da demonstração
  resultados-*.txt          saída real dos scripts (consultas, otimização, transações, concorrência)
  mer-conceitual.pdf        MER exportado (A2)
  mer-conceitual.drawio     arquivo-fonte do MER (abrir no draw.io)
  mer-conceitual.png        MER em imagem
  modelo-logico.pdf         esquema relacional e decisões de mapeamento (A4)
  dicionario-dados.pdf      dicionário de dados conceitual (A3)
  guia-da-equipe.md         explicação das decisões da Etapa 1
sql/
  01_ddl.sql                cria o banco e as 15 tabelas (A6)
  02_carga.sql              dados fictícios (A7)
  03_consultas.sql          15 consultas comentadas (A8)
  04_seguranca.sql          usuários da aplicação (hash+sal), visões e papéis GRANT/REVOKE (B5)
  05_auditoria.sql          tabela de auditoria e 2 gatilhos (B6)
  06_otimizacao.sql         3 estudos de EXPLAIN antes/depois com índices (B4)
  07_transacoes.sql         COMMIT, ROLLBACK provocado e roteiro de concorrência (B3)
app/                        aplicação web em Flask (B1, B2)
  app.py                    telas (rotas)
  repositorio.py            TODO o SQL da aplicação, sempre parametrizado
  db.py                     conexão: um usuário do MySQL por perfil, senhas do .env
  erros.py                  traduz erros do MySQL em mensagens para o usuário
  templates/                páginas HTML
ferramentas/
  criar_usuarios_banco.py   cria os usuários do MySQL da aplicação (senhas do .env)
  experimento_concorrencia.py  roda o experimento de duas sessões (B3)
  gerar_relatorio_etapa2.py gera docs/relatorio-etapa2.pdf a partir do .md
  gerar_carga.py            gera o 02_carga.sql (semente fixa)
  gerar_mer.py              gera o mer-conceitual.drawio
  gerar_docs.py             gera os PDFs da Etapa 1
```

## Rodando em outro computador (laboratório da faculdade)

1. Baixar o projeto: botão verde **Code → Download ZIP** no GitHub, ou `git clone`.
2. Abrir o MySQL Workbench e conectar no servidor MySQL da máquina.
3. Executar `sql/01_ddl.sql`, `sql/02_carga.sql` e `sql/03_consultas.sql`, nesta ordem.

Os scripts não dependem de nada além de um MySQL 8. O `01_ddl.sql` recria o banco do
zero, então pode ser executado quantas vezes for preciso.

Se não houver MySQL disponível na máquina, `docs/resultados-consultas.txt` traz a saída
das 15 consultas já executada.

## Como reconstruir o banco do zero

Com um MySQL 8 rodando, na pasta do projeto:

```bash
mysql -u root -p < sql/01_ddl.sql
mysql -u root -p < sql/02_carga.sql
mysql -u root -p --table < sql/03_consultas.sql
```

O `01_ddl.sql` começa com `DROP DATABASE IF EXISTS escola_musica`, então pode ser
rodado quantas vezes for preciso. No MySQL Workbench: *File → Open SQL Script*,
abrir cada arquivo na ordem e executar com o raio (⚡).

## Como regenerar os arquivos gerados

```bash
python ferramentas/gerar_carga.py    # sql/02_carga.sql
python ferramentas/gerar_mer.py      # docs/mer-conceitual.drawio
python ferramentas/gerar_docs.py     # docs/*.pdf (usa o Microsoft Edge)
```

Todos os dados são fictícios. Os CPFs são sequências aleatórias sem dígito
verificador válido, e os e-mails usam o domínio reservado `exemplo.com`.

## Etapa 2 — rodando a aplicação

Precisa de **MySQL 8** e **Python 3.10+**.

**1. Banco** (na pasta do projeto; no Workbench, abrir e executar cada arquivo nesta ordem):

```bash
mysql -u root -p < sql/01_ddl.sql
mysql -u root -p < sql/02_carga.sql
mysql -u root -p < sql/04_seguranca.sql
mysql -u root -p < sql/05_auditoria.sql
mysql -u root -p --table < sql/06_otimizacao.sql          # opcional: estudo de índices
mysql -u root -p --force --table < sql/07_transacoes.sql  # opcional: demo de transação
```

> Sempre que rodar o `01_ddl.sql` de novo, rode também o `04`, o `05` e o passo 3
> abaixo: o `01` apaga o banco, e o `04` recria os papéis do MySQL.

**2. Configuração:** copiar `.env.example` para `.env` e trocar as senhas. O `.env`
está no `.gitignore` e nunca deve ser enviado ao GitHub.

**3. Bibliotecas e usuários do MySQL:**

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python ferramentas/criar_usuarios_banco.py
```

**4. Subir a aplicação:**

```bash
python app/app.py
```

Abrir http://127.0.0.1:5000

### Logins de demonstração

Contas **só para demonstração**; no banco ficam apenas hash e sal (PBKDF2).

| Login | Senha | Perfil |
|---|---|---|
| `admin` | `Admin@2026` | ADMIN — tudo, inclusive a tela de Auditoria |
| `secretaria` | `Secretaria@2026` | SECRETARIA — alunos, turmas, matrícula, mensalidades |
| `prof.julia` | `Professor@2026` | PROFESSOR — turmas, consulta de desempenho; sem CPF |

### Regerar o relatório consolidado

```bash
python ferramentas/gerar_relatorio_etapa2.py
pdfunite docs/relatorio-etapa2.pdf docs/relatorio-etapa1.pdf docs/relatorio-final.pdf
```

(`pdfunite` vem no pacote poppler; qualquer ferramenta que junte PDFs serve.)
