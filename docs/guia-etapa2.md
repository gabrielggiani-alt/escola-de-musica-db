# Guia da equipe — Etapa 2

Este guia é para quem não participou da montagem da Etapa 2. Na demonstração de
23/11, o professor sorteia integrantes e pergunta **qualquer parte a qualquer um**.
Leia este guia e rode a aplicação pelo menos uma vez antes da aula.

O relatório completo é `docs/relatorio-etapa2.pdf`. Aqui está o essencial, em
linguagem direta.

## 1. Rodar em 15 minutos

Siga a seção **"Etapa 2 — rodando a aplicação"** do `README.md`. Resumo:
scripts `01`, `02`, `04` e `05` no MySQL → copiar `.env.example` para `.env` →
`pip install -r requirements.txt` → `python ferramentas/criar_usuarios_banco.py`
→ `python app/app.py`.

## 2. O que cada arquivo novo faz, em uma frase

| Arquivo | Em uma frase |
|---|---|
| `sql/04_seguranca.sql` | Cria a tabela de logins com senha em hash, três visões e quatro papéis (perfis) do MySQL com o que cada um pode fazer. |
| `sql/05_auditoria.sql` | Cria a tabela AUDITORIA e dois gatilhos que gravam quem mudou mensalidade e matrícula. |
| `sql/06_otimizacao.sql` | Gera 50 mil pessoas falsas, mede 3 consultas, cria índices, mede de novo e apaga as pessoas falsas. |
| `sql/07_transacoes.sql` | Mostra uma matrícula que dá certo (COMMIT) e uma que falha no meio (ROLLBACK). |
| `app/repositorio.py` | Todo o SQL da aplicação. É o arquivo mais importante para a arguição. |
| `app/erros.py` | Transforma "Error 1062 Duplicate entry" em "Já existe uma pessoa com este CPF". |
| `ferramentas/criar_usuarios_banco.py` | Cria os usuários do MySQL lendo as senhas do `.env`. |
| `ferramentas/experimento_concorrencia.py` | Duas conexões tentam a última vaga ao mesmo tempo. |

## 3. As perguntas que o professor provavelmente vai fazer

**"Qual é a operação transacional? Por que precisa ser transação?"**
Matricular aluno. Ela grava em três tabelas: MATRICULA, HISTORICO_SITUACAO e
MENSALIDADE. Se uma falhar e as outras ficarem, temos aluno sem cobrança ou cobrança
sem aluno. Ou grava as três, ou nenhuma.

**"Mostre a falha."**
Tela Matrícula, valor **0**. O terceiro INSERT viola `ck_mensalidade_valor`. A
aplicação faz ROLLBACK e nada fica gravado.

**"O MySQL não desfaz sozinho quando dá erro?"**
**Não.** Ele desfaz só o comando que falhou. A matrícula inserida antes continua
pendente na conexão. Por isso existe o `con.rollback()` no `except` do
`repositorio.matricular()`. O `07_transacoes.sql` mostra isso: dentro da transação,
depois do erro, a contagem dá 1; depois do ROLLBACK, dá 0.

**"O que é o FOR UPDATE?"**
Uma trava na linha da turma. Se duas secretárias matriculam na mesma turma ao mesmo
tempo, a segunda espera a primeira terminar. Sem isso, as duas veem "tem 1 vaga" e
as duas matriculam: no nosso experimento ficaram **9 alunos numa turma de 8 vagas**.
Com a trava, a segunda esperou 1,48 s, viu a turma cheia e desistiu.

**"Qual o nível de isolamento e por quê?"**
REPEATABLE READ, o padrão do MySQL. Trocar o nível não resolveria o problema da
vaga, porque o problema é ler, decidir e gravar sem trava. SERIALIZABLE resolveria,
mas travaria todas as leituras do sistema, inclusive os relatórios. A trava
explícita só na turma é mais precisa.

**"Como vocês evitam injeção de SQL?"**
Todo valor do usuário vai como parâmetro (`%s`), nunca colado no texto do SQL.
Teste: na busca de alunos, digitar `' OR 1=1 -- ` devolve **0 alunos**. Se o SQL
fosse montado colando texto, devolveria **todos os 47**.

**"Onde está a senha do banco?"**
No arquivo `.env`, que está no `.gitignore`. O repositório só tem o `.env.example`.

**"Como a senha do usuário é guardada?"**
Não é guardada. Guardamos o hash PBKDF2 (SHA-256, 200 mil repetições) da senha
misturada a um sal aleatório, diferente para cada usuário. O sal faz senhas iguais
virarem hashes diferentes.

**"Quais são os perfis e o que muda?"**
Cada perfil conecta ao MySQL com um usuário diferente:
- **ADMIN** faz tudo.
- **SECRETARIA** cuida de cadastro, matrícula e mensalidade, mas não apaga mensalidade (REVOKE) e não lê a auditoria.
- **PROFESSOR** não vê CPF nem mensalidades. Vê os alunos só pela visão `vw_aluno_contato`.

Quem barra é o **banco**, não a tela. Teste: logar como `prof.julia` e abrir
`/alunos` no navegador. O banco recusa.

**"Explique um dos índices."**
Busca por nome: antes, o banco lia as 50 mil pessoas (*table scan*), 12 ms. Com o
índice em `nome`, vai direto na faixa de nomes que começam com o texto, 0,18 ms.
Só funciona com `LIKE 'texto%'`. Com `LIKE '%texto'` o índice não ajuda.

**"Por que o índice composto está nessa ordem?"**
`(data_pagamento, data_vencimento)`: primeiro a coluna testada por **igualdade**
(`IS NULL`), depois a de **faixa** (`<`). Coluna de faixa sempre por último.

**"Teve índice que não ajudou?"**
O do relatório mensal ajudou pouco e de forma instável: 21% numa execução, 51% em
outra. A consulta precisa ler todas as linhas de qualquer jeito, porque é um
relatório do histórico inteiro. O PDF diz que resultado fraco bem explicado vale nota.

**"O que os gatilhos auditam e por quê?"**
Mensalidade, porque é dinheiro, e situação da matrícula, porque libera vaga e muda
o histórico do aluno. Gravam quem (login da aplicação e usuário do MySQL), quando,
e o antes e depois. Frequência não é auditada: tem muito movimento e nenhum
impacto financeiro.

**"Vale particionar alguma tabela?"**
Não. Em 2 anos o banco inteiro fica em poucos megabytes. Particionamento é para
dezenas de milhões de linhas.

## 4. Pendências da equipe antes da entrega

- [ ] **Devolutiva da Etapa 1:** se o professor apontar correções, aplicar e registrar na seção 9 do relatório (`docs/relatorio-etapa2.md`), depois rodar `python ferramentas/gerar_relatorio_etapa2.py` e o `pdfunite` do README.
- [ ] **Declaração de uso de IA** (seção 11 do relatório): conferir se descreve o uso real da equipe.
- [ ] **Commits por autor:** o professor usa o histórico do Git para a nota individual (seção 8 do enunciado).
- [ ] Cada integrante rodar a aplicação e a demonstração (seção 10 do relatório) pelo menos uma vez.
