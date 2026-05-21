import sys
import time
from datetime import datetime


def executar_etl_vendas(run_id):
    """
    Simula uma ETL de extração de vendas
    """
    print(f"[{datetime.now()}] Iniciando ETL Vendas - Run ID: {run_id}")
    
    # Extração
    print("📥 Extraindo dados de vendas...")
    time.sleep(2)
    dados = [
        {"id": 1, "valor": 100.00},
        {"id": 2, "valor": 250.50},
    ]
    


    # Transformação
    print("🔄 Transformando dados...")
    time.sleep(2)
    dados_transformados = [
        {"id": d["id"], "valor": d["valor"] * 1.1}  # aplica 10%
        for d in dados
    ]
    

    # Carregamento (salva em arquivo, banco, API, etc)
    print("💾 Carregando dados...")
    time.sleep(1)
    
    print(f"✅ ETL Vendas concluída para run {run_id}")
    print(f"Total de registros: {len(dados_transformados)}")
    
    return {"status": "success", "records": len(dados_transformados)}


if __name__ == "__main__":
    run_id = sys.argv[1] if len(sys.argv) > 1 else "local_test"
    resultado = executar_etl_vendas(run_id)
    print(f"\nResultado: {resultado}")
    print("funcionando")


# teste 1

# MUDEI ISSO AGORA