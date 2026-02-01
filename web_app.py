# -*- coding: utf-8 -*-
"""
Chamados TI - SOTRIGO
Interface Web (Flask)

Versão 6.0 - Arquitetura Modular
"""
import os

# Configurar Oracle ANTES de qualquer import
os.environ['ORACLE_HOME'] = r'C:\oracle\instantclient_23_0'
os.environ['TNS_ADMIN'] = r'C:\oracle\instantclient_23_0'
os.environ['PATH'] = r'C:\oracle\instantclient_23_0;' + os.environ.get('PATH', '')

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

from config.settings import settings
from config.database import get_connection
from services.chamado_service import ChamadoService
from services.sla_service import SLAService
from utils.logger import logger

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# ==========================
# CONFIG E-MAIL
# ==========================
SMTP_HOST = os.getenv('SMTP_HOST', 'seu_servidor_smtp')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', 'ti@suaempresa.com.br')
SMTP_PASS = os.getenv('SMTP_PASS', '')
EMAIL_TI = os.getenv('EMAIL_TI', 'ti@suaempresa.com.br')


def enviar_email(assunto, texto, para):
    """Envia email de notificação"""
    try:
        if not SMTP_PASS:
            logger.warning("SMTP não configurado, email não enviado")
            return False

        msg = MIMEText(texto, "plain", "utf-8")
        msg["Subject"] = assunto
        msg["From"] = SMTP_USER
        msg["To"] = para

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)

        logger.info(f"Email enviado: {assunto}")
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar email: {e}")
        return False


# ==========================
# ROTAS
# ==========================

@app.route('/')
def index():
    """Página inicial - Lista de chamados"""
    filtro_status = request.args.get('status')
    filtro_prioridade = request.args.get('prioridade')

    try:
        chamados = listar_chamados(filtro_status, filtro_prioridade)
        return render_template(
            'index.html',
            chamados=chamados,
            filtro_status=filtro_status,
            filtro_prioridade=filtro_prioridade
        )
    except Exception as e:
        logger.error(f"Erro ao listar chamados: {e}")
        flash(f"Erro ao carregar chamados: {e}", "error")
        return render_template('index.html', chamados=[])


