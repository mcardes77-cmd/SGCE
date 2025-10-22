# app.py (Arquivo consolidado)
from flask import Flask, render_template, Blueprint, jsonify, request, send_file
from datetime import datetime
from calendar import monthrange
import os
import logging
import io
from fpdf import FPDF # Necessário para a rota de PDF (se implementada)

# Importa todas as utilidades do banco de dados e funções auxiliares
# Assumindo que db_utils.py está no mesmo diretório e contém 'get_supabase', 'handle_supabase_response', etc.
from db_utils import (
    get_supabase, handle_supabase_response,
    formatar_data_hora, _to_bool, DEFAULT_AUTOTEXT, 
    calcular_dias_resposta, safe_pdf_text, get_alunos_por_sala_data, 
    get_equipamentos_disponiveis
)

# --- Importa Blueprints Remanescentes (Tutoria e Aulas, se não forem unificados) ---
# Se os arquivos routes_tutoria.py e routes_aulas.py ainda existirem
from routes_tutoria import tutoria_bp
from routes_aulas import aulas_bp 
from routes_cadastro import cadastro_bp # Manter se a lógica de cadastro for complexa/grande

# Configuração
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
logging.basicConfig(level=logging.INFO)

# ===============================================
# 1. DEFINIÇÃO DO BLUEPRINT PRINCIPAL (main_bp)
# ===============================================

main_bp = Blueprint('main', __name__)

# Rotas de Menu (Front-end)
@main_bp.route('/')
def home():
    return render_template('index.html')

# Rotas de Módulos (Gestão)
@main_bp.route('/gestao_frequencia')
def gestao_frequencia(): return render_template('gestao_frequencia.html')
@main_bp.route('/gestao_frequencia_registro')
def gestao_frequencia_registro(): return render_template('gestao_frequencia_registro.html')
@main_bp.route('/gestao_frequencia_atraso')
def gestao_frequencia_atraso(): return render_template('gestao_frequencia_atraso.html')
@main_bp.route('/gestao_frequencia_saida')
def gestao_frequencia_saida(): return render_template('gestao_frequencia_saida.html')
@main_bp.route('/gestao_relatorio_frequencia')
def gestao_relatorio_frequencia(): return render_template('gestao_relatorio_frequencia.html')
@main_bp.route('/gestao_ocorrencia')
def gestao_ocorrencia(): return render_template('gestao_ocorrencia.html')
@main_bp.route('/gestao_ocorrencia_nova')
def gestao_ocorrencia_nova(): return render_template('gestao_ocorrencia_nova.html')
@main_bp.route('/gestao_ocorrencia_abertas')
def gestao_ocorrencia_abertas(): return render_template('gestao_ocorrencia_aberta.html')
@main_bp.route('/gestao_ocorrencia_finalizadas')
def gestao_ocorrencia_finalizadas(): return render_template('gestao_ocorrencia_finalizada.html')
@main_bp.route('/gestao_ocorrencia_editar')
def gestao_ocorrencia_editar(): return render_template('gestao_ocorrencia_editar.html')
@main_bp.route('/gestao_relatorio_impressao')
def gestao_relatorio_impressao(): return render_template('gestao_relatorio_impressao.html')
@main_bp.route('/gestao_tecnologia')
def gestao_tecnologia(): return render_template('gestao_tecnologia.html')
@main_bp.route('/gestao_tecnologia_agendamento')
def gestao_tecnologia_agendamento(): return render_template('gestao_tecnologia_agendamento.html')
@main_bp.route('/gestao_tecnologia_historico')
def gestao_tecnologia_historico(): return render_template('gestao_tecnologia_historico.html')
@main_bp.route('/gestao_tecnologia_ocorrencia')
def gestao_tecnologia_ocorrencia(): return render_template('gestao_tecnologia_ocorrencia.html')

