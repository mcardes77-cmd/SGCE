import os
import logging
import time
from typing import Optional
from supabase import create_client, Client

# Configuração de logging (apenas uma vez)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis de ambiente
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # ou SUPABASE_SERVICE_KEY
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

# Log das variáveis (sem mostrar valores sensíveis)
if not SUPABASE_URL:
    logger.warning("SUPABASE_URL não encontrada nas variáveis de ambiente.")
if not SUPABASE_KEY:
    logger.warning("SUPABASE_KEY não encontrada nas variáveis de ambiente.")
if not SUPABASE_ANON_KEY:
    logger.info("SUPABASE_ANON_KEY não definida.")

_supabase_client: Optional[Client] = None  # Use Client em vez de SupabaseClient

def _init_supabase_client(retries: int = 3, backoff: float = 1.0) -> Optional[Client]:
    global _supabase_client
    if _supabase_client:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Não é possível inicializar Supabase: SUPABASE_URL ou SUPABASE_KEY ausentes.")
        return None

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Tentando inicializar Supabase (tentativa {attempt}/{retries})...")
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Testa a conexão com uma consulta simples
            try:
                _supabase_client.table('professores').select('*').limit(1).execute()
                logger.info("Conexão Supabase inicializada e testada com sucesso.")
            except Exception as test_error:
                logger.warning(f"Conexão estabelecida, mas teste falhou: {test_error}")
            
            return _supabase_client
        except Exception as e:
            logger.error(f"Falha ao criar client Supabase (tentativa {attempt}): {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                logger.error("Não foi possível inicializar Supabase após várias tentativas.")
                return None

def get_supabase() -> Optional[Client]:
    """Retorna o cliente Supabase, inicializando-o se necessário."""
    return _init_supabase_client()

# Cria uma instância global para importação
supabase = get_supabase()

def handle_supabase_response(response):
    """Trata a resposta do Supabase, lançando exceção em caso de erro."""
    try:
        if response is None:
            raise Exception("Resposta Supabase é None.")
        if isinstance(response, dict):
            if response.get("error"):
                raise Exception(f"Erro Postgrest: {response['error']}")
            return response.get("data", response)
        if hasattr(response, "error") and response.error:
            raise Exception(f"Erro Postgrest: {response.error}")
        if hasattr(response, "data"):
            return response.data
        return response
    except Exception:
        logger.exception("Erro ao tratar resposta Supabase.")
        raise

# Exportações explícitas
__all__ = ['supabase', 'get_supabase', 'handle_supabase_response']
