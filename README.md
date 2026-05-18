# Reference Checker

Validador em Python para listas de referências bibliográficas típicas de textos científicos. Ele identifica problemas comuns antes da submissão de artigos, TCCs, dissertações ou relatórios técnicos.

## Recursos

- Divide blocos de bibliografia em referências individuais, inclusive listas numeradas.
- Detecta DOI, URL, ano de publicação, autores iniciais e segmentos que se parecem com título.
- Sinaliza referências curtas, sem ano, sem DOI/URL, com ano futuro ou possíveis duplicatas.
- Opcionalmente consulta a API pública da Crossref para confirmar DOIs e comparar o ano publicado.
- Oferece saída textual para revisão humana ou JSON para integração com outros sistemas.

## Instalação local

```bash
python -m pip install -e .
```

## Uso

Validar um arquivo com referências:

```bash
reference-checker referencias.txt
```

Validar a partir da entrada padrão:

```bash
cat referencias.txt | reference-checker --fail-on-warning
```

Gerar JSON:

```bash
reference-checker referencias.txt --json
```

Confirmar DOIs na Crossref:

```bash
reference-checker referencias.txt --online --mailto voce@example.com
```

## Exemplo de referência aceita

```text
[1] Silva, J.; Santos, M. Validação de referências bibliográficas em textos científicos. Revista Brasileira de Informação, 2022. doi:10.1234/rbi.2022.001
```

## Observações

O projeto não substitui uma revisão bibliotecária. Ele atua como uma checagem automática inicial e deve ser combinado com as normas bibliográficas exigidas pela instituição ou periódico.
