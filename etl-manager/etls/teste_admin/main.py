import sys

if __name__ == "__main__":
    run_id = sys.argv[1] if len(sys.argv) > 1 else "local_test"
    print(f"Hello World - Executando ETL teste_admin com run_id: {run_id}")
    # Adicione sua lógica ETL aqui
    print("ETL teste_admin concluída!")