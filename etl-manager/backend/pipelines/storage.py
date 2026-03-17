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


class LocalStorage(PipelineStorage):
    """Armazena scripts no filesystem local"""
    
    def __init__(self):
        self.base_path = Path(settings.BASE_DIR).parent / "etls"
    
    def _get_pipeline_dir(self, pipeline_name: str) -> Path:
        """Retorna o diretório da pipeline, validando o nome"""
        # Segurança: previne directory traversal
        if ".." in pipeline_name or "/" in pipeline_name or "\\" in pipeline_name:
            raise ValueError(f"Nome inválido de pipeline: {pipeline_name}")
        
        return self.base_path / pipeline_name
    
    def save_script(self, pipeline_name: str, filename: str, content: str) -> None:
        """Salva um script no disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = pipeline_dir / filename
        file_path.write_text(content)

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