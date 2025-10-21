# app.py
from flask import Flask, render_template, Blueprint
import os
import logging

# --- Importa Blueprints de API ---
from routes_frequencia import frequencia_bp
from routes_tutoria import tutoria_bp
from routes_cadastro import cadastro_bp
from routes_aulas import aulas_bp
from routes_ocorrencias import ocorrencias_bp

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
app.register_blueprint(frequencia_bp, url_prefix='/api')
app.register_blueprint(tutoria_bp, url_prefix='/api') 
app.register_blueprint(cadastro_bp, url_prefix='/api')
app.register_blueprint(aulas_bp, url_prefix='/api')
app.register_blueprint(ocorrencias_bp, url_prefix='/api')

# Registrar blueprints opcionais apenas se existirem
try:
    from routes_tecnologia import tecnologia_bp
    app.register_blueprint(tecnologia_bp, url_prefix='/api')
    logging.info("Blueprint de tecnologia registrado com sucesso")
except ImportError as e:
    logging.warning(f"Blueprint de tecnologia não encontrado: {e}")

try:
    from routes_vinculos_disciplinas import vinculos_bp
    app.register_blueprint(vinculos_bp, url_prefix='/api')
    logging.info("Blueprint de vínculos registrado com sucesso")
except ImportError as e:
    logging.warning(f"Blueprint de vínculos não encontrado: {e}")

# ===============================================
# ROTAS DE API BÁSICAS (TEMPORÁRIAS)
# ===============================================

@app.route('/api/funcionarios', methods=['GET'])
def api_get_funcionarios():
    """Busca todos os funcionários"""
    try:
        from db_utils import supabase, handle_supabase_response
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
        from db_utils import supabase, handle_supabase_response
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
        from db_utils import supabase, handle_supabase_response
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
        from db_utils import supabase, handle_supabase_response
        response = supabase.table('d_alunos').select('*').order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/alunos: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos: {str(e)}"}), 500

@app.route('/api/alunos/<int:aluno_id>', methods=['GET'])
def api_get_aluno(aluno_id):
    """Busca um aluno específico"""
    try:
        from db_utils import supabase, handle_supabase_response
        response = supabase.table('d_alunos').select('*').eq('id', aluno_id).single().execute()
        aluno = handle_supabase_response(response)
        return jsonify(aluno), 200
    except Exception as e:
        logging.error(f"Erro /api/alunos/<id>: {str(e)}")
        return jsonify({"error": f"Falha ao buscar aluno: {str(e)}"}), 500

@app.route('/api/tutores', methods=['GET'])
def api_get_tutores():
    """Busca apenas os funcionários que são tutores"""
    try:
        from db_utils import supabase, handle_supabase_response
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
        from db_utils import supabase, handle_supabase_response
        response = supabase.table('d_alunos').select('*').eq('sala_id', sala_id).order('nome').execute()
        alunos = handle_supabase_response(response)
        return jsonify(alunos), 200
    except Exception as e:
        logging.error(f"Erro /api/alunos_por_sala: {str(e)}")
        return jsonify({"error": f"Falha ao buscar alunos da sala: {str(e)}"}), 500

# ===============================================
# VARIÁVEL APP PARA GUNICORN
# ===============================================

# Esta variável 'app' é necessária para o Gunicorn
# O Gunicorn procura por 'app' quando executamos 'gunicorn --bind 0.0.0.0:$PORT "app:app"'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