@app.route('/novo', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def novo_chamado():
    """Abre novo chamado"""
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        prioridade = request.form.get('prioridade', 'MEDIA')
        categoria = request.form.get('categoria', 'Outros')
        descricao = request.form.get('descricao', '').strip()

        if not matricula or not descricao:
            flash("Matrícula e descrição são obrigatórios.", "error")
            return render_template('novo.html')

        try:
            id_chamado = ChamadoService.abrir_chamado(
                int(matricula),
                prioridade,
                categoria,
                descricao
            )

            if id_chamado:
                # Enviar email
                assunto = f"[TI] Novo chamado #{id_chamado} - {prioridade}"
                corpo = f"Matrícula: {matricula}\nPrioridade: {prioridade}\nCategoria: {categoria}\n\nDescrição:\n{descricao}"
                enviar_email(assunto, corpo, EMAIL_TI)

                flash(f"Chamado #{id_chamado} aberto com sucesso!", "success")
                return redirect(url_for('index'))
            else:
                flash("Erro ao abrir chamado.", "error")

        except Exception as e:
            logger.error(f"Erro ao abrir chamado: {e}")
            flash(f"Erro: {e}", "error")

    return render_template('novo.html', categorias=settings.LISTA_CATEGORIA_ABERTURA)


@app.route('/chamado/<int:id_chamado>')
def detalhes_chamado(id_chamado):
    """Detalhes de um chamado"""
    try:
        # Buscar chamado
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ID, DATA_ABERTURA, MATRICULA, NOME_USUARIO, SETOR,
                   CATEGORIA, PRIORIDADE, STATUS, DESCRICAO,
                   STATUS_SLA, DATA_LIMITE_SLA, SLA_MINUTOS,
                   ANALISTA_RESP, DATA_FECHAMENTO
            FROM PCS_CHAMADOS_TI WHERE ID = :id
        """, {"id": id_chamado})
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            flash("Chamado não encontrado.", "error")
            return redirect(url_for('index'))

        chamado = {
            'id': row[0],
            'data_abertura': row[1],
            'matricula': row[2],
            'nome_usuario': row[3],
            'setor': row[4],
            'categoria': row[5],
            'prioridade': row[6],
            'status': row[7],
            'descricao': row[8],
            'status_sla': row[9],
            'data_limite_sla': row[10],
            'sla_minutos': row[11],
            'analista': row[12],
            'data_fechamento': row[13]
        }

        # Buscar histórico
        historico = ChamadoService.buscar_historico(id_chamado)

        return render_template('detalhes.html', chamado=chamado, historico=historico)

    except Exception as e:
        logger.error(f"Erro ao carregar chamado {id_chamado}: {e}")
        flash(f"Erro: {e}", "error")
        return redirect(url_for('index'))


@app.route('/responder/<int:id_chamado>', methods=['POST'])
@limiter.limit("20 per minute")
def responder(id_chamado):
    """Adiciona resposta ao chamado"""
    matricula = request.form.get('matricula')
    resposta = request.form.get('resposta', '').strip()
    is_analista = request.form.get('is_analista') == '1'

    if not matricula or not resposta:
        flash("Matrícula e resposta são obrigatórios.", "error")
        return redirect(url_for('detalhes_chamado', id_chamado=id_chamado))

    try:
        if is_analista:
            success = ChamadoService.resposta_analista(id_chamado, int(matricula), resposta)
        else:
            finalizar = request.form.get('finalizar') == '1'
            success = ChamadoService.resposta_usuario(id_chamado, int(matricula), resposta, finalizar)

        if success:
            flash("Resposta enviada!", "success")
        else:
            flash("Erro ao enviar resposta.", "error")

    except Exception as e:
        logger.error(f"Erro ao responder chamado {id_chamado}: {e}")
        flash(f"Erro: {e}", "error")

    return redirect(url_for('detalhes_chamado', id_chamado=id_chamado))


# ==========================
# API JSON
# ==========================

@app.route('/api/chamados')
def api_chamados():
    """API: Lista chamados"""
    try:
        status = request.args.get('status')
        prioridade = request.args.get('prioridade')

        chamados = listar_chamados(status, prioridade)

        return jsonify({
            'success': True,
            'data': [
                {
                    'id': c[0],
                    'data_abertura': c[1].isoformat() if c[1] else None,
                    'matricula': c[2],
                    'nome_usuario': c[3],
                    'setor': c[4],
                    'prioridade': c[5],
                    'status': c[6],
                    'tecnico': c[7],
                    'status_sla': c[8]
                }
                for c in chamados
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard')
def api_dashboard():
    """API: Dashboard resumo"""
    try:
        chamados = ChamadoService.listar_chamados_ti(apenas_nao_finalizados=False)

        total = len(chamados)
        abertos = len([c for c in chamados if c.status != 'FINALIZADO'])
        atrasados = len([c for c in chamados if c.status_sla == 'ATRASADO' and c.status != 'FINALIZADO'])

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'abertos': abertos,
                'atrasados': atrasados
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================
# FUNÇÕES AUXILIARES
# ==========================

def listar_chamados(filtro_status=None, filtro_prioridade=None):
    """Lista chamados com filtros"""
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT ID, DATA_ABERTURA, MATRICULA, NOME_USUARIO, SETOR,
               PRIORIDADE, STATUS, TECNICO_RESP, STATUS_SLA, DATA_LIMITE_SLA
        FROM PCS_CHAMADOS_TI
        WHERE 1=1
    """
    params = {}

    if filtro_status:
        sql += " AND STATUS = :status"
        params["status"] = filtro_status

    if filtro_prioridade:
        sql += " AND PRIORIDADE = :prioridade"
        params["prioridade"] = filtro_prioridade

    sql += " ORDER BY DATA_ABERTURA DESC"

    cur.execute(sql, params)
    dados = cur.fetchall()
    cur.close()
    conn.close()

    return dados


# ==========================
# MAIN
# ==========================

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=settings.FLASK_DEBUG
    )
