# Sistema de Gerenciamento de Biblioteca

Projeto Integrador IV (PUC-Campinas, Sistemas de Informação, turma 102, grupo 05). Sistema web que substitui as planilhas de uma biblioteca: o responsável cadastra livros e usuários, registra empréstimos e devoluções, pesquisa o acervo e acompanha os atrasos. Um painel de disponibilidade se atualiza sozinho: um empréstimo registrado numa tela aparece nas outras telas abertas, sem recarregar a página.

## Integrantes

| Nome | RA | Responde por |
|---|---|---|
| Victor Hugo Gulino dos Santos | 22968572 | Backend 1 (API e banco), Compose, integração e testes de ponta a ponta |
| Lucas Joaquim de Souza | 24020901 | Backend 2 (eventos em tempo real) |
| Gabriel Gregorio Ribeiro Leite | 20060547 | Frontend |

## Repositórios

| Repositório | O que tem |
|---|---|
| [pi4-2026-2-0102-grupo05](https://github.com/ElVictron/pi4-2026-2-0102-grupo05) (este, repositório principal) | `docker-compose.yml`, este README, o Documento de Projeto, os fluxos, os prints, os scripts de integração e o escopo da Entrega 1 |
| [pi4-0101-g5-backend-1](https://github.com/ElVictron/pi4-0101-g5-backend-1) | Backend 1 (API REST em Python/FastAPI), banco PostgreSQL, contratos e ADRs |
| [pi4-0101-g5-backend-2](https://github.com/ElVictron/pi4-0101-g5-backend-2) | Backend 2: recebe eventos do Backend 1 e os envia às telas por WebSocket seguro |
| [pi4-0101-g5-frontend](https://github.com/ElVictron/pi4-0101-g5-frontend) | Frontend em React |

## Pré-requisitos

- Docker Engine com o plugin Docker Compose v2 (`docker compose version`); testado com o Docker Engine 29. Docker Desktop no Windows e no macOS (não testado).
- Git.
- Acesso à internet para baixar as imagens (`postgres`, `python`, `node`, `nginx`, `alpine`) do Docker Hub.
- Um navegador (Chrome, Edge ou Firefox).
- Portas livres: 5173, 8000 e 8443.
- Opcional, só para o teste automático: Python 3.12 ou superior (`python3`).

## Como subir

1. Clone os quatro repositórios na mesma pasta:
   ```bash
   mkdir biblioteca && cd biblioteca
   git clone https://github.com/ElVictron/pi4-2026-2-0102-grupo05.git
   git clone https://github.com/ElVictron/pi4-0101-g5-backend-1.git
   git clone https://github.com/ElVictron/pi4-0101-g5-backend-2.git
   git clone https://github.com/ElVictron/pi4-0101-g5-frontend.git
   ```
2. Entre na pasta do repositório principal e suba o sistema (não é preciso criar `.env`; os padrões servem para a demonstração):
   ```bash
   cd pi4-2026-2-0102-grupo05
   docker compose up --build -d
   ```
   Na primeira vez leva alguns minutos. O serviço `certificados` gera, sozinho, a pasta `certs/`.
3. Confira que tudo subiu (quatro serviços em execução, `backend2` e `postgres` como `healthy`):
   ```bash
   docker compose ps
   ```
4. Carregue os dados de exemplo (4 livros, 3 usuários e 3 empréstimos, um deles atrasado; só insere se o banco estiver vazio):
   ```bash
   docker compose exec -T postgres psql -U biblioteca -d biblioteca < db/dados-demo.sql
   ```
5. Confie na autoridade certificadora local no navegador, para ele aceitar o HTTPS do Backend 1 e o WSS do Backend 2: importe o arquivo `certs/ca.pem` como "autoridade de certificação raiz confiável" (Windows: duplo clique, "Instalar certificado", "Autoridades de Certificação Raiz Confiáveis"; Firefox: Configurações, Certificados, Importar; Chrome ou Edge no Linux: `sudo apt install libnss3-tools` e `certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "Biblioteca CA local" -i certs/ca.pem`) e reinicie o navegador por completo.
6. Abra <http://localhost:5173>. O indicador do canto superior direito deve mostrar **Tempo real: conectado**.

Para desligar: `docker compose down` (mantém os dados) ou `docker compose down -v` (apaga também o banco).

Para conferir tudo de uma vez, com um teste automático das duas abas: `python3 -m pip install playwright && python3 -m playwright install chromium && python3 scripts/integracao/verificar_docker.py`.

## Como usar

O sistema não tem login: quem abre a tela é o responsável da biblioteca. Menu lateral: Painel, Acervo, Usuários, Empréstimos.

| Entregável | Como fazer |
|---|---|
| E1 Cadastro de livros | Acervo, "Cadastrar livro": título, autor, ISBN e quantidade de exemplares, depois Cadastrar |
| E2 Consulta de livros | Acervo, "Pesquisar livros": digite parte do título, autor ou ISBN e clique em Buscar |
| E3 Cadastro de usuários | Usuários, "Novo usuário": nome, CPF e contato, depois Cadastrar |
| E4 Consulta de usuários | Usuários, "Usuários cadastrados": busque por nome ou CPF; cada cartão mostra os empréstimos |
| E5 Registro de empréstimo | Empréstimos, "Registrar empréstimo": busque e marque o usuário, escolha o livro e clique em Registrar empréstimo. O prazo é de 15 dias |
| E6 Registro de devolução | Empréstimos, lista de empréstimos: clique em Devolver na linha do empréstimo |
| E7 Controle de disponibilidade | Painel: mostra os livros com exemplares disponíveis e se atualiza sozinho. Abra duas abas, registre um empréstimo numa e veja a outra mudar |
| E8 Consulta de empréstimos | Empréstimos, "Empréstimos registrados": filtre por Ativos, Atrasados ou Devolvidos e busque por usuário ou livro |

Roteiro completo de demonstração: [`docs/roteiro-demonstracao.md`](docs/roteiro-demonstracao.md).

## Documentação

- [Documento de Projeto](docs/documento-de-projeto.md): visão geral, requisitos, arquitetura, banco, contratos, testes, telas e conclusão.
- [Fluxos](docs/fluxos/) de cada entregável e o [escopo da Entrega 1](docs/ESCOPO-0102-grupo05.pdf).
- [Contratos](https://github.com/ElVictron/pi4-0101-g5-backend-1/blob/main/docs/contratos/) (comece por [`00-convencoes.md`](https://github.com/ElVictron/pi4-0101-g5-backend-1/blob/main/docs/contratos/00-convencoes.md)) e [decisões (ADR)](https://github.com/ElVictron/pi4-0101-g5-backend-1/blob/main/docs/adr/), no repositório do Backend 1.
- [`agentes.md`](https://github.com/ElVictron/pi4-0101-g5-backend-1/blob/main/agentes.md): plano, decisões e processo de desenvolvimento do Backend 1.
- [Histórico de versões](CHANGELOG.md) e [quadro do OpenProject](https://srv1889234.hstgr.cloud/projects/pi-iv-0101-g5).
