# Proposta de melhoria · Pontuação divergente

**Contexto:** campanha Desafio Trimestral Q3/2026 · análise de 640 chamados e 9.999 vendas importadas
**Fontes:** `sql/06_recorrencia.sql`, `reports/indicadores_suporte.xlsx` (abas Pareto e Recorrência)

## 1. O problema, em números

| Indicador | Pontuação divergente | Demais categorias |
|---|---:|---:|
| Participação no volume | 32,3% (207 chamados) | 67,7% |
| Resolução dentro do SLA | 56,6% | 81,2% |
| Reabertura | 17,4% | 3,2% |

É a maior categoria, a mais lenta e a que mais volta. Cada reabertura é um participante que recebeu uma resposta e não acreditou nela.

## 2. Evidência da causa

Média de chamados de pontuação por semana:

- semanas **sem** reimportação: **7,9**
- semanas 5 e 9 (**com** reimportação): **59,5** — cerca de 7,5×

| Lote | Vendas no lote | Duplicatas |
|---|---:|---:|
| LOTE-05 | 1.403 | 696 (reimportado inteiro) |
| LOTE-09 | 960 | 248 (reimportado parcialmente) |
| demais | ~650–850 | 0 |

## 3. Cinco porquês

1. **Por que o participante abriu chamado?** A pontuação no app subiu e depois caiu (ou não bateu com o que ele calculou).
2. **Por que a pontuação oscilou?** A prévia foi calculada com vendas duplicadas e corrigida depois.
3. **Por que havia vendas duplicadas?** O mesmo arquivo de vendas foi importado duas vezes (o LOTE-05 inteiro; o LOTE-09 após uma importação interrompida).
4. **Por que a plataforma aceitou a segunda importação?** Não existe verificação de lote já processado nem chave única por venda.
5. **Por que não foi pego antes da prévia?** As regras de qualidade não rodam antes de publicar a prévia — só na apuração final.

**Causa raiz:** importação não idempotente + ausência de validação antes da publicação da prévia.

## 4. Plano de ação

| # | Ação | Tipo | Dono sugerido | Esforço | Efeito esperado |
|---|---|---|---|---|---|
| 1 | Chave de idempotência por venda (hash de matrícula + data + cliente + produto + quantidade + valor) e rejeição de duplicata na importação | Sistema | Produto / Dev | Médio | elimina DQ01 na origem |
| 2 | Hash do arquivo de lote: se o mesmo arquivo for enviado de novo, pedir confirmação | Sistema | Produto / Dev | Baixo | evita reimportação acidental |
| 3 | Rodar as regras DQ01–DQ07 **antes** de publicar a prévia; publicar só com 0 ocorrências bloqueantes ou com aceite de Campanhas | Processo | Suporte & Dados | Baixo | prévia deixa de oscilar |
| 4 | Limitar resgate durante a campanha a um percentual do saldo da prévia (ex.: 50%) até a apuração final | Regra de negócio | Campanhas / Cliente | Baixo | evita os 19 resgates sem lastro |
| 5 | Alerta para resgate acima de um teto (ex.: 10.000 pts em um pedido) | Sistema | Produto / Dev | Baixo | barra os 9 pedidos anômalos |
| 6 | Artigo KB-001 + macro de resposta para "pontuação divergente" com o extrato de vendas do participante | Suporte | Suporte & Dados | Baixo | resposta mais rápida e com evidência, menos reabertura |
| 7 | Alerta (e-mail/Slack) na abertura de chamado Crítico | Ferramenta de tickets | Suporte & Dados | Baixo | ataca o SLA de 1ª resposta de 29% |

Prioridade sugerida: **3, 6 e 7 já** (não dependem de desenvolvimento) → **1 e 2** no próximo ciclo de produto → **4 e 5** negociados com o cliente para a próxima campanha.

## 5. Ganho estimado

Se as semanas 5 e 9 tivessem o volume de uma semana normal, seriam **~103 chamados a menos** no trimestre (de 119 para ~16), cerca de **16% da fila total**. Só retirar esse pico já levaria o SLA de resolução da fila de 73,3% para cerca de **77%**; o restante do ganho vem das ações 6 e 7 (resposta com evidência e alerta para Críticos).

Do lado financeiro, a conferência evitou **129 mil pontos** pagos indevidamente e **28 resgates** sem lastro neste trimestre.

## 6. Como medir se funcionou

| Indicador | Hoje | Meta próxima campanha |
|---|---:|---:|
| Ocorrências DQ01 na apuração | 944 | 0 |
| % do volume em "Pontuação divergente" | 32% | < 15% |
| Reabertura em "Pontuação divergente" | 17,4% | < 5% |
| SLA de 1ª resposta — Crítica | 29% | > 90% |