# Rotas de Tutoria (Incompleto - Adicionar todos os tutoriais main_bp)
@main_bp.route('/gestao_tutoria')
def gestao_tutoria(): return render_template('gestao_tutoria.html')
@main_bp.route('/gestao_tutoria_ficha')
def gestao_tutoria_ficha(): return render_template('gestao_tutoria_ficha.html')
@main_bp.route('/gestao_tutoria_agendamento')
def gestao_tutoria_agendamento(): return render_template('gestao_tutoria_agendamento.html')
@main_bp.route('/gestao_tutoria_registro')
def gestao_tutoria_registro(): return render_template('gestao_tutoria_registro.html')
@main_bp.route('/gestao_tutoria_notas')
def gestao_tutoria_notas(): return render_template('gestao_tutoria_notas.html')
@main_bp.route('/gestao_relatorio_tutoria')
def gestao_relatorio_tutoria(): return render_template('gestao_relatorio_tutoria.html')
@main_bp.route('/gestao_cadastro')
def gestao_cadastro(): return render_template('gestao_cadastro.html')
@main_bp.route('/gestao_cadastro_professor_funcionario')
def gestao_cadastro_professor_funcionario(): return render_template('gestao_cadastro_professor_funcionario.html')
@main_bp.route('/gestao_cadastro_aluno')
def gestao_cadastro_aluno(): return render_template('gestao_cadastro_aluno.html')
@main_bp.route('/gestao_cadastro_tutor')
def gestao_cadastro_tutor(): return render_template('gestao_cadastro_tutor.html')
@main_bp.route('/gestao_cadastro_sala')
def gestao_cadastro_sala(): return render_template('gestao_cadastro_sala.html')
@main_bp.route('/gestao_cadastro_disciplinas')
def gestao_cadastro_disciplinas(): return render_template('gestao_cadastro_disciplinas.html')
@main_bp.route('/gestao_cadastro_eletiva')
def gestao_cadastro_eletiva(): return render_template('gestao_cadastro_eletiva.html')
@main_bp.route('/gestao_cadastro_clube')
def gestao_cadastro_clube(): return render_template('gestao_cadastro_clube.html')
@main_bp.route('/gestao_cadastro_equipamento')
def gestao_cadastro_equipamento(): return render_template('gestao_cadastro_equipamento.html')
@main_bp.route('/gestao_cadastro_vinculacao_tutor_aluno')
def gestao_cadastro_vinculacao_tutor_aluno(): return render_template('gestao_cadastro_vinculacao_tutor_aluno.html')
@main_bp.route('/gestao_cadastro_vinculacao_disciplina_sala')
def gestao_cadastro_vinculacao_disciplina_sala(): return render_template('gestao_cadastro_vinculacao_disciplina_sala.html')
@main_bp.route('/gestao_aulas')
def gestao_aulas(): return render_template('gestao_aulas.html')
@main_bp.route('/gestao_aulas_plano')
def gestao_aulas_plano(): return render_template('gestao_aulas_plano.html')
@main_bp.route('/gestao_aulas_guia')
def gestao_aulas_guia(): return render_template('gestao_aulas_guia.html')
@main_bp.route('/gestao_validacao_documentos')
def gestao_validacao_documentos(): return render_template('gestao_validacao_documentos.html')
@main_bp.route('/gestao_aulas_menu')
def gestao_aulas_menu(): return render_template('gestao_aulas.html')


# ===============================================
# 2. MÓDULO DE FREQUÊNCIA (API - CONSOLIDADO)
# Substitui o routes_frequencia.py
# ===============================================

@app.route('/api/frequencia/status', methods=['GET'])
def api_frequencia_status():
    sala_id = request.args.get('sala_id')
    data = request.args.get('data')
    if not sala_id or not data:
        return jsonify({"error": "Parâmetros sala_id e data são obrigatórios."}), 400
    try:
        supabase = get_supabase()
        if not supabase: return jsonify({"error": "Serviço de banco de dados indisponível"}), 503
        resp = supabase.table('t_frequencia').select("id").eq('sala_id', int(sala_id)).eq('data', data).limit(1).execute()
        return jsonify({"registrada": len(resp.data) > 0}), 200
    except Exception as e:
        logging.exception("Erro /api/frequencia/status")
        return jsonify({"error": str(e)}), 500

@app.route('/api/salvar_frequencia', methods=['POST'])
def api_salvar_frequencia():
    registros = request.json
    if not isinstance(registros, list) or not registros: return jsonify({"error": "O corpo deve ser uma lista não vazia."}), 400
    try:
        supabase = get_supabase()
        if not supabase: return jsonify({"error": "Serviço de banco de dados indisponível"}), 503
        primeiro_registro = registros[0]
        sala_id = primeiro_registro.get('sala_id')
        data = primeiro_registro.get('data')
        if not sala_id or not data: return jsonify({"error": "Dados de sala e data obrigatórios ausentes."}), 400
        resp_status = supabase.table('t_frequencia').select("id").eq('sala_id', int(sala_id)).eq('data', data).limit(1).execute()
        if len(resp_status.data) > 0: return jsonify({"error": "Frequência já registrada."}), 409
        dados_a_inserir = []
        for reg in registros:
            if reg.get('status') in ['P', 'F']:
                 dados_a_inserir.append({"aluno_id": int(reg.get('aluno_id')), "sala_id": int(reg.get('sala_id')), "data": reg.get('data'), "status": reg.get('status'), "timestamp_registro": datetime.now().isoformat()})
        if not dados_a_inserir: return jsonify({"error": "Nenhum registro P/F válido para salvar."}), 400
        response = supabase.table('t_frequencia').insert(dados_a_inserir).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Frequência de {len(dados_a_inserir)} alunos registrada com sucesso.", "status": 201}), 201
    except Exception as e:
        logging.exception("Erro /api/salvar_frequencia")
        return jsonify({"error": f"Falha ao salvar a frequência: {e}"}), 500

