import sys
import os
import importlib.util
from pathlib import Path

def executar_etl(etl_name, run_id):
    """
    Carrega e executa uma ETL dinamicamente
    """
    # Define o caminho da ETL
    etl_dir = Path(__file__).parent / etl_name
    main_file = etl_dir / "main.py"
    
    if not main_file.exists():
        print(f" ETL não encontrada: {etl_name}")
        sys.exit(1)
    
    # Adiciona a pasta da ETL ao path
    sys.path.insert(0, str(etl_dir))
    
    # Importa o módulo dinamicamente
    spec = importlib.util.spec_from_file_location("etl_main", main_file)
    etl_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(etl_module)
    
    # Executa a função principal da ETL
    print(f" Executando ETL: {etl_name} (Run ID: {run_id})")
    resultado = etl_module.executar_etl_vendas(run_id)  # ou o nome da função
    print(f"✅ ETL {etl_name} finalizada com sucesso!")
    
    return resultado


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python runner.py <etl_name> <run_id>")
        sys.exit(1)
    
    etl_name = sys.argv[1]
    run_id = sys.argv[2]
    
    executar_etl(etl_name, run_id)