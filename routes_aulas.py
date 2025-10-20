from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from db_utils import supabase, handle_supabase_response # Assumindo db_utils existe

# Define o Blueprint para as rotas de Gestão de Aulas
aulas_bp = Blueprint('aulas', __name__)

# Nome da tabela que armazenará os documentos submetidos
DOCS_TABLE = 't_documentos_aulas' 

# =========================================================
# 1. ROTA DE SUBMISSÃO (PROFESSOR)
# =========================================================

# ROTA: /api/aulas/submeter_documento (POST)
@aulas_bp.route('/api/aulas/submeter_documento', methods=['POST'])
def api_submeter_documento():
    data = request.json
    
    required_fields = ['tipo', 'professor_id', 'disciplina', 'conteudo_principal', 'periodo_inicio']
    
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        documento = {
            "tipo": data['tipo'],
            "professor_id": int(data['professor_id']),
            "disciplina": data['disciplina'], # Abreviação da Disciplina
            "sala_serie": data.get('sala_serie'), # ID da Sala
            "bimestre": data.get('bimestre'),
            "periodo_inicio": data['periodo_inicio'],
            "periodo_fim": data.get('periodo_fim'),
            "conteudo_principal": data['conteudo_principal'],
            "conteudo_json": data.get('conteudo_json', {}), # Conteúdo detalhado (Plano/Guia)
            "status": "PENDENTE",
            "data_submissao": datetime.now().isoformat()
        }
        
        response = supabase.table(DOCS_TABLE).insert(documento).execute()
        handle_supabase_response(response)
        
        return jsonify({"message": f"Documento '{data['conteudo_principal']}' submetido para validação.", "id": response.data[0]['id']}), 201

    except Exception as e:
        logging.exception("Erro /api/aulas/submeter_documento")
        return jsonify({"error": f"Falha ao submeter documento: {e}"}), 500

# =========================================================
# 2. ROTAS DE VALIDAÇÃO (COORDENADOR)
# =========================================================

# ROTA: /api/aulas/documentos_pendentes (GET)
@aulas_bp.route('/api/aulas/documentos_pendentes', methods=['GET'])
def api_documentos_pendentes():
    try:
        # Busca documentos PENDENTES ou que precisam de CORREÇÃO
        # Faz JOIN para obter os nomes do professor e disciplina
        resp = supabase.table(DOCS_TABLE).select(
            'id, tipo, conteudo_principal, periodo_inicio, professor_id:d_professores_funcionarios(nome), disciplina:d_disciplinas(nome)'
        ).in_('status', ['PENDENTE', 'CORRECAO']).order('data_submissao', desc=False).execute()
        
        documentos = handle_supabase_response(resp)
        
        # Formata o output para o frontend
        documentos_formatados = [
            {
                'id': doc['id'],
                'tipo': doc['tipo'],
                'conteudo_principal': doc['conteudo_principal'],
                'periodo_inicio': doc['periodo_inicio'],
                # Extrai os nomes do JOIN
                'professor_nome': doc.get('professor_id', {}).get('nome', 'N/A'),
                'disciplina_nome': doc.get('disciplina', {}).get('nome', doc['disciplina']),
            } for doc in documentos
        ]
        
        return jsonify(documentos_formatados), 200
        
    except Exception as e:
        logging.exception("Erro /api/aulas/documentos_pendentes")
        return jsonify({"error": f"Falha ao buscar documentos pendentes: {e}"}), 500

# ROTA: /api/aulas/documento/<doc_id> (GET)
@aulas_bp.route('/api/aulas/documento/<int:doc_id>', methods=['GET'])
def api_get_documento_detalhe(doc_id):
    try:
        # Busca todos os campos do documento, incluindo o JSON de conteúdo
        resp = supabase.table(DOCS_TABLE).select(
            '*, professor_nome:d_professores_funcionarios(nome), disciplina_nome:d_disciplinas(nome)'
        ).eq('id', doc_id).single().execute()
        
        documento = handle_supabase_response(resp)
        if not documento:
            return jsonify({"error": "Documento não encontrado."}), 404
            
        # Simplifica os nomes do JOIN
        documento['professor_nome'] = documento.pop('professor_nome', {}).get('nome', 'N/A')
        documento['disciplina_nome'] = documento.pop('disciplina_nome', {}).get('nome', documento['disciplina'])
        
        return jsonify(documento), 200
        
    except Exception as e:
        logging.exception("Erro /api/aulas/documento/<doc_id>")
        return jsonify({"error": f"Falha ao buscar detalhe do documento: {e}"}), 500


# ROTA: /api/aulas/validar (POST)
@aulas_bp.route('/api/aulas/validar', methods=['POST'])
def api_validar_documento():
    data = request.json
    doc_id = data.get('doc_id')
    status = data.get('status')
    motivo_correcao = data.get('motivo_correcao')

    if not doc_id or status not in ['APROVADO', 'CORRECAO']:
        return jsonify({"error": "ID do documento e status (APROVADO/CORRECAO) são obrigatórios."}), 400
        
    if status == 'CORRECAO' and not motivo_correcao:
        return jsonify({"error": "O motivo da correção é obrigatório para solicitar correções."}), 400

    try:
        update_data = {
            "status": status,
            "motivo_correcao": motivo_correcao if status == 'CORRECAO' else None,
            "data_validacao": datetime.now().isoformat()
        }
        
        response = supabase.table(DOCS_TABLE).update(update_data).eq('id', doc_id).execute()
        handle_supabase_response(response)
        
        msg = f"Documento validado com sucesso. Status: {status.capitalize()}."
        return jsonify({"message": msg}), 200

    except Exception as e:
        logging.exception("Erro /api/aulas/validar")
        return jsonify({"error": f"Falha ao validar documento: {e}"}), 500