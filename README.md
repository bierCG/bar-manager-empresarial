## Requisitos
Docker Desktop aberto.

## Rodar os testes
    docker compose run --rm tests

## Rodar a API
    docker compose up --build api

Documentação: http://localhost:8000/docs
(banco local em container, começa vazio)

## Limpar tudo
    docker compose down -v

## Variáveis de ambiente
Valores fake em `.env.example`. Para usar outro banco (ex.: Neon), defina `DATABASE_URL` num `.env` seu.