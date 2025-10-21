from flask import Blueprint, request, jsonify, send_file
import io
import json
from datetime import datetime
import logging
from fpdf import FPDF

# Importa as utilidades do banco de dados CORRETAS
from db_utils import (
    supabase, handle_supabase_response, formatar_data_hora, 
    _to_bool, DEFAULT_AUTOTEXT, calcular_dias_resposta, safe_pdf_text,
    get_alunos_por_sala_data
)

# Define o Blueprint para as rotas de Ocorrências
ocorrencias_bp = Blueprint('ocorrencias', __name__)

# =========================================================
# ROTAS DE OCORRÊNCIAS (MANTIDAS COM CORREÇÕES)
# =========================================================

@ocorrencias_bp.route("/api/salas", methods=["GET"])
def api_salas():
    try:
        resp = supabase.table("d_salas").select("id, sala").order("sala").execute()
        salas = handle_supabase_response(resp)
        salas_norm = [{"id": s.get("id"), "nome": s.get("sala")} for s in salas]
        return jsonify(salas_norm), 200
    except Exception as e:
        logging.exception("Erro /api/salas")
        return jsonify({"error": str(e)}), 500

@ocorrencias_bp.route('/api/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala(sala_id):
    try:
        alunos = get_alunos_por_sala_data(sala_id)
        return jsonify(alunos), 200
    except Exception as e:
        logging.exception("Erro api_get_alunos_por_sala")
        return jsonify({"error": str(e)}), 500

@ocorrencias_bp.route('/api/funcionarios', methods=['GET'])
def api_get_funcionarios():
    try:
        response = supabase.table('d_funcionarios').select('id, nome, funcao, is_tutor, email').order('nome').execute()
        funcionarios = [{"id": str(f['id']), "nome": f['nome'], "funcao": f.get('funcao', ''), "is_tutor": f.get('is_tutor', False), "email": f.get('email', '')} for f in handle_supabase_response(response)]
        return jsonify(funcionarios)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar funcionários: {e}", "status": 500}), 500

# ... (TODAS AS OUTRAS ROTAS DO SEU ARQUIVO ORIGINAL MANTIDAS)
# [O resto do código do routes_ocorrencias.py permanece IGUAL]

# ROTA CORRIGIDA: /api/salvar_atendimento (nome correto)
@ocorrencias_bp.route("/api/salvar_atendimento", methods=["POST"])
def salvar_atendimento():
    """Rota para registrar atendimento - nome correto para o frontend"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Corpo da requisição vazio ou JSON inválido."}), 400

        ocorrencia_id = data.get("id")
        nivel = data.get("nivel")
        texto = data.get("texto")
        
        if not ocorrencia_id or not nivel or not texto:
            return jsonify({"error": "Dados incompletos: ID, nível ou texto ausente."}), 400

        campos = {
            "tutor": ("atendimento_tutor", "dt_atendimento_tutor"),
            "coordenacao": ("atendimento_coordenacao", "dt_atendimento_coordenacao"),
            "gestao": ("atendimento_gestao", "dt_atendimento_gestao"),
        }

        if nivel not in campos:
            return jsonify({"error": f"Nível de atendimento inválido: {nivel}"}), 400

        campo_texto, campo_data = campos[nivel]
        
        agora = datetime.utcnow().isoformat(timespec='milliseconds') + "Z"

        # Atualiza os campos de atendimento
        update_data = {
            campo_texto: texto,
            campo_data: agora
        }
        
        supabase.table("ocorrencias").update(update_data).eq("numero", ocorrencia_id).execute()

        return jsonify({"success": True, "message": "Atendimento registrado com sucesso"}), 200

    except Exception as e:
        logging.exception(f"Erro ao registrar atendimento {ocorrencia_id}")
        return jsonify({"error": str(e)}), 500