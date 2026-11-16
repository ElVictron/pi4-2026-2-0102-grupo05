"""Compose do sistema completo (cards #780 e #801): serviços, TLS, dependências e variáveis.

Valida `docker-compose.yml` com `docker compose config` (não precisa de daemon). Os testes do
`Dockerfile` e do `scripts/iniciar.sh` ficam no repositório do Backend 1.
Uso: `python3 -m pip install pytest && python3 -m pytest tests`.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

import pytest

RAIZ = Path(__file__).resolve().parents[1]
COMPOSE = RAIZ / "docker-compose.yml"

VARIAVEIS_CONVENCOES = (
    "DATABASE_URL",
    "BACKEND2_URL",
    "BACKEND2_TIMEOUT_SEGUNDOS",
    "BACKEND2_VERIFY_TLS",
    "BACKEND2_CA_BUNDLE",
    "CORS_ORIGENS",
    "SSL_CERTFILE",
    "SSL_KEYFILE",
)


# --------------------------------------------------------------------------- docker compose


@pytest.fixture(scope="module")
def compose():
    """Saída de `docker compose config --format json`, com as variáveis da §10 ausentes."""
    if shutil.which("docker") is None:
        pytest.skip("CLI do docker não instalado")
    ambiente = {
        k: v
        for k, v in os.environ.items()
        if k not in VARIAVEIS_CONVENCOES and k != "POSTGRES_PASSWORD"
    }
    processo = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE),
            "--project-directory",
            str(RAIZ),
            "config",
            "--format",
            "json",
        ],
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if processo.returncode != 0 and "unknown" in processo.stderr.lower():
        pytest.skip(f"docker compose indisponível: {processo.stderr.strip()}")
    assert processo.returncode == 0, processo.stderr
    return json.loads(processo.stdout)


# D22/D23 · sistema completo (card #780): postgres, backend1, backend2, frontend e certificados
def test_compose_servicos(compose):
    assert set(compose["services"]) == {
        "postgres",
        "backend1",
        "backend2",
        "frontend",
        "certificados",
    }


# D23 · Backend 2 só em TLS (8443), com certificado da pasta certs e saúde verificada
def test_compose_backend2(compose):
    backend2 = compose["services"]["backend2"]

    assert backend2["environment"]["SSL_CERTFILE"] == "/certs/backend2.pem"
    assert backend2["environment"]["SSL_KEYFILE"] == "/certs/backend2-key.pem"
    portas = [p for p in backend2["ports"] if p["target"] == 8443]
    assert len(portas) == 1
    assert str(portas[0]["published"]) == "8443"
    assert backend2["depends_on"]["certificados"]["condition"] == "service_completed_successfully"
    assert "healthcheck" in backend2
    certs = [v for v in backend2["volumes"] if v["target"] == "/certs"]
    assert len(certs) == 1
    assert certs[0].get("read_only") is True


# D23 · frontend chama os backends pelo host; WSS direto no Backend 2
def test_compose_frontend(compose):
    frontend = compose["services"]["frontend"]
    args = frontend["build"]["args"]

    assert args["VITE_API_URL"] == "https://localhost:8000"
    assert args["VITE_WS_URL"] == "wss://localhost:8443/ws/biblioteca"
    assert str(frontend["ports"][0]["published"]) == "5173"


# D22 · postgres:16, volume persistente e healthcheck com pg_isready
def test_compose_postgres(compose):
    postgres = compose["services"]["postgres"]

    assert postgres["image"] == "postgres:16"
    dados = [v for v in postgres["volumes"] if v["target"] == "/var/lib/postgresql/data"]
    assert len(dados) == 1
    assert dados[0]["type"] == "volume"
    assert dados[0]["source"] in compose.get("volumes", {})
    teste = postgres["healthcheck"]["test"]
    assert any("pg_isready" in parte for parte in teste)


# D18 / D22 · db/schema.sql montado em docker-entrypoint-initdb.d, somente leitura
def test_compose_schema_no_initdb(compose):
    volumes = compose["services"]["postgres"]["volumes"]
    schema = [v for v in volumes if v["source"].endswith("/db/schema.sql")]

    assert len(schema) == 1
    assert schema[0]["type"] == "bind"
    assert schema[0]["target"].startswith("/docker-entrypoint-initdb.d/")
    assert schema[0]["target"].endswith(".sql")
    assert schema[0].get("read_only") is True


# D22 · backend1 depende do postgres saudável e publica a porta 8000
def test_compose_backend1_dependencia_e_porta(compose):
    backend1 = compose["services"]["backend1"]

    assert backend1["depends_on"]["postgres"]["condition"] == "service_healthy"
    portas = [p for p in backend1["ports"] if p["target"] == 8000]
    assert len(portas) == 1
    assert str(portas[0]["published"]) == "8000"
    assert "build" in backend1


# §10 · todas as variáveis das convenções no ambiente do backend1; DATABASE_URL → postgres
def test_compose_backend1_ambiente(compose):
    ambiente = compose["services"]["backend1"]["environment"]

    assert set(VARIAVEIS_CONVENCOES) <= set(ambiente)
    url = urlsplit(ambiente["DATABASE_URL"])
    assert url.scheme in ("postgresql", "postgres")
    assert url.hostname == "postgres"
    assert (url.port or 5432) == 5432
    assert url.path.lstrip("/")


# D24 · Backend 1 sobe em HTTPS no Compose, com o certificado gerado em ./certs
@pytest.mark.parametrize(
    ("variavel", "valor"),
    [("SSL_CERTFILE", "/certs/backend1.pem"), ("SSL_KEYFILE", "/certs/backend1-key.pem")],
)
def test_compose_backend1_https_por_padrao(compose, variavel, valor):
    assert compose["services"]["backend1"]["environment"][variavel] == valor


# D24 · backend1 espera o serviço certificados terminar (os arquivos precisam existir)
def test_compose_backend1_espera_certificados(compose):
    depends = compose["services"]["backend1"]["depends_on"]

    assert depends["certificados"]["condition"] == "service_completed_successfully"


# D23 · Backend 1 chama o Backend 2 por HTTPS, verificando a CA local do Compose
def test_compose_backend1_aponta_para_o_backend2(compose):
    ambiente = compose["services"]["backend1"]["environment"]

    assert ambiente["BACKEND2_URL"] == "https://backend2:8443"
    assert ambiente["BACKEND2_CA_BUNDLE"] == "/certs/ca.pem"
    assert ambiente["BACKEND2_VERIFY_TLS"] == "true"
    assert (
        compose["services"]["backend1"]["depends_on"]["backend2"]["condition"] == "service_healthy"
    )