@app.route('/api/salvar_atraso', methods=['POST'])
def api_salvar_atraso():
    data = request.json
    aluno_id, sala_id, data_dia, hora_atraso = data.get('aluno_id'), data.get('sala_id'), data.get('data'), data.get('hora_atraso')
    if not all([aluno_id, sala_id, data_dia, hora_atraso]): return jsonify({"error": "Dados obrigatórios ausentes."}), 400
    try:
        supabase = get_supabase()
        if not supabase: return jsonify({"error": "Serviço de banco de dados indisponível"}), 503
        aluno_id, sala_id = int(aluno_id), int(sala_id)
        resp_freq = supabase.table('t_frequencia').select("status").eq('aluno_id', aluno_id).eq('data', data_dia).limit(1).execute()
        status_atual = resp_freq.data[0]['status'] if resp_freq.data else None
        novo_status = 'PA' 
        if status_atual in ['PS', 'PSA']: novo_status = 'PSA'
        if status_atual:
            supabase.table('t_frequencia').update({'status': novo_status, 'timestamp_registro': datetime.now().isoformat()}).eq('aluno_id', aluno_id).eq('data', data_dia).execute()
        else:
            supabase.table('t_frequencia').insert({"aluno_id": aluno_id, "sala_id": sala_id, "data": data_dia, "status": novo_status, "timestamp_registro": datetime.now().isoformat()}).execute()
        registro_detalhe = {"aluno_id": aluno_id, "sala_id": sala_id, "data": data_dia, "hora_atraso": hora_atraso, "motivo": data.get('motivo_atraso'), "responsavel": data.get('responsavel_atraso'), "telefone": data.get('telefone_atraso'), "tipo_registro": 'ATRASO'}
        resp_detalhe = supabase.table('t_atrasos_saidas').select("*").eq('aluno_id', aluno_id).eq('data', data_dia).eq('tipo_registro', 'ATRASO').limit(1).execute()
        if resp_detalhe.data:
             supabase.table('t_atrasos_saidas').update(registro_detalhe).eq('id', resp_detalhe.data[0]['id']).execute()
        else:
             supabase.table('t_atrasos_saidas').insert(registro_detalhe).execute()
        return jsonify({"message": f"Atraso registrado com sucesso. Status atualizado para {novo_status}.", "status": 200}), 200
    except Exception as e:
        logging.exception("Erro /api/salvar_atraso")
        return jsonify({"error": f"Falha ao salvar atraso: {e}"}), 500

@app.route('/api/salvar_saida_antecipada', methods=['POST'])
def api_salvar_saida_antecipada():
    data = request.json
    aluno_id, sala_id, data_dia, hora_saida = data.get('aluno_id'), data.get('sala_id'), data.get('data'), data.get('hora_saida')
    if not all([aluno_id, sala_id, data_dia, hora_saida]): return jsonify({"error": "Dados obrigatórios ausentes."}), 400
    try:
        supabase = get_supabase()
        if not supabase: return jsonify({"error": "Serviço de banco de dados indisponível"}), 503
        aluno_id, sala_id = int(aluno_id), int(sala_id)
        resp_freq = supabase.table('t_frequencia').select("status").eq('aluno_id', aluno_id).eq('data', data_dia).limit(1).execute()
        status_atual = resp_freq.data[0]['status'] if resp_freq.data else None
        novo_status = 'PS'
        if status_atual in ['PA', 'PSA']: novo_status = 'PSA'
        if status_atual:
            supabase.table('t_frequencia').update({'status': novo_status, 'timestamp_registro': datetime.now().isoformat()}).eq('aluno_id', aluno_id).eq('data', data_dia).execute()
        else:
            supabase.table('t_frequencia').insert({"aluno_id": aluno_id, "sala_id": sala_id, "data": data_dia, "status": novo_status, "timestamp_registro": datetime.now().isoformat()}).execute()
        registro_detalhe = {"aluno_id": aluno_id, "sala_id": sala_id, "data": data_dia, "hora_saida": hora_saida, "motivo": data.get('motivo_saida'), "responsavel": data.get('responsavel_saida'), "telefone": data.get('telefone_saida'), "tipo_registro": 'SAIDA'}
        resp_detalhe = supabase.table('t_atrasos_saidas').select("*").eq('aluno_id', aluno_id).eq('data', data_dia).eq('tipo_registro', 'SAIDA').limit(1).execute()
        if resp_detalhe.data:
             supabase.table('t_atrasos_saidas').update(registro_detalhe).eq('id', resp_detalhe.data[0]['id']).execute()
        else:
             supabase.table('t_atrasos_saidas').insert(registro_detalhe).execute()
        return jsonify({"message": f"Saída antecipada registrada com sucesso. Status atualizado para {novo_status}.", "status": 200}), 200
    except Exception as e:
        logging.exception("Erro /api/salvar_saida_antecipada")
        return jsonify({"error": f"Falha ao salvar saída antecipada: {e}"}), 500

