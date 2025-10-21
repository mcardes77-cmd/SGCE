# app.py
from flask import Flask, render_template, Blueprint, jsonify
import os
import logging
from db_utils import supabase, handle_supabase_response
from datetime import datetime, timedelta

# Configuração
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
logging.basicConfig(level=logging.INFO)

# --- 1. Definição do Blueprint Principal ---
main_bp = Blueprint('main', __name__)

# ===============================================
# ROTAS PRINCIPAIS
# ===============================================

@main_bp.route('/')
def home():
    return render_template('index.html')

# ===============================================
# MÓDULO DE FREQUÊNCIA
# ===============================================

@main_bp.route('/gestao_frequencia')
def gestao_frequencia():
    return render_template('gestao_frequencia.html')

@main_bp.route('/gestao_frequencia_registro')
def gestao_frequencia_registro():
    return render_template('gestao_frequencia_registro.html')

@main_bp.route('/gestao_frequencia_atraso')
def gestao_frequencia_atraso():
    return render_template('gestao_frequencia_atraso.html')

@main_bp.route('/gestao_frequencia_saida')
def gestao_frequencia_saida():
    return render_template('gestao_frequencia_saida.html')

@main_bp.route('/gestao_relatorio_frequencia')
def gestao_relatorio_frequencia():
    return render_template('gestao_relatorio_frequencia.html')

# ===============================================
# MÓDULO DE TUTORIA
# ===============================================

@main_bp.route('/gestao_tutoria')
def gestao_tutoria():
    return render_template('gestao_tutoria.html')

@main_bp.route('/gestao_tutoria_ficha')
def gestao_tutoria_ficha():
    return render_template('gestao_tutoria_ficha.html')

@main_bp.route('/gestao_tutoria_agendamento')
def gestao_tutoria_agendamento():
    return render_template('gestao_tutoria_agendamento.html')

@main_bp.route('/gestao_tutoria_registro')
def gestao_tutoria_registro():
    return render_template('gestao_tutoria_registro.html')

@main_bp.route('/gestao_tutoria_notas')
def gestao_tutoria_notas():
    return render_template('gestao_tutoria_notas.html')

@main_bp.route('/gestao_relatorio_tutoria')
def gestao_relatorio_tutoria():
    return render_template('gestao_relatorio_tutoria.html')

# ===============================================
# MÓDULO DE CADASTRO
# ===============================================

@main_bp.route('/gestao_cadastro')
def gestao_cadastro():
    return render_template('gestao_cadastro.html')

@main_bp.route('/gestao_cadastro_professor_funcionario')
def gestao_cadastro_professor_funcionario():
    return render_template('gestao_cadastro_professor_funcionario.html')

@main_bp.route('/gestao_cadastro_aluno')
def gestao_cadastro_aluno():
    return render_template('gestao_cadastro_aluno.html')

@main_bp.route('/gestao_cadastro_tutor')
def gestao_cadastro_tutor():
    return render_template('gestao_cadastro_tutor.html')

@main_bp.route('/gestao_cadastro_sala')
def gestao_cadastro_sala():
    return render_template('gestao_cadastro_sala.html')

@main_bp.route('/gestao_cadastro_disciplinas')
def gestao_cadastro_disciplinas():
    return render_template('gestao_cadastro_disciplinas.html')

@main_bp.route('/gestao_cadastro_eletiva')
def gestao_cadastro_eletiva():
    return render_template('gestao_cadastro_eletiva.html')

@main_bp.route('/gestao_cadastro_clube')
def gestao_cadastro_clube():
    return render_template('gestao_cadastro_clube.html')

@main_bp.route('/gestao_cadastro_equipamento')
def gestao_cadastro_equipamento():
    return render_template('gestao_cadastro_equipamento.html')

@main_bp.route('/gestao_cadastro_vinculacao_tutor_aluno')
def gestao_cadastro_vinculacao_tutor_aluno():
    return render_template('gestao_cadastro_vinculacao_tutor_aluno.html')

@main_bp.route('/gestao_cadastro_vinculacao_disciplina_sala')
def gestao_cadastro_vinculacao_disciplina_sala():
    return render_template('gestao_cadastro_vinculacao_disciplina_sala.html')

# ===============================================
# MÓDULO DE AULAS
# ===============================================

@main_bp.route('/gestao_aulas')
def gestao_aulas():
    return render_template('gestao_aulas.html')

@main_bp.route('/gestao_aulas_plano')
def gestao_aulas_plano():
    return render_template('gestao_aulas_plano.html')

@main_bp.route('/gestao_aulas_guia')
def gestao_aulas_guia():
    return render_template('gestao_aulas_guia.html')

