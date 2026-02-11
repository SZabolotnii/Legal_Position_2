"""
Модуль для завантаження індексів з різних джерел.
Підтримує: Hugging Face Datasets, AWS S3, локальні файли.
"""
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def download_indexes_from_hf(
    repo_id: str = "DocSA/legal-position-indexes",
    local_dir: str = "Save_Index_Ivan",
    token: Optional[str] = None
) -> bool:
    """
    Завантажити індекси з Hugging Face Datasets.
    
    Args:
        repo_id: ID датасету на HF
        local_dir: Локальна директорія для збереження
        token: HF токен (для приватних датасетів)
    
    Returns:
        True якщо успішно, False якщо помилка
    """
    try:
        from huggingface_hub import snapshot_download
        
        local_path = Path(local_dir)
        
        # Перевірити чи індекси вже існують
        if local_path.exists() and any(local_path.iterdir()):
            logger.info(f"✅ Indexes already exist in {local_dir}")
            return True
        
        logger.info(f"📥 Downloading indexes from Hugging Face: {repo_id}")
        
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(local_path),
            token=token,
            allow_patterns=["*"]
        )
        
        logger.info(f"✅ Indexes downloaded successfully to {local_dir}")
        return True
        
    except ImportError:
        logger.error("❌ huggingface_hub not installed. Install: pip install huggingface_hub")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to download from HF: {str(e)}")
        return False


def download_indexes_from_s3(
    bucket_name: str = "legal-position",
    prefix: str = "Save_Index_Ivan/",
    local_dir: str = "Save_Index_Ivan"
) -> bool:
    """
    Завантажити індекси з AWS S3.
    
    Args:
        bucket_name: Назва S3 bucket
        prefix: Префікс шляху в S3
        local_dir: Локальна директорія
    
    Returns:
        True якщо успішно, False якщо помилка
    """
    try:
        import boto3
        
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📥 Downloading indexes from S3: s3://{bucket_name}/{prefix}")
        
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name="eu-north-1"
        )
        
        # Список всіх об'єктів
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                s3_key = obj['Key']
                local_file = local_path / s3_key.replace(prefix, '')
                local_file.parent.mkdir(parents=True, exist_ok=True)
                
                logger.debug(f"Downloading {s3_key} -> {local_file}")
                s3_client.download_file(bucket_name, s3_key, str(local_file))
        
        logger.info(f"✅ Indexes downloaded from S3 to {local_dir}")
        return True
        
    except ImportError:
        logger.error("❌ boto3 not installed. Install: pip install boto3")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to download from S3: {str(e)}")
        return False


def download_indexes_from_gcs(
    bucket_name: str = "legal-position",
    prefix: str = "Save_Index_Ivan/",
    local_dir: str = "Save_Index_Ivan"
) -> bool:
    """
    Завантажити індекси з Google Cloud Storage.
    
    Args:
        bucket_name: Назва GCS bucket
        prefix: Префікс шляху в GCS
        local_dir: Локальна директорія
    
    Returns:
        True якщо успішно, False якщо помилка
    """
    try:
        from google.cloud import storage
        
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📥 Downloading indexes from GCS: gs://{bucket_name}/{prefix}")
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        
        for blob in blobs:
            local_file = local_path / blob.name.replace(prefix, '')
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Downloading {blob.name} -> {local_file}")
            blob.download_to_filename(str(local_file))
        
        logger.info(f"✅ Indexes downloaded from GCS to {local_dir}")
        return True
        
    except ImportError:
        logger.error("❌ google-cloud-storage not installed. Install: pip install google-cloud-storage")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to download from GCS: {str(e)}")
        return False


def load_indexes_with_fallback(local_dir: str = "Save_Index_Ivan") -> bool:
    """
    Завантажити індекси з автоматичним fallback між джерелами.
    
    Порядок спроб:
    1. Локальні файли (якщо існують)
    2. Hugging Face Datasets
    3. AWS S3
    4. Google Cloud Storage
    
    Args:
        local_dir: Локальна директорія для індексів
    
    Returns:
        True якщо індекси доступні, False якщо помилка
    """
    local_path = Path(local_dir)
    
    # 1. Перевірити локальні файли
    if local_path.exists() and any(local_path.iterdir()):
        logger.info(f"✅ Using existing local indexes from {local_dir}")
        return True
    
    logger.info("🔍 Local indexes not found, trying remote sources...")
    
    # 2. Спробувати Hugging Face Datasets
    logger.info("📥 Attempt 1: Hugging Face Datasets")
    if download_indexes_from_hf(local_dir=local_dir):
        return True
    
    # 3. Спробувати AWS S3
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        logger.info("📥 Attempt 2: AWS S3")
        if download_indexes_from_s3(local_dir=local_dir):
            return True
    else:
        logger.info("⏭️  Skipping S3 (no AWS credentials)")
    
    # 4. Спробувати Google Cloud Storage
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCS_BUCKET"):
        logger.info("📥 Attempt 3: Google Cloud Storage")
        if download_indexes_from_gcs(local_dir=local_dir):
            return True
    else:
        logger.info("⏭️  Skipping GCS (no credentials)")
    
    logger.error("❌ Failed to load indexes from any source")
    return False


def check_indexes_exist(local_dir: str = "Save_Index_Ivan") -> bool:
    """
    Перевірити чи існують локальні індекси.
    
    Args:
        local_dir: Локальна директорія
    
    Returns:
        True якщо індекси існують
    """
    local_path = Path(local_dir)
    return local_path.exists() and any(local_path.iterdir())


# Приклад використання
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Завантажити індекси з fallback
    success = load_indexes_with_fallback()
    
    if success:
        print("✅ Indexes are ready to use!")
    else:
        print("❌ Failed to load indexes")
