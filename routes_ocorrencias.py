# routes_ocorrencias.py - COMPLETO E CORRIGIDO
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from db_utils import get_supabase, handle_supabase_response

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

@ocorrencias_bp.route('/api/ocorrencias/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala_ocorrencias(sala_id):
    """Busca alunos por sala específica com dados do tutor"""
    try:
        supabase = get_supabase()
        
        # Busca alunos com informações do tutor
        response = supabase.table('d_alunos').select(
            'id, nome, tutor_id, d_funcionarios!d_alunos_tutor_id_fkey(nome)'
        ).eq('sala_id', sala_id).order('nome').execute()
        
        alunos = response.data if response.data else []
        
        # Formata a resposta para incluir o nome do tutor
        alunos_formatados = []
        for aluno in alunos:
            aluno_formatado = {
                "id": aluno['id'],
                "nome": aluno['nome'],
                "tutor_id": aluno['tutor_id'],
                "tutor_nome": aluno.get('d_funcionarios', {}).get('nome', '') if aluno.get('d_funcionarios') else ''
            }
            alunos_formatados.append(aluno_formatado)
        
        return jsonify(alunos_formatados), 200
        
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/alunos_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos da sala: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/tutor_por_aluno/<int:aluno_id>', methods=['GET'])
def api_get_tutor_por_aluno(aluno_id):
    """Busca informações do tutor por aluno"""
    try:
        supabase = get_supabase()
        
        # Busca aluno com informações do tutor
        response = supabase.table('d_alunos').select(
            'id, nome, tutor_id, d_funcionarios!d_alunos_tutor_id_fkey(id, nome)'
        ).eq('id', aluno_id).single().execute()
        
        if not response.data:
            return jsonify({"error": "Aluno não encontrado"}), 404
            
        aluno = response.data
        tutor_info = {
            "tutor_id": aluno['tutor_id'],
            "tutor_nome": aluno.get('d_funcionarios', {}).get('nome', '') if aluno.get('d_funcionarios') else '',
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
        response = supabase.table('ocorrencias').select('*').in_('status', ['AGUARDANDO ATENDIMENTO', 'EM ANDAMENTO']).order('data_hora', desc=True).execute()
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

@ocorrencias_bp.route('/api/ocorrencias', methods=['POST'])
def api_criar_ocorrencia():
    """Cria uma nova ocorrência"""
    data = request.json
    
    required_fields = ['descricao', 'aluno_id', 'tipo']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        supabase = get_supabase()
        
        # Buscar próximo número de ocorrência
        max_response = supabase.table('ocorrencias').select('numero').order('numero', desc=True).limit(1).execute()
        max_numero = max_response.data[0]['numero'] + 1 if max_response.data and len(max_response.data) > 0 else 1
        
        ocorrencia_data = {
            "numero": max_numero,
            "descricao": data['descricao'],
            "tipo": data['tipo'],
            "aluno_id": data['aluno_id'],
            "aluno_nome": data.get('aluno_nome'),
            "tutor_id": data.get('tutor_id'),
            "professor_id": data.get('professor_id'),
            "sala_id": data.get('sala_id'),
            "atendimento_professor": data.get('atendimento_professor'),
            "solicitado_tutor": data.get('solicitado_tutor', 'NÃO'),
            "solicitado_coordenacao": data.get('solicitado_coordenacao', 'NÃO'),
            "solicitado_gestao": data.get('solicitado_gestao', 'NÃO'),
            "status": "AGUARDANDO ATENDIMENTO",
            "assinada": "NÃO",
            "data_hora": datetime.now().isoformat()
        }
        
        response = supabase.table('ocorrencias').insert(ocorrencia_data).execute()
        
        if response.data:
            return jsonify({
                "message": "Ocorrência criada com sucesso",
                "numero": max_numero
            }), 201
        else:
            return jsonify({"error": "Falha ao criar ocorrência"}), 500

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias POST: {str(e)}")
        return jsonify({"error": f"Falha ao criar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/<int:ocorrencia_numero>', methods=['PUT'])
def api_atualizar_ocorrencia(ocorrencia_numero):
    """Atualiza uma ocorrência existente"""
    data = request.json
    
    try:
        supabase = get_supabase()
        
        update_data = {}
        campos_permitidos = [
            'descricao', 'tipo', 'status', 'atendimento_professor', 
            'atendimento_tutor', 'atendimento_coordenacao', 'atendimento_gestao',
            'solicitado_tutor', 'solicitado_coordenacao', 'solicitado_gestao',
            'dt_atendimento_tutor', 'dt_atendimento_coordenacao', 'dt_atendimento_gestao',
            'assinada', 'impressao_pdf'
        ]
        
        for campo in campos_permitidos:
            if campo in data:
                update_data[campo] = data[campo]
        
        if not update_data:
            return jsonify({"error": "Nenhum campo válido para atualização"}), 400
        
        response = supabase.table('ocorrencias').update(update_data).eq('numero', ocorrencia_numero).execute()
        
        if response.data:
            return jsonify({"message": "Ocorrência atualizada com sucesso"}), 200
        else:
            return jsonify({"error": "Falha ao atualizar ocorrência"}), 500

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias PUT: {str(e)}")
        return jsonify({"error": f"Falha ao atualizar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/<int:ocorrencia_numero>', methods=['GET'])
def api_get_ocorrencia(ocorrencia_numero):
    """Busca uma ocorrência específica"""
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*').eq('numero', ocorrencia_numero).single().execute()
        
        if response.data:
            return jsonify(response.data), 200
        else:
            return jsonify({"error": "Ocorrência não encontrada"}), 404

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias GET: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/tipos', methods=['GET'])
def api_get_tipos_ocorrencia():
    """Retorna os tipos de ocorrência"""
    tipos = [
        {"value": "COMPORTAMENTO", "label": "Comportamento"},
        {"value": "DESEMPENHO", "label": "Desempenho Acadêmico"},
        {"value": "FREQUENCIA", "label": "Frequência"},
        {"value": "CONVIVENCIA", "label": "Convivência"},
        {"value": "OUTROS", "label": "Outros"}
    ]
    return jsonify(tipos), 200

@ocorrencias_bp.route('/api/ocorrencias/status', methods=['GET'])
def api_get_status_ocorrencia():
    """Retorna os status disponíveis"""
    status = [
        {"value": "AGUARDANDO ATENDIMENTO", "label": "Aguardando Atendimento"},
        {"value": "EM ANDAMENTO", "label": "Em Andamento"},
        {"value": "FINALIZADA", "label": "Finalizada"}
    ]
    return jsonify(status), 200