@main_bp.route('/gestao_validacao_documentos')
def gestao_validacao_documentos():
    return render_template('gestao_validacao_documentos.html')

# ===============================================
# MÓDULO DE OCORRÊNCIAS
# ===============================================

@main_bp.route('/gestao_ocorrencia')
def gestao_ocorrencia():
    return render_template('gestao_ocorrencia.html')

@main_bp.route('/gestao_ocorrencia_nova')
def gestao_ocorrencia_nova():
    return render_template('gestao_ocorrencia_nova.html')

@main_bp.route('/gestao_ocorrencia_abertas')
def gestao_ocorrencia_abertas():
    return render_template('gestao_ocorrencia_aberta.html')

@main_bp.route('/gestao_ocorrencia_finalizadas')
def gestao_ocorrencia_finalizadas():
    return render_template('gestao_ocorrencia_finalizada.html')

@main_bp.route('/gestao_ocorrencia_editar')
def gestao_ocorrencia_editar():
    return render_template('gestao_ocorrencia_editar.html')

@main_bp.route('/gestao_relatorio_impressao')
def gestao_relatorio_impressao():
    return render_template('gestao_relatorio_impressao.html')

# ===============================================
# MÓDULO DE TECNOLOGIA
# ===============================================

@main_bp.route('/gestao_tecnologia')
def gestao_tecnologia():
    return render_template('gestao_tecnologia.html')

@main_bp.route('/gestao_tecnologia_agendamento')
def gestao_tecnologia_agendamento():
    return render_template('gestao_tecnologia_agendamento.html')

@main_bp.route('/gestao_tecnologia_historico')
def gestao_tecnologia_historico():
    return render_template('gestao_tecnologia_historico.html')

@main_bp.route('/gestao_tecnologia_ocorrencia')
def gestao_tecnologia_ocorrencia():
    return render_template('gestao_tecnologia_ocorrencia.html')

# ===============================================
# ROTAS DE REDIRECIONAMENTO (PARA INDEX.HTML)
# ===============================================

@main_bp.route('/gestao_aulas_menu')
def gestao_aulas_menu():
    """Rota corrigida para o botão 'GESTÃO DE AULAS'"""
    return render_template('gestao_aulas.html')

# ===============================================
# REGISTRO DOS BLUEPRINTS
# ===============================================

app.register_blueprint(main_bp, url_prefix='/')

# Registrar blueprints que funcionam
try:
    from routes_frequencia import frequencia_bp
    app.register_blueprint(frequencia_bp, url_prefix='/api')
    logging.info("Blueprint de frequência registrado com sucesso")
except ImportError as e:
    logging.warning(f"Blueprint de frequência não encontrado: {e}")

try:
    from routes_tutoria import tutoria_bp
    app.register_blueprint(tutoria_bp, url_prefix='/api')
    logging.info("Blueprint de tutoria registrado com sucesso")
except ImportError as e:
    logging.warning(f"Blueprint de tutoria não encontrado: {e}")

try:
    from routes_aulas import aulas_bp
    app.register_blueprint(aulas_bp, url_prefix='/api')
    logging.info("Blueprint de aulas registrado com sucesso")
except ImportError as e:
    logging.warning(f"Blueprint de aulas não encontrado: {e}")

try:
    from routes_ocorrencias import ocorrencias_bp
    app.register_blueprint(ocorrencias_bp, url_prefix='/api')
    logging.info("Blueprint de ocorrências registrado com sucesso")
except ImportError as e:
    logging.warning(f"Blueprint de ocorrências não encontrado: {e}")

try:
    from routes_tecnologia import tecnologia_bp
    app.register_blueprint(tecnologia_bp, url_prefix='/api')
    logging.info("Blueprint de tecnologia registrado com sucesso")
except ImportError as e:
    logging.warning(f"Blueprint de tecnologia não encontrado: {e}")

# NÃO registrar blueprint problemático de cadastro
# from routes_cadastro import cadastro_bp
# app.register_blueprint(cadastro_bp, url_prefix='/api')

# ===============================================
# ROTAS DE API DIRETAS (SUBSTITUEM O BLUEPRINT PROBLEMÁTICO)
# ===============================================

@app.route('/api/funcionarios', methods=['GET'])
def api_get_funcionarios():
    """Busca todos os funcionários"""
    try:
        response = supabase.table('d_funcionarios').select('*').order('nome').execute()
        funcionarios = handle_supabase_response(response)
        return jsonify(funcionarios), 200
    except Exception as e:
        logging.error(f"Erro /api/funcionarios: {str(e)}")
        return jsonify({"error": f"Falha ao buscar funcionários: {str(e)}"}), 500

