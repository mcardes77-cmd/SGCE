from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from db_utils import supabase, handle_supabase_response

aulas_bp = Blueprint('aulas', __name__)
DOCS_TABLE = 't_documentos_aulas'

# Tipos de documentos permitidos
ALLOWED_DOC_TYPES = ['PLANO_AULA', 'AGENDA_SEMANAL', 'GUIA_APRENDIZAGEM']

# =========================================================
# 1. ROTAS DE SUBMISSÃO (PROFESSOR)
# =========================================================

@aulas_bp.route('/api/aulas/submeter_documento', methods=['POST'])
def api_submeter_documento():
    data = request.json
    
    required_fields = ['tipo', 'professor_id', 'disciplina', 'conteudo_principal', 'periodo_inicio']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    if data['tipo'] not in ALLOWED_DOC_TYPES:
        return jsonify({"error": f"Tipo de documento inválido. Permitidos: {ALLOWED_DOC_TYPES}"}), 400

    try:
        documento = {
            "tipo": data['tipo'],
            "professor_id": int(data['professor_id']),
            "disciplina": data['disciplina'],
            "sala_serie": data.get('sala_serie'),
            "bimestre": data.get('bimestre'),
            "periodo_inicio": data['periodo_inicio'],
            "periodo_fim": data.get('periodo_fim'),
            "conteudo_principal": data['conteudo_principal'],
            "conteudo_json": data.get('conteudo_json', {}),
            "status": "PENDENTE",
            "data_submissao": datetime.now().isoformat()
        }
        
        response = supabase.table(DOCS_TABLE).insert(documento).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": f"Documento '{data['conteudo_principal']}' submetido para validação.", 
            "id": result[0]['id'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/aulas/submeter_documento")
        return jsonify({"error": f"Falha ao submeter documento: {str(e)}"}), 500

# =========================================================
# 2. ROTAS DE VALIDAÇÃO (COORDENADOR)
# =========================================================

@aulas_bp.route('/api/aulas/documentos_pendentes', methods=['GET'])
def api_documentos_pendentes():
    try:
        # Busca documentos PENDENTES ou que precisam de CORREÇÃO
        resp = supabase.table(DOCS_TABLE).select(
            'id, tipo, conteudo_principal, periodo_inicio, periodo_fim, status, data_submissao, '
            'professor_id:d_funcionarios(nome), disciplina:d_disciplinas(nome), sala_serie:d_salas(sala)'
        ).in_('status', ['PENDENTE', 'CORRECAO']).order('data_submissao', desc=True).execute()
        
        documentos = handle_supabase_response(resp)
        
        # Formata o output para o frontend
        documentos_formatados = []
        for doc in documentos:
            documentos_formatados.append({
                'id': doc['id'],
                'tipo': doc['tipo'],
                'conteudo_principal': doc['conteudo_principal'],
                'periodo_inicio': doc['periodo_inicio'],
                'periodo_fim': doc.get('periodo_fim'),
                'status': doc['status'],
                'data_submissao': doc['data_submissao'],
                'professor_nome': doc.get('professor_id', {}).get('nome', 'N/A'),
                'disciplina_nome': doc.get('disciplina', {}).get('nome', doc.get('disciplina', 'N/A')),
                'sala_nome': doc.get('sala_serie', {}).get('sala', 'N/A') if doc.get('sala_serie') else 'N/A'
            })
        
        return jsonify(documentos_formatados), 200
        
    except Exception as e:
        logging.exception("Erro /api/aulas/documentos_pendentes")
        return jsonify({"error": f"Falha ao buscar documentos pendentes: {str(e)}"}), 500

@aulas_bp.route('/api/aulas/documento/<int:doc_id>', methods=['GET'])
def api_get_documento_detalhe(doc_id):
    try:
        resp = supabase.table(DOCS_TABLE).select(
            '*, professor_id:d_funcionarios(nome), disciplina:d_disciplinas(nome), sala_serie:d_salas(sala, nivel_ensino)'
        ).eq('id', doc_id).single().execute()
        
        documento = handle_supabase_response(resp)
        if not documento:
            return jsonify({"error": "Documento não encontrado."}), 404
            
        # Simplifica os nomes do JOIN
        documento['professor_nome'] = documento.get('professor_id', {}).get('nome', 'N/A')
        documento['disciplina_nome'] = documento.get('disciplina', {}).get('nome', documento.get('disciplina', 'N/A'))
        documento['sala_nome'] = documento.get('sala_serie', {}).get('sala', 'N/A')
        documento['nivel_ensino'] = documento.get('sala_serie', {}).get('nivel_ensino', 'N/A')
        
        return jsonify(documento), 200
        
    except Exception as e:
        logging.exception("Erro /api/aulas/documento/<doc_id>")
        return jsonify({"error": f"Falha ao buscar detalhe do documento: {str(e)}"}), 500

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
            "data_validacao": datetime.now().isoformat() if status == 'APROVADO' else None
        }
        
        response = supabase.table(DOCS_TABLE).update(update_data).eq('id', doc_id).execute()
        handle_supabase_response(response)
        
        msg = f"Documento validado com sucesso. Status: {status.capitalize()}."
        return jsonify({"message": msg}), 200

    except Exception as e:
        logging.exception("Erro /api/aulas/validar")
        return jsonify({"error": f"Falha ao validar documento: {str(e)}"}), 500

# =========================================================
# 3. ROTAS AUXILIARES
# =========================================================

@aulas_bp.route('/api/aulas/documentos_aprovados', methods=['GET'])
def api_documentos_aprovados():
    try:
        resp = supabase.table(DOCS_TABLE).select(
            'id, tipo, conteudo_principal, periodo_inicio, periodo_fim, data_validacao, '
            'professor_id:d_funcionarios(nome), disciplina:d_disciplinas(nome), sala_serie:d_salas(sala)'
        ).eq('status', 'APROVADO').order('data_validacao', desc=True).execute()
        
        documentos = handle_supabase_response(resp)
        
        documentos_formatados = []
        for doc in documentos:
            documentos_formatados.append({
                'id': doc['id'],
                'tipo': doc['tipo'],
                'conteudo_principal': doc['conteudo_principal'],
                'periodo_inicio': doc['periodo_inicio'],
                'periodo_fim': doc.get('periodo_fim'),
                'data_validacao': doc['data_validacao'],
                'professor_nome': doc.get('professor_id', {}).get('nome', 'N/A'),
                'disciplina_nome': doc.get('disciplina', {}).get('nome', doc.get('disciplina', 'N/A')),
                'sala_nome': doc.get('sala_serie', {}).get('sala', 'N/A') if doc.get('sala_serie') else 'N/A'
            })
        
        return jsonify(documentos_formatados), 200
        
    except Exception as e:
        logging.exception("Erro /api/aulas/documentos_aprovados")
        return jsonify({"error": f"Falha ao buscar documentos aprovados: {str(e)}"}), 500

@aulas_bp.route('/api/aulas/meus_documentos/<int:professor_id>', methods=['GET'])
def api_meus_documentos(professor_id):
    try:
        resp = supabase.table(DOCS_TABLE).select(
            'id, tipo, conteudo_principal, periodo_inicio, status, data_submissao, data_validacao, motivo_correcao'
        ).eq('professor_id', professor_id).order('data_submissao', desc=True).execute()
        
        documentos = handle_supabase_response(resp)
        return jsonify(documentos), 200
        
    except Exception as e:
        logging.exception("Erro /api/aulas/meus_documentos")
        return jsonify({"error": f"Falha ao buscar documentos do professor: {str(e)}"}), 500