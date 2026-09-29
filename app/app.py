import os
import secrets
import string
import time

import pymysql
from flask import Flask, abort, redirect, render_template, request, url_for

app = Flask(__name__)

# Toda a configuração vem de variáveis de ambiente (nada fixo no código).
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "database": os.environ["DB_NAME"],
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

ALFABETO = string.ascii_letters + string.digits
TAMANHO_CODIGO = 6


def conectar():
    return pymysql.connect(**DB_CONFIG)


def criar_tabela(tentativas=10):
    """Cria a tabela na inicialização. O healthcheck já garante que o banco
    está pronto, mas algumas tentativas extras deixam a subida mais robusta."""
    for tentativa in range(1, tentativas + 1):
        try:
            with conectar() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS links (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        codigo VARCHAR(16) NOT NULL UNIQUE,
                        url_original TEXT NOT NULL,
                        acessos INT NOT NULL DEFAULT 0,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            return
        except pymysql.err.OperationalError as erro:
            print(f"Banco indisponível (tentativa {tentativa}): {erro}", flush=True)
            time.sleep(3)
    raise RuntimeError("Não foi possível conectar ao banco de dados.")


def gerar_codigo():
    return "".join(secrets.choice(ALFABETO) for _ in range(TAMANHO_CODIGO))


@app.route("/", methods=["GET"])
def index():
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT codigo, url_original, acessos, criado_em "
            "FROM links ORDER BY criado_em DESC LIMIT 20"
        )
        links = cur.fetchall()
    return render_template("index.html", links=links, novo=request.args.get("novo"))


@app.route("/encurtar", methods=["POST"])
def encurtar():
    url = request.form.get("url", "").strip()
    if not url:
        return redirect(url_for("index"))
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    with conectar() as conn, conn.cursor() as cur:
        # Repete em caso (raro) de colisão de código.
        while True:
            codigo = gerar_codigo()
            try:
                cur.execute(
                    "INSERT INTO links (codigo, url_original) VALUES (%s, %s)",
                    (codigo, url),
                )
                break
            except pymysql.err.IntegrityError:
                continue
    return redirect(url_for("index", novo=codigo))


@app.route("/<codigo>")
def redirecionar(codigo):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute("SELECT url_original FROM links WHERE codigo = %s", (codigo,))
        link = cur.fetchone()
        if not link:
            abort(404)
        cur.execute("UPDATE links SET acessos = acessos + 1 WHERE codigo = %s", (codigo,))
    return redirect(link["url_original"])


@app.route("/stats/<codigo>")
def estatisticas(codigo):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT codigo, url_original, acessos, criado_em FROM links WHERE codigo = %s",
            (codigo,),
        )
        link = cur.fetchone()
    if not link:
        return {"erro": "código não encontrado"}, 404
    link["criado_em"] = link["criado_em"].isoformat()
    return link


@app.route("/health")
def health():
    return {"status": "ok"}


criar_tabela()
