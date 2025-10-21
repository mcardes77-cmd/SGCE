from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from db_utils import supabase, handle_supabase_response

ocorrencias_bp = Blueprint('ocorrencias', __name__)

# =========================================================
# 1. ROTAS PARA OCORRÊNCIAS
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias', methods=['GET'])
def api_get_ocorrencias():
    """Busca todas as ocorrências"""
    try:
        response = supabase.table('ocorrencias').select(
            '*, aluno_id:d_alunos(nome), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala)'
        ).order('data_hora', desc=True).execute()
        
        ocorrencias = handle_supabase_response(response)
        return jsonify(ocorrencias), 200
        
    except Exception as e:
        logging.exception("Erro /api/ocorrencias")
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/<int:ocorrencia_id>', methods=['GET'])
def api_get_ocorrencia(ocorrencia_id):
    """Busca uma ocorrência específica"""
    try:
        response = supabase.table('ocorrencias').select(
            '*, aluno_id:d_alunos(nome), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala)'
        ).eq('numero', ocorrencia_id).single().execute()
        
        ocorrencia = handle_supabase_response(response)
        return jsonify(ocorrencia), 200
        
    except Exception as e:
        logging.exception("Erro /api/ocorrencias/<id>")
        return jsonify({"error": f"Falha ao buscar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias', methods=['POST'])
def api_criar_ocorrencia():
    """Cria uma nova ocorrência"""
    data = request.json
    
    required_fields = ['descricao', 'tipo', 'aluno_id']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        # Buscar próximo número de ocorrência
        max_response = supabase.table('ocorrencias').select('numero').order('numero', desc=True).limit(1).execute()
        max_numero = handle_supabase_response(max_response)
        proximo_numero = max_numero[0]['numero'] + 1 if max_numero else 1
        
        ocorrencia_data = {
            "numero": proximo_numero,
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
            "status": data.get('status', 'AGUARDANDO ATENDIMENTO'),
            "data_hora": datetime.now().isoformat()
        }
        
        response = supabase.table('ocorrencias').insert(ocorrencia_data).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": "Ocorrência criada com sucesso",
            "numero": proximo_numero,
            "id": result[0]['numero'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/ocorrencias POST")
        return jsonify({"error": f"Falha ao criar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/<int:ocorrencia_id>', methods=['PUT'])
def api_atualizar_ocorrencia(ocorrencia_id):
    """Atualiza uma ocorrência existente"""
    data = request.json
    
    try:
        update_data = {}
        
        # Campos que podem ser atualizados
        campos_permitidos = [
            'descricao', 'tipo', 'atendimento_professor', 'atendimento_tutor',
            'atendimento_coordenacao', 'atendimento_gestao', 'status',
            'dt_atendimento_tutor', 'dt_atendimento_coordenacao', 'dt_atendimento_gestao',
            'solicitado_tutor', 'solicitado_coordenacao', 'solicitado_gestao',
            'assinada', 'impressao_pdf'
        ]
        
        for campo in campos_permitidos:
            if campo in data:
                update_data[campo] = data[campo]
        
        if not update_data:
            return jsonify({"error": "Nenhum campo válido para atualização"}), 400
        
        response = supabase.table('ocorrencias').update(update_data).eq('numero', ocorrencia_id).execute()
        handle_supabase_response(response)
        
        return jsonify({"message": "Ocorrência atualizada com sucesso"}), 200

    except Exception as e:
        logging.exception("Erro /api/ocorrencias/<id> PUT")
        return jsonify({"error": f"Falha ao atualizar ocorrência: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/abertas', methods=['GET'])
def api_get_ocorrencias_abertas():
    """Busca ocorrências em aberto"""
    try:
        response = supabase.table('ocorrencias').select(
            '*, aluno_id:d_alunos(nome), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala)'
        ).in_('status', ['AGUARDANDO ATENDIMENTO', 'EM ANDAMENTO']).order('data_hora', desc=True).execute()
        
        ocorrencias = handle_supabase_response(response)
        return jsonify(ocorrencias), 200
        
    except Exception as e:
        logging.exception("Erro /api/ocorrencias/abertas")
        return jsonify({"error": f"Falha ao buscar ocorrências abertas: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/finalizadas', methods=['GET'])
def api_get_ocorrencias_finalizadas():
    """Busca ocorrências finalizadas"""
    try:
        response = supabase.table('ocorrencias').select(
            '*, aluno_id:d_alunos(nome), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala)'
        ).eq('status', 'FINALIZADA').order('data_hora', desc=True).execute()
        
        ocorrencias = handle_supabase_response(response)
        return jsonify(ocorrencias), 200
        
    except Exception as e:
        logging.exception("Erro /api/ocorrencias/finalizadas")
        return jsonify({"error": f"Falha ao buscar ocorrências finalizadas: {str(e)}"}), 500

# =========================================================
# 2. ROTAS AUXILIARES PARA FORMULÁRIOS
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias/tipos', methods=['GET'])
def api_get_tipos_ocorrencia():
    """Retorna os tipos de ocorrência disponíveis"""
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

# =========================================================
# 3. ROTAS PARA RELATÓRIOS E IMPRESSÃO
# =========================================================

@ocorrencias_bp.route('/api/ocorrencias/relatorio', methods=['POST'])
def api_gerar_relatorio_ocorrencias():
    """Gera relatório de ocorrências com filtros"""
    data = request.json
    
    try:
        query = supabase.table('ocorrencias').select(
            '*, aluno_id:d_alunos(nome), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala)'
        )
        
        # Aplicar filtros
        if data.get('data_inicio'):
            query = query.gte('data_hora', data['data_inicio'])
        if data.get('data_fim'):
            query = query.lte('data_hora', data['data_fim'])
        if data.get('tipo'):
            query = query.eq('tipo', data['tipo'])
        if data.get('status'):
            query = query.eq('status', data['status'])
        if data.get('sala_id'):
            query = query.eq('sala_id', data['sala_id'])
        
        response = query.order('data_hora', desc=True).execute()
        ocorrencias = handle_supabase_response(response)
        
        return jsonify({
            "ocorrencias": ocorrencias,
            "total": len(ocorrencias),
            "filtros": data
        }), 200
        
    except Exception as e:
        logging.exception("Erro /api/ocorrencias/relatorio")
        return jsonify({"error": f"Falha ao gerar relatório: {str(e)}"}), 500

@ocorrencias_bp.route('/api/ocorrencias/<int:ocorrencia_id>/imprimir', methods=['GET'])
def api_imprimir_ocorrencia(ocorrencia_id):
    """Prepara dados para impressão de ocorrência"""
    try:
        response = supabase.table('ocorrencias').select(
            '*, aluno_id:d_alunos(nome, sala_id), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala, nivel_ensino)'
        ).eq('numero', ocorrencia_id).single().execute()
        
        ocorrencia = handle_supabase_response(response)
        
        # Marcar como impressa
        supabase.table('ocorrencias').update({
            "impressao_pdf": True
        }).eq('numero', ocorrencia_id).execute()
        
        return jsonify(ocorrencia), 200
        
    except Exception as e:
        logging.exception("Erro /api/ocorrencias/<id>/imprimir")
        return jsonify({"error": f"Falha ao preparar impressão: {str(e)}"}), 500
