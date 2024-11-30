from io import BytesIO
from zipfile import ZipFile
from typing import Dict, Optional, Union
from common.logger_config import setup_logger

class ZipUtil:
    def __init__(self):
        self.logger = setup_logger('ZipUtil')

    def extract_to_memory(self, zip_data: Union[BytesIO, bytes], ) -> Dict[str, bytes]:
        """
        Extract ZIP contents to memory

        Args:
            zip_data: ZIP file as BytesIO or bytes object
            password: Optional password for encrypted ZIP files

        Returns:
            Dictionary mapping filenames to their contents as bytes

        Raises:
            zipfile.BadZipFile: If ZIP file is invalid
            RuntimeError: If ZIP file is encrypted and no password provided
        """
        self.logger.info("Extracting ZIP contents to memory")

        if isinstance(zip_data, bytes):
            zip_data = BytesIO(zip_data)

        extracted_files = {}

        with ZipFile(zip_data) as zip_file:
            for file_info in zip_file.filelist:

                # Skip files in subdirectories if requested
                #if '/' in file_info.filename:
                #    continue

                self.logger.info(f"Extracting {file_info.filename}")
                try:
                    extracted_files[file_info.filename] = zip_file.read(
                        file_info.filename
                    )
                except Exception as e:
                    self.logger.error(f"Failed to extract {file_info.filename}: {str(e)}")
                    raise

        return extracted_files