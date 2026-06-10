from abc import ABC, abstractmethod
from pathlib import Path
from django.conf import settings
import base64
import sys
from pathlib import Path

class PipelineStorage(ABC):
    """Abstração para armazenamento de scripts de pipelines"""
    
    @abstractmethod
    def save_script(self, pipeline_name: str, filename: str, content: str) -> None:
        """Salva um script na storage"""
        pass
    
    @abstractmethod
    def get_script(self, pipeline_name: str, filename: str) -> str:
        """Recupera um script da storage"""
        pass
    
    @abstractmethod
    def delete_pipeline(self, pipeline_name: str) -> None:
        """Deleta todos os scripts de uma pipeline"""
        pass

    @abstractmethod
    def rename_pipeline(self, old_pipeline_name: str, new_pipeline_name: str) -> None:
        """Renomeia a pasta base da pipeline"""
        pass

    @abstractmethod
    def save_config_file(self, pipeline_name: str, content: str) -> None:
        """Salva um arquivo de configuração na pipeline"""
        pass

    @abstractmethod
    def get_config_file(self, pipeline_name: str) -> str:
        """Recupera um arquivo de configuração da pipeline"""
        pass

    @abstractmethod
    def delete_config_file(self, pipeline_name: str) -> None:
        """Deleta o arquivo de configuração da pipeline"""
        pass

    @abstractmethod
    def config_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se um arquivo de configuração existe na pipeline"""
        pass


class LocalStorage(PipelineStorage):
    """Armazena scripts no filesystem local"""
    
    def __init__(self):
        self.base_path = Path(settings.BASE_DIR).parent / "etls"
    
    def _get_pipeline_dir(self, pipeline_name: str) -> Path:
        """Retorna o diretório da pipeline, validando o nome"""
        # Segurança: previne directory traversal e classes de caminho inválidas
        if ".." in pipeline_name or "/" in pipeline_name or "\\" in pipeline_name:
            raise ValueError(f"Nome inválido de pipeline: {pipeline_name}")
        
        return self.base_path / pipeline_name
    
    def save_script(self, pipeline_name: str, filename: str, content: str) -> None:
        """Salva um script no disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = pipeline_dir / filename
        file_path.write_text(content)
        # Cria o diretório quando necessário e grava o arquivo de forma simples

    def save_script_main_py(self, pipeline_name: str, filename: str, content: str) -> None:        
        """Salva um script no disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = pipeline_dir / filename
        file_path.write_text(content)

    def get_script(self, pipeline_name: str, filename: str) -> str:
        """Lê um script do disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        file_path = pipeline_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Script {filename} não encontrado em {pipeline_name}")
        
        return file_path.read_text()
    

    
    def delete_pipeline(self, pipeline_name: str) -> None:
        """Deleta a pasta da pipeline"""
        import shutil
        
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        if pipeline_dir.exists():
            shutil.rmtree(pipeline_dir)

    def rename_pipeline(self, old_pipeline_name: str, new_pipeline_name: str) -> None:
        """Renomeia a pasta da pipeline mantendo os arquivos existentes"""
        old_pipeline_dir = self._get_pipeline_dir(old_pipeline_name)
        new_pipeline_dir = self._get_pipeline_dir(new_pipeline_name)

        if not old_pipeline_dir.exists():
            raise FileNotFoundError(f"Pipeline {old_pipeline_name} nao encontrada")

        if new_pipeline_dir.exists() and old_pipeline_dir != new_pipeline_dir:
            raise FileExistsError(f"Ja existe uma pipeline com o nome {new_pipeline_name}")

        if old_pipeline_dir != new_pipeline_dir:
            old_pipeline_dir.rename(new_pipeline_dir)

    def save_env_file(self, pipeline_name: str, content: str) -> None:
        """Salva um arquivo .env na pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        env_file_path = pipeline_dir / ".env"
        env_file_path.write_text(content)

    def get_env_file(self, pipeline_name: str) -> str:
        """Recupera um arquivo .env da pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        env_file_path = pipeline_dir / ".env"
        
        if not env_file_path.exists():
            raise FileNotFoundError(f"Arquivo .env não encontrado em {pipeline_name}")
        
        return env_file_path.read_text()

    def delete_env_file(self, pipeline_name: str) -> None:
        """Deleta o arquivo .env da pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        env_file_path = pipeline_dir / ".env"
        
        if env_file_path.exists():
            env_file_path.unlink()

    def env_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se um arquivo .env existe na pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        env_file_path = pipeline_dir / ".env"
        return env_file_path.exists()

    def save_config_file(self, pipeline_name: str, content: str) -> None:
        """Salva um arquivo config.ini na pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        config_file_path = pipeline_dir / "config.ini"
        config_file_path.write_text(content)

    def get_config_file(self, pipeline_name: str) -> str:
        """Recupera um arquivo config.ini da pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        config_file_path = pipeline_dir / "config.ini"
        
        if not config_file_path.exists():
            raise FileNotFoundError(f"Arquivo config.ini não encontrado em {pipeline_name}")
        
        return config_file_path.read_text()

    def delete_config_file(self, pipeline_name: str) -> None:
        """Deleta o arquivo config.ini da pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        config_file_path = pipeline_dir / "config.ini"
        
        if config_file_path.exists():
            config_file_path.unlink()

    def config_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se um arquivo config.ini existe na pipeline"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        config_file_path = pipeline_dir / "config.ini"
        return config_file_path.exists()