@app.route('/api/frequencia', methods=['GET'])
def api_relatorio_frequencia():
    sala_id = request.args.get('sala')
    mes = request.args.get('mes')
    if not sala_id or not mes: return jsonify({"error": "Parâmetros sala e mes são obrigatórios."}), 400
    try:
        supabase = get_supabase()
        if not supabase: return jsonify({"error": "Serviço de banco de dados indisponível"}), 503
        sala_id, mes, ano_atual = int(sala_id), int(mes), datetime.now().year
        resp_alunos = supabase.table('d_alunos').select("id, nome").eq('sala_id', sala_id).order('nome').execute()
        alunos_sala = handle_supabase_response(resp_alunos)
        aluno_ids = [a['id'] for a in alunos_sala]
        if not aluno_ids: return jsonify([]), 200
        _, num_dias = monthrange(ano_atual, mes)
        data_inicio = f"{ano_atual}-{str(mes).zfill(2)}-01"
        data_fim = f"{ano_atual}-{str(mes).zfill(2)}-{str(num_dias).zfill(2)}"
        resp_freq = supabase.table('t_frequencia').select("aluno_id, data, status").in_('aluno_id', aluno_ids).gte('data', data_inicio).lte('data', data_fim).execute()
        registros = handle_supabase_response(resp_freq)
        frequencia_por_aluno = {}
        for reg in registros:
            aluno_id = reg['aluno_id']
            if aluno_id not in frequencia_por_aluno: frequencia_por_aluno[aluno_id] = {}
            frequencia_por_aluno[aluno_id][reg['data']] = reg['status']
        relatorio_final = []
        for aluno in alunos_sala:
            relatorio_final.append({"id": aluno['id'], "nome": aluno['nome'], "frequencia": frequencia_por_aluno.get(aluno['id'], {})})
        return jsonify(relatorio_final), 200
    except ValueError:
        return jsonify({"error": "Os parâmetros sala_id e mes devem ser números inteiros."}), 400
    except Exception as e:
        logging.exception("Erro /api/frequencia")
        return jsonify({"error": f"Falha ao gerar relatório de frequência: {e}"}), 500

# ===============================================
# 3. MÓDULO DE OCORRÊNCIAS (API - CONSOLIDADO)
# Substitui o routes_ocorrencias.py
# ===============================================

@app.route("/api/salas_com_ocorrencias", methods=["GET"])
def api_salas_com_ocorrencias():
    try:
        supabase = get_supabase()
        resp = supabase.table("d_salas").select("id, sala").order("sala").execute()
        salas = handle_supabase_response(resp)
        salas_norm = [{"id": s.get("id"), "nome": s.get("sala")} for s in salas]
        return jsonify(salas_norm), 200
    except Exception as e:
        logging.exception("Erro /api/salas_com_ocorrencias")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alunos_com_ocorrencias_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_com_ocorrencias_por_sala(sala_id):
    try:
        # Reutilizando função auxiliar para buscar alunos com info de tutor
        alunos = get_alunos_por_sala_data(sala_id)
        # Filtro de alunos que REALMENTE tem ocorrência (simulação simplificada)
        aluno_ids = [a['id'] for a in alunos]
        supabase = get_supabase()
        resp_ocorrencias = supabase.table('ocorrencias').select('aluno_id').in_('aluno_id', aluno_ids).execute()
        ocorrencia_alunos = {o['aluno_id'] for o in handle_supabase_response(resp_ocorrencias)}
        alunos_filtrados = [a for a in alunos if a['id'] in ocorrencia_alunos]
        return jsonify(alunos_filtrados), 200
    except Exception as e:
        logging.exception("Erro /api/alunos_com_ocorrencias_por_sala")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocorrencias_por_aluno/<int:aluno_id>', methods=['GET'])
