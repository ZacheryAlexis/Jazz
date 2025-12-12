from app.src.embeddings.scrapers.abstract_scraper import Scraper
from app.src.embeddings.rag_errors import ScrapingFailedError
from pathlib import Path

# docx
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

# pdf
import pymupdf4llm
import datetime
import signal
import os


class SimpleScraper(Scraper):

    def scrape(self, file_path: str | Path) -> dict:
        """Extract text and metadata from a file using simple methods."""

        file_lower = str(file_path).lower()

        if file_lower.endswith(".pdf"):
            try:
                text = self._extract_pdf(file_path)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to scrape PDF file: {e}")

        elif file_lower.endswith(".docx"):
            try:
                text = self._extract_docx(file_path)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to scrape DOCX file: {e}")

        elif file_lower.endswith((".epub", ".mobi", ".azw3")):
            try:
                text = self._extract_ebook(file_path)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to scrape eBook file: {e}")

        else:
            try:
                text = self.read_regular_file(file_path)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to scrape file: {e}")

        text = text.strip()

        return {
            "content": text,
            "metadata": {
                "file_path": Path(file_path).as_posix(),
                "mod_date": datetime.datetime.fromtimestamp(
                    Path(file_path).stat().st_mtime
                ).isoformat(),
                "hash": self.get_hash(file_path),
            },
        }

    @staticmethod
    def _extract_pdf(file_path: str | Path) -> str:
        """Extract text from PDF using fast method (PyMuPDF)."""
        try:
            # Try fast extraction first using fitz (PyMuPDF)
            import fitz
            
            doc = fitz.open(file_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    # Clean up problematic characters for embedding
                    # Remove null bytes and control characters except newlines/tabs
                    cleaned = ''.join(
                        c if c not in '\x00' and (ord(c) >= 32 or c in '\n\r\t') else ' '
                        for c in text
                    )
                    # Replace multiple spaces/newlines with single space
                    import re
                    cleaned = re.sub(r'\s+', ' ', cleaned)
                    if cleaned.strip():
                        text_parts.append(cleaned.strip())
            
            doc.close()
            result = ' '.join(text_parts).strip()
            
            if not result:
                raise ScrapingFailedError(f"PDF extraction returned empty content: {file_path}")
            
            return result
        except ScrapingFailedError:
            raise
        except Exception as e:
            # Fallback to pymupdf4llm if fitz fails (with timeout to prevent hanging)
            try:
                import pymupdf4llm
                import signal
                
                def _timeout_handler(signum, frame):
                    raise TimeoutError("PDF extraction timeout - pymupdf4llm took too long")
                
                # Set 30 second timeout for pymupdf4llm
                signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(30)
                try:
                    md = pymupdf4llm.to_markdown(file_path)
                    signal.alarm(0)  # Cancel alarm if successful
                    return md.strip()
                except TimeoutError:
                    raise ScrapingFailedError(f"PDF extraction timeout on {file_path}")
                finally:
                    signal.alarm(0)  # Always cancel alarm
            except Exception as fallback_err:
                raise ScrapingFailedError(f"Failed to extract PDF with both methods: fitz={e}, pymupdf4llm={fallback_err}")

    @staticmethod
    def _extract_docx(file_path: str | Path) -> str:
        """Extract all text content from a DOCX file including headers, footers, and tables (as markdown)."""
        doc = Document(str(file_path))
        output = []

        # Headers
        for section in doc.sections:
            for hdr_ftr in [
                section.header,
                section.first_page_header,
                section.even_page_header,
            ]:
                if not hdr_ftr.is_linked_to_previous:
                    for item in hdr_ftr.iter_inner_content():
                        if isinstance(item, Paragraph):
                            if item.text.strip():
                                output.append(item.text)
                        elif isinstance(item, Table):
                            output.append(SimpleScraper._table_to_markdown(item))

        # Main body
        for item in doc.iter_inner_content():
            if isinstance(item, Paragraph):
                if item.text.strip():
                    output.append(item.text)
            elif isinstance(item, Table):
                output.append(SimpleScraper._table_to_markdown(item))

        # Footers
        for section in doc.sections:
            for hdr_ftr in [
                section.footer,
                section.first_page_footer,
                section.even_page_footer,
            ]:
                if not hdr_ftr.is_linked_to_previous:
                    for item in hdr_ftr.iter_inner_content():
                        if isinstance(item, Paragraph):
                            if item.text.strip():
                                output.append(item.text)
                        elif isinstance(item, Table):
                            output.append(SimpleScraper._table_to_markdown(item))

        return "\n\n".join(output)

    @staticmethod
    def _extract_ebook(file_path: str | Path) -> str:
        """Extract text from EPUB, MOBI, or AZW3 files."""
        import zipfile
        import xml.etree.ElementTree as ET
        
        file_lower = str(file_path).lower()
        
        # EPUB is a ZIP file with HTML/XML content
        if file_lower.endswith(".epub"):
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Find all HTML/XHTML files
                    text_parts = []
                    for filename in zip_ref.namelist():
                        if filename.endswith(('.html', '.xhtml', '.htm')):
                            try:
                                content = zip_ref.read(filename).decode('utf-8', errors='ignore')
                                # Basic HTML tag removal
                                import re
                                text = re.sub('<[^<]+?>', '', content)
                                text = re.sub(r'\s+', ' ', text)
                                if text.strip():
                                    text_parts.append(text.strip())
                            except:
                                pass
                    return ' '.join(text_parts)
            except Exception as e:
                raise ScrapingFailedError(f"Failed to extract EPUB: {e}")
        
        # MOBI and AZW3 are Kindle formats - need special library
        elif file_lower.endswith(('.mobi', '.azw3')):
            try:
                # Try using KindleUnpack or ebooklib, fall back to basic binary extraction
                try:
                    import ebooklib
                    from ebooklib import epub
                    # Try to treat as EPUB-like format
                    book = epub.read_epub(str(file_path))
                    text_parts = []
                    for item in book.get_items():
                        if item.get_type() == 9:  # 9 = EBOB_DOCUMENT
                            try:
                                text = item.get_content().decode('utf-8', errors='ignore')
                                import re
                                text = re.sub('<[^<]+?>', '', text)
                                text = re.sub(r'\s+', ' ', text)
                                if text.strip():
                                    text_parts.append(text.strip())
                            except:
                                pass
                    if text_parts:
                        return ' '.join(text_parts)
                except:
                    pass
                
                # Fallback: Extract printable ASCII text from binary file
                with open(file_path, 'rb') as f:
                    content = f.read()
                # Extract printable ASCII strings
                import re
                printable = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \t\n\r.,:;!?\'"-()[]{}')
                text_parts = []
                current_string = []
                for byte in content:
                    char = chr(byte) if 32 <= byte <= 126 else ''
                    if char and char in printable:
                        current_string.append(char)
                    elif current_string and len(''.join(current_string)) > 5:
                        text_parts.append(''.join(current_string))
                        current_string = []
                return ' '.join(text_parts[:500])  # Limit to avoid huge outputs
            except Exception as e:
                raise ScrapingFailedError(f"Failed to extract eBook: {e}")
        
        raise ScrapingFailedError(f"Unsupported eBook format: {file_path}")

    @staticmethod
    def _table_to_markdown(table: Table) -> str:
        """Convert a table to markdown format."""
        if not table.rows:
            return ""

        lines = []
        for row_idx, row in enumerate(table.rows):
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            lines.append("| " + " | ".join(cells) + " |")

            if row_idx == 0:
                lines.append("| " + " | ".join(["---"] * len(cells)) + " |")

        return "\n".join(lines)
