# Escola de Música — Banco de Dados

Projeto final de **Laboratório de Banco de Dados** (UCB, 2026/2, Prof. Samuel Novais).
Banco de dados de uma escola de música: pessoas (alunos e professores), instrumentos,
níveis com pré-requisito, turmas, matrículas com histórico de situação, aulas,
frequência, avaliações e mensalidades.

**Integrantes:** _(preencher)_

**SGBD:** MySQL 8.4 · **Notação do MER:** Engenharia da Informação (pé de galinha)

## Estrutura

```
README.md
docs/
  relatorio-etapa1.pdf      relatório único (A1 a A5, implementação e uso de IA)
  mer-conceitual.pdf        MER exportado (A2)
  mer-conceitual.drawio     arquivo-fonte do MER (abrir no draw.io)
  mer-conceitual.png        MER em imagem
  modelo-logico.pdf         esquema relacional e decisões de mapeamento (A4)
  dicionario-dados.pdf      dicionário de dados conceitual (A3)
  guia-da-equipe.md         explicação das decisões e roteiro da apresentação
sql/
  01_ddl.sql                cria o banco e as 15 tabelas (A6)
  02_carga.sql              dados fictícios (A7)
  03_consultas.sql          15 consultas comentadas (A8)
ferramentas/
  gerar_carga.py            gera o 02_carga.sql (semente fixa)
  gerar_mer.py              gera o mer-conceitual.drawio
  gerar_docs.py             gera os PDFs de docs/
```

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
