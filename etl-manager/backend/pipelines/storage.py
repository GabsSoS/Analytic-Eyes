from abc import ABC, abstractmethod
from pathlib import Path
from django.conf import settings
import base64
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def _validate_pipeline_name(pipeline_name: str) -> None:
    """Previne directory traversal e nomes de pipeline invalidos"""
    if ".." in pipeline_name or "/" in pipeline_name or "\\" in pipeline_name:
        raise ValueError(f"Nome inválido de pipeline: {pipeline_name}")


# Nome base fixo do arquivo de dados de entrada (ex.: planilha) que o script da
# pipeline processa. A extensao original do upload e preservada (input.xlsx,
# input.csv, ...) para que bibliotecas como pandas escolham o parser certo;
# um novo upload sempre substitui o arquivo anterior, mesmo com extensao diferente.
INPUT_FILE_BASENAME = "input"

# Nome base fixo do arquivo de saida (ex.: output.xlsx) que o script da pipeline
# pode gravar no seu proprio diretorio de trabalho. Mesma logica do arquivo de
# entrada: extensao livre, um unico arquivo por pipeline, sempre substituido a
# cada execucao (ver sync_output_from_local).
OUTPUT_FILE_BASENAME = "output"


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

    @abstractmethod
    def save_input_file(self, pipeline_name: str, filename: str, content: bytes) -> str:
        """Salva o arquivo de dados (ex.: planilha) que o script da pipeline vai
        processar, substituindo qualquer arquivo de dados anterior. Retorna o
        nome final salvo (ex.: 'input.xlsx')"""
        pass

    @abstractmethod
    def get_input_file_name(self, pipeline_name: str) -> str | None:
        """Retorna o nome do arquivo de dados atual da pipeline, ou None se
        nenhum arquivo foi enviado ainda"""
        pass

    @abstractmethod
    def delete_input_file(self, pipeline_name: str) -> None:
        """Remove o arquivo de dados da pipeline, se existir"""
        pass

    @abstractmethod
    def input_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se a pipeline possui um arquivo de dados enviado"""
        pass

    @abstractmethod
    def get_output_file_name(self, pipeline_name: str) -> str | None:
        """Retorna o nome do arquivo de saida gerado pela ultima execucao
        bem-sucedida, ou None se nenhuma execucao gerou saida"""
        pass

    @abstractmethod
    def get_output_file_bytes(self, pipeline_name: str) -> bytes:
        """Le o conteudo binario do arquivo de saida atual"""
        pass

    @abstractmethod
    def save_output_file(self, pipeline_name: str, filename: str, content: bytes) -> str:
        """Persiste o arquivo de saida na storage, substituindo o anterior.
        Retorna o nome final salvo (ex.: 'output.xlsx')"""
        pass

    @abstractmethod
    def delete_output_file(self, pipeline_name: str) -> None:
        """Remove o arquivo de saida da pipeline, se existir"""
        pass

    @abstractmethod
    def sync_output_from_local(self, pipeline_name: str, local_dir: Path) -> str | None:
        """Depois que o container termina, garante que o arquivo de saida
        (output.*) que o script tenha gravado em local_dir fique persistido na
        storage. Retorna o nome do arquivo encontrado, ou None se o script nao
        gerou nenhuma saida nesta execucao"""
        pass

    @abstractmethod
    def sync_to_local(self, pipeline_name: str, local_dir: Path) -> None:
        """Garante que os arquivos da pipeline existam em local_dir no disco local
        (usado antes de executar a ETL em um container, que só lê do disco)"""
        pass

    @abstractmethod
    def cleanup_local(self, pipeline_name: str, local_dir: Path) -> None:
        """Remove local_dir se ele for apenas uma cópia temporária criada por
        sync_to_local (não deve remover nada quando local_dir É a storage real)"""
        pass


class LocalStorage(PipelineStorage):
    """Armazena scripts no filesystem local"""

    def __init__(self):
        self.base_path = Path(settings.BASE_DIR).parent / "etls"

    def _get_pipeline_dir(self, pipeline_name: str) -> Path:
        """Retorna o diretório da pipeline, validando o nome"""
        # Segurança: previne directory traversal e classes de caminho inválidas
        _validate_pipeline_name(pipeline_name)

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

    def save_input_file(self, pipeline_name: str, filename: str, content: bytes) -> str:
        """Salva o arquivo de dados no disco local, substituindo o anterior"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)

        self.delete_input_file(pipeline_name)

        extension = Path(filename).suffix.lower()
        saved_name = f"{INPUT_FILE_BASENAME}{extension}"
        (pipeline_dir / saved_name).write_bytes(content)
        return saved_name

    def get_input_file_name(self, pipeline_name: str) -> str | None:
        """Encontra o arquivo de dados atual (input.*) no disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        if not pipeline_dir.exists():
            return None

        matches = sorted(pipeline_dir.glob(f"{INPUT_FILE_BASENAME}.*"))
        return matches[0].name if matches else None

    def delete_input_file(self, pipeline_name: str) -> None:
        """Remove o arquivo de dados (input.*) do disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        if not pipeline_dir.exists():
            return

        for match in pipeline_dir.glob(f"{INPUT_FILE_BASENAME}.*"):
            match.unlink()

    def input_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se existe um arquivo de dados (input.*) no disco local"""
        return self.get_input_file_name(pipeline_name) is not None

    def get_output_file_name(self, pipeline_name: str) -> str | None:
        """Encontra o arquivo de saida atual (output.*) no disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        if not pipeline_dir.exists():
            return None

        matches = sorted(pipeline_dir.glob(f"{OUTPUT_FILE_BASENAME}.*"))
        return matches[0].name if matches else None

    def get_output_file_bytes(self, pipeline_name: str) -> bytes:
        """Le o conteudo binario do arquivo de saida atual"""
        output_name = self.get_output_file_name(pipeline_name)
        if not output_name:
            raise FileNotFoundError(f"Nenhum arquivo de saida encontrado para {pipeline_name}")

        return (self._get_pipeline_dir(pipeline_name) / output_name).read_bytes()

    def save_output_file(self, pipeline_name: str, filename: str, content: bytes) -> str:
        """Salva o arquivo de saida no disco local, substituindo o anterior"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        pipeline_dir.mkdir(parents=True, exist_ok=True)

        self.delete_output_file(pipeline_name)

        extension = Path(filename).suffix.lower()
        saved_name = f"{OUTPUT_FILE_BASENAME}{extension}"
        (pipeline_dir / saved_name).write_bytes(content)
        return saved_name

    def delete_output_file(self, pipeline_name: str) -> None:
        """Remove o arquivo de saida (output.*) do disco local"""
        pipeline_dir = self._get_pipeline_dir(pipeline_name)
        if not pipeline_dir.exists():
            return

        for match in pipeline_dir.glob(f"{OUTPUT_FILE_BASENAME}.*"):
            match.unlink()

    def sync_output_from_local(self, pipeline_name: str, local_dir: Path) -> str | None:
        """local_dir JA E a storage real; so identifica o que o script gravou"""
        return self.get_output_file_name(pipeline_name)

    def sync_to_local(self, pipeline_name: str, local_dir: Path) -> None:
        """Os arquivos já residem no disco local; nada a fazer"""
        pass

    def cleanup_local(self, pipeline_name: str, local_dir: Path) -> None:
        """local_dir É a storage real (não uma cópia); nunca remover"""
        pass


class S3Storage(PipelineStorage):
    """Armazena scripts de pipelines em um bucket S3 da AWS"""

    def __init__(self):
        self.bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        if not self.bucket:
            raise ValueError(
                "AWS_STORAGE_BUCKET_NAME não configurado para uso do S3Storage"
            )

        self.prefix = getattr(settings, "PIPELINE_S3_PREFIX", "etls").strip("/")

        client_kwargs = {
            "region_name": getattr(settings, "AWS_S3_REGION_NAME", None) or None,
        }

        endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        session_token = getattr(settings, "AWS_SESSION_TOKEN", None)
        if access_key and secret_key:
            client_kwargs["aws_access_key_id"] = access_key
            client_kwargs["aws_secret_access_key"] = secret_key
            if session_token:
                client_kwargs["aws_session_token"] = session_token
        # Sem credenciais explícitas, o boto3 recorre à cadeia padrão de
        # credenciais (variáveis de ambiente, ~/.aws/credentials, IAM role, etc.)

        self.client = boto3.client("s3", **client_kwargs)

    def _pipeline_prefix(self, pipeline_name: str) -> str:
        _validate_pipeline_name(pipeline_name)
        return f"{self.prefix}/{pipeline_name}/" if self.prefix else f"{pipeline_name}/"

    def _get_key(self, pipeline_name: str, filename: str) -> str:
        return f"{self._pipeline_prefix(pipeline_name)}{filename}"

    def _object_exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise

    def _read_object(self, key: str, not_found_message: str) -> str:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                raise FileNotFoundError(not_found_message) from exc
            raise

        return response["Body"].read().decode("utf-8")

    def _write_object(self, key: str, content: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content.encode("utf-8"))

    def _delete_object_if_exists(self, key: str) -> None:
        if self._object_exists(key):
            self.client.delete_object(Bucket=self.bucket, Key=key)

    def _list_pipeline_keys(self, pipeline_name: str) -> list:
        prefix = self._pipeline_prefix(pipeline_name)
        keys = []

        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])

        return keys

    def save_script(self, pipeline_name: str, filename: str, content: str) -> None:
        """Salva um script no bucket S3"""
        self._write_object(self._get_key(pipeline_name, filename), content)

    def save_script_main_py(self, pipeline_name: str, filename: str, content: str) -> None:
        """Salva um script no bucket S3"""
        self.save_script(pipeline_name, filename, content)

    def get_script(self, pipeline_name: str, filename: str) -> str:
        """Lê um script do bucket S3"""
        key = self._get_key(pipeline_name, filename)
        return self._read_object(key, f"Script {filename} não encontrado em {pipeline_name}")

    def delete_pipeline(self, pipeline_name: str) -> None:
        """Deleta todos os objetos da pipeline no bucket S3"""
        keys = self._list_pipeline_keys(pipeline_name)
        if not keys:
            return

        # delete_objects aceita no máximo 1000 chaves por chamada
        for start in range(0, len(keys), 1000):
            batch = keys[start:start + 1000]
            self.client.delete_objects(
                Bucket=self.bucket,
                Delete={"Objects": [{"Key": key} for key in batch]},
            )

    def rename_pipeline(self, old_pipeline_name: str, new_pipeline_name: str) -> None:
        """Renomeia o prefixo da pipeline copiando e removendo os objetos antigos"""
        old_prefix = self._pipeline_prefix(old_pipeline_name)
        new_prefix = self._pipeline_prefix(new_pipeline_name)

        if old_prefix == new_prefix:
            return

        old_keys = self._list_pipeline_keys(old_pipeline_name)
        if not old_keys:
            raise FileNotFoundError(f"Pipeline {old_pipeline_name} nao encontrada")

        if self._list_pipeline_keys(new_pipeline_name):
            raise FileExistsError(f"Ja existe uma pipeline com o nome {new_pipeline_name}")

        for key in old_keys:
            new_key = new_prefix + key[len(old_prefix):]
            self.client.copy_object(
                Bucket=self.bucket,
                CopySource={"Bucket": self.bucket, "Key": key},
                Key=new_key,
            )

        self.delete_pipeline(old_pipeline_name)

    def save_env_file(self, pipeline_name: str, content: str) -> None:
        """Salva um arquivo .env no bucket S3"""
        self._write_object(self._get_key(pipeline_name, ".env"), content)

    def get_env_file(self, pipeline_name: str) -> str:
        """Recupera um arquivo .env do bucket S3"""
        key = self._get_key(pipeline_name, ".env")
        return self._read_object(key, f"Arquivo .env não encontrado em {pipeline_name}")

    def delete_env_file(self, pipeline_name: str) -> None:
        """Deleta o arquivo .env do bucket S3"""
        self._delete_object_if_exists(self._get_key(pipeline_name, ".env"))

    def env_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se um arquivo .env existe no bucket S3"""
        return self._object_exists(self._get_key(pipeline_name, ".env"))

    def save_config_file(self, pipeline_name: str, content: str) -> None:
        """Salva um arquivo config.ini no bucket S3"""
        self._write_object(self._get_key(pipeline_name, "config.ini"), content)

    def get_config_file(self, pipeline_name: str) -> str:
        """Recupera um arquivo config.ini do bucket S3"""
        key = self._get_key(pipeline_name, "config.ini")
        return self._read_object(key, f"Arquivo config.ini não encontrado em {pipeline_name}")

    def delete_config_file(self, pipeline_name: str) -> None:
        """Deleta o arquivo config.ini do bucket S3"""
        self._delete_object_if_exists(self._get_key(pipeline_name, "config.ini"))

    def config_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se um arquivo config.ini existe no bucket S3"""
        return self._object_exists(self._get_key(pipeline_name, "config.ini"))

    def save_input_file(self, pipeline_name: str, filename: str, content: bytes) -> str:
        """Salva o arquivo de dados no bucket S3, substituindo o anterior"""
        self.delete_input_file(pipeline_name)

        extension = Path(filename).suffix.lower()
        saved_name = f"{INPUT_FILE_BASENAME}{extension}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._get_key(pipeline_name, saved_name),
            Body=content,
        )
        return saved_name

    def get_input_file_name(self, pipeline_name: str) -> str | None:
        """Encontra o arquivo de dados atual (input.*) no bucket S3"""
        prefix = self._pipeline_prefix(pipeline_name)
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=f"{prefix}{INPUT_FILE_BASENAME}.",
            MaxKeys=1,
        )
        contents = response.get("Contents", [])
        if not contents:
            return None

        return contents[0]["Key"][len(prefix):]

    def delete_input_file(self, pipeline_name: str) -> None:
        """Remove o arquivo de dados (input.*) do bucket S3"""
        current_name = self.get_input_file_name(pipeline_name)
        if current_name:
            self._delete_object_if_exists(self._get_key(pipeline_name, current_name))

    def input_file_exists(self, pipeline_name: str) -> bool:
        """Verifica se existe um arquivo de dados (input.*) no bucket S3"""
        return self.get_input_file_name(pipeline_name) is not None

    def get_output_file_name(self, pipeline_name: str) -> str | None:
        """Encontra o arquivo de saida atual (output.*) no bucket S3"""
        prefix = self._pipeline_prefix(pipeline_name)
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=f"{prefix}{OUTPUT_FILE_BASENAME}.",
            MaxKeys=1,
        )
        contents = response.get("Contents", [])
        if not contents:
            return None

        return contents[0]["Key"][len(prefix):]

    def get_output_file_bytes(self, pipeline_name: str) -> bytes:
        """Le o conteudo binario do arquivo de saida atual no bucket S3"""
        output_name = self.get_output_file_name(pipeline_name)
        if not output_name:
            raise FileNotFoundError(f"Nenhum arquivo de saida encontrado para {pipeline_name}")

        try:
            response = self.client.get_object(
                Bucket=self.bucket, Key=self._get_key(pipeline_name, output_name)
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                raise FileNotFoundError(
                    f"Nenhum arquivo de saida encontrado para {pipeline_name}"
                ) from exc
            raise

        return response["Body"].read()

    def save_output_file(self, pipeline_name: str, filename: str, content: bytes) -> str:
        """Salva o arquivo de saida no bucket S3, substituindo o anterior"""
        self.delete_output_file(pipeline_name)

        extension = Path(filename).suffix.lower()
        saved_name = f"{OUTPUT_FILE_BASENAME}{extension}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._get_key(pipeline_name, saved_name),
            Body=content,
        )
        return saved_name

    def delete_output_file(self, pipeline_name: str) -> None:
        """Remove o arquivo de saida (output.*) do bucket S3"""
        current_name = self.get_output_file_name(pipeline_name)
        if current_name:
            self._delete_object_if_exists(self._get_key(pipeline_name, current_name))

    def sync_output_from_local(self, pipeline_name: str, local_dir: Path) -> str | None:
        """Procura um arquivo output.* na copia local usada pelo container e,
        se existir, envia para o S3 antes que cleanup_local apague a copia
        temporaria (ver execute_pipeline em tasks.py)"""
        matches = sorted(Path(local_dir).glob(f"{OUTPUT_FILE_BASENAME}.*"))
        if not matches:
            return None

        output_path = matches[0]
        return self.save_output_file(pipeline_name, output_path.name, output_path.read_bytes())

    def sync_to_local(self, pipeline_name: str, local_dir: Path) -> None:
        """Baixa todos os arquivos da pipeline do S3 para local_dir no disco
        (o container que executa a ETL só lê do disco local, não do S3)"""
        prefix = self._pipeline_prefix(pipeline_name)
        keys = self._list_pipeline_keys(pipeline_name)
        if not keys:
            raise FileNotFoundError(
                f"Nenhum arquivo encontrado no S3 para a pipeline {pipeline_name} (prefixo {prefix})"
            )

        local_dir = local_dir.resolve()
        local_dir.mkdir(parents=True, exist_ok=True)

        for key in keys:
            relative_path = key[len(prefix):]
            if not relative_path:
                continue

            target_path = (local_dir / relative_path).resolve()
            if not target_path.is_relative_to(local_dir):
                raise ValueError(f"Caminho inválido vindo do S3: {key}")

            target_path.parent.mkdir(parents=True, exist_ok=True)
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            target_path.write_bytes(response["Body"].read())

    def cleanup_local(self, pipeline_name: str, local_dir: Path) -> None:
        """Remove a cópia local temporária baixada do S3 por sync_to_local"""
        import shutil

        _validate_pipeline_name(pipeline_name)
        if local_dir.exists():
            shutil.rmtree(local_dir)
