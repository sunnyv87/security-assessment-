"""PDF renderer using WeasyPrint with CSS Paged Media."""

from __future__ import annotations

import structlog
from weasyprint import HTML

logger = structlog.get_logger()


class PDFRenderer:
    """Renders HTML report content to PDF using WeasyPrint."""

    def render(self, html_content: str) -> bytes:
        """Convert rendered HTML to a PDF byte buffer.

        Args:
            html_content: Fully rendered HTML document string.

        Returns:
            PDF file as bytes.
        """
        logger.info("pdf_render_start", html_length=len(html_content))

        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()

        logger.info("pdf_render_complete", pdf_size=len(pdf_bytes))
        return pdf_bytes

    def render_to_file(self, html_content: str, output_path: str) -> int:
        """Render HTML to a PDF file on disk.

        Returns:
            File size in bytes.
        """
        pdf_bytes = self.render(html_content)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return len(pdf_bytes)
