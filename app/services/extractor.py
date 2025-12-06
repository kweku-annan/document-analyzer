from pathlib import Path
from typing import Optional
import PyPDF2
from docx import Document


class TextExtractor:
    """
    Service for extracting text from various document formats.
    Supports: PDF, DOCX
    """

    @staticmethod
    def extract_from_pdf(file_path: Path) -> str:
        """
        Extract text from PDF file.

        Args:
            file_path: Path to the PDF file.
        :param file_path:
        :return:
        """
        text_content = []

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract text from each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)

            return "\n\n".join(text_content)

        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    def extract_from_docx(file_path: Path) -> str:
        """
        Extract text from DOCX file.

        Args:
            file_path: Path to the DOCX file.
        :param file_path:
        :return:
        """
        text_content = []

        try:
            doc = Document(file_path)

            # Extract text from each paragraph
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    text_content.append(text)

            return "\n\n".join(text_content)

        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")


    @classmethod
    def extract_text(cls, file_path: Path, file_type: str) -> str:
        """
        Extract text based on file type.
        :param file_path:
        :param file_type:
        :return:
        """
        file_type = file_type.lower()

        if file_type == "pdf":
            return cls.extract_from_pdf(file_path)
        elif file_type in ['docx', 'doc']:
            return cls.extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type for extraction: {file_type}")


# Singleton instance
text_extractor = TextExtractor()
