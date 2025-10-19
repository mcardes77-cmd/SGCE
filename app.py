import os
import logging
from dotenv import load_dotenv
# IMPORTS CONSOLIDADOS (INCLUINDO PDF)
from flask import Flask, render_template, request, jsonify, send_file
from supabase import create_client, Client
import json
from datetime import datetime
from calendar import monthrange 
import io
from fpdf import FPDF

# =========================================================
# CONFIGURAÇÕES INICIAIS
# =========================================================

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("As variáveis SUPABASE_URL e SUPABASE_KEY devem ser configuradas no arquivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__, template_folder='templates')


# =========================================================
# LOG DE REQUISIÇÕES (para debug)
# =========================================================
@app.before_request
def log_request():
    print(f"[LOG] Rota acessada: {request.path}")

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def handle_supabase_response(response):
    if not response:
        return []
    if hasattr(response, "data"):
        return response.data or []
    if isinstance(response, dict) and "data" in response:
        return response.get("data") or []
    return []

def formatar_data_hora(data_str):
    if not data_str:
        return 'N/A'
    try:
        dt_obj = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
        return dt_obj.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return data_str

def _to_bool(value):
    if value is True or value == 1:
        return True
    if value is False or value == 0 or value is None:
        return False
    s = str(value).strip().lower()
    if s in ('true', '1', 't', 'y', 'yes', 'sim'):
        return True
    if s in ('false', '0', 'f', 'n', 'no', 'nao', 'não'):
        return False
    return False

def calcular_dias_resposta(dt_abertura, dt_fechamento_str):
    """Calcula a diferença em dias entre a abertura e o fechamento da ocorrência."""
    if not dt_fechamento_str or not dt_abertura:
        return None
    try:
        dt_fechamento = datetime.fromisoformat(dt_fechamento_str.replace('Z', '+00:00'))
        dt_abertura = datetime.fromisoformat(dt_abertura.replace('Z', '+00:00'))
        
        diff = dt_fechamento - dt_abertura
        # Retorna o número de dias arredondado para cima (mínimo 1 dia se fechado no dia seguinte)
        return diff.days + (1 if diff.seconds > 0 else 0) 
    except Exception:
        return None

DEFAULT_AUTOTEXT = "ATENDIMENTO NÃO SOLICITADO PELO RESPONSÁVEL DA OCORRÊNCIA"

def safe_pdf_text(text):
    """Garante que o texto seja compatível com a codificação Latin-1/Cp1252 do FPDF."""
    if not text:
        return ''
    # Força a codificação para Latin-1 (comum em FPDF) e decodifica, 
    # substituindo caracteres incompatíveis para evitar o erro \ufffd.
    return str(text).encode('latin-1', 'replace').decode('latin-1')


# =========================================================
# ROTAS DE PÁGINA PRINCIPAIS (Renderiza templates)
# =========================================================

@app.route('/')
def home():
    return render_template('home.html')  

@app.route('/gestao_aulas')
def gestao_aulas():
    return render_template('gestao_aulas.html')

@app.route('/gestao_agenda')
def gestao_agenda():
    return render_template('gestao_agenda.html')

@app.route('/gestao_plano_aula')
def gestao_plano_aula():
    return render_template('gestao_plano_aula.html')

@app.route('/gestao_guia_aprendizagem')
def gestao_guia_aprendizagem():
    return render_template('gestao_guia_aprendizagem.html')

@app.route('/gestao_ocorrencia')
def gestao_ocorrencia():
    return render_template('gestao_ocorrencia.html')

@app.route('/gestao_ocorrencia_nova')
def gestao_ocorrencia_nova():
    return render_template('gestao_ocorrencia_nova.html')
    
@app.route("/gestao_ocorrencia_abertas")
def gestao_ocorrencia_abertas():
    return render_template("gestao_ocorrencia_abertas.html")

@app.route("/gestao_ocorrencia_editar")
def gestao_ocorrencia_editar():
    return render_template("gestao_ocorrencia_editar.html")

@app.route('/gestao_ocorrencia_finalizadas')
def gestao_ocorrencia_finalizadas():
    return render_template('gestao_ocorrencia_finalizadas.html')

@app.route('/gestao_relatorio_estatistico')
def gestao_relatorio_estatistico():
    return render_template('gestao_relatorio_estatistico.html')

@app.route('/gestao_relatorio_frequencia')
def gestao_relatorio_frequencia():
    # ROTA CORRIGIDA: Aponta para o arquivo que contém a lógica de filtro/tabela de frequência
    return render_template('gestao_relatorio_frequencia.html') 

@app.route('/gestao_relatorio_impressao')
def gestao_relatorio_impressao():
    return render_template('gestao_relatorio_impressao.html')

@app.route('/gestao_relatorio_tutoria')
def gestao_relatorio_tutoria():
    return render_template('gestao_relatorio_tutoria.html')

@app.route('/gestao_frequencia')
def gestao_frequencia():
    return render_template('gestao_frequencia.html')

@app.route('/gestao_frequencia_registro')
def gestao_frequencia_registro():
    return render_template('gestao_frequencia_registro.html')

@app.route('/gestao_frequencia_atraso')
def gestao_frequencia_atraso():
    return render_template('gestao_frequencia_atraso.html')

@app.route('/gestao_frequencia_saida')
def gestao_frequencia_saida():
    return render_template('gestao_frequencia_saida.html')

@app.route('/gestao_tutoria')
def gestao_tutoria():
    return render_template('gestao_tutoria.html')

@app.route('/gestao_tutoria_agendamento')
def gestao_tutoria_agendamento():
    return render_template('gestao_tutoria_agendamento.html')

@app.route('/gestao_tutoria_ficha')
def gestao_tutoria_ficha():
    return render_template('gestao_tutoria_ficha.html')

@app.route('/gestao_tutoria_registro')
def gestao_tutoria_registro():
    return render_template('gestao_tutoria_registro.html')

@app.route('/gestao_tutoria_notas')
def gestao_tutoria_notas():
    return render_template('gestao_tutoria_notas.html')

@app.route('/gestao_tecnologia')
def gestao_tecnologia():
    return render_template('gestao_tecnologia.html')

@app.route('/gestao_tecnologia_agendamento')
def gestao_tecnologia_agendamento():
    return render_template('gestao_tecnologia_agendamento.html')

@app.route('/gestao_tecnologia_ocorrencia')
def gestao_tecnologia_ocorrencia():
    return render_template('gestao_tecnologia_ocorrencia.html')

@app.route('/gestao_tecnologia_historico')
def gestao_tecnologia_historico():
    return render_template('gestao_tecnologia_historico.html')

@app.route('/gestao_tecnologia_retirada')
def gestao_tecnologia_retirada():
    return render_template('gestao_tecnologia_retirada.html')

@app.route('/gestao_cadastro')
def gestao_cadastro():
    return render_template('gestao_cadastro.html')

@app.route('/gestao_cadastro_salas')
def gestao_cadastro_salas():
    return render_template('gestao_cadastro_sala.html')

@app.route('/gestao_cadastro_tutores')
def gestao_cadastro_tutores():
    return render_template('gestao_cadastro_tutor.html')

@app.route('/gestao_cadastro_alunos')
def gestao_cadastro_alunos():
    return render_template('gestao_cadastro_aluno.html')

@app.route('/gestao_cadastro_disciplinas')
def gestao_cadastro_disciplinas():
    return render_template('gestao_cadastro_disciplinas.html')

@app.route('/gestao_cadastro_eletivas')
def gestao_cadastro_eletivas():
    return render_template('gestao_cadastro_eletiva.html')

@app.route('/gestao_cadastro_clubes')
def gestao_cadastro_clubes():
    return render_template('gestao_cadastro_clube.html')

@app.route('/gestao_cadastro_professores')
def gestao_cadastro_professores():
    return render_template('gestao_cadastro_professor_funcionario.html')

@app.route('/gestao_cadastro_equipamentos')
def gestao_cadastro_equipamentos():
    return render_template('gestao_cadastro_equipamento.html')

@app.route('/gestao_cadastro_vincular_tutor_aluno')
def gestao_cadastro_vincular_tutor_aluno():
    return render_template('gestao_cadastro_vinculacao_tutor_aluno.html')

@app.route('/gestao_cadastro_vincular_disciplina_sala')
def gestao_cadastro_vincular_disciplina_sala():
    return render_template('gestao_cadastro_vinculacao_disciplina_sala.html')


# =========================================================
# ROTAS DE API (DADOS)
# =========================================================

@app.route('/api/funcionarios', methods=['GET'])
def api_get_funcionarios():
    try:
        response = supabase.table('d_funcionarios').select('id, nome, funcao, is_tutor, email').order('nome').execute()
        funcionarios = [{"id": str(f['id']), "nome": f['nome'], "funcao": f.get('funcao', ''), "is_tutor": f.get('is_tutor', False), "email": f.get('email', '')} for f in handle_supabase_response(response)]
        return jsonify(funcionarios)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar funcionários: {e}", "status": 500}), 500

@app.route('/api/alunos_por_sala/<sala_id>', methods=['GET'])
def api_get_alunos_por_sala(sala_id):
    try:
        sala_id_bigint = int(sala_id)
        response_alunos = supabase.table('d_alunos').select('id, nome, tutor_id').eq('sala_id', sala_id_bigint).order('nome').execute()
        alunos_raw = handle_supabase_response(response_alunos)
        response_tutores = supabase.table('d_funcionarios').select('id, nome').eq('is_tutor', True).execute()
        tutores_raw = handle_supabase_response(response_tutores)
        tutores_dict = {str(t['id']): t['nome'] for t in tutores_raw}
        alunos = []
        for a in alunos_raw:
            tutor_id_str = str(a['tutor_id']) if a.get('tutor_id') else None
            tutor_nome = tutores_dict.get(tutor_id_str, 'Tutor Não Definido')
            alunos.append({
                "id": str(a['id']),
                "nome": a['nome'],
                "tutor_id": tutor_id_str,
                "tutor_nome": tutor_nome
            })
        return jsonify(alunos)
    except Exception as e:
        logging.error(f"Erro ao buscar alunos por sala: {e}")
        return jsonify({"error": f"Erro ao buscar alunos por sala: {e}", "status": 500}), 500

@app.route('/api/tutores', methods=['GET'])
def api_get_tutores():
    try:
        response = supabase.table('d_funcionarios').select('id, nome, email, funcao').eq('is_tutor', True).order('nome').execute()
        tutores_raw = handle_supabase_response(response)
        tutores = [{"id": str(t["id"]), "nome": t["nome"], "email": t.get("email", ""), "funcao": t.get("funcao", "")} for t in tutores_raw]
        return jsonify(tutores)
    except Exception as e:
        logging.error(f"Erro ao buscar tutores: {e}")
        return jsonify({"error": f"Erro ao buscar tutores: {e}", "status": 500}), 500

@app.route('/api/relatorio_frequencia')
def api_relatorio_frequencia():
    # Simulação de dados para a rota de relatório
    try:
        sala_id = request.args.get('salaId')
        aluno_id = request.args.get('alunoId')
        data_inicial = request.args.get('dataInicial')
        data_final = request.args.get('dataFinal')
        return jsonify({
            'presencas_percentual': 92,
            'faltas_totais': 5,
            'atrasos_totais': 2,
            'saidas_antecipadas_totais': 1
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar relatório de frequência: {e}", "status": 500}), 500

@app.route('/api/frequencia/datas_registradas_por_sala/<int:sala_id>')
def api_datas_registradas(sala_id):
    try:
        resp = supabase.table('f_frequencia').select('data').eq('fk_sala_id', sala_id).order('data').execute()
        datas = sorted(list({r['data'] for r in handle_supabase_response(resp)}))
        return jsonify(datas)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar datas: {e}", "status": 500}), 500

@app.route('/api/alunos_por_tutor/<tutor_id>')
def get_alunos_por_tutor(tutor_id):
    try:
        data = supabase.table('alunos').select('id, nome').eq('tutor_id', tutor_id).execute()
        return jsonify(data.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/disciplinas', methods=['GET'])
def api_get_disciplinas():
    try:
        response = supabase.table('d_disciplinas').select('id, nome').order('nome').execute()
        disciplinas = handle_supabase_response(response)
        return jsonify(disciplinas)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar disciplinas: {e}", "status": 500}), 500

@app.route('/api/clubes', methods=['GET'])
def api_get_clubes():
    try:
        response = supabase.table('d_clubes').select('id, nome, semestre').order('semestre, nome').execute()
        clubes = handle_supabase_response(response)
        return jsonify(clubes)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar clubes: {e}", "status": 500}), 500

@app.route('/api/eletivas', methods=['GET'])
def api_get_eletivas():
    try:
        response = supabase.table('d_eletivas').select('id, nome, semestre').order('semestre, nome').execute()
        eletivas = handle_supabase_response(response)
        return jsonify(eletivas)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar eletivas: {e}", "status": 500}), 500

@app.route('/api/inventario', methods=['GET'])
def api_get_inventario():
    try:
        response = supabase.table('d_inventario_equipamentos').select('id, colmeia, equipamento_id, status').order('colmeia, equipamento_id').execute()
        inventario = handle_supabase_response(response)
        return jsonify(inventario)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar inventário: {e}", "status": 500}), 500

@app.route('/api/agendamentos_pendentes/<professor_id>', methods=['GET'])
def api_get_agendamentos_pendentes(professor_id):
    try:
        professor_id_bigint = int(professor_id)
        response = supabase.table('reservas_equipamentos').select('id, fk_sala_id, data_uso, periodo_uso, status, fk_professor_id').eq('fk_professor_id', professor_id_bigint).neq('status', 'FINALIZADO').execute()
        agendamentos_raw = handle_supabase_response(response)
        agendamentos = []
        for ag in agendamentos_raw:
            agendamentos.append({
                "id": str(ag['id']),
                "fk_sala_id": str(ag.get('fk_sala_id')),
                "data_uso": str(ag.get('data_uso')),
                "periodo_uso": ag.get('periodo_uso'),
                "status": ag.get('status')
            })
        return jsonify(agendamentos)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar agendamentos pendentes: {e}", "status": 500}), 500

@app.route('/api/ocorrencias_abertas', methods=['GET'])
def api_ocorrencias_abertas():
    try:
        # Consulta principal, buscando todos os campos necessários
        resp = supabase.table('ocorrencias').select(
            "numero, data_hora, status, aluno_nome, tutor_nome, solicitado_tutor, solicitado_coordenacao, solicitado_gestao, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, professor_id(nome), sala_id(sala)"
        ).order('data_hora', desc=True).execute()

        items = resp.data or []
        abertas = []

        for item in items:
            numero = item.get('numero')
            update_fields = {}

            st = _to_bool(item.get('solicitado_tutor'))
            sc = _to_bool(item.get('solicitado_coordenacao'))
            sg = _to_bool(item.get('solicitado_gestao'))

            at_tutor = (item.get('atendimento_tutor') or "").strip()
            at_coord = (item.get('atendimento_coordenacao') or "").strip()
            at_gest = (item.get('atendimento_gestao') or "").strip()

            # Preenche atendimento automático quando não solicitado
            if not st and at_tutor == "":
                at_tutor = DEFAULT_AUTOTEXT
                update_fields['atendimento_tutor'] = at_tutor
            if not sc and at_coord == "":
                at_coord = DEFAULT_AUTOTEXT
                update_fields['atendimento_coordenacao'] = at_coord
            if not sg and at_gest == "":
                at_gest = DEFAULT_AUTOTEXT
                update_fields['atendimento_gestao'] = at_gest

            pendente_tutor = st and (at_tutor == "")
            pendente_coord = sc and (at_coord == "")
            pendente_gestao = sg and (at_gest == "")

            # Cálculo de status 
            novo_status = "Aberta" if (pendente_tutor or pendente_coord or pendente_gestao) else "Finalizada"

            # Atualiza status automaticamente no Supabase se necessário
            if item.get('status') != novo_status:
                update_fields['status'] = novo_status
                try:
                    supabase.table('ocorrencias').update(update_fields).eq('numero', numero).execute()
                    logging.info(f"[OCORRÊNCIA] Nº {numero} atualizada → {novo_status}")
                except Exception as e:
                    logging.error(f"Falha ao atualizar ocorrência {numero}: {e}")

            if novo_status == "Aberta":
                # Extração segura dos nomes referenciados
                professor_nome = (item.get('professor_id') or {}).get('nome', 'N/A')
                sala_nome = (item.get('sala_id') or {}).get('sala', 'N/A')
                
                abertas.append({
                    "numero": numero,
                    "data_hora": formatar_data_hora(item.get('data_hora')),
                    "aluno_nome": item.get('aluno_nome', 'N/A'),
                    "tutor_nome": item.get('tutor_nome', 'N/A'),
                    "professor_nome": professor_nome,
                    "sala_nome": sala_nome,
                    "status": novo_status,
                    "solicitado_tutor": st,
                    "solicitado_coordenacao": sc,
                    "solicitado_gestao": sg,
                    "atendimento_tutor": at_tutor,
                    "atendimento_coordenacao": at_coord,
                    "atendimento_gestao": at_gest
                })

        return jsonify(abertas), 200

    except Exception as e:
        logging.exception("Erro /api/ocorrencias_abertas")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ocorrencias_finalizadas', methods=['GET'])
def api_ocorrencias_finalizadas():
    try:
        sala = request.args.get('sala')
        aluno = request.args.get('aluno')

        q = supabase.table('ocorrencias').select(
            "numero, data_hora, status, aluno_nome, tutor_nome, solicitado_tutor, solicitado_coordenacao, solicitado_gestao, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, professor_id(nome), sala_id(sala)"
        ).order('data_hora', desc=True)
        
        # APLICAÇÃO DOS FILTROS (conversão para int para garantir a tipagem)
        if sala:
            try:
                q = q.eq('sala_id', int(sala))
            except ValueError:
                logging.warning(f"Filtro de sala inválido: {sala}")
        if aluno:
            try:
                q = q.eq('aluno_id', int(aluno))
            except ValueError:
                logging.warning(f"Filtro de aluno inválido: {aluno}")

        resp = q.execute()
        items = resp.data or []
        finalizadas = []

        for item in items:
            numero = item.get('numero')
            update_fields = {}

            st = _to_bool(item.get('solicitado_tutor'))
            sc = _to_bool(item.get('solicitado_coordenacao'))
            sg = _to_bool(item.get('solicitado_gestao'))

            at_tutor = (item.get('atendimento_tutor') or "").strip()
            at_coord = (item.get('atendimento_coordenacao') or "").strip()
            at_gest = (item.get('atendimento_gestao') or "").strip()

            if not st and at_tutor == "":
                at_tutor = DEFAULT_AUTOTEXT
                update_fields['atendimento_tutor'] = at_tutor
            if not sc and at_coord == "":
                at_coord = DEFAULT_AUTOTEXT
                update_fields['atendimento_coordenacao'] = at_coord
            if not sg and at_gest == "":
                at_gest = DEFAULT_AUTOTEXT
                update_fields['atendimento_gestao'] = at_gest

            pendente_tutor = st and (at_tutor == "")
            pendente_coord = sc and (at_coord == "")
            pendente_gestao = sg and (at_gest == "")

            # Cálculo de status
            novo_status = "Aberta" if (pendente_tutor or pendente_coord or pendente_gestao) else "Finalizada"

            if item.get('status') != novo_status:
                update_fields['status'] = novo_status
                try:
                    supabase.table('ocorrencias').update(update_fields).eq('numero', numero).execute()
                    logging.info(f"[OCORRÊNCIA] Nº {numero} atualizada → {novo_status}")
                except Exception as e:
                    logging.error(f"Falha ao atualizar ocorrência {numero}: {e}")

            if novo_status == "Finalizada":
                # Extração segura dos nomes referenciados
                professor_nome = (item.get('professor_id') or {}).get('nome', 'N/A')
                sala_nome = (item.get('sala_id') or {}).get('sala', 'N/A')

                finalizadas.append({
                    "numero": numero,
                    "data_hora": formatar_data_hora(item.get('data_hora')),
                    "aluno_nome": item.get('aluno_nome', 'N/A'),
                    "tutor_nome": item.get('tutor_nome', 'N/A'),
                    "professor_nome": professor_nome,
                    "sala_nome": sala_nome,
                    "status": novo_status,
                    "solicitado_tutor": st,
                    "solicitado_coordenacao": sc,
                    "solicitado_gestao": sg,
                    "atendimento_tutor": at_tutor,
                    "atendimento_coordenacao": at_coord,
                    "atendimento_gestao": at_gest
                })

        return jsonify(finalizadas), 200

    except Exception as e:
        logging.exception("Erro /api/ocorrencias_finalizadas")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocorrencias_todas')
def api_ocorrencias_todas():
    try:
        response = supabase.table('ocorrencias').select('*').order('data_hora', desc=True).execute()
        return jsonify(handle_supabase_response(response))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/salas_com_ocorrencias')
def get_salas_com_ocorrencias():
    try:
        # Busca todas as salas que aparecem em alguma ocorrência
        ocorrencias = supabase.table('ocorrencias').select('sala_id').execute()
        sala_ids = list({o['sala_id'] for o in ocorrencias.data if o.get('sala_id')})
        
        # Busca detalhes das salas
        salas = supabase.table('d_salas').select('id, sala').in_('id', sala_ids).execute()
        
        # O frontend espera: [{"id": 1, "sala": "Nome Sala"}, ...]
        salas_formatadas = [{"id": s['id'], "sala": s['sala']} for s in handle_supabase_response(salas)]
        
        return jsonify(salas_formatadas)
    except Exception as e:
        logging.exception("Erro ao buscar salas com ocorrências")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alunos_com_ocorrencias_por_sala/<int:sala_id>')
def get_alunos_com_ocorrencias_por_sala(sala_id):
    try:
        # Busca todos os alunos que aparecem em ocorrências daquela sala
        ocorrencias = supabase.table('ocorrencias').select('aluno_id').eq('sala_id', sala_id).execute()
        aluno_ids = list({o['aluno_id'] for o in ocorrencias.data if o.get('aluno_id')})
        
        # Busca detalhes dos alunos
        alunos = supabase.table('d_alunos').select('id, nome').in_('id', aluno_ids).execute()
        
        # O frontend espera: [{"id": 1, "nome": "Nome Aluno"}, ...]
        alunos_formatados = [{"id": a['id'], "nome": a['nome']} for a in handle_supabase_response(alunos)]
        
        return jsonify(alunos_formatados)
    except Exception as e:
        logging.exception(f"Erro ao buscar alunos com ocorrências na sala {sala_id}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/relatorio_ocorrencias')
def get_relatorio_ocorrencias():
    try:
        sala_id = request.args.get('salaId')
        aluno_id = request.args.get('alunoId')
        data_inicial = request.args.get('dataInicial')
        data_final = request.args.get('dataFinal')
        query = supabase.table('ocorrencias').select('*, aluno_id(nome)').order('data_hora')
        if sala_id:
            query = query.eq('sala_id', int(sala_id))
        if aluno_id:
            query = query.eq('aluno_id', int(aluno_id))
        if data_inicial:
            query = query.gte('data_hora', data_inicial)
        if data_final:
            query = query.lte('data_hora', data_final)
        resp = query.execute()
        return jsonify(handle_supabase_response(resp))
    except Exception as e:
        logging.exception("Erro ao gerar relatório de ocorrências") # Log mais detalhado
        return jsonify({"error": f"Erro ao gerar relatório de ocorrências: {e}"}), 500

@app.route('/api/ocorrencias', methods=['GET'])
@app.route('/api/ocorrencias/<ocorrencia_id>', methods=['GET'])
def api_get_ocorrencias(ocorrencia_id=None):
    try:
        select_query_detail = "numero, data_hora, descricao, atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, dt_atendimento_tutor, dt_atendimento_coordenacao, dt_atendimento_gestao, aluno_nome, tutor_nome, professor_id(nome), sala_id(sala)"
        if ocorrencia_id:
            response = supabase.table('ocorrencias').select(select_query_detail).eq('numero', int(ocorrencia_id)).single().execute()
            data = handle_supabase_response(response)
            if data and isinstance(data, dict):
                data['id'] = data.get('numero')
                data['professor_nome'] = data.get('professor_id', {}).get('nome', 'N/A')
                data['sala_nome'] = data.get('sala_id', {}).get('sala', 'N/A')
                if 'professor_id' in data:
                    del data['professor_id']
                if 'sala_id' in data:
                    del data['sala_id']
            return jsonify(data), 200
        else:
            response = supabase.table('ocorrencias').select('*').order('data_hora', desc=True).execute()
            return jsonify(handle_supabase_response(response)), 200
    except Exception as e:
        logging.error(f"Erro ao buscar ocorrência de detalhe: {e}")
        return jsonify({"error": f"Falha ao buscar detalhes: {e}", "status": 500}), 500

@app.route('/api/alunos', methods=['GET'])
def api_get_alunos_all():
    try:
        response = supabase.table('d_alunos').select('id, ra, nome, sala_id, tutor_id').order('nome').execute()
        alunos_raw = handle_supabase_response(response)
        alunos = []
        for a in alunos_raw:
            try:
                sala_nome = None
                tutor_nome = None
                if a.get('sala_id'):
                    sala_resp = supabase.table('d_salas').select('sala').eq('id', a['sala_id']).single().execute()
                    sala_data = handle_supabase_response(sala_resp)
                    sala_nome = sala_data.get('sala') if isinstance(sala_data, dict) else None
                if a.get('tutor_id'):
                    tut_resp = supabase.table('d_funcionarios').select('nome').eq('id', a['tutor_id']).single().execute()
                    tut_data = handle_supabase_response(tut_resp)
                    tutor_nome = tut_data.get('nome') if isinstance(tut_data, dict) else None
                alunos.append({
                    "id": str(a.get('id')),
                    "ra": a.get('ra'),
                    "nome": a.get('nome'),
                    "sala_nome": sala_nome or 'N/A',
                    "tutor_nome": tutor_nome or 'Não Vinculado'
                })
            except Exception as inner_e:
                logging.warning(f"Erro ao processar aluno {a.get('nome')}: {inner_e}")
                continue
        return jsonify(alunos)
    except Exception as e:
        logging.exception("Erro /api/alunos")
        return jsonify({"error": f"Erro ao buscar todos os alunos: {e}", "status": 500}), 500

@app.route('/api/vinculacoes_disciplinas/<sala_id>', methods=['GET'])
def api_get_vinculacoes_disciplinas(sala_id):
    try:
        sala_id_bigint = int(sala_id)
        response = supabase.table('vinculos_disciplina_sala').select('fk_disciplina_id').eq('fk_sala_id', sala_id_bigint).execute()
        vinculos_raw = handle_supabase_response(response)
        disciplinas_ids = [v['fk_disciplina_id'] for v in vinculos_raw]
        return jsonify({"sala_id": sala_id, "disciplinas": disciplinas_ids})
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar vínculos de disciplinas: {e}", "status": 500}), 500

@app.route('/api/horarios_fixos/<nivel_ensino>', methods=['GET'])
def api_get_horarios_fixos(nivel_ensino):
    try:
        response = supabase.table('d_horarios_fixos').select('*').eq('nivel_ensino', nivel_ensino).order('dia_semana').execute()
        horarios = handle_supabase_response(response)
        return jsonify(horarios)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar horários fixos: {e}", "status": 500}), 500

@app.route('/api/agenda_semanal', methods=['GET'])
def api_get_agenda_semanal():
    sala_id = request.args.get('sala_id')
    data_referencia = request.args.get('data_referencia')
    if not sala_id or not data_referencia:
        return jsonify({"error": "Parâmetros sala_id e data_referencia são obrigatórios.", "status": 400}), 400
    try:
        response = supabase.table('f_agenda_aulas').select('id, dia_semana, ordem_aula, tema_aula, tipo_aula, fk_disciplina_id, fk_professor_id').eq('fk_sala_id', int(sala_id)).eq('data_referencia', data_referencia).execute()
        agenda_raw = handle_supabase_response(response)
        agenda = []
        for item in agenda_raw:
            disc_nome = None
            prof_nome = None
            if item.get('fk_disciplina_id'):
                dresp = supabase.table('d_disciplinas').select('nome').eq('id', item['fk_disciplina_id']).single().execute()
                ddata = handle_supabase_response(dresp)
                disc_nome = ddata.get('nome') if isinstance(ddata, dict) else None
            if item.get('fk_professor_id'):
                presp = supabase.table('d_funcionarios').select('nome').eq('id', item['fk_professor_id']).single().execute()
                pdata = handle_supabase_response(presp)
                prof_nome = pdata.get('nome') if isinstance(pdata, dict) else None
            agenda.append({
                "id": str(item.get('id')),
                "dia_semana": item.get('dia_semana'),
                "ordem_aula": item.get('ordem_aula'),
                "tema_aula": item.get('tema_aula'),
                "tipo_aula": item.get('tipo_aula'),
                "disciplina_nome": disc_nome,
                "professor_nome": prof_nome
            })
        return jsonify(agenda)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar agenda semanal: {e}", "status": 500}), 500

@app.route('/api/guia_aprendizagem', methods=['GET'])
def api_get_guia_aprendizagem():
    disciplina_id = request.args.get('disciplina_id')
    bimestre = request.args.get('bimestre')
    serie = request.args.get('serie')
    if not disciplina_id or not bimestre or not serie:
        return jsonify({"error": "Parâmetros disciplina, bimestre e série são obrigatórios.", "status": 400}), 400
    try:
        response = supabase.table('f_guia_aprendizagem').select('*').eq('fk_disciplina_id', disciplina_id).eq('bimestre', int(bimestre)).eq('serie', serie).execute()
        guia = handle_supabase_response(response)
        if guia and isinstance(guia, list) and guia[0].get('habilidades_planejadas'):
            # É comum JSONB vir como dict/list, se estiver como string precisa do json.loads
            # Aqui mantemos a lógica que assume que pode estar como JSON String se o Supabase não deserializou.
            try:
                guia[0]['habilidades_planejadas'] = json.dumps(guia[0]['habilidades_planejadas'])
            except:
                pass 
        return jsonify(guia)
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar Guia de Aprendizagem: {e}", "status": 500}), 500

@app.route('/api/salas')
def api_salas():
    # Exemplo: buscar salas no Supabase
    response = supabase.table("d_salas").select("id, nome").execute()
    return jsonify(response.data)

@app.route('/api/frequencia')
def api_frequencia():
    sala_id = request.args.get('sala')
    mes = int(request.args.get('mes'))
    ano = 2025  # ou datetime.now().year

    # Buscar alunos da sala
    alunos = supabase.table("d_alunos").select("id, nome").eq("sala_id", sala_id).execute().data

    # Buscar registros de frequência do mês
    registros = supabase.table("f_frequencia") \
        .select("aluno_id, data, status") \
        .gte("data", f"{ano}-{mes:02d}-01") \
        .lte("data", f"{ano}-{mes:02d}-31") \
        .execute().data

    resultado = []
    for aluno in alunos:
        freq_map = {r['data']: r['status'] for r in registros if r['aluno_id'] == aluno['id']}
        resultado.append({
            "nome": aluno['nome'],
            "frequencia": freq_map
        })

    return jsonify(resultado)

@app.route('/api/detalhe_frequencia')
def detalhe_frequencia():
    aluno_nome = request.args.get('aluno')
    data = request.args.get('data')

    if not aluno_nome or not data:
        return jsonify({"erro": "Parâmetros inválidos"}), 400

    # Buscar o aluno pelo nome (ou ID, se preferir)
    aluno = supabase.table("d_alunos").select("id").ilike("nome", aluno_nome).execute().data
    if not aluno:
        return jsonify({"erro": "Aluno não encontrado"}), 404

    aluno_id = aluno[0]['id']

    # Buscar registro de frequência específico
    registro = supabase.table("f_frequencia") \
        .select("data, status, hora_entrada, hora_saida, observacao") \
        .eq("aluno_id", aluno_id) \
        .eq("data", data) \
        .execute().data

    if not registro:
@app.route("/api/frequencia")
def get_frequencia():
    """
    Retorna os registros de frequência de uma sala e mês,
    formatando apenas o número do dia como coluna.
    """
    sala = request.args.get("sala")
    mes = request.args.get("mes")
    ano = datetime.now().year

    if not sala or not mes:
        return jsonify({"erro": "Sala e mês são obrigatórios"}), 400

    # 🧩 Busca alunos da sala
    alunos_resp = supabase.table("d_alunos") \
        .select("id, nome") \
        .eq("sala_id", sala) \
        .order("nome", desc=False) \
        .execute()

    alunos = alunos_resp.data or []

    # 📆 Intervalo do mês
    inicio_mes = f"{ano}-{str(mes).zfill(2)}-01"
    fim_mes = f"{ano}-{str(mes).zfill(2)}-31"

    # 🔍 Frequência do mês
    freq_resp = supabase.table("f_frequencia") \
        .select("id, fk_aluno_id, fk_sala_id, status, created_at") \
        .eq("fk_sala_id", sala) \
        .gte("created_at", inicio_mes) \
        .lte("created_at", fim_mes) \
        .execute()

    frequencias = freq_resp.data or []

    # 🗂️ Monta dicionário aluno → dia → status
    resultado = []
    for aluno in alunos:
        freq_dict = {}
        for f in frequencias:
            if f["fk_aluno_id"] == aluno["id"]:
                try:
                    data = datetime.strptime(f["created_at"], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    data = datetime.fromisoformat(f["created_at"].replace("Z", "+00:00"))
                dia = str(data.day).zfill(2)
                freq_dict[dia] = f.get("status", "")
        resultado.append({
            "nome": aluno["nome"],
            "id": aluno["id"],
            "frequencia": freq_dict
        })

    return jsonify(resultado)


@app.route("/api/detalhe_frequencia")
def detalhe_frequencia():
    """
    Retorna os detalhes do registro de atraso ou saída antecipada
    para exibir no modal.
    """
    aluno_id = request.args.get("aluno_id")
    sala_id = request.args.get("sala_id")
    dia = request.args.get("dia")
    mes = request.args.get("mes")
    ano = datetime.now().year

    if not aluno_id or not sala_id or not dia or not mes:
        return jsonify({"erro": "Parâmetros obrigatórios ausentes"}), 400

    # Constrói o intervalo do dia
    data_inicio = f"{ano}-{str(mes).zfill(2)}-{str(dia).zfill(2)}T00:00:00Z"
    data_fim = f"{ano}-{str(mes).zfill(2)}-{str(dia).zfill(2)}T23:59:59Z"

    # 🔎 Busca o registro específico
    resp = supabase.table("f_frequencia") \
        .select("*") \
        .eq("fk_aluno_id", aluno_id) \
        .eq("fk_sala_id", sala_id) \
        .gte("created_at", data_inicio) \
        .lte("created_at", data_fim) \
        .limit(1) \
        .execute()

    if not resp.data:
        return jsonify({"erro": "Registro não encontrado"}), 404

    registro = resp.data[0]

    # Retorna apenas os campos de atraso/saída
    detalhes = {
        "status": registro.get("status"),
        "hora_atraso": registro.get("hora_atraso"),
        "motivo_atraso": registro.get("motivo_atraso"),
        "responsavel_atraso": registro.get("responsavel_atraso"),
        "documento_atraso": registro.get("documento_atraso"),
        "hora_saida": registro.get("hora_saida"),
        "motivo_saida": registro.get("motivo_saida"),
        "responsavel_saida": registro.get("responsavel_saida"),
        "documento_saida": registro.get("documento_saida"),
        "created_at": registro.get("created_at")
    }

    return jsonify(detalhes)

@app.route("/api/registrar_atendimento/<int:ocorrencia_id>", methods=["POST"])
def registrar_atendimento(ocorrencia_id):
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Corpo da requisição vazio ou JSON inválido."}), 400

        nivel = data.get("nivel")
        texto = data.get("texto")
        
        # Suporte a campo 'atendimento' se o frontend antigo estiver sendo usado
        if not texto:
            texto = data.get("atendimento")

        if not nivel or not texto:
            return jsonify({"error": "Dados incompletos: Nível ou texto ausente."}), 400

        campos = {
            "professor": ("atendimento_professor", "dt_atendimento_professor"),
            "tutor": ("atendimento_tutor", "dt_atendimento_tutor"),
            "coordenacao": ("atendimento_coordenacao", "dt_atendimento_coordenacao"),
            "gestao": ("atendimento_gestao", "dt_atendimento_gestao"),
        }

        if nivel not in campos:
            return jsonify({"error": f"Nível de atendimento inválido: {nivel}"}), 400

        campo_texto, campo_data = campos[nivel]
        
        # CORREÇÃO CRÍTICA DO FORMATO DA DATA: 
        # Usando o formato ISO 8601 completo (incluindo milissegundos) para ser mais compatível com Supabase/PostgreSQL.
        agora = datetime.utcnow().isoformat(timespec='milliseconds') + "Z"

        # 1. ATUALIZA OS CAMPOS DE ATENDIMENTO E DATA
        update_data = {
            campo_texto: texto,
            campo_data: agora
        }
        
        update_result = supabase.table("ocorrencias").update(update_data).eq("numero", ocorrencia_id).execute()

        if update_result.count == 0:
             logging.warning(f"Supabase update falhou silenciosamente para ocorrência {ocorrencia_id}. Dados: {update_data}")
             # Retorna OK mesmo com falha silenciosa para evitar loop do frontend, mas registra o erro.
             return jsonify({"success": True, "novo_status": "Aberta", "warning": "Falha ao salvar no banco, status não atualizado."}), 200

        # 2. REAVALIA O STATUS (Busca os dados *após* a atualização)
        # Consulta sem a coluna 'solicitado_professor' que foi removida
        resp = supabase.table('ocorrencias').select(
            "solicitado_tutor, solicitado_coordenacao, solicitado_gestao, "
            "atendimento_tutor, atendimento_coordenacao, atendimento_gestao, status"
        ).eq("numero", ocorrencia_id).single().execute()

        if not resp.data:
            return jsonify({"error": "Ocorrência não encontrada"}), 404

        occ = resp.data
        
        # Converte strings 'SIM'/'NÃO' para booleanos
        st = _to_bool(occ.get('solicitado_tutor'))
        sc = _to_bool(occ.get('solicitado_coordenacao'))
        sg = _to_bool(occ.get('solicitado_gestao'))

        # Limpa o texto de atendimento
        at_tutor = (occ.get('atendimento_tutor') or "").strip()
        at_coord = (occ.get('atendimento_coordenacao') or "").strip()
        at_gest = (occ.get('atendimento_gestao') or "").strip()

        # Lógica de Pendência (Se solicitado E o texto for vazio/default)
        pendente_tutor = st and (at_tutor == "" or at_tutor == DEFAULT_AUTOTEXT)
        pendente_coord = sc and (at_coord == "" or at_coord == DEFAULT_AUTOTEXT)
        pendente_gestao = sg and (at_gest == "" or at_gest == DEFAULT_AUTOTEXT)

        novo_status = "Aberta"
        
        # Ocorrência está FINALIZADA se NENHUMA das pendências solicitadas estiver ativa.
        if not (pendente_tutor or pendente_coord or pendente_gestao):
            novo_status = "Finalizada"

        if novo_status == "Finalizada" and occ.get('status') != "Finalizada":
            supabase.table("ocorrencias").update({"status": novo_status}).eq("numero", ocorrencia_id).execute()
            logging.info(f"[ATENDIMENTO] Nº {ocorrencia_id} finalizada pelo nível {nivel}")
        
        # 3. Retorna Sucesso
        return jsonify({"success": True, "novo_status": novo_status}), 200

    except Exception as e:
        logging.exception(f"Erro ao registrar atendimento {ocorrencia_id}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cadastrar_sala', methods=['POST'])
def api_cadastrar_sala():
    data = request.json
    sala = data.get('sala')
    nivel_ensino = data.get('nivel_ensino')
    if not sala or not nivel_ensino:
        return jsonify({"error": "Nome da sala e nível de ensino são obrigatórios.", "status": 400}), 400
    try:
        nova_sala = {"sala": sala, "nivel_ensino": nivel_ensino}
        response = supabase.table('d_salas').insert(nova_sala).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Sala {sala} cadastrada com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: A sala '{sala}' já existe. Não foi cadastrada.", "status": 409}), 409
        logging.error(f"Erro no Supabase durante o cadastro de sala: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/cadastrar_funcionario', methods=['POST'])
def api_cadastrar_funcionario():
    data = request.json
    nome = data.get('nome')
    funcao = data.get('funcao')
    is_tutor = data.get('is_tutor', False)
    email_base = f"{nome.lower().replace(' ', '.').replace('prof.', 'p')[:15].strip('.')}"
    # Cria um email de fallback se o fornecido for nulo ou vazio
    email = data.get('email', f"{email_base}@{os.urandom(4).hex()}.escola.com.br")

    if not nome or not funcao:
        return jsonify({"error": "Nome e função são obrigatórios.", "status": 400}), 400
    try:
        novo_funcionario = {
            # O 'id' deve ser gerado automaticamente pelo Supabase, não incluído se for nulo
            "nome": nome,
            "email": email,
            "funcao": funcao,
            "is_tutor": is_tutor,
            "hobby": data.get('hobby', None),
        }
        # Se 'id' for passado explicitamente na payload, o Supabase tentará usá-lo ou dará erro.
        # Removemos para evitar conflitos se o Supabase for configurado para autoincremento.
        if 'id' in data and data['id'] is not None:
             novo_funcionario['id'] = data['id']
             
        response = supabase.table('d_funcionarios').insert(novo_funcionario).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"{nome} ({funcao}) cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": "Erro: Já existe um funcionário com um nome similar/ID cadastrado.", "status": 409}), 409
        logging.error(f"Erro no Supabase durante o cadastro de funcionário: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/cadastrar_disciplina', methods=['POST'])
def api_cadastrar_disciplina():
    data = request.json
    nome = data.get('nome')
    abreviacao = data.get('abreviacao')
    if not nome or not abreviacao:
        return jsonify({"error": "Nome e abreviação são obrigatórios.", "status": 400}), 400
    try:
        nova_disciplina = {
            "id": abreviacao.upper(),
            "nome": nome,
            "area_conhecimento": data.get('area_conhecimento', 'Geral')
        }
        response = supabase.table('d_disciplinas').insert(nova_disciplina).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Disciplina '{nome}' cadastrada com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: A abreviação '{abreviacao}' ou o nome já existe.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar disciplina: {e}", "status": 500}), 500

@app.route('/api/cadastrar_clube', methods=['POST'])
def api_cadastrar_clube():
    data = request.json
    nome = data.get('nome')
    semestre = data.get('semestre')
    if not nome or not semestre:
        return jsonify({"error": "Nome do clube e semestre são obrigatórios.", "status": 400}), 400
    try:
        novo_clube = {"nome": nome, "semestre": semestre}
        response = supabase.table('d_clubes').insert(novo_clube).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Clube '{nome}' cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: Clube '{nome}' já existe neste semestre.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar clube: {e}", "status": 500}), 500

@app.route('/api/cadastrar_eletiva', methods=['POST'])
def api_cadastrar_eletiva():
    data = request.json
    nome = data.get('nome')
    semestre = data.get('semestre')
    if not nome or not semestre:
        return jsonify({"error": "Nome da eletiva e semestre são obrigatórios.", "status": 400}), 400
    try:
        nova_eletiva = {"nome": nome, "semestre": semestre}
        response = supabase.table('d_eletivas').insert(nova_eletiva).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Eletiva '{nome}' cadastrada com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: Eletiva '{nome}' já existe neste semestre.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar eletiva: {e}", "status": 500}), 500

@app.route('/api/cadastrar_equipamento', methods=['POST'])
def api_cadastrar_equipamento():
    data = request.json
    colmeia = data.get('colmeia')
    equipamento_id = data.get('equipamento_id')
    if not colmeia or not equipamento_id:
        return jsonify({"error": "Colmeia e ID do equipamento são obrigatórios.", "status": 400}), 400
    try:
        novo_equipamento = {"colmeia": colmeia, "equipamento_id": int(equipamento_id), "status": "DISPONÍVEL"}
        response = supabase.table('d_inventario_equipamentos').insert(novo_equipamento).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Equipamento {equipamento_id} da {colmeia} cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: O Equipamento {equipamento_id} na {colmeia} já existe.", "status": 409}), 409
        return jsonify({"error": f"Falha ao cadastrar equipamento: {e}", "status": 500}), 500

@app.route('/api/cadastrar_aluno', methods=['POST'])
def api_cadastrar_aluno():
    data = request.json
    ra = data.get('ra')
    nome = data.get('nome')
    sala_id = data.get('sala_id')
    tutor_id = data.get('tutor_id')
    if not ra or not nome or not sala_id or not tutor_id:
        return jsonify({"error": "RA, Nome, Sala e Tutor são obrigatórios.", "status": 400}), 400
    try:
        sala_id_bigint = int(sala_id)
        tutor_id_bigint = int(tutor_id)
        novo_aluno = {"ra": ra, "nome": nome, "sala_id": sala_id_bigint, "tutor_id": tutor_id_bigint}
        response = supabase.table('d_alunos').insert(novo_aluno).execute()
        handle_supabase_response(response)
        return jsonify({"message": f"Aluno(a) {nome} (RA: {ra}) cadastrado com sucesso!", "status": 201}), 201
    except Exception as e:
        if "unique constraint" in str(e):
            return jsonify({"error": f"Erro: O RA '{ra}' já está cadastrado no sistema.", "status": 409}), 409
        logging.error(f"Erro no Supabase durante o cadastro de aluno: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/salvar_frequencia', methods=['POST'])
def api_salvar_frequencia_massa():
    """Salva a frequência P/F em massa, utilizando UPSERT para evitar duplicatas."""
    data_list = request.json
    if not data_list or not isinstance(data_list, list):
        return jsonify({"error": "Dados inválidos: Esperado uma lista de registros."}, 400)
        
    registros_a_salvar = []
    
    for item in data_list:
        try:
            aluno_id_bigint = int(item['aluno_id'])
            sala_id_bigint = int(item['sala_id'])
            data = item['data']
            status = item['status']
            
            # Garante que só P e F podem ser inseridos aqui, para não sobrescrever PA/PS/PAS
            if status not in ['P', 'F']:
                logging.warning(f"Status inválido {status} na frequência em massa. Ignorando.")
                continue

            registro = {
                "fk_aluno_id": aluno_id_bigint,
                "fk_sala_id": sala_id_bigint,
                "data": data,
                "status": status,
                # Chaves de conflito para UPSERT:
                "data": data, 
                "fk_aluno_id": aluno_id_bigint
            }
            registros_a_salvar.append(registro)
        except (ValueError, KeyError, TypeError):
            continue
            
    if not registros_a_salvar:
        return jsonify({"error": "Nenhum registro válido foi encontrado para salvar."}, 400)
        
    try:
        # Usa UPSERT (on_conflict na PK) para atualizar se já existir ou inserir se for novo.
        response = supabase.table('f_frequencia').upsert(registros_a_salvar, on_conflict='fk_aluno_id, data').execute()
        handle_supabase_response(response)
        return jsonify({"message": f"{len(registros_a_salvar)} registros de frequência salvos/atualizados com sucesso!", "status": 201}), 201
    except Exception as e:
        logging.error(f"Erro no Supabase ao salvar frequência em massa: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/salvar_atraso', methods=['POST'])
def api_salvar_atraso():
    """Salva um registro de PA ou PAS, atualizando o status se necessário."""
    data = request.json
    required_fields = ['aluno_id', 'sala_id', 'data', 'hora', 'motivo']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Dados incompletos: Aluno, Data, Hora e Motivo são obrigatórios."}, 400)
    
    aluno_id, sala_id = int(data['aluno_id']), int(data['sala_id'])
    registro_data = data['data']
    
    try:
        # 1. Busca o status atual
        resp = supabase.table('f_frequencia').select('status, id').eq('fk_aluno_id', aluno_id).eq('data', registro_data).maybe_single().execute()
        current_status = resp.data['status'] if resp.data else None
        
        # 2. Determina o novo status combinado
        novo_status = "PA"
        if current_status == 'PS' or current_status == 'PAS': # Já tinha PS ou PAS
            novo_status = 'PAS'
        elif current_status == 'F': # Estava faltando, mas apareceu com atraso.
             novo_status = 'PA'
        elif current_status == 'P': # Estava presente. Vira PA.
             novo_status = 'PA'

        # 3. Prepara o registro (usa UPSERT)
        registro = {
            "fk_aluno_id": aluno_id,
            "fk_sala_id": sala_id,
            "data": registro_data,
            "hora_atraso": data['hora'],
            "motivo_atraso": data['motivo'],
            "responsavel_atraso": data.get('responsavel'),
            "telefone_atraso": data.get('telefone'),
            "status": novo_status
        }
        
        response = supabase.table('f_frequencia').upsert(registro, on_conflict='fk_aluno_id, data').execute()
        handle_supabase_response(response)
        
        return jsonify({"message": f"Registro de Atraso salvo com sucesso! Status: {novo_status}", "status": 201}), 201
    except Exception as e:
        logging.error(f"Erro no Supabase ao salvar atraso: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/salvar_saida_antecipada', methods=['POST'])
def api_salvar_saida_antecipada():
    """Salva um registro de PS ou PAS, atualizando o status se necessário."""
    data = request.json
    required_fields = ['aluno_id', 'sala_id', 'data', 'hora', 'motivo']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Dados incompletos: Aluno, Data, Hora e Motivo são obrigatórios."}, 400)
        
    aluno_id, sala_id = int(data['aluno_id']), int(data['sala_id'])
    registro_data = data['data']

    try:
        # 1. Busca o status atual
        resp = supabase.table('f_frequencia').select('status, id').eq('fk_aluno_id', aluno_id).eq('data', registro_data).maybe_single().execute()
        current_status = resp.data['status'] if resp.data else None
        
        # 2. Determina o novo status combinado
        novo_status = "PS"
        if current_status == 'PA' or current_status == 'PAS': # Já tinha PA ou PAS
            novo_status = 'PAS'
        elif current_status == 'F': # Estava faltando, mas saiu cedo (o que implica presença).
             novo_status = 'PS'
        elif current_status == 'P': # Estava presente. Vira PS.
             novo_status = 'PS'
        
        # 3. Prepara o registro (usa UPSERT)
        registro = {
            "fk_aluno_id": aluno_id,
            "fk_sala_id": sala_id,
            "data": registro_data,
            "hora_saida": data['hora'],
            "motivo_saida": data['motivo'],
            "responsavel_saida": data.get('responsavel'),
            "telefone_saida": data.get('telefone'),
            "status": novo_status
        }
        
        response = supabase.table('f_frequencia').upsert(registro, on_conflict='fk_aluno_id, data').execute()
        handle_supabase_response(response)
        
        return jsonify({"message": f"Registro de Saída Antecipada salvo com sucesso! Status: {novo_status}", "status": 201}), 201
    except Exception as e:
        logging.error(f"Erro no Supabase ao salvar saída antecipada: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}", "status": 500}), 500

@app.route('/api/registrar_ocorrencia', methods=['POST'])
def api_registrar_ocorrencia():
    data = request.json
    try:
        # Tenta converter IDs para int/bigint. Se falhar, assume None
        prof_id_bigint = int(data.get('prof_id')) if data.get('prof_id') and str(data.get('prof_id')).isdigit() else None
        aluno_id_bigint = int(data.get('aluno_id')) if data.get('aluno_id') and str(data.get('aluno_id')).isdigit() else None
        sala_id_bigint = int(data.get('sala_id')) if data.get('sala_id') and str(data.get('sala_id')).isdigit() else None
    except ValueError:
        # Se a conversão falhar (ex: string não numérica), trata como None
        prof_id_bigint, aluno_id_bigint, sala_id_bigint = None, None, None
        
    descricao = data.get('descricao')
    atendimento_professor = data.get('atendimento_professor')
    
    # --------------------------------------------------------------------------------
    # VALIDAÇÃO CORRIGIDA: Se houver falha na conversão para int, a validação abaixo
    # garante que os IDs são obrigatórios.
    if not all([prof_id_bigint, aluno_id_bigint, sala_id_bigint, descricao, atendimento_professor]):
        return jsonify({"error": "Dados obrigatórios (Professor, Aluno, Sala, Descrição e Atendimento Professor) são necessários. Verifique se os IDs de Professor, Aluno e Sala são válidos.", "status": 400}), 400
    # --------------------------------------------------------------------------------
    
    try:
        # Obtém o nome do tutor a partir do aluno_id
        tutor_id_resp = supabase.table('d_alunos').select('tutor_id').eq('id', aluno_id_bigint).single().execute()
        tutor_id = tutor_id_resp.data.get('tutor_id') if tutor_id_resp.data else None
        
        tutor_nome_resp = None
        if tutor_id:
            tutor_nome_resp = supabase.table('d_funcionarios').select('nome').eq('id', tutor_id).single().execute()
            
        tutor_nome = tutor_nome_resp.data.get('nome') if tutor_nome_resp and tutor_nome_resp.data else 'Tutor Não Encontrado'
        
        # O Supabase irá setar a coluna 'numero' (bigint) automaticamente (sequência)
        nova_ocorrencia = {
            "professor_id": prof_id_bigint,
            "aluno_id": aluno_id_bigint,
            "sala_id": sala_id_bigint,
            "data_hora": datetime.now().isoformat(), # Usando datetime.now().isoformat()
            "descricao": descricao,
            "atendimento_professor": atendimento_professor,
            "aluno_nome": data.get('aluno_nome'),
            "tutor_nome": tutor_nome, # Usa o nome buscado
            "tutor_id": tutor_id,
            "tipo": data.get('tipo', 'Comportamental'),
            "status": "Aberta",
            # Valores booleanos são salvos como string 'SIM'/'NÃO' se a coluna for TEXT (conforme o CSV)
            "solicitado_tutor": 'SIM' if _to_bool(data.get('solicitar_tutor')) else 'NÃO',
            "solicitado_coordenacao": 'SIM' if _to_bool(data.get('solicitar_coordenacao')) else 'NÃO',
            "solicitado_gestao": 'SIM' if _to_bool(data.get('solicitar_gestao')) else 'NÃO',
        }
        
        # A coluna 'solicitado_*' é TEXT, então 'NÃO' e 'SIM' são os valores corretos.
        # A função _to_bool irá interpretar isso corretamente na busca.
        
        response = supabase.table('ocorrencias').insert(nova_ocorrencia).execute()
        handle_supabase_response(response)
        
        logging.info(f"Ocorrência registrada para Aluno ID {aluno_id_bigint}")
        
        return jsonify({"message": "Ocorrência registrada com sucesso! Aguardando atendimento.", "status": 201}), 201
    
    except Exception as e:
        # Registra o erro detalhado no log do servidor
        logging.exception(f"Erro no Supabase ao registrar ocorrência: {e}")
        # Retorna o erro detalhado (ou um genérico) para o cliente
        return jsonify({"error": f"Falha ao registrar ocorrência: {e}", "status": 500}), 500

@app.route('/api/agendar_tutoria', methods=['POST'])
def api_agendar_tutoria():
    data = request.json
    if not all(data.get(f) for f in ['tutor_id', 'aluno_id', 'data_agendamento', 'hora_agendamento']):
        return jsonify({"error": "Dados de agendamento incompletos.", "status": 400}), 400
    try:
        agendamento = {
            "fk_aluno_id": int(data['aluno_id']),
            "fk_tutor_id": int(data['tutor_id']),
            "data_agendamento": data['data_agendamento'],
            "hora_agendamento": data['hora_agendamento'],
            "status": "AGENDADO",
        }
        response = supabase.table('agendamentos_tutoria').insert(agendamento).execute()
        handle_supabase_response(response)
        return jsonify({"message": "Agendamento de Tutoria criado com sucesso!", "status": 201}), 201
    except Exception as e:
        return jsonify({"error": f"Falha ao agendar tutoria: {e}", "status": 500}), 500

@app.route('/api/salvar_parametros', methods=['POST'])
def api_salvar_parametros():
    data = request.json
    if not data:
        return jsonify({"error": "Nenhum parâmetro enviado.", "status": 400}), 400
    try:
        updates = []
        for key, value in data.items():
            updates.append({"parametro": key, "valor": value})
        response = supabase.table('cfg_parametros').upsert(updates, on_conflict='parametro').execute()
        handle_supabase_response(response)
        return jsonify({"message": "Parâmetros de configuração salvos com sucesso!", "status": 200}), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao salvar configurações: {e}", "status": 500}), 500

@app.route('/api/salvar_agenda', methods=['POST'])
def api_salvar_agenda():
    data = request.json
    registros = data.get('registros')
    if not registros or not isinstance(registros, list):
        return jsonify({"error": "Nenhum registro de agenda válido enviado.", "status": 400}), 400
    try:
        registros_a_salvar = []
        for item in registros:
            disciplina_id = item['fk_disciplina_id']
            registros_a_salvar.append({
                "fk_sala_id": int(item['fk_sala_id']),
                "fk_professor_id": int(item['fk_professor_id']),
                "data_referencia": item['data_referencia'],
                "dia_semana": item['dia_semana'],
                "ordem_aula": int(item['ordem_aula']),
                "fk_disciplina_id": disciplina_id,
                "tema_aula": item['tema_aula'],
                "tipo_aula": item['tipo_aula'],
            })
        response = supabase.table('f_agenda_aulas').upsert(registros_a_salvar, on_conflict='fk_sala_id, data_referencia, dia_semana, ordem_aula').execute()
        handle_supabase_response(response)
        return jsonify({"message": f"{len(registros_a_salvar)} registros de agenda salvos/atualizados com sucesso!", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao salvar agenda: {e}")
        return jsonify({"error": f"Falha ao salvar agenda: {e}", "status": 500}), 500

@app.route('/api/atualizar_ocorrencia/<ocorrencia_id>', methods=['PUT'])
def api_atualizar_ocorrencia(ocorrencia_id):
    data = request.json
    if not data:
        return jsonify({"error": "Nenhum dado de atualização enviado.", "status": 400}), 400
    try:
        ocorrencia_id_bigint = int(ocorrencia_id)
        response = supabase.table('ocorrencias').update(data).eq('numero', ocorrencia_id_bigint).execute()
        handle_supabase_response(response)
        return jsonify({"message": "Ocorrência atualizada com sucesso.", "status": 200}), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao atualizar ocorrência: {e}", "status": 500}), 500

@app.route('/api/finalizar_retirada_equipamento', methods=['POST'])
def api_finalizar_retirada_equipamento():
    data = request.json
    agendamento_id = data.get('agendamento_id')
    vinculacoes = data.get('vinculacoes')
    status_agendamento = data.get('status_agendamento')
    if not agendamento_id or not status_agendamento:
        return jsonify({"error": "ID do agendamento e Status são obrigatórios.", "status": 400}), 400
    try:
        update_data = {"status": status_agendamento, "data_retirada_geral": data.get('data_retirada_geral'), "termo_aceite_registro": data.get('termo_aceite_registro')}
        supabase.table('reservas_equipamentos').update(update_data).eq('id', agendamento_id).execute()
        if vinculacoes:
            registros = []
            for v in vinculacoes:
                registros.append({
                    "fk_agendamento_id": int(agendamento_id),
                    "fk_aluno_id": int(v['aluno_id']),
                    "equipamento_id": v['equipamento_id'],
                    "data_retirada": v['data_retirada']
                })
            if registros:
                supabase.table('rastreamento_equipamento').insert(registros).execute()
        return jsonify({"message": f"Retirada do agendamento {agendamento_id} finalizada e equipamentos vinculados!", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao finalizar retirada: {e}")
        return jsonify({"error": f"Erro interno ao finalizar retirada: {e}", "status": 500}), 500

@app.route('/api/finalizar_devolucao_equipamento', methods=['POST'])
def api_finalizar_devolucao_equipamento():
    data = request.json
    agendamento_id = data.get('agendamento_id')
    if not agendamento_id:
        return jsonify({"error": "ID do agendamento é obrigatório.", "status": 400}), 400
    try:
        update_data = {"status": "FINALIZADO", "data_devolucao": data.get('data_devolucao', datetime.now().isoformat())}
        supabase.table('reservas_equipamentos').update(update_data).eq('id', agendamento_id).execute()
        return jsonify({"message": f"Devolução do agendamento {agendamento_id} finalizada com sucesso!", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao finalizar devolução: {e}")
        return jsonify({"error": f"Erro interno ao finalizar devolução: {e}", "status": 500}), 500

@app.route('/api/relatorio_estatistico', methods=['GET'])
def api_relatorio_estatistico():
    """Gera o JSON de estatísticas de ocorrências."""
    try:
        # 1. Obter todas as ocorrências detalhadas
        resp_occ = supabase.table('ocorrencias').select(
            "numero, data_hora, status, tipo, tutor_id, sala_id, "
            "solicitado_tutor, solicitado_coordenacao, solicitado_gestao, "
            "atendimento_tutor, atendimento_coordenacao, atendimento_gestao, "
            "dt_atendimento_gestao" # Usamos o dt_atendimento_gestao como data de fechamento final
        ).execute()
        ocorrencias = handle_supabase_response(resp_occ)
        
        # 2. Obter mapeamentos de Sala e Tutor
        resp_salas = supabase.table('d_salas').select('id, sala').execute()
        salas_map = {str(s['id']): s['sala'] for s in handle_supabase_response(resp_salas)}
        
        resp_tutores = supabase.table('d_funcionarios').select('id, nome').eq('is_tutor', True).execute()
        tutores_map = {str(t['id']): t['nome'] for t in handle_supabase_response(resp_tutores)}

        # 3. Agregação de dados
        total = len(ocorrencias)
        abertas = 0
        finalizadas = 0
        
        tipos_count = {}
        salas_stats = {} # Por Sala: {total, menos_7d, mais_7d, nao_respondidas}
        tutores_stats = {} # Por Tutor: {total, finalizadas, abertas, tempos_resposta: []}
        tempo_resposta_faixas = {
            '1-7 dias': 0, '8-30 dias': 0, 'mais de 30 dias': 0, 'não finalizadas': 0
        }
        ocorrencias_por_mes = {} # {mes_ano: count}
        
        hoje = datetime.now()
        
        for occ in ocorrencias:
            occ_status = occ.get('status')
            occ_data_hora = occ.get('data_hora')
            occ_tipo = occ.get('tipo', 'Outros')
            sala_id_str = str(occ.get('sala_id'))
            tutor_id_str = str(occ.get('tutor_id')) if occ.get('tutor_id') else None
            
            # 3.1. Totais e Tipos
            if occ_status == 'Aberta':
                abertas += 1
            elif occ_status == 'Finalizada':
                finalizadas += 1
            
            tipos_count[occ_tipo] = tipos_count.get(occ_tipo, 0) + 1
            
            # 3.2. Por Mês
            if occ_data_hora:
                # Tratamento para datetime.fromisoformat: 
                try:
                    dt = datetime.fromisoformat(occ_data_hora.replace('Z', '+00:00'))
                    mes_ano_key = dt.strftime("%Y-%m")
                    ocorrencias_por_mes[mes_ano_key] = ocorrencias_por_mes.get(mes_ano_key, 0) + 1
                except Exception:
                    logging.warning(f"Data de ocorrência inválida: {occ_data_hora}")
            
            # 3.3. Estatísticas por Sala
            if sala_id_str in salas_map:
                sala_name = salas_map[sala_id_str]
                if sala_id_str not in salas_stats:
                    salas_stats[sala_id_str] = {'sala': sala_name, 'total': 0, 'menos_7d': 0, 'mais_7d': 0, 'nao_respondidas': 0}
                salas_stats[sala_id_str]['total'] += 1
                
                if occ_status == 'Aberta' and occ_data_hora:
                    try:
                        dt_abertura = datetime.fromisoformat(occ_data_hora.replace('Z', '+00:00'))
                        dias_aberta = (hoje - dt_abertura).days
                        
                        if dias_aberta <= 7:
                            salas_stats[sala_id_str]['menos_7d'] += 1
                        else:
                            salas_stats[sala_id_str]['mais_7d'] += 1
                            
                        # Verifica se é "Não Respondida"
                        solicitado = (_to_bool(occ.get('solicitado_tutor')) or 
                                      _to_bool(occ.get('solicitado_coordenacao')) or 
                                      _to_bool(occ.get('solicitado_gestao')))
                        
                        atendimento_tutor = occ.get('atendimento_tutor')
                        atendimento_coord = occ.get('atendimento_coordenacao')
                        atendimento_gestao = occ.get('atendimento_gestao')
                        
                        respondido = (
                            (atendimento_tutor and atendimento_tutor != DEFAULT_AUTOTEXT) or
                            (atendimento_coord and atendimento_coord != DEFAULT_AUTOTEXT) or
                            (atendimento_gestao and atendimento_gestao != DEFAULT_AUTOTEXT)
                        )
                        
                        if solicitado and not respondido:
                            salas_stats[sala_id_str]['nao_respondidas'] += 1
                    except Exception:
                        logging.warning(f"Erro no cálculo de dias abertas para ocorrência {occ.get('numero')}")


            # 3.4. Estatísticas por Tutor
            if tutor_id_str and tutor_id_str in tutores_map:
                tutor_name = tutores_map[tutor_id_str]
                if tutor_id_str not in tutores_stats:
                    tutores_stats[tutor_id_str] = {'tutor': tutor_name, 'total': 0, 'finalizadas': 0, 'abertas': 0, 'tempos_resposta': []}
                
                tutores_stats[tutor_id_str]['total'] += 1
                if occ_status == 'Finalizada':
                    tutores_stats[tutor_id_str]['finalizadas'] += 1
                    
                    # Calcula o tempo de resposta
                    dias_resp = calcular_dias_resposta(occ_data_hora, occ.get('dt_atendimento_gestao'))
                    if dias_resp is not None:
                        tutores_stats[tutor_id_str]['tempos_resposta'].append(dias_resp)
                        
                        if dias_resp <= 7:
                            tempo_resposta_faixas['1-7 dias'] += 1
                        elif dias_resp <= 30:
                            tempo_resposta_faixas['8-30 dias'] += 1
                        else:
                            tempo_resposta_faixas['mais de 30 dias'] += 1
                else:
                    tutores_stats[tutor_id_str]['abertas'] += 1
                    tempo_resposta_faixas['não finalizadas'] += 1

        # 4. Finalização dos cálculos e formatação
        
        # Média de dias de resposta por tutor
        final_tutores = []
        for t_id, t_data in tutores_stats.items():
            t_data['media_dias_resposta'] = sum(t_data['tempos_resposta']) / len(t_data['tempos_resposta']) if t_data['tempos_resposta'] else 0
            # Formatação para o JS
            final_tutores.append({
                'tutor': t_data['tutor'],
                'total': t_data['total'],
                'finalizadas': t_data['finalizadas'],
                'abertas': t_data['abertas'],
                'media_dias_resposta': round(t_data['media_dias_resposta'], 1) if t_data['media_dias_resposta'] else 0
            })
            
        # Formatação do Tempo de Resposta para Gráfico
        tempo_resp_grafico = {
            'labels': list(tempo_resposta_faixas.keys()),
            'valores': list(tempo_resposta_faixas.values())
        }
        
        # Formatação Ocorrências por Mês para Gráfico
        meses_ordenados = sorted(ocorrencias_por_mes.keys())
        ocorrencias_por_mes_grafico = {
            'labels': [datetime.strptime(m, "%Y-%m").strftime("%b/%y") for m in meses_ordenados],
            'valores': [ocorrencias_por_mes[m] for m in meses_ordenados]
        }

        # 5. Retorno do JSON final
        return jsonify({
            'total': total,
            'abertas': abertas,
            'finalizadas': finalizadas,
            'tipos': tipos_count,
            'por_sala': list(salas_stats.values()),
            'por_tutor': final_tutores,
            'tempo_resposta': tempo_resp_grafico,
            'ocorrencias_por_mes': ocorrencias_por_mes_grafico
        }), 200

    except Exception as e:
        logging.exception("Erro ao gerar relatório estatístico")
        # Retorna um JSON de erro válido
        return jsonify({"error": f"Erro interno ao gerar relatório: {e}"}), 500


@app.route('/api/vincular_disciplina_sala', methods=['POST'])
def api_vincular_disciplina_sala():
    data = request.json
    sala_id = data.get('sala_id')
    disciplinas_ids = data.get('disciplinas')
    if not sala_id:
        return jsonify({"error": "ID da sala é obrigatório.", "status": 400}), 400
    try:
        sala_id_bigint = int(sala_id)
        # Limpa todos os vínculos existentes para esta sala
        supabase.table('vinculos_disciplina_sala').delete().eq('fk_sala_id', sala_id_bigint).execute()
        if disciplinas_ids:
            # Insere os novos vínculos
            registros = [{"fk_sala_id": sala_id_bigint, "fk_disciplina_id": d_id} for d_id in disciplinas_ids]
            supabase.table('vinculos_disciplina_sala').insert(registros).execute()
        return jsonify({"message": f"Vínculos da sala {sala_id} atualizados com sucesso.", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao salvar vínculos de disciplina: {e}")
        return jsonify({"error": f"Falha ao salvar vínculos de disciplina: {e}", "status": 500}), 500

@app.route('/api/vincular_tutor_aluno', methods=['POST'])
def api_vincular_tutor_aluno():
    data = request.json
    tutor_id = data.get('tutor_id')
    vinculos = data.get('vinculos')
    sala_id = data.get('sala_id') # Adicionado para melhor escopo de desvinculação
    
    if not tutor_id or not sala_id:
        return jsonify({"error": "ID do tutor e ID da sala são obrigatórios.", "status": 400}), 400
    
    try:
        tutor_id_bigint = int(tutor_id)
        sala_id_bigint = int(sala_id)
        
        alunos_a_vincular_ids = [int(v['aluno_id']) for v in vinculos if 'aluno_id' in v]
        
        # 1. Desvincula o tutor de todos os alunos da sala que atualmente estão vinculados ao tutor_id passado
        alunos_na_sala_raw = supabase.table('d_alunos').select('id').eq('sala_id', sala_id_bigint).eq('tutor_id', tutor_id_bigint).execute()
        alunos_na_sala_ids = [int(a['id']) for a in handle_supabase_response(alunos_na_sala_raw)]
        
        # Alunos que estavam vinculados a este tutor e foram desmarcados
        alunos_a_desvincular_ids = [a_id for a_id in alunos_na_sala_ids if a_id not in alunos_a_vincular_ids]
        
        if alunos_a_desvincular_ids:
            logging.info(f"Desvinculando alunos: {alunos_a_desvincular_ids} da sala {sala_id_bigint} do tutor {tutor_id_bigint}")
            supabase.table('d_alunos').update({'tutor_id': None}).in_('id', alunos_a_desvincular_ids).execute()
        
        # 2. Vincula o tutor aos alunos selecionados
        if alunos_a_vincular_ids:
            # O Supabase Python SDK não suporta 'update().in_()' para a lista de alunos diretamente. 
            # Fazemos um loop para garantir a atomicidade por aluno.
            for aluno_id in alunos_a_vincular_ids:
                supabase.table('d_alunos').update({'tutor_id': tutor_id_bigint}).eq('id', aluno_id).execute()
                
        return jsonify({"message": "Vínculos atualizados com sucesso.", "status": 200}), 200
    except Exception as e:
        logging.error(f"Erro ao vincular tutor/aluno: {e}")
        return jsonify({"error": f"Falha ao vincular tutor/aluno: {e}", "status": 500}), 500

@app.route('/api/ocorrencia_detalhes')
def ocorrencia_detalhes():
    numero = request.args.get('numero')
    if not numero:
        return jsonify({'error': 'Número da ocorrência não fornecido'}), 400

    try:
        # Consulta ao Supabase na tabela de ocorrências, buscando as referências
        select_query_detail = "numero, data_hora, descricao, atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, dt_atendimento_tutor, dt_atendimento_coordenacao, dt_atendimento_gestao, aluno_nome, tutor_nome, professor_id(nome), sala_id(sala), status"
        resp = supabase.table('ocorrencias').select(select_query_detail).eq('numero', numero).single().execute()

        occ = resp.data

        if occ is None:
            return jsonify({'error': 'Ocorrência não encontrada'}), 404

        # Extrai nomes aninhados
        professor_nome = occ.get('professor_id', {}).get('nome', 'N/A')
        sala_nome = occ.get('sala_id', {}).get('sala', 'N/A')
        
        # Retorna os campos esperados pelo JS
        return jsonify({
            'numero': occ.get('numero'),
            'aluno_nome': occ.get('aluno_nome'),
            'sala_nome': sala_nome,
            'tutor_nome': occ.get('tutor_nome'),
            'professor_nome': professor_nome,
            'status': occ.get('status'),
            'descricao': occ.get('descricao'),
            'atendimento_professor': occ.get('atendimento_professor'),
            'atendimento_tutor': occ.get('atendimento_tutor'),
            'atendimento_coordenacao': occ.get('atendimento_coordenacao'),
            'atendimento_gestao': occ.get('atendimento_gestao')
        })
    except Exception as e:
        logging.exception(f"Erro ao consultar Supabase para detalhes da ocorrência {numero}")
        return jsonify({'error': f'Erro ao consultar Supabase: {str(e)}'}), 500

@app.route('/api/frequencia/status', methods=['GET'])
def api_frequencia_status():
    """Verifica se a frequência de uma sala em uma data já foi registrada."""
    try:
        sala_id = request.args.get('sala_id')
        data = request.args.get('data')

        if not sala_id or not data:
            return jsonify({"error": "Parâmetros sala_id e data são obrigatórios."}), 400
        
        # Busca qualquer registro para aquela sala e data
        q = supabase.table('f_frequencia').select('id').eq('fk_sala_id', int(sala_id)).eq('data', data)
        resp = q.limit(1).execute()
        
        registrada = len(resp.data or []) > 0
        
        return jsonify({"registrada": registrada}), 200
    except Exception as e:
        logging.exception("Erro ao verificar status da frequência.")
        return jsonify({"error": str(e)}), 500

@app.route('/api/frequencia/detalhes', methods=['GET'])
def api_frequencia_detalhes():
    """Busca detalhes de frequência por aluno e data (usado pelo modal do relatório)."""
    try:
        aluno_id = request.args.get('aluno_id')
        data = request.args.get('data')

        if not aluno_id or not data:
            return jsonify({"error": "Parâmetros aluno_id e data são obrigatórios."}), 400
            
        resp = supabase.table('f_frequencia').select('*').eq('fk_aluno_id', int(aluno_id)).eq('data', data).maybe_single().execute()
        
        if not resp.data:
            return jsonify({"error": "Registro não encontrado."}), 404
            
        return jsonify(resp.data), 200
        
    except Exception as e:
        logging.exception("Erro ao buscar detalhes da frequência.")
        return jsonify({"error": str(e)}), 500

@app.route('/api/relatorio_frequencia_detalhada', methods=['GET'])
def api_relatorio_frequencia_detalhada():
    """Gera o relatório de frequência detalhada por sala e mês/ano."""
    try:
        sala_id = request.args.get('sala_id')
        mes_ano_str = request.args.get('mes_ano') # Formato 'YYYY-MM'

        if not sala_id or not mes_ano_str:
            return jsonify({"error": "Filtros Sala e Mês/Ano são obrigatórios."}), 400

        ano, mes = map(int, mes_ano_str.split('-'))
        dias_no_mes = monthrange(ano, mes)[1]
        data_inicio = f"{ano}-{mes:02d}-01"
        data_fim = f"{ano}-{mes:02d}-{dias_no_mes:02d}"
        
        sala_id_int = int(sala_id)

        # 1. Busca todos os alunos da sala
        resp_alunos = supabase.table('d_alunos').select('id, nome').eq('sala_id', sala_id_int).order('nome').execute()
        alunos = handle_supabase_response(resp_alunos)
        
        aluno_ids = [a['id'] for a in alunos]
        
        if not aluno_ids:
             return jsonify({"error": "Nenhum aluno encontrado nesta sala."}), 404

        # 2. Busca todos os registros de frequência para esses alunos no período
        resp_frequencia = supabase.table('f_frequencia').select('*').in_('fk_aluno_id', aluno_ids).gte('data', data_inicio).lte('data', data_fim).execute()
        frequencia_raw = handle_supabase_response(resp_frequencia)

        # Mapeia registros por (aluno_id, data)
        frequencia_map = {}
        for reg in frequencia_raw:
            key = (reg['fk_aluno_id'], reg['data'])
            frequencia_map[key] = reg

        # 3. Monta a matriz de relatório
        relatorio = []
        
        # Gera a lista completa de datas no mês para a coluna do relatório
        dias_uteis = [datetime(ano, mes, d).strftime('%Y-%m-%d') for d in range(1, dias_no_mes + 1)]

        for aluno in alunos:
            aluno_row = {'id': aluno['id'], 'nome': aluno['nome'], 'dias': []}
            
            for data in dias_uteis:
                key = (aluno['id'], data)
                registro = frequencia_map.get(key)
                
                status_final = '?' # Não registrado / Fim de semana, etc.
                detalhes = None

                if registro:
                    status_final = registro['status']
                    if status_final in ['PA', 'PS', 'PAS']:
                        # Coleta os detalhes para o modal
                        detalhes = {
                            'hora_atraso': registro.get('hora_atraso'),
                            'motivo_atraso': registro.get('motivo_atraso'),
                            'responsavel_atraso': registro.get('responsavel_atraso'),
                            'telefone_atraso': registro.get('telefone_atraso'),
                            'hora_saida': registro.get('hora_saida'),
                            'motivo_saida': registro.get('motivo_saida'),
                            'responsavel_saida': registro.get('responsavel_saida'),
                            'telefone_saida': registro.get('telefone_saida'),
                        }

                aluno_row['dias'].append({'data': data, 'status': status_final, 'detalhes': detalhes})
            
            relatorio.append(aluno_row)
        
        return jsonify({
            'dias_mes': dias_no_mes,
            'relatorio': relatorio,
            'dias_uteis': dias_uteis # Lista de datas YYYY-MM-DD
        }), 200

    except Exception as e:
        logging.exception("Erro ao gerar relatório de frequência detalhada")
        return jsonify({"error": f"Erro ao gerar relatório: {e}"}), 500


@app.route('/api/ocorrencias_por_aluno/<aluno_id>', methods=['GET'])
def api_ocorrencias_por_aluno(aluno_id):
    """Busca todas as ocorrências de um aluno específico."""
    if not aluno_id:
        return jsonify({"error": "ID do aluno é obrigatório."}), 400
    try:
        aluno_id_bigint = int(aluno_id)
        
        # Seleciona apenas os campos necessários
        resp = supabase.table('ocorrencias').select(
            "numero, data_hora, descricao, status, aluno_nome, aluno_id, sala_id"
        ).eq('aluno_id', aluno_id_bigint).order('data_hora', desc=True).execute()
        
        ocorrencias_raw = resp.data  # ou handle_supabase_response(resp), dependendo da sua função
        
        # Formata os dados
        ocorrencias_formatadas = [
            {
                "numero": o.get("numero"),
                "data_hora": o.get("data_hora"),
                "descricao": o.get("descricao"),
                "status": o.get("status"),
                "aluno_nome": o.get("aluno_nome")
            } for o in ocorrencias_raw
        ]
        
        return jsonify(ocorrencias_formatadas), 200
    except ValueError:
        return jsonify({"error": "ID do aluno inválido."}), 400
    except Exception as e:
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500


@app.route('/api/gerar_pdf_ocorrencias', methods=['POST'])
def gerar_pdf_ocorrencias():
    dados = request.get_json()
    numeros = dados.get('numeros', [])

    if not numeros:
        return jsonify({"error": "Nenhuma ocorrência selecionada"}), 400

    try:
        # Buscar ocorrências no Supabase
        # ATUALIZAÇÃO: Incluindo 'impressao_pdf' na consulta
        resp = supabase.table('ocorrencias').select(
            "numero, data_hora, descricao, status, aluno_nome, sala_id, tutor_nome, atendimento_professor, atendimento_tutor, atendimento_coordenacao, atendimento_gestao, impressao_pdf"
        ).in_('numero', numeros).order('data_hora', desc=True).execute()

        ocorrencias = resp.data

        if not ocorrencias:
            return jsonify({"error": "Nenhuma ocorrência encontrada"}), 404

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.set_font("Arial", "B", 14)
        # CORREÇÃO: Usando safe_pdf_text para cabeçalhos fixos
        pdf.cell(0, 10, safe_pdf_text("RELATÓRIO DE REGISTRO DE OCORRÊNCIAS"), ln=True, align='C')
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 7, safe_pdf_text("E.E. PEI PROFESSOR IRENE DIAS RIBEIRO"), ln=True, align='C')
        pdf.ln(5)

        # Cabeçalho do aluno (usando primeira ocorrência)
        aluno_nome = ocorrencias[0].get("aluno_nome", "Aluno Desconhecido")
        sala = ocorrencias[0].get("sala_id", "Indefinida")
        # CORREÇÃO: 'tutor' alterado para 'tutor_nome'
        tutor = ocorrencias[0].get("tutor_nome", "Indefinido") 
        
        # CORREÇÃO: Usando safe_pdf_text
        pdf.cell(0, 7, safe_pdf_text(f"Aluno: {aluno_nome}    Sala: {sala}"), ln=True)
        pdf.cell(0, 7, safe_pdf_text(f"Tutor: {tutor}"), ln=True)
        pdf.ln(5)

        for o in ocorrencias:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 7, safe_pdf_text(f"Ocorrência nº: {o.get('numero')}"), ln=True)
            
            pdf.set_font("Arial", "", 12)
            data_hora = o.get('data_hora', '')
            if data_hora:
                # O Supabase retorna a data no formato ISO com 'T' no meio, se não for formatado antes
                try:
                    dt = datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
                    data = dt.strftime("%d/%m/%Y")
                    hora = dt.strftime("%H:%M:%S")
                except:
                    data, hora = 'N/A', 'N/A'
            else:
                data, hora = '', ''
            
            # CORREÇÃO: Usando safe_pdf_text
            professor = o.get('atendimento_professor', '---')
            pdf.cell(0, 6, safe_pdf_text(f"Data: {data}    Hora: {hora}"), ln=True)
            pdf.cell(0, 6, safe_pdf_text(f"Professor: {professor}"), ln=True)
            
            # CORREÇÃO: Usando safe_pdf_text em multi_cell
            pdf.multi_cell(0, 6, safe_pdf_text(f"Descrição:\n{o.get('descricao', '')}"))
            
            # CORREÇÃO: Usando safe_pdf_text
            pdf.cell(0, 6, safe_pdf_text(f"Atendimento Professor:\n{o.get('atendimento_professor', '')}"), ln=True)
            pdf.cell(0, 6, safe_pdf_text(f"Atendimento Tutor (Se solicitado):\n{o.get('atendimento_tutor', '')}"), ln=True)
            pdf.cell(0, 6, safe_pdf_text(f"Atendimento Coordenação (Se solicitado):\n{o.get('atendimento_coordenacao', '')}"), ln=True)
            pdf.cell(0, 6, safe_pdf_text(f"Atendimento Gestão (Se solicitado):\n{o.get('atendimento_gestao', '')}"), ln=True)
            pdf.ln(3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # linha separadora
            pdf.ln(3)

        # Assinatura no final
        pdf.ln(10)
        pdf.cell(0, 10, safe_pdf_text("Assinatura Responsável: _______________________________"), ln=True)
        pdf.cell(0, 10, safe_pdf_text("Data: ___ / ___ / ______"), ln=True)

        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        # LÓGICA DE ATUALIZAÇÃO NO SUPABASE APÓS SUCESSO DO PDF
        if pdf_buffer.getbuffer().nbytes > 0:
            # Marcando 'impressao_pdf' como True para os números da ocorrência
            update_data = {"impressao_pdf": True}
            supabase.table('ocorrencias').update(update_data).in_('numero', numeros).execute()
            logging.info(f"Ocorrências {numeros} marcadas como impressas (impressao_pdf=True).")


        nome_arquivo = aluno_nome.replace(' ', '_') + "_ocorrencias.pdf"
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )

    except Exception as e:
        logging.exception("Falha ao gerar PDF ou atualizar status de impressão.")
        return jsonify({"error": f"Falha ao gerar PDF ou registrar impressão: {str(e)}"}), 500

@app.route('/api/tutores')
def get_tutores():
    try:
        data = supabase.table('tutores').select('id, nome').execute()
        return jsonify(data.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ficha_tutoria/<aluno_id>')
def get_ficha_tutoria(aluno_id):
    try:
        data = supabase.table('ficha_tutoria').select('*').eq('aluno_id', aluno_id).execute()
        if data.data:
            return jsonify(data.data[0])
        return jsonify({'error': 'Ficha não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Frequência
@app.route("/frequencia")
def frequencia():
    alunos = supabase_client.table("f_frequencia").select("*").execute().data
    return render_template("frequencia.html", alunos=alunos)

# Tutoria
@app.route("/tutoria")
def tutoria():
    tutores = supabase_client.table("f_tutoria").select("*").execute().data
    return render_template("tutoria.html", tutores=tutores)

# Ocorrências abertas
@app.route("/ocorrencias_abertas")
def ocorrencias_abertas():
    ocorrencias = supabase_client.table("f_ocorrencias").select("*").eq("status", "aberta").execute().data
    return render_template("ocorrencias_abertas.html", ocorrencias=ocorrencias)

# Editar ocorrência
@app.route("/ocorrencia_editar/<int:id>", methods=["GET", "POST"])
def ocorrencia_editar(id):
    if request.method == "POST":
        dados = request.form.to_dict()
        supabase_client.table("f_ocorrencias").update(dados).eq("id", id).execute()
        return redirect(url_for("ocorrencias_abertas"))
    else:
        ocorrencia = supabase_client.table("f_ocorrencias").select("*").eq("id", id).single().execute().data
        return render_template("ocorrencia_editar.html", ocorrencia=ocorrencia)

# API para frequência (JSON)
@app.route("/api/frequencia")
def api_frequencia():
    dados = supabase_client.table("f_frequencia").select("*").execute().data
    return jsonify(dados)

# API para tutoria (JSON)
@app.route("/api/tutoria")
def api_tutoria():
    dados = supabase_client.table("f_tutoria").select("*").execute().data
    return jsonify(dados)

# ----------------- FILTROS -----------------

@app.route("/filtrar_frequencia", methods=["POST"])
def filtrar_frequencia():
    filtros = request.json
    query = supabase_client.table("f_frequencia").select("*")
    if filtros.get("curso"):
        query = query.eq("curso", filtros["curso"])
    if filtros.get("turma"):
        query = query.eq("turma", filtros["turma"])
    if filtros.get("mes"):
        query = query.eq("mes", filtros["mes"])
    alunos = query.execute().data
    return jsonify(alunos)

@app.route("/filtrar_tutoria", methods=["POST"])
def filtrar_tutoria():
    filtros = request.json
    query = supabase_client.table("f_tutoria").select("*")
    if filtros.get("tutor"):
        query = query.eq("tutor", filtros["tutor"])
    if filtros.get("mes"):
        query = query.eq("mes", filtros["mes"])
    atendimentos = query.execute().data
    return jsonify(atendimentos)

        
# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))









