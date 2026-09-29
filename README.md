# Encurtador de URLs

Aplicação web que recebe um endereço longo, gera um código curto e redireciona quem acessa esse código para o endereço original, contabilizando os acessos.

Trabalho da disciplina de Computação em Nuvem (Engenharia de Software, FAG Cascavel).

**Dupla:** Marcus Penso e Gabriel Heidrich

## Tecnologias

A aplicação é escrita em Python com Flask e servida pelo Gunicorn. Os dados ficam em um MySQL 8. Os dois serviços são orquestrados com Docker Compose.

## Como funciona

O ambiente tem dois containers, definidos no `docker-compose.yml`:

- **db**: MySQL 8, com os dados guardados no volume nomeado `dados_mysql`. Possui um healthcheck (`mysqladmin ping`) que indica quando o banco está pronto para receber conexões.
- **app**: a aplicação Flask, construída a partir do `app/Dockerfile`. Ela só é iniciada depois que o banco passa no healthcheck (`depends_on` com `condition: service_healthy`).

A aplicação acessa o banco pelo nome do serviço, `db`, e não por IP ou `localhost`. O Docker Compose cria uma rede interna em que cada serviço é encontrado pelo próprio nome. Usuário, senha e nome do banco chegam à aplicação por variáveis de ambiente lidas do arquivo `.env`.

## Pré-requisitos

É preciso ter instalado o [Docker](https://docs.docker.com/get-docker/) com o plugin Docker Compose (já incluso no Docker Desktop) e o Git.

## Como executar

```bash
git clone https://github.com/MarcusZanol/Computa-o-em-nuvem.git
cd Computa-o-em-nuvem
cp .env.example .env
docker compose up -d
```

Na primeira execução, o MySQL leva alguns segundos para inicializar. A aplicação só sobe depois que o banco passa no healthcheck. Para acompanhar a subida:

```bash
docker compose ps
docker compose logs -f app
```

No Windows (PowerShell), troque `cp` por `copy .env.example .env`.

## Como acessar

Abra http://localhost:8000 no navegador (ou a porta definida em `APP_PORT` no `.env`).

| Rota | Método | Descrição |
|------|--------|-----------|
| `/` | GET | Página com o formulário e os últimos links criados |
| `/encurtar` | POST | Recebe o campo `url` e cria o link curto |
| `/<codigo>` | GET | Redireciona para a URL original e soma um acesso |
| `/stats/<codigo>` | GET | Retorna em JSON a URL, os acessos e a data de criação |
| `/health` | GET | Verificação simples de que a aplicação responde |

Também é possível testar pelo terminal:

```bash
curl -X POST -d "url=https://www.fag.edu.br" http://localhost:8000/encurtar -i
curl http://localhost:8000/stats/<codigo>
```

## Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `APP_PORT` | Porta do host onde a aplicação fica disponível |
| `DB_NAME` | Nome do banco criado no MySQL |
| `DB_USER` | Usuário da aplicação no banco |
| `DB_PASSWORD` | Senha desse usuário |
| `DB_ROOT_PASSWORD` | Senha do usuário root do MySQL |

O arquivo `.env` não é versionado. O `.env.example` traz os nomes das variáveis com valores fictícios.

## Como parar o ambiente

```bash
docker compose down
```

Os containers são removidos, mas os dados do banco continuam no volume. Ao rodar `docker compose up -d` de novo, os links criados anteriormente ainda estarão lá.

## Persistência dos dados

Os dados do MySQL ficam no volume nomeado `dados_mysql`. Eles continuam existindo depois de um `docker compose down`. Para apagar tudo, inclusive os dados:

```bash
docker compose down -v
```

## Estrutura

```
.
├── app/
│   ├── app.py              # código da aplicação Flask
│   ├── templates/
│   │   └── index.html      # página principal
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Problemas comuns

Se aparecer `port is already allocated`, altere `APP_PORT` no `.env` para outra porta (por exemplo, 8080) e rode `docker compose up -d` novamente.
