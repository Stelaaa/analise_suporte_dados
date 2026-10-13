# Guia passo a passo · Montar o painel no Power BI e publicar na web

Este guia monta o painel descrito em [powerbi_modelo.md](powerbi_modelo.md) usando os arquivos de `powerbi/dados/`. Leva de 2 a 3 horas na primeira vez.

Em cada etapa há um **número para conferir**. Se o seu painel mostrar o mesmo valor, está tudo certo até ali.

---

## Etapa 0 · O que você precisa

| Item | Para quê | Custo |
|---|---|---|
| Windows 10 ou 11 | o Power BI Desktop só roda no Windows | — |
| Power BI Desktop | montar o painel | gratuito, não precisa de login |
| Pasta `powerbi/dados/` deste repositório | os dados do painel | — |
| Conta de trabalho ou escola da Microsoft | **só para publicar na web** (Gmail e Outlook pessoal não são aceitos) | ver Etapa 9 |

## Etapa 1 · Instalar o Power BI Desktop

1. Abra a [página do Power BI Desktop na Microsoft Store](https://aka.ms/pbidesktopstore) e clique em **Obter / Instalar**.
2. Abra o programa. Se aparecer uma tela pedindo para entrar, feche-a: não precisa de conta para montar o painel.

## Etapa 2 · Conferir o padrão Português (Brasil)

Os arquivos de `powerbi/dados/` já estão no **padrão brasileiro**, o mesmo do Power BI em português:

| Item | Formato nos arquivos |
|---|---|
| Separador de colunas | ponto e vírgula (`;`) |
| Separador decimal | vírgula (`12,5`) |
| Datas | `dd/mm/aaaa` (`01/07/2026`) e `dd/mm/aaaa hh:mm` |
| Acentos | UTF-8 |

Você não precisa mudar nada, só confirmar:

1. **Arquivo → Opções e configurações → Opções**.
2. Na coluna da esquerda, em **ARQUIVO ATUAL**, clique em **Configurações regionais**.
3. **Localidade para importação** deve estar em **Português (Brasil)**, que é o padrão. Clique em **OK**.

> **Sobre as fórmulas DAX:** mesmo com o Power BI em português, o padrão do DAX é usar **vírgula** para separar os argumentos das funções, por exemplo `CALCULATE ( [Chamados], fChamados[status] <> "Resolvido" )`. As fórmulas deste guia já seguem esse padrão. Só se você tiver ativado a opção de **separadores locais** em **GLOBAL → Configurações regionais** é que o Power BI passa a pedir **ponto e vírgula**. Nesse caso, troque `,` por `;` nas fórmulas.

## Etapa 3 · Importar os 9 arquivos

Repita para cada arquivo de `powerbi/dados/`:

1. **Página Inicial → Obter dados → Texto/CSV**.
2. Selecione o arquivo e clique em **Abrir**.
3. Na prévia, confira: **Origem do Arquivo** = **65001: Unicode (UTF-8)** e **Delimitador** = **Ponto e vírgula**. As colunas devem aparecer separadas, com acentos e números com vírgula (`13,4`).
4. Clique em **Carregar**.

| Arquivo | Linhas esperadas |
|---|---:|
| fChamados | 640 |
| fVendas | 9.999 |
| fOcorrenciasDQ | 1.153 |
| fApuracao | 180 |
| fResgates | 87 |
| dParticipante | 180 |
| dProduto | 8 |
| dPrioridade | 4 |
| dCalendario | 153 |

**Conferir tipos:** clique em **Transformar dados** e verifique:

- colunas `data` de todas as tabelas → tipo **Data**
- `data_abertura`, `data_primeira_resposta`, `data_resolucao` → **Data/Hora**
- `valor_total`, `horas_resposta`, `horas_resolucao`, `atingimento`, `faturamento` → **Número decimal**
- `matricula`, `cod_cliente`, `cod_produto` → **Texto**

Para trocar, clique no ícone à esquerda do nome da coluna. Depois clique em **Fechar e Aplicar**.

## Etapa 4 · Montar o modelo (relacionamentos)

1. Clique no ícone **Exibição de modelo** (o terceiro, na barra da esquerda).
2. O Power BI tenta criar relacionamentos sozinho. Apague os que não estiverem na lista abaixo (clique na linha → **Delete**).
3. Para criar um relacionamento, arraste a coluna da tabela `d...` até a coluna de mesmo nome na tabela `f...`.

| De (lado 1) | Para (lado *) |
|---|---|
| dCalendario[data] | fChamados[data] |
| dCalendario[data] | fVendas[data] |
| dCalendario[data] | fResgates[data] |
| dPrioridade[prioridade] | fChamados[prioridade] |
| dParticipante[matricula] | fVendas[matricula] |
| dParticipante[matricula] | fResgates[matricula] |
| dParticipante[matricula] | fOcorrenciasDQ[matricula] |
| dParticipante[matricula] | fApuracao[matricula] (1 para 1) |
| dProduto[cod_produto] | fVendas[cod_produto] |

4. **Marcar o calendário:** clique com o botão direito em `dCalendario` → **Marcar como tabela de datas** → coluna `data`.
5. **Ordenar prioridades:** na Exibição de tabela, selecione `dPrioridade[prioridade]` → **Ferramentas de coluna → Classificar por coluna → ordem**. Assim aparece Crítica, Alta, Média, Baixa, e não em ordem alfabética.

Ao final, o desenho deve parecer uma estrela: tabelas `d` no meio das `f`.

## Etapa 5 · Criar as medidas

1. **Página Inicial → Inserir dados** → nomeie a tabela `_Medidas` → **Carregar**. Ela vai guardar todas as fórmulas.
2. Selecione `_Medidas` no painel **Dados** → **Nova medida** → cole a fórmula → Enter. Repita para cada uma.
3. Depois de criar a primeira medida, apague a coluna vazia `Coluna1` da tabela `_Medidas`.

```dax
Chamados = COUNTROWS ( fChamados )
```
```dax
Backlog = CALCULATE ( [Chamados], fChamados[status] <> "Resolvido" )
```
```dax
% SLA Resolução = AVERAGE ( fChamados[res_no_prazo] )
```
```dax
% SLA 1ª Resposta = AVERAGE ( fChamados[resp_no_prazo] )
```
```dax
TMR (h) = AVERAGE ( fChamados[horas_resolucao] )
```
```dax
% Reabertura = DIVIDE ( CALCULATE ( [Chamados], fChamados[reaberto] = "Sim" ), [Chamados] )
```
```dax
Chamados Pontuação = CALCULATE ( [Chamados], fChamados[categoria] = "Pontuação divergente" )
```
```dax
Pareto % Acumulado =
VAR _atual = [Chamados]
VAR _tabela = ADDCOLUMNS ( ALL ( fChamados[categoria] ), "@qtd", [Chamados] )
RETURN
    DIVIDE ( SUMX ( FILTER ( _tabela, [@qtd] >= _atual ), [@qtd] ), SUMX ( _tabela, [@qtd] ) )
```
```dax
Duplicatas Importadas = CALCULATE ( COUNTROWS ( fVendas ), fVendas[motivo_bloqueio] = "DQ01 Venda duplicada" )
```
```dax
Faturamento Inflado = CALCULATE ( SUM ( fVendas[valor_total] ), fVendas[motivo_bloqueio] = "DQ01 Venda duplicada" )
```
```dax
% Vendas Válidas = DIVIDE ( SUM ( fVendas[venda_valida] ), COUNTROWS ( fVendas ) )
```
```dax
Ocorrências = COUNTROWS ( fOcorrenciasDQ )
```
```dax
Ocorrências Bloqueantes = CALCULATE ( [Ocorrências], fOcorrenciasDQ[severidade] = "Bloqueia" )
```
```dax
Pontos Apurados = SUM ( fApuracao[pontos_total] )
```
```dax
Participantes Elegíveis = CALCULATE ( COUNTROWS ( fApuracao ), fApuracao[situacao] = "Elegível" )
```

**Formatar:** selecione cada medida de `%` → **Ferramentas de medida → Formato: Porcentagem**, 1 casa decimal. `Faturamento Inflado` → **Moeda**.

**Conferir** (crie um visual de **Cartão** com cada medida, sem filtro nenhum):

| Medida | Valor esperado |
|---|---:|
| Chamados | 640 |
| Backlog | 52 |
| % SLA Resolução | 73,3% |
| % SLA 1ª Resposta | 66,4% |
| TMR (h) | 13,4 |
| % Reabertura | 7,8% |
| Chamados Pontuação | 207 |
| Duplicatas Importadas | 944 |
| Faturamento Inflado | R$ 144.861,80 |
| % Vendas Válidas | 88,9% |
| Ocorrências Bloqueantes | 1.141 |
| Pontos Apurados | 388.000 |
| Participantes Elegíveis | 169 |

## Etapa 6 · Montar as 4 páginas

Volte para a **Exibição de relatório** (primeiro ícone da esquerda). Para renomear uma página, clique duas vezes na aba lá embaixo.

Para criar um visual: clique no tipo em **Visualizações**, depois marque ou arraste os campos para os espaços **Eixo X**, **Eixo Y**, **Valores** e **Legenda**.

### Página 1 · Visão geral

| Visual | Campos |
|---|---|
| 6 × **Cartão** (linha do topo) | Chamados · Backlog · % SLA Resolução · % SLA 1ª Resposta · TMR (h) · % Reabertura |
| **Gráfico de colunas clusterizado** | Eixo X: `dCalendario[semana_campanha]` · Eixo Y: `Chamados` |
| **Gráfico de barras clusterizado** | Eixo Y: `dPrioridade[prioridade]` · Eixo X: `% SLA 1ª Resposta` e `% SLA Resolução` |
| 2 × **Segmentação de dados** | `fChamados[categoria]` · `fChamados[analista]` |

👉 Conferir: na barra de prioridade, **Crítica** deve mostrar 29,0% de 1ª resposta. É o achado "o urgente é atendido por último".

### Página 2 · Recorrência (a página mais importante)

| Visual | Campos |
|---|---|
| **Gráfico de linhas e de colunas clusterizado** | Eixo X: `dCalendario[semana_campanha]` · Colunas: `Chamados Pontuação` · Linha: `Duplicatas Importadas` |
| **Gráfico de linhas e de colunas clusterizado** (Pareto) | Eixo X: `fChamados[categoria]` · Colunas: `Chamados` · Linha: `Pareto % Acumulado` |
| **Matriz** | Linhas: `fChamados[categoria]` · Colunas: `dCalendario[semana_campanha]` · Valores: `Chamados` |

- No primeiro gráfico, as colunas e a linha devem disparar juntas nas **semanas 5 e 9**. Esse é o gráfico que conta a história da causa raiz.
- No Pareto: clique nos **...** do visual → **Classificar eixo → Chamados**, decrescente.
- Na Matriz: selecione o campo `Chamados` em Valores → seta → **Formatação condicional → Cor da tela de fundo** → escala do branco ao laranja.

### Página 3 · Qualidade da base

| Visual | Campos |
|---|---|
| 3 × **Cartão** | Ocorrências Bloqueantes · Faturamento Inflado · % Vendas Válidas |
| **Gráfico de barras clusterizado** | Eixo Y: `fOcorrenciasDQ[regra]` · Eixo X: `Ocorrências` · Legenda: `fOcorrenciasDQ[severidade]` |
| **Tabela** | `fOcorrenciasDQ[regra]`, `id_registro`, `matricula`, `detalhe` |
| **Segmentação de dados** | `fOcorrenciasDQ[regra]` |

### Página 4 · Apuração

| Visual | Campos |
|---|---|
| 2 × **Cartão** | Pontos Apurados · Participantes Elegíveis |
| **Gráfico de colunas clusterizado** | Eixo X: `fApuracao[faixa]` · Eixo Y: `Participantes Elegíveis` |
| **Gráfico de barras clusterizado** | Eixo Y: `dParticipante[regional]` · Eixo X: `Pontos Apurados` |
| **Tabela** | `fApuracao[matricula]`, `nome`, `situacao`, `faturamento`, `meta_faturamento`, `atingimento`, `pontos_total` |

Formate `atingimento` como Porcentagem (selecione a coluna no painel Dados → Ferramentas de coluna).

## Etapa 7 · Deixar com cara de profissional

1. **Exibir → Temas** → escolha um tema discreto (azul ou cinza). Use a mesma cor de destaque em todas as páginas.
2. Em cada página, **Inserir → Caixa de texto** no topo com um título que diga **a conclusão**, não só o assunto. Exemplo: "Pontuação divergente dispara nas semanas de reimportação", em vez de "Chamados por semana".
3. Alinhe os visuais: selecione vários com Ctrl → **Formatar → Alinhar**.
4. Em cada visual, vá em **Formatar visual → Geral → Título** e escreva um título claro.
5. Rodapé em letra pequena em todas as páginas: "Dados fictícios gerados para fins de portfólio".

## Etapa 8 · Salvar e gerar um PDF (não precisa de conta)

1. **Arquivo → Salvar como** → salve na pasta `powerbi/` com o nome `painel_suporte_dados.pbix`.
2. **Arquivo → Exportar → Exportar para PDF**. Salve como `powerbi/painel_suporte_dados.pdf`.
3. Tire um print de cada página (tecla Windows + Shift + S) e salve em `reports/img/`, por exemplo `powerbi_pagina1.png`.
4. No README, acrescente as imagens:
   ```markdown
   ![Painel Power BI - Recorrência](reports/img/powerbi_pagina2.png)
   ```

Assim o painel já aparece no GitHub, mesmo antes de ser publicado na web.

## Etapa 9 · Publicar na web

### 9.1 Conseguir uma conta de trabalho ou escola

O serviço online do Power BI (app.powerbi.com) **não aceita Gmail nem Outlook pessoal**. Escolha uma opção:

| Opção | Como | Observação |
|---|---|---|
| E-mail institucional | o e-mail da faculdade (a pós, por exemplo) | o mais simples, se a instituição liberar o Power BI |
| Teste do Microsoft 365 para empresas | contrate o teste gratuito em microsoft.com/microsoft-365 → plano Business. Você ganha um e-mail como `stela@seunome.onmicrosoft.com` e vira administradora | pode pedir cartão; anote a data de fim e cancele se não for usar |

### 9.2 Publicar o relatório

1. No Power BI Desktop, clique em **Entrar** (canto superior direito) com a conta de trabalho.
2. **Página Inicial → Publicar** → escolha **Meu workspace** → **Selecionar**.
3. Quando terminar, clique no link **Abrir 'painel_suporte_dados.pbix' no Power BI**.

### 9.3 Liberar a publicação na web (uma vez só)

A opção vem desligada. Como administradora da sua conta de teste, você mesma liga:

1. Em app.powerbi.com, clique na **engrenagem** (canto superior direito) → **Portal de administração**.
2. **Configurações de locatário** → seção **Configurações de exportação e compartilhamento** → **Publicar na Web**.
3. Marque **Habilitado**, deixe **Toda a organização** e clique em **Aplicar**.
4. A liberação pode levar alguns minutos para valer.

### 9.4 Gerar o link público

1. Abra o relatório em **Meu workspace**.
2. **Arquivo → Inserir relatório → Publicar na Web (público)**.
3. **Criar código de inserção** → leia o aviso → **Publicar**.
4. Copie o **link** (para o README e o LinkedIn) ou o **HTML** (para colocar num site, como o seu portfólio).

### 9.5 Colocar no README

```markdown
**[▶ Ver o painel interativo](COLE-O-LINK-AQUI)**
```

## Cuidados

- **"Publicar na Web" é público de verdade.** Qualquer pessoa com o link vê o painel e consegue chegar aos dados por trás dele. Aqui não há problema porque tudo é fictício, mas **nunca** use essa opção com dados reais de empresa.
- **O link depende da sua conta.** Se a conta de teste expirar ou for cancelada, o link pode parar de funcionar. Por isso mantenha o PDF e os prints no repositório como reserva.
- Cada relatório gera **um** código de inserção. Para gerenciar ou apagar: no workspace, **Configurações → Gerenciar códigos de inserção**.
- Visuais em Python ou R não funcionam no Publicar na Web. Este painel não usa nenhum.

## Se der errado

| Sintoma | Causa provável | Solução |
|---|---|---|
| `TMR (h)` deu 134 em vez de 13,4, ou as datas viraram texto | a localidade de importação não está em Português (Brasil) | refaça a Etapa 2 e, em Transformar dados, clique em **Atualizar visualização** |
| Todas as colunas vieram juntas numa só | delimitador errado | na prévia da importação, escolha **Delimitador: Ponto e vírgula** |
| Acentos viraram `Ã§` | codificação do arquivo | na importação, escolha **65001: Unicode (UTF-8)** |
| Cartão mostra o mesmo número em qualquer filtro | relacionamento faltando | revise a tabela da Etapa 4 |
| Erro "a sintaxe para ',' está incorreta" | a opção de separadores locais do DAX está ativada | troque `,` por `;` nas fórmulas (nota da Etapa 2) |
| A opção "Publicar na Web" não aparece | configuração de locatário desligada | Etapa 9.3 e espere alguns minutos |
| "Entre em contato com o administrador para habilitar a criação de código" | idem | Etapa 9.3 |
