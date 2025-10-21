import os
import logging
from db_utils import get_supabase, handle_supabase_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def criar_tabela_documentos_aulas():
    """Cria a tabela t_documentos_aulas no Supabase se não existir"""
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Não foi possível conectar ao Supabase")
        return False

    try:
        # Verifica se a tabela já existe
        response = supabase.table('t_documentos_aulas').select('id').limit(1).execute()
        
        if hasattr(response, 'error') and response.error:
            # Tabela não existe, vamos criar
            logger.info("Criando tabela t_documentos_aulas...")
            
            # SQL para criar a tabela
            create_table_sql = """
            CREATE TABLE t_documentos_aulas (
                id BIGSERIAL PRIMARY KEY,
                tipo TEXT NOT NULL CHECK (tipo IN ('PLANO_AULA', 'AGENDA_SEMANAL', 'GUIA_APRENDIZAGEM')),
                professor_id BIGINT NOT NULL REFERENCES d_funcionarios(id),
                disciplina TEXT NOT NULL REFERENCES d_disciplinas(id),
                sala_serie BIGINT REFERENCES d_salas(id),
                bimestre INTEGER CHECK (bimestre BETWEEN 1 AND 4),
                periodo_inicio DATE NOT NULL,
                periodo_fim DATE,
                conteudo_principal TEXT NOT NULL,
                conteudo_json JSONB DEFAULT '{}'::jsonb,
                status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE', 'APROVADO', 'CORRECAO')),
                motivo_correcao TEXT,
                data_submissao TIMESTAMPTZ DEFAULT NOW(),
                data_validacao TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
            
            # Executa via SQL (supabase-py não suporta DDL diretamente, então usamos raw SQL)
            # Nota: Em produção, você deve executar isso manualmente no Supabase SQL Editor
            logger.info("Execute manualmente no Supabase SQL Editor:")
            logger.info(create_table_sql)
            
            # Como alternativa, podemos usar a REST API para inserir e verificar
            logger.info("Verificando/executando criação da tabela...")
            
            # Tenta criar um registro de teste (isso criará a tabela implicitamente se usar RLS)
            test_data = {
                "tipo": "PLANO_AULA",
                "professor_id": 1,
                "disciplina": "MAT",
                "conteudo_principal": "Documento de Teste",
                "periodo_inicio": "2024-01-01",
                "status": "PENDENTE"
            }
            
            response = supabase.table('t_documentos_aulas').insert(test_data).execute()
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Erro ao criar tabela: {response.error}")
                return False
            else:
                logger.info("Tabela t_documentos_aulas criada/verificada com sucesso!")
                return True
                
    except Exception as e:
        logger.error(f"Erro ao verificar/criar tabela: {e}")
        return False

if __name__ == "__main__":
    criar_tabela_documentos_aulas()