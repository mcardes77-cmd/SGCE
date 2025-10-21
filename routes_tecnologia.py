from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from db_utils import supabase, handle_supabase_response

tecnologia_bp = Blueprint('tecnologia', __name__)

# =========================================================
# 1. ROTAS DE AGENDAMENTO DE EQUIPAMENTOS
# =========================================================

@tecnologia_bp.route('/api/agendar_equipamento', methods=['POST'])
def api_agendar_equipamento():
    """Rota 18: Cria um agendamento de equipamentos"""
    data = request.json
    
    required_fields = ['fk_professor_id', 'fk_sala_id', 'data_uso', 'aula_id', 'quantidade']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        # Verifica disponibilidade primeiro
        disponibilidade_response = supabase.table('d_inventario_equipamentos').select('id').eq('status', 'DISPONÍVEL').execute()
        equipamentos_disponiveis = handle_supabase_response(disponibilidade_response)
        
        if len(equipamentos_disponiveis) < data['quantidade']:
            return jsonify({"error": f"Apenas {len(equipamentos_disponiveis)} equipamentos disponíveis. Solicitação: {data['quantidade']}"}), 400

        # Cria o agendamento
        agendamento = {
            "professor_id": data['fk_professor_id'],
            "sala_id": data['fk_sala_id'],
            "data_uso": data['data_uso'],
            "aula_id": data['aula_id'],
            "quantidade": data['quantidade'],
            "status": "AGENDADO",
            "equipamentos_reservados_json": data.get('equipamentos_reservados_ids', []),
            "data_agendamento": datetime.now().isoformat()
        }
        
        response = supabase.table('reservas_equipamentos').insert(agendamento).execute()
        result = handle_supabase_response(response)
        
        # Atualiza status dos equipamentos para RESERVADO
        if data.get('equipamentos_reservados_ids'):
            for eq_id in data['equipamentos_reservados_ids']:
                supabase.table('d_inventario_equipamentos').update({
                    "status": "RESERVADO",
                    "reserva_id": result[0]['id'] if result else None
                }).eq('id', eq_id).execute()
        
        return jsonify({
            "message": f"Agendamento criado com sucesso para {data['quantidade']} equipamentos.",
            "id": result[0]['id'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/agendar_equipamento")
        return jsonify({"error": f"Falha ao criar agendamento: {str(e)}"}), 500

@tecnologia_bp.route('/api/agendamentos_pendentes/<int:professor_id>', methods=['GET'])
def api_agendamentos_pendentes(professor_id):
    """Rota 19: Busca agendamentos pendentes do professor"""
    try:
        response = supabase.table('reservas_equipamentos').select(
            'id, professor_id, sala_id, data_uso, aula_id, quantidade, status, data_agendamento, '
            'd_salas(sala), d_funcionarios(nome)'
        ).eq('professor_id', professor_id).in_('status', ['AGENDADO', 'EM USO']).order('data_uso').execute()
        
        agendamentos = handle_supabase_response(response)
        
        agendamentos_formatados = []
        for ag in agendamentos:
            agendamentos_formatados.append({
                'id': ag['id'],
                'professor_id': ag['professor_id'],
                'prof_nome': ag.get('d_funcionarios', {}).get('nome', 'N/A'),
                'sala_id': ag['sala_id'],
                'sala_nome': ag.get('d_salas', {}).get('sala', 'N/A'),
                'data_uso': ag['data_uso'],
                'aula_id': ag['aula_id'],
                'quantidade': ag['quantidade'],
                'status': ag['status'],
                'data_agendamento': ag['data_agendamento']
            })
        
        return jsonify(agendamentos_formatados), 200
        
    except Exception as e:
        logging.exception("Erro /api/agendamentos_pendentes")
        return jsonify({"error": f"Falha ao buscar agendamentos: {str(e)}"}), 500

# =========================================================
# 2. ROTAS DE RECEBIMENTO/DEVOLUÇÃO
# =========================================================

@tecnologia_bp.route('/api/finalizar_retirada_equipamento', methods=['POST'])
def api_finalizar_retirada_equipamento():
    """Rota 20: Finaliza a retirada dos equipamentos"""
    data = request.json
    
    required_fields = ['agendamento_id', 'vinculacoes']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        # Atualiza status do agendamento
        update_agendamento = supabase.table('reservas_equipamentos').update({
            "status": "EM USO",
            "data_recebimento": datetime.now().isoformat()
        }).eq('id', data['agendamento_id']).execute()
        
        handle_supabase_response(update_agendamento)
        
        # Cria vinculações aluno-equipamento
        for vinculacao in data['vinculacoes']:
            vinculacao_data = {
                "agendamento_id": data['agendamento_id'],
                "aluno_id": vinculacao['aluno_id'],
                "equipamento_id": vinculacao['equipamento_id'],
                "data_retirada": vinculacao.get('data_retirada', datetime.now().isoformat()),
                "status": "EM USO"
            }
            
            supabase.table('vinculos_equipamento_aluno').insert(vinculacao_data).execute()
            
            # Atualiza status do equipamento para EM USO
            supabase.table('d_inventario_equipamentos').update({
                "status": "EM USO",
                "aluno_id": vinculacao['aluno_id']
            }).eq('id', vinculacao['equipamento_id']).execute()
        
        return jsonify({"message": "Retirada de equipamentos finalizada com sucesso."}), 200

    except Exception as e:
        logging.exception("Erro /api/finalizar_retirada_equipamento")
        return jsonify({"error": f"Falha ao finalizar retirada: {str(e)}"}), 500

@tecnologia_bp.route('/api/finalizar_devolucao_equipamento', methods=['POST'])
def api_finalizar_devolucao_equipamento():
    """Rota 21: Finaliza a devolução dos equipamentos"""
    data = request.json
    
    if not data.get('agendamento_id'):
        return jsonify({"error": "ID do agendamento é obrigatório."}), 400

    try:
        # Atualiza status do agendamento
        update_agendamento = supabase.table('reservas_equipamentos').update({
            "status": "FINALIZADO",
            "data_devolucao": datetime.now().isoformat()
        }).eq('id', data['agendamento_id']).execute()
        
        handle_supabase_response(update_agendamento)
        
        # Busca equipamentos vinculados ao agendamento
        vinculacoes_response = supabase.table('vinculos_equipamento_aluno').select(
            'equipamento_id'
        ).eq('agendamento_id', data['agendamento_id']).execute()
        
        vinculacoes = handle_supabase_response(vinculacoes_response)
        
        # Atualiza status dos equipamentos para DISPONÍVEL
        for vinculacao in vinculacoes:
            supabase.table('d_inventario_equipamentos').update({
                "status": "DISPONÍVEL",
                "aluno_id": None
            }).eq('id', vinculacao['equipamento_id']).execute()
        
        # Atualiza status das vinculações
        supabase.table('vinculos_equipamento_aluno').update({
            "status": "FINALIZADO",
            "data_devolucao": datetime.now().isoformat()
        }).eq('agendamento_id', data['agendamento_id']).execute()
        
        return jsonify({"message": "Devolução de equipamentos finalizada com sucesso."}), 200

    except Exception as e:
        logging.exception("Erro /api/finalizar_devolucao_equipamento")
        return jsonify({"error": f"Falha ao finalizar devolução: {str(e)}"}), 500

# =========================================================
# 3. ROTAS DE OCORRÊNCIAS
# =========================================================

@tecnologia_bp.route('/api/registrar_ocorrencia_equipamento', methods=['POST'])
def api_registrar_ocorrencia_equipamento():
    """Rota 22: Registra ocorrência de equipamento"""
    data = request.json
    
    required_fields = ['fk_equipamento_id', 'fk_professor_id', 'data_ocorrencia', 'descricao', 'acao']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    try:
        ocorrencia = {
            "equipamento_id": data['fk_equipamento_id'],
            "professor_id": data['fk_professor_id'],
            "aluno_id": data.get('fk_aluno_id'),
            "data_ocorrencia": data['data_ocorrencia'],
            "hora_ocorrencia": data.get('hora_ocorrencia'),
            "descricao": data['descricao'],
            "acao_tomada": data['acao'],
            "status": "REGISTRADA",
            "data_registro": datetime.now().isoformat()
        }
        
        response = supabase.table('ocorrencias_equipamentos').insert(ocorrencia).execute()
        result = handle_supabase_response(response)
        
        # Atualiza status do equipamento para EM MANUTENÇÃO se necessário
        if "danificado" in data['descricao'].lower() or "quebrado" in data['descricao'].lower():
            supabase.table('d_inventario_equipamentos').update({
                "status": "EM MANUTENÇÃO"
            }).eq('id', data['fk_equipamento_id']).execute()
        
        return jsonify({
            "message": "Ocorrência registrada com sucesso.",
            "id": result[0]['id'] if result else None
        }), 201

    except Exception as e:
        logging.exception("Erro /api/registrar_ocorrencia_equipamento")
        return jsonify({"error": f"Falha ao registrar ocorrência: {str(e)}"}), 500

@tecnologia_bp.route('/api/ocorrencias_equipamentos', methods=['GET'])
def api_ocorrencias_equipamentos():
    """Rota 23: Lista ocorrências de equipamentos"""
    try:
        response = supabase.table('ocorrencias_equipamentos').select(
            'id, equipamento_id, professor_id, aluno_id, data_ocorrencia, descricao, acao_tomada, status, '
            'd_inventario_equipamentos(colmeia, equipamento_id), d_funcionarios(nome), d_alunos(nome)'
        ).order('data_ocorrencia', desc=True).execute()
        
        ocorrencias = handle_supabase_response(response)
        
        ocorrencias_formatadas = []
        for oc in ocorrencias:
            ocorrencias_formatadas.append({
                'id': oc['id'],
                'equipamento_id': oc['equipamento_id'],
                'equipamento_info': f"Colmeia {oc.get('d_inventario_equipamentos', {}).get('colmeia', 'N/A')} - Eq. {oc.get('d_inventario_equipamentos', {}).get('equipamento_id', 'N/A')}",
                'professor_nome': oc.get('d_funcionarios', {}).get('nome', 'N/A'),
                'aluno_nome': oc.get('d_alunos', {}).get('nome', 'N/A') if oc.get('aluno_id') else 'Não vinculado',
                'data_ocorrencia': oc['data_ocorrencia'],
                'descricao': oc['descricao'],
                'acao_tomada': oc['acao_tomada'],
                'status': oc['status']
            })
        
        return jsonify(ocorrencias_formatadas), 200
        
    except Exception as e:
        logging.exception("Erro /api/ocorrencias_equipamentos")
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500

# =========================================================
# 4. ROTAS AUXILIARES
# =========================================================

@tecnologia_bp.route('/api/inventario', methods=['GET'])
def api_inventario():
    """Rota 24: Lista todos os equipamentos do inventário"""
    try:
        response = supabase.table('d_inventario_equipamentos').select(
            'id, colmeia, equipamento_id, status, aluno_id, reserva_id'
        ).order('colmeia', 'equipamento_id').execute()
        
        equipamentos = handle_supabase_response(response)
        return jsonify(equipamentos), 200
        
    except Exception as e:
        logging.exception("Erro /api/inventario")
        return jsonify({"error": f"Falha ao buscar inventário: {str(e)}"}), 500

@tecnologia_bp.route('/api/inventario/disponibilidade/<data>/<aula_id>', methods=['GET'])
def api_inventario_disponibilidade(data, aula_id):
    """Rota 25: Verifica disponibilidade de equipamentos por data e aula"""
    try:
        # Busca equipamentos reservados para a data e aula
        reservas_response = supabase.table('reservas_equipamentos').select(
            'quantidade, equipamentos_reservados_json'
        ).eq('data_uso', data).eq('aula_id', aula_id).in_('status', ['AGENDADO', 'EM USO']).execute()
        
        reservas = handle_supabase_response(reservas_response)
        
        total_reservado = 0
        for reserva in reservas:
            total_reservado += reserva.get('quantidade', 0)
        
        # Busca total de equipamentos disponíveis
        inventario_response = supabase.table('d_inventario_equipamentos').select(
            'id', count='exact'
        ).eq('status', 'DISPONÍVEL').execute()
        
        total_disponivel = len(inventario_response.data) if inventario_response.data else 0
        
        disponibilidade = {
            "data": data,
            "aula_id": aula_id,
            "total_equipamentos": 80,  # Capacidade total fixa
            "total_disponivel": total_disponivel,
            "total_reservado": total_reservado,
            "disponivel_para_reserva": total_disponivel - total_reservado
        }
        
        return jsonify(disponibilidade), 200
        
    except Exception as e:
        logging.exception("Erro /api/inventario/disponibilidade")
        return jsonify({"error": f"Falha ao verificar disponibilidade: {str(e)}"}), 500

@tecnologia_bp.route('/api/equipamentos_em_uso', methods=['GET'])
def api_equipamentos_em_uso():
    """Rota 26: Lista equipamentos atualmente em uso"""
    try:
        response = supabase.table('d_inventario_equipamentos').select(
            'id, colmeia, equipamento_id, status, aluno_id, '
            'd_alunos(nome, sala_id), d_salas(sala)'
        ).eq('status', 'EM USO').execute()
        
        equipamentos = handle_supabase_response(response)
        
        equipamentos_formatados = []
        for eq in equipamentos:
            equipamentos_formatados.append({
                'id': eq['id'],
                'colmeia': eq['colmeia'],
                'equipamento_id': eq['equipamento_id'],
                'aluno_nome': eq.get('d_alunos', {}).get('nome', 'N/A'),
                'sala_nome': eq.get('d_alunos', {}).get('d_salas', {}).get('sala', 'N/A'),
                'status': eq['status']
            })
        
        return jsonify(equipamentos_formatados), 200
        
    except Exception as e:
        logging.exception("Erro /api/equipamentos_em_uso")
        return jsonify({"error": f"Falha ao buscar equipamentos em uso: {str(e)}"}), 500