def api_get_ocorrencias_por_aluno(aluno_id):
    try:
        supabase = get_supabase()
        resp = supabase.table('ocorrencias').select('*').eq('aluno_id', aluno_id).order('data_hora', desc=True).execute()
        ocorrencias = handle_supabase_response(resp)
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.exception("Erro /api/ocorrencias_por_aluno")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocorrencias', methods=['POST'])
def api_criar_ocorrencia():
    data = request.json
    required_fields = ['descricao', 'aluno_id', 'prof_id', 'sala_id', 'atendimento_professor']
    missing = [field for field in required_fields if not data.get(field)]
    if missing: return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400
    try:
        supabase = get_supabase()
        max_response = supabase.table('ocorrencias').select('numero').order('numero', desc=True).limit(1).execute()
        proximo_numero = 1
        if max_response.data and max_response.data[0].get('numero'): proximo_numero = max_response.data[0]['numero'] + 1 
        ocorrencia_data = {
            "numero": proximo_numero, "descricao": data['descricao'], "aluno_id": data['aluno_id'], "aluno_nome": data.get('aluno_nome'),
            "tutor_id": data.get('tutor_id'), "professor_id": data.get('prof_id'), "sala_id": data.get('sala_id'), "atendimento_professor": data['atendimento_professor'],
            "solicitado_tutor": 'SIM' if data.get('solicitar_tutor') else 'NÃO',
            "solicitado_coordenacao": 'SIM' if data.get('solicitar_coordenacao') else 'NÃO',
            "solicitado_gestao": 'SIM' if data.get('solicitar_gestao') else 'NÃO',
            "status": "AGUARDANDO ATENDIMENTO", "data_hora": datetime.now().isoformat()
        }
        response = supabase.table('ocorrencias').insert(ocorrencia_data).execute()
        return jsonify({"message": "Ocorrência criada com sucesso", "numero": proximo_numero}), 201
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias POST: {str(e)}")
        return jsonify({"error": f"Falha ao criar ocorrência: {str(e)}"}), 500

@app.route('/api/ocorrencia_detalhes', methods=['GET'])
def api_get_ocorrencia_detalhes():
    numero = request.args.get('numero')
    if not numero: return jsonify({"error": "Número da ocorrência não fornecido"}), 400
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias').select('*, aluno_id:d_alunos(nome, tutor_id), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala)').eq('numero', numero).single().execute()
        if not response.data: return jsonify({"error": "Ocorrência não encontrada"}), 404
        data = response.data
        detalhes = {
            'numero': data.get('numero'), 'status': data.get('status'), 'descricao': data.get('descricao'),
            'atendimento_professor': data.get('atendimento_professor', ''), 'atendimento_tutor': data.get('atendimento_tutor', ''),
            'atendimento_coordenacao': data.get('atendimento_coordenacao', ''), 'atendimento_gestao': data.get('atendimento_gestao', ''),
            'aluno_nome': data['aluno_id']['nome'] if data.get('aluno_id') and isinstance(data['aluno_id'], dict) else data.get('aluno_nome', 'N/A'),
            'sala': data['sala_id']['sala'] if data.get('sala_id') and isinstance(data['sala_id'], dict) else data.get('sala', 'N/A'),
            'tutor': data['tutor_id']['nome'] if data.get('tutor_id') and isinstance(data['tutor_id'], dict) else 'N/A',
            'professor': data['professor_id']['nome'] if data.get('professor_id') and isinstance(data['professor_id'], dict) else 'N/A',
            'solicitado_tutor': data.get('solicitado_tutor'), 'solicitado_coordenacao': data.get('solicitado_coordenacao'),
            'solicitado_gestao': data.get('solicitado_gestao')
        }
        return jsonify(detalhes), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencia_detalhes: {str(e)}")
        return jsonify({"error": f"Falha ao buscar detalhes: {str(e)}"}), 500

@app.route("/api/salvar_atendimento", methods=["POST"])
def salvar_atendimento():
    try:
        data = request.get_json()
        ocorrencia_id, nivel, texto = data.get("id"), data.get("nivel"), data.get("texto")
        if not all([ocorrencia_id, nivel, texto]): return jsonify({"error": "Dados incompletos: ID, nível ou texto ausente."}), 400
        campos = {"tutor": ("atendimento_tutor", "dt_atendimento_tutor"), "coordenacao": ("atendimento_coordenacao", "dt_atendimento_coordenacao"), "gestao": ("atendimento_gestao", "dt_atendimento_gestao")}
        if nivel not in campos: return jsonify({"error": f"Nível de atendimento inválido: {nivel}"}), 400
        campo_texto, campo_data = campos[nivel]
        supabase = get_supabase()
        agora = datetime.utcnow().isoformat(timespec='milliseconds') + "Z"
        update_data = {campo_texto: texto, campo_data: agora}
        response_current = supabase.table('ocorrencias').select('status').eq('numero', ocorrencia_id).single().execute()
        current_status = response_current.data.get('status') if response_current.data else 'AGUARDANDO ATENDIMENTO'
        if current_status == 'AGUARDANDO ATENDIMENTO': update_data['status'] = 'EM ANDAMENTO'
        if nivel == 'gestao' and texto.strip(): update_data['status'] = 'FINALIZADA'
        supabase.table("ocorrencias").update(update_data).eq("numero", ocorrencia_id).execute()
        return jsonify({"success": True, "message": "Atendimento registrado com sucesso"}), 200
    except Exception as e:
        logging.exception(f"Erro ao registrar atendimento {ocorrencia_id}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocorrencias/abertas', methods=['GET'])
def api_get_ocorrencias_abertas():
    try:
        supabase = get_supabase()
        resp = supabase.table('ocorrencias').select('*').in_('status', ['AGUARDANDO ATENDIMENTO', 'EM ANDAMENTO']).order('data_hora', desc=True).execute()
        return jsonify(handle_supabase_response(resp)), 200
    except Exception as e:
        logging.exception("Erro /api/ocorrencias/abertas")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocorrencias/finalizadas', methods=['GET'])
def api_get_ocorrencias_finalizadas():
    try:
        supabase = get_supabase()
        resp = supabase.table('ocorrencias').select('*').eq('status', 'FINALIZADA').order('data_hora', desc=True).execute()
        return jsonify(handle_supabase_response(resp)), 200
    except Exception as e:
        logging.exception("Erro /api/ocorrencias/finalizadas")
        return jsonify({"error": str(e)}), 500

# Rota para gerar PDF (Simulação)
@app.route('/api/gerar_pdf_ocorrencias', methods=['POST'])
def api_gerar_pdf_ocorrencias():
    # Esta rota precisa de uma implementação completa de geração de PDF (FPDF, ReportLab, etc.)
    return jsonify({"message": "Geração de PDF simulada com sucesso."}), 200 # 200/201 é esperado pelo front-end

# ===============================================
# 4. MÓDULO DE TECNOLOGIA (API - CONSOLIDADO)
# Substitui o routes_tecnologia.py
# ===============================================

@app.route('/api/agendar_equipamento', methods=['POST'])
def api_agendar_equipamento():
    data = request.json
    required_fields = ['fk_professor_id', 'fk_sala_id', 'data_uso', 'aula_id', 'quantidade']
    missing = [field for field in required_fields if not data.get(field)]
    if missing: return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400
    try:
        supabase = get_supabase()
        disponibilidade_response = supabase.table('d_inventario_equipamentos').select('id').eq('status', 'DISPONÍVEL').execute()
        equipamentos_disponiveis = handle_supabase_response(disponibilidade_response)
        if len(equipamentos_disponiveis) < data['quantidade']: return jsonify({"error": f"Apenas {len(equipamentos_disponiveis)} equipamentos disponíveis. Solicitação: {data['quantidade']}"}), 400
        agendamento = {"professor_id": data['fk_professor_id'], "sala_id": data['fk_sala_id'], "data_uso": data['data_uso'], "aula_id": data['aula_id'], "quantidade": data['quantidade'], "status": "AGENDADO", "equipamentos_reservados_json": data.get('equipamentos_reservados_ids', []), "data_agendamento": datetime.now().isoformat()}
        response = supabase.table('reservas_equipamentos').insert(agendamento).execute()
        result = handle_supabase_response(response)
        if data.get('equipamentos_reservados_ids'):
            for eq_id in data['equipamentos_reservados_ids']:
                supabase.table('d_inventario_equipamentos').update({"status": "RESERVADO", "reserva_id": result[0]['id'] if result else None}).eq('id', eq_id).execute()
        return jsonify({"message": f"Agendamento criado com sucesso para {data['quantidade']} equipamentos.", "id": result[0]['id'] if result else None}), 201
    except Exception as e:
        logging.exception("Erro /api/agendar_equipamento")
        return jsonify({"error": f"Falha ao criar agendamento: {str(e)}"}), 500

@app.route('/api/agendamentos_pendentes/<int:professor_id>', methods=['GET'])
def api_agendamentos_pendentes(professor_id):
    try:
        supabase = get_supabase()
        response = supabase.table('reservas_equipamentos').select('id, professor_id, sala_id, data_uso, aula_id, quantidade, status, data_agendamento, d_salas(sala), d_funcionarios(nome)').eq('professor_id', professor_id).in_('status', ['AGENDADO', 'EM USO']).order('data_uso').execute()
        agendamentos = handle_supabase_response(response)
        agendamentos_formatados = []
        for ag in agendamentos:
            agendamentos_formatados.append({'id': ag['id'], 'prof_nome': ag.get('d_funcionarios', {}).get('nome', 'N/A'), 'sala_nome': ag.get('d_salas', {}).get('sala', 'N/A'), 'data_uso': ag['data_uso'], 'aula_id': ag['aula_id'], 'quantidade': ag['quantidade'], 'status': ag['status'], 'data_agendamento': ag['data_agendamento']})
        return jsonify(agendamentos_formatados), 200
    except Exception as e:
        logging.exception("Erro /api/agendamentos_pendentes")
        return jsonify({"error": f"Falha ao buscar agendamentos: {str(e)}"}), 500

@app.route('/api/finalizar_retirada_equipamento', methods=['POST'])
def api_finalizar_retirada_equipamento():
    data = request.json
    required_fields = ['agendamento_id', 'vinculacoes']
    missing = [field for field in required_fields if not data.get(field)]
    if missing: return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400
    try:
        supabase = get_supabase()
        update_agendamento = supabase.table('reservas_equipamentos').update({"status": "EM USO", "data_recebimento": datetime.now().isoformat()}).eq('id', data['agendamento_id']).execute()
        handle_supabase_response(update_agendamento)
        for vinculacao in data['vinculacoes']:
            vinculacao_data = {"agendamento_id": data['agendamento_id'], "aluno_id": vinculacao['aluno_id'], "equipamento_id": vinculacao['equipamento_id'], "data_retirada": vinculacao.get('data_retirada', datetime.now().isoformat()), "status": "EM USO"}
            supabase.table('vinculos_equipamento_aluno').insert(vinculacao_data).execute()
            supabase.table('d_inventario_equipamentos').update({"status": "EM USO", "aluno_id": vinculacao['aluno_id']}).eq('id', vinculacao['equipamento_id']).execute()
        return jsonify({"message": "Retirada de equipamentos finalizada com sucesso."}), 200
    except Exception as e:
        logging.exception("Erro /api/finalizar_retirada_equipamento")
        return jsonify({"error": f"Falha ao finalizar retirada: {str(e)}"}), 500

@app.route('/api/finalizar_devolucao_equipamento', methods=['POST'])
def api_finalizar_devolucao_equipamento():
    data = request.json
    if not data.get('agendamento_id'): return jsonify({"error": "ID do agendamento é obrigatório."}), 400
    try:
        supabase = get_supabase()
        update_agendamento = supabase.table('reservas_equipamentos').update({"status": "FINALIZADO", "data_devolucao": datetime.now().isoformat()}).eq('id', data['agendamento_id']).execute()
        handle_supabase_response(update_agendamento)
        vinculacoes_response = supabase.table('vinculos_equipamento_aluno').select('equipamento_id').eq('agendamento_id', data['agendamento_id']).execute()
        vinculacoes = handle_supabase_response(vinculacoes_response)
        for vinculacao in vinculacoes:
            supabase.table('d_inventario_equipamentos').update({"status": "DISPONÍVEL", "aluno_id": None}).eq('id', vinculacao['equipamento_id']).execute()
        supabase.table('vinculos_equipamento_aluno').update({"status": "FINALIZADO", "data_devolucao": datetime.now().isoformat()}).eq('agendamento_id', data['agendamento_id']).execute()
        return jsonify({"message": "Devolução de equipamentos finalizada com sucesso."}), 200
    except Exception as e:
        logging.exception("Erro /api/finalizar_devolucao_equipamento")
        return jsonify({"error": f"Falha ao finalizar devolução: {str(e)}"}), 500

@app.route('/api/registrar_ocorrencia_equipamento', methods=['POST'])
def api_registrar_ocorrencia_equipamento():
    data = request.json
    required_fields = ['fk_equipamento_id', 'fk_professor_id', 'data_ocorrencia', 'descricao', 'acao']
    missing = [field for field in required_fields if not data.get(field)]
    if missing: return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400
    try:
        supabase = get_supabase()
        ocorrencia = {"equipamento_id": data['fk_equipamento_id'], "professor_id": data['fk_professor_id'], "aluno_id": data.get('fk_aluno_id'), "data_ocorrencia": data['data_ocorrencia'], "hora_ocorrencia": data.get('hora_ocorrencia'), "descricao": data['descricao'], "acao_tomada": data['acao'], "status": "REGISTRADA", "data_registro": datetime.now().isoformat()}
        response = supabase.table('ocorrencias_equipamentos').insert(ocorrencia).execute()
        result = handle_supabase_response(response)
        if "danificado" in data['descricao'].lower() or "quebrado" in data['descricao'].lower():
            supabase.table('d_inventario_equipamentos').update({"status": "EM MANUTENÇÃO"}).eq('id', data['fk_equipamento_id']).execute()
        return jsonify({"message": "Ocorrência registrada com sucesso.", "id": result[0]['id'] if result else None}), 201
    except Exception as e:
        logging.exception("Erro /api/registrar_ocorrencia_equipamento")
        return jsonify({"error": f"Falha ao registrar ocorrência: {str(e)}"}), 500

@app.route('/api/ocorrencias_equipamentos', methods=['GET'])
def api_ocorrencias_equipamentos():
    try:
        supabase = get_supabase()
        response = supabase.table('ocorrencias_equipamentos').select('id, equipamento_id, professor_id, aluno_id, data_ocorrencia, descricao, acao_tomada, status, d_inventario_equipamentos(colmeia, equipamento_id), d_funcionarios(nome), d_alunos(nome)').order('data_ocorrencia', desc=True).execute()
        ocorrencias = handle_supabase_response(response)
        ocorrencias_formatadas = []
        for oc in ocorrencias:
            ocorrencias_formatadas.append({'id': oc['id'], 'equipamento_info': f"Colmeia {oc.get('d_inventario_equipamentos', {}).get('colmeia', 'N/A')} - Eq. {oc.get('d_inventario_equipamentos', {}).get('equipamento_id', 'N/A')}", 'professor_nome': oc.get('d_funcionarios', {}).get('nome', 'N/A'), 'aluno_nome': oc.get('d_alunos', {}).get('nome', 'N/A') if oc.get('aluno_id') else 'Não vinculado', 'data_ocorrencia': oc['data_ocorrencia'], 'descricao': oc['descricao'], 'acao_tomada': oc['acao_tomada'], 'status': oc['status']})
        return jsonify(ocorrencias_formatadas), 200
    except Exception as e:
        logging.exception("Erro /api/ocorrencias_equipamentos")
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500

@app.route('/api/inventario', methods=['GET'])
def api_inventario():
    try:
        supabase = get_supabase()
        response = supabase.table('d_inventario_equipamentos').select('id, colmeia, equipamento_id, status, aluno_id, reserva_id').order('colmeia', 'equipamento_id').execute()
        return jsonify(handle_supabase_response(response)), 200
    except Exception as e:
        logging.exception("Erro /api/inventario")
        return jsonify({"error": f"Falha ao buscar inventário: {str(e)}"}), 500

@app.route('/api/inventario/disponibilidade/<data>/<aula_id>', methods=['GET'])
def api_inventario_disponibilidade(data, aula_id):
    try:
        supabase = get_supabase()
        reservas_response = supabase.table('reservas_equipamentos').select('quantidade, equipamentos_reservados_json').eq('data_uso', data).eq('aula_id', aula_id).in_('status', ['AGENDADO', 'EM USO']).execute()
        reservas = handle_supabase_response(reservas_response)
        total_reservado = sum(reserva.get('quantidade', 0) for reserva in reservas)
        inventario_response = supabase.table('d_inventario_equipamentos').select('id', count='exact').eq('status', 'DISPONÍVEL').execute()
        total_disponivel = len(inventario_response.data) if inventario_response.data else 0
        disponibilidade = {"data": data, "aula_id": aula_id, "total_equipamentos": 80, "total_disponivel": total_disponivel, "total_reservado": total_reservado, "disponivel_para_reserva": total_disponivel - total_reservado}
        return jsonify(disponibilidade), 200
    except Exception as e:
        logging.exception("Erro /api/inventario/disponibilidade")
        return jsonify({"error": f"Falha ao verificar disponibilidade: {str(e)}"}), 500

@app.route('/api/equipamentos_em_uso', methods=['GET'])
def api_equipamentos_em_uso():
    try:
        supabase = get_supabase()
        response = supabase.table('d_inventario_equipamentos').select('id, colmeia, equipamento_id, status, aluno_id, d_alunos(nome, sala_id), d_salas(sala)').eq('status', 'EM USO').execute()
        equipamentos = handle_supabase_response(response)
        equipamentos_formatados = []
        for eq in equipamentos:
            equipamentos_formatados.append({'id': eq['id'], 'colmeia': eq['colmeia'], 'equipamento_id': eq['equipamento_id'], 'aluno_nome': eq.get('d_alunos', {}).get('nome', 'N/A'), 'sala_nome': eq.get('d_alunos', {}).get('d_salas', {}).get('sala', 'N/A'), 'status': eq['status']})
        return jsonify(equipamentos_formatados), 200
    except Exception as e:
        logging.exception("Erro /api/equipamentos_em_uso")
        return jsonify({"error": f"Falha ao buscar equipamentos em uso: {str(e)}"}), 500

# Rota para listar equipamentos disponíveis (reutiliza a função auxiliar)
@app.route('/api/inventario/disponiveis', methods=['GET'])
def api_inventario_disponiveis():
    try:
        equipamentos = get_equipamentos_disponiveis()
        return jsonify(equipamentos), 200
    except Exception as e:
        logging.exception("Erro /api/inventario/disponiveis")
        return jsonify({"error": f"Falha ao buscar equipamentos disponíveis: {str(e)}"}), 500


# ===============================================
# 5. REGISTRO DOS BLUEPRINTS E EXECUÇÃO
# ===============================================

# 1. Registra o Blueprint Principal
app.register_blueprint(main_bp, url_prefix='/')

# 2. Registra Blueprints que permaneceram separados
app.register_blueprint(tutoria_bp, url_prefix='/api') 
app.register_blueprint(aulas_bp, url_prefix='/api')
app.register_blueprint(cadastro_bp, url_prefix='/api')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
