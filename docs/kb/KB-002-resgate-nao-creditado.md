# KB-002 · Resgate não creditado

**Categoria:** Resgate não creditado · **Prioridade padrão:** Alta · **Atualizado em:** out/2026

## Sintoma

O participante fez o resgate (crédito no cartão, vale, produto) e não recebeu.

## Árvore de diagnóstico

```
O resgate aparece no histórico do participante?
├── Não → falhou na plataforma. Verificar saldo no momento do pedido.
│         └── Saldo insuficiente? → resgate bloqueado pela regra DQ07. Explicar e mostrar o saldo.
└── Sim → saiu do saldo?
          ├── Não → erro de processamento. Escalar para Produto com id do resgate.
          └── Sim → foi enviado ao parceiro?
                    ├── Não → fila de envio. Prazo do parceiro conforme regulamento.
                    └── Sim → acionar Operações de premiação com o id e o protocolo do parceiro.
```

## Consulta de apoio

```sql
SELECT matricula, pontos_apurados, pontos_resgatados, saldo, qtd_resgates
FROM vw_saldo_resgates
WHERE matricula = 'HZ0001';
```

## Atenção

Resgates **acima do saldo apurado** (regra DQ07) não devem ser liberados. Neste trimestre foram 28:

- 9 pedidos de 25.000 pontos de uma vez — padrão anômalo, verificar com o gestor da conta antes de qualquer contato com o participante;
- 19 resgates feitos com base na prévia, que estava inflada pelas vendas duplicadas. Tratar com o cliente se o prêmio é mantido ou estornado — **não** decidir sozinho(a) no chamado.
