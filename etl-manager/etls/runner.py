import sys
import os
import subprocess
from pathlib import Path

def executar_etl(etl_name, run_id):
    """
    Executa uma ETL executando seu main.py diretamente
    """
    # Define o caminho da ETL
    etl_dir = Path(__file__).parent / etl_name
    main_file = etl_dir / "main.py"
    
    if not main_file.exists():
        print(f" ETL não encontrada: {etl_name}")
        sys.exit(1)
    
    # Executa o script Python diretamente
    print(f" Executando ETL: {etl_name} (Run ID: {run_id})")
    try:
        # Se existir requirements.txt na pasta da ETL, instala dependências
        req_file = etl_dir / "requirements.txt"
        if req_file.exists():
            print(f" Instalando dependências de {req_file}")
            try:
                subprocess.run([
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "--upgrade",
                    "--force-reinstall",
                    "-r",
                    str(req_file),
                ], cwd=str(etl_dir), check=True)
            except subprocess.CalledProcessError as e:
                print(f" Falha ao instalar dependências: {e}", file=sys.stderr)
                sys.exit(1)

        result = subprocess.run(
            [sys.executable, str(main_file), run_id],
            cwd=str(etl_dir),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f" ETL {etl_name} falhou com código {result.returncode}")
            sys.exit(result.returncode)
        print(f" ETL {etl_name} finalizada com sucesso!")
        return {"status": "success"}
    except subprocess.TimeoutExpired:
        print(f" ETL {etl_name} expirou o tempo limite")
        sys.exit(1)
    except Exception as e:
        print(f" Erro ao executar ETL {etl_name}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python runner.py <etl_name> <run_id>")
        sys.exit(1)
    
    etl_name = sys.argv[1]
    run_id = sys.argv[2]
    
    executar_etl(etl_name, run_id)