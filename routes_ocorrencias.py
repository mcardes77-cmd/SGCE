from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import logging
import io
from db_utils import get_supabase
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

ocorrencias_bp = Blueprint('ocorrencias', __name__)

# =========================================================
# ROTAS AUXILIARES PARA FORMULÁRIO DE OCORRÊNCIA
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias/salas', methods=['GET'])
def api_get_salas_ocorrencias():
    """Busca salas para o formulário de ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_salas').select('id, sala').order('sala').execute()
        salas = response.data if response.data else []
        return jsonify(salas), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/salas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500


@ocorrencias_bp.route('/api/salas_com_ocorrencias', methods=['GET'])
def api_get_salas_com_ocorrencias():
    """Busca salas que possuem ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_salas').select('id, sala').order('sala').execute()
        salas = response.data if response.data else []
        return jsonify(salas), 200
    except Exception as e:
        logging.error(f"Erro /api/salas_com_ocorrencias: {str(e)}")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500


@ocorrencias_bp.route('/api/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala(sala_id):
    """Busca todos os alunos de uma sala"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_alunos').select('id, nome, tutor_id').eq('sala_id', sala_id).order('nome').execute()
        alunos = response.data if response.data else []
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/alunos_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500


@ocorrencias_bp.route('/api/alunos_com_ocorrencias_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_com_ocorrencias_por_sala(sala_id):
    """Busca alunos por sala que possuem ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_alunos').select('id, nome, tutor_id').eq('sala_id', sala_id).order('nome').execute()
        alunos = response.data if response.data else []
        alunos_com_ocorrencias = []
        for aluno in alunos:
            ocorrencias_response = supabase.table('ocorrencias').select('id').eq('aluno_id', aluno['id']).limit(1).execute()
            if ocorrencias_response.data:
                alunos_com_ocorrencias.append(aluno)
        return jsonify(alunos_com_ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/alunos_com_ocorrencias_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500


@ocorrencias_bp.route('/api/ocorrencias_por_aluno/<int:aluno_id>', methods=['GET'])
def api_get_ocorrencias_por_aluno(aluno_id):
    """Busca ocorrências de um aluno específico"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').eq('aluno_id', aluno_id).order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias_por_aluno: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências do aluno: {str(e)}"}), 500


@ocorrencias_bp.route('/api/ocorrencias/tutor_por_aluno/<int:aluno_id>', methods=['GET'])
def api_get_tutor_por_aluno(aluno_id):
    """Busca informações do tutor por aluno"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_alunos').select(
            'id, nome, tutor_id, d_funcionarios!inner(id, nome)'
        ).eq('id', aluno_id).single().execute()

        if not response.data:
            return jsonify({"error": "Aluno não encontrado"}), 404

        aluno = response.data
        tutor_nome = ''

        if aluno.get('d_funcionarios'):
            if isinstance(aluno['d_funcionarios'], list) and aluno['d_funcionarios']:
                tutor_nome = aluno['d_funcionarios'][0].get('nome', '')
            elif isinstance(aluno['d_funcionarios'], dict):
                tutor_nome = aluno['d_funcionarios'].get('nome', '')

        tutor_info = {
            "tutor_id": aluno.get('tutor_id'),
            "tutor_nome": tutor_nome,
            "aluno_id": aluno['id'],
            "aluno_nome": aluno['nome']
        }

        return jsonify(tutor_info), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/tutor_por_aluno: {str(e)}")
        return jsonify({"error": f"Falha ao buscar tutor do aluno: {str(e)}"}), 500


@ocorrencias_bp.route('/api/ocorrencias/professores', methods=['GET'])
def api_get_professores_ocorrencias():
    """Busca professores para ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('d_funcionarios').select('id, nome').order('nome').execute()
        professores = response.data if response.data else []
        return jsonify(professores), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/professores: {str(e)}")
        return jsonify({"error": f"Falha ao buscar professores: {str(e)}"}), 500


# =========================================================
# ROTAS PRINCIPAIS DE OCORRÊNCIAS
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias', methods=['GET'])
def api_get_ocorrencias():
    """Busca todas as ocorrências"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500


@ocorrencias_bp.route('/api/ocorrencias/abertas', methods=['GET'])
def api_get_ocorrencias_abertas():
    """Busca ocorrências em aberto"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').in_(
            'status', ['AGUARDANDO ATENDIMENTO', 'EM ANDAMENTO']
        ).order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/abertas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências abertas: {str(e)}"}), 500


@ocorrencias_bp.route('/api/ocorrencias/finalizadas', methods=['GET'])
def api_get_ocorrencias_finalizadas():
    """Busca ocorrências finalizadas"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').eq('status', 'FINALIZADA').order('data_hora', desc=True).execute()
        ocorrencias = response.data if response.data else []
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/finalizadas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências finalizadas: {str(e)}"}), 500
