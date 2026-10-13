# Playbook de triagem de chamados

Como receber, classificar, diagnosticar e encerrar um chamado em uma plataforma SaaS de apuração de campanhas.

## Fluxo

```
Abertura → Triagem (≤ SLA de 1ª resposta) → Diagnóstico → Solução ou escalonamento → Validação com o solicitante → Encerramento + registro na base de conhecimento
```

## 1. Triagem — o que registrar sempre

| Campo | Por quê |
|---|---|
| Categoria | alimenta o Pareto e a análise de recorrência |
| Prioridade (pela matriz de SLA) | define prazo e fila |
| Campanha e matrícula | sem isso não dá para cruzar dados |
| Evidência (print, data/hora, valor esperado × valor exibido) | evita ida e volta |
| Quantos participantes afetados | 1 pessoa = Alta; um grupo ou uma regional inteira = Crítica |

**Regra prática:** se a mesma categoria chegar 5 vezes em 2 horas, trate como incidente — abra um chamado-pai Crítico e vincule os demais.

## 2. Categorias e primeira pergunta de diagnóstico

| Categoria | Prioridade padrão | Primeira pergunta | Artigo |
|---|---|---|---|
| Pontuação divergente | Alta | A venda está na base importada? Está duplicada, fora do período ou sem meta? | [BC-001](Base_de_Conhecimento/BC-001-pontuacao-divergente.md) |
| Resgate não creditado | Alta | O resgate saiu do saldo? O parceiro confirmou o envio? | [BC-002](Base_de_Conhecimento/BC-002-resgate-nao-creditado.md) |
| Importação de base | Crítica | O arquivo segue o layout? Já foi importado antes? | [BC-003](Base_de_Conhecimento/BC-003-importacao-de-base.md) |
| Acesso / login | Média | Matrícula está ativa e no formato certo (sem espaço / maiúscula)? | — |
| Cadastro de participante | Média | O participante está no arquivo de participantes e no de metas? | — |
| Relatório / dashboard | Média | A divergência é de dado ou de filtro/atualização? | — |
| Dúvida de regulamento | Baixa | Resposta com o trecho do regulamento | — |

## 3. Diagnóstico com dados

Para qualquer chamado que envolva número, a resposta deve trazer a **evidência do cruzamento**, não só a conclusão:

1. Extrato das vendas do participante na campanha (válidas e bloqueadas, com o motivo).
2. Meta cadastrada e atingimento.
3. Faixa e pontos calculados.
4. Resgates e saldo.

Consultas prontas: `src/sql_preparacao/02_qualidade_dados.sql` (`dq_ocorrencias` filtrando por matrícula) e `src/sql_preparacao/03_apuracao.sql` (`apuracao`).

## 4. Escalonamento

| Situação | Para quem | Prazo |
|---|---|---|
| Erro de regra de apuração ou parâmetro | Negócio / Campanhas | mesmo dia |
| Bug na plataforma (reprodutível) | Produto / Dev, com passo a passo e evidência | conforme prioridade |
| Dado errado vindo do cliente | Gestor da conta, com lista dos registros afetados | 1 dia útil |
| Divergência em resgate com parceiro | Operações de premiação | 1 dia útil |

## 5. Encerramento

- Confirmar com o solicitante antes de fechar (reduz reabertura).
- Se a solução não estava documentada: criar ou atualizar o artigo na base de conhecimento.
- Marcar se o chamado é recorrente — é isso que permite a análise de causa raiz no fim do mês.
