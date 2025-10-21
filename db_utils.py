import os
import logging
import time
import supabase
from typing import Optional
from supabase import create_client, Client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_ANON = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL:
    logger.warning("SUPABASE_URL não encontrada nas variáveis de ambiente.")
if not SUPABASE_KEY:
    logger.warning("SUPABASE_KEY (service role) não encontrada nas variáveis de ambiente.")
if not SUPABASE_ANON:
    logger.info("SUPABASE_ANON_KEY não definida.")

_supabase_client: Optional[SupabaseClient] = None

def _init_supabase_client(retries: int = 3, backoff: float = 1.0) -> Optional[SupabaseClient]:
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
            logger.info("Conexão Supabase inicializada com sucesso.")
            return _supabase_client
        except Exception as e:
            logger.exception(f"Falha ao criar client Supabase (tentativa {attempt}): {e}")
            time.sleep(backoff * attempt)

    logger.error("Não foi possível inicializar Supabase após várias tentativas.")
    return None

def get_supabase() -> Optional[SupabaseClient]:
    """Retorna o cliente Supabase, inicializando-o se necessário."""
    return _init_supabase_client()

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