@app.route('/api/salas', methods=['GET'])
def api_get_salas():
    """Busca todas as salas"""
    try:
        response = supabase.table('d_salas').select('*').order('sala').execute()
        salas = handle_supabase_response(response)
        return jsonify(salas), 200
    except Exception as e:
        logging.error(f"Erro /api/salas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500

@app.route('/api/disciplinas', methods=['GET'])
def api_get_disciplinas():
    """Busca todas as disciplinas"""
    try:
        response = supabase.table('d_disciplinas').select('*').order('nome').execute()
        disciplinas = handle_supabase_response(response)
        return jsonify(disciplinas), 200
    except Exception as e:
        logging.error(f"Erro /api/disciplinas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar disciplinas: {str(e)}"}), 500

@app.route('/api/alunos', methods=['GET'])
def api_get_alunos():
    """Busca todos os alunos"""
    try:
        response = supabase.table('d_alunos').select('*').order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/alunos: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500

@app.route('/api/tutores', methods=['GET'])
def api_get_tutores():
    """Busca apenas os funcionários que são tutores"""
    try:
        response = supabase.table('d_funcionarios').select('*').eq('is_tutor', True).order('nome').execute()
        tutores = handle_supabase_response(response)
        return jsonify(tutores), 200
    except Exception as e:
        logging.error(f"Erro /api/tutores: {str(e)}")
        return jsonify({"error": f"Falha ao buscar tutores: {str(e)}"}), 500

@app.route('/api/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala(sala_id):
    """Busca alunos por sala"""
    try:
        response = supabase.table('d_alunos').select('*').eq('sala_id', sala_id).order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/alunos_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos da sala: {str(e)}"}), 500

@app.route('/api/ocorrencias', methods=['GET'])
def api_get_ocorrencias():
    """Busca todas as ocorrências"""
    try:
        response = supabase.table('ocorrencias').select(
            '*, aluno_id:d_alunos(nome), tutor_id:d_funcionarios(nome), professor_id:d_funcionarios(nome), sala_id:d_salas(sala)'
        ).order('data_hora', desc=True).execute()
        
        ocorrencias = handle_supabase_response(response)
        return jsonify(ocorrencias), 200
        
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500

@app.route('/api/ocorrencias', methods=['POST'])
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
            "status": "AGUARDANDO ATENDIMENTO",
            "data_hora": datetime.now().isoformat()
        }
        
        response = supabase.table('ocorrencias').insert(ocorrencia_data).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": "Ocorrência criada com sucesso",
            "numero": proximo_numero
        }), 201

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias POST: {str(e)}")
        return jsonify({"error": f"Falha ao criar ocorrência: {str(e)}"}), 500

@app.route('/api/ocorrencias/tipos', methods=['GET'])
def api_get_tipos_ocorrencia():
    """Retorna os tipos de ocorrência"""
    tipos = [
        {"value": "COMPORTAMENTO", "label": "Comportamento"},
        {"value": "DESEMPENHO", "label": "Desempenho Acadêmico"},
        {"value": "FREQUENCIA", "label": "Frequência"},
        {"value": "OUTROS", "label": "Outros"}
    ]
    return jsonify(tipos), 200

# ===============================================
# VARIÁVEL APP PARA GUNICORN
# ===============================================

# =========================================================
# ROTAS DE API PARA OCORRÊNCIAS (COMPLETAS)
# =========================================================

from datetime import datetime

# 1. APIs para Formulário de Nova Ocorrência
@app.route('/api/ocorrencias/salas', methods=['GET'])
def api_get_salas_ocorrencias():
    """Busca salas para o formulário de ocorrências"""
    try:
        response = supabase.table('d_salas').select('id, sala').order('sala').execute()
        salas = handle_supabase_response(response)
        return jsonify(salas), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/salas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar salas: {str(e)}"}), 500

@app.route('/api/ocorrencias/alunos', methods=['GET'])
def api_get_alunos_ocorrencias():
    """Busca todos os alunos para ocorrências"""
    try:
        response = supabase.table('d_alunos').select('id, nome, sala_id').order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/alunos: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500

@app.route('/api/ocorrencias/alunos_por_sala/<int:sala_id>', methods=['GET'])
def api_get_alunos_por_sala_ocorrencias(sala_id):
    """Busca alunos por sala específica"""
    try:
        response = supabase.table('d_alunos').select('id, nome, tutor_id').eq('sala_id', sala_id).order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/alunos_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos da sala: {str(e)}"}), 500

@app.route('/api/ocorrencias/tutores', methods=['GET'])
def api_get_tutores_ocorrencias():
    """Busca tutores para ocorrências"""
    try:
        response = supabase.table('d_funcionarios').select('id, nome').eq('is_tutor', True).order('nome').execute()
        tutores = handle_supabase_response(response)
        return jsonify(tutores), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/tutores: {str(e)}")
        return jsonify({"error": f"Falha ao buscar tutores: {str(e)}"}), 500

@app.route('/api/ocorrencias/professores', methods=['GET'])
def api_get_professores_ocorrencias():
    """Busca professores para ocorrências"""
    try:
        response = supabase.table('d_funcionarios').select('id, nome').order('nome').execute()
        professores = handle_supabase_response(response)
        return jsonify(professores), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/professores: {str(e)}")
        return jsonify({"error": f"Falha ao buscar professores: {str(e)}"}), 500

# 2. APIs para Listagem de Ocorrências
@app.route('/api/ocorrencias', methods=['GET'])
def api_get_ocorrencias():
    """Busca todas as ocorrências"""
    try:
        response = supabase.table('ocorrencias').select('*').order('data_hora', desc=True).execute()
        ocorrencias = handle_supabase_response(response)
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências: {str(e)}"}), 500

@app.route('/api/ocorrencias/abertas', methods=['GET'])
def api_get_ocorrencias_abertas():
    """Busca ocorrências em aberto"""
    try:
        response = supabase.table('ocorrencias').select('*').in_('status', ['AGUARDANDO ATENDIMENTO', 'EM ANDAMENTO']).order('data_hora', desc=True).execute()
        ocorrencias = handle_supabase_response(response)
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/abertas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências abertas: {str(e)}"}), 500

@app.route('/api/ocorrencias/finalizadas', methods=['GET'])
def api_get_ocorrencias_finalizadas():
    """Busca ocorrências finalizadas"""
    try:
        response = supabase.table('ocorrencias').select('*').eq('status', 'FINALIZADA').order('data_hora', desc=True).execute()
        ocorrencias = handle_supabase_response(response)
        return jsonify(ocorrencias), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias/finalizadas: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrências finalizadas: {str(e)}"}), 500

# 3. API para Criar Nova Ocorrência
@app.route('/api/ocorrencias', methods=['POST'])
def api_criar_ocorrencia():
    """Cria uma nova ocorrência"""
    data = request.json
    
    required_fields = ['descricao', 'aluno_id', 'tipo']
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
            "status": "AGUARDANDO ATENDIMENTO",
            "assinada": "NÃO",
            "data_hora": datetime.now().isoformat()
        }
        
        response = supabase.table('ocorrencias').insert(ocorrencia_data).execute()
        result = handle_supabase_response(response)
        
        return jsonify({
            "message": "Ocorrência criada com sucesso",
            "numero": proximo_numero
        }), 201

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias POST: {str(e)}")
        return jsonify({"error": f"Falha ao criar ocorrência: {str(e)}"}), 500

# 4. API para Atualizar Ocorrência
@app.route('/api/ocorrencias/<int:ocorrencia_numero>', methods=['PUT'])
def api_atualizar_ocorrencia(ocorrencia_numero):
    """Atualiza uma ocorrência existente"""
    data = request.json
    
    try:
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
        handle_supabase_response(response)
        
        return jsonify({"message": "Ocorrência atualizada com sucesso"}), 200

    except Exception as e:
        logging.error(f"Erro /api/ocorrencias PUT: {str(e)}")
        return jsonify({"error": f"Falha ao atualizar ocorrência: {str(e)}"}), 500

# 5. API para Buscar Ocorrência Específica
@app.route('/api/ocorrencias/<int:ocorrencia_numero>', methods=['GET'])
def api_get_ocorrencia(ocorrencia_numero):
    """Busca uma ocorrência específica"""
    try:
        response = supabase.table('ocorrencias').select('*').eq('numero', ocorrencia_numero).single().execute()
        ocorrencia = handle_supabase_response(response)
        return jsonify(ocorrencia), 200
    except Exception as e:
        logging.error(f"Erro /api/ocorrencias GET: {str(e)}")
        return jsonify({"error": f"Falha ao buscar ocorrência: {str(e)}"}), 500

# 6. APIs para Dados Auxiliares
@app.route('/api/ocorrencias/tipos', methods=['GET'])
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

@app.route('/api/ocorrencias/status', methods=['GET'])
def api_get_status_ocorrencia():
    """Retorna os status disponíveis"""
    status = [
        {"value": "AGUARDANDO ATENDIMENTO", "label": "Aguardando Atendimento"},
        {"value": "EM ANDAMENTO", "label": "Em Andamento"},
        {"value": "FINALIZADA", "label": "Finalizada"}
    ]
    return jsonify(status), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)



