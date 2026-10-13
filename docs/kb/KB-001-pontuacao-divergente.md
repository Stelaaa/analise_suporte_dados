# KB-001 · Pontuação divergente

**Categoria:** Pontuação divergente · **Prioridade padrão:** Alta · **Atualizado em:** out/2026

## Sintoma

O participante diz que a pontuação no app está errada: menor do que ele calculou, ou mudou de um dia para o outro.

## Causas mais comuns (em ordem de frequência neste trimestre)

1. **Venda duplicada** por reimportação de lote → prévia sobe e depois cai na correção.
2. **Venda fora do período** da campanha (junho / outubro) → não conta.
3. **Venda com valor zero ou negativo** (estorno) → não conta.
4. **Participante sem meta cadastrada** → fica "Pendente" e não pontua.
5. Venda registrada em **outra matrícula** (ex.: matrícula com erro de digitação no arquivo do cliente).

## Diagnóstico (5 minutos)

```sql
-- 1. O que foi bloqueado para esta matrícula e por quê
SELECT regra, id_registro, detalhe
FROM dq_ocorrencias
WHERE matricula = 'HZ0133';

-- 2. Como foi apurado
SELECT situacao, meta_faturamento, faturamento, atingimento,
       faixa, pontos_faturamento, pontos_positivacao, pontos_total
FROM apuracao
WHERE matricula = 'HZ0133';
```

## Resposta

Use o modelo abaixo e **anexe o extrato** (vendas válidas e bloqueadas com o motivo). Sem extrato, a chance de reabertura é alta.

> Olá, [nome]! Conferimos suas vendas da campanha Desafio Trimestral.
> Seu faturamento válido no período foi de **R$ [valor]**, que corresponde a **[x]%** da sua meta de R$ [meta] — faixa **[faixa]**, **[pontos] pontos**. [Se houver bônus: você também atingiu a meta de positivação, +1.500 pontos.]
> A diferença em relação ao valor que apareceu antes acontece porque **[n] vendas** foram registradas em duplicidade na importação de [data] e já foram corrigidas. Segue em anexo o extrato com todas as suas vendas consideradas.
> Se alguma venda sua não estiver na lista, responda este chamado com o número do pedido que verificamos.

## Quando escalar

- Mais de 5 participantes da mesma regional com o mesmo sintoma → incidente Crítico, avisar Campanhas.
- Venda que o participante comprova e não está na base → gestor da conta (dado do cliente).

## Prevenção

Ver [proposta de melhoria](../proposta_melhoria.md) — ações 1, 2 e 3.
