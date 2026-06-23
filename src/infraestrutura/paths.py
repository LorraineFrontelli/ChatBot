from pathlib import Path
from tempfile import gettempdir

ROOT = Path(__file__).parent.parent.parent
REFERENCIAS_DIR = ROOT / "referencias"
FAISS_DIR = Path(gettempdir()) / "assessor_ia_faiss"

FAQ_PDF = REFERENCIAS_DIR / "faq" / "FAQ_assessor_v1.1.pdf"
FAQ_INDEX = FAISS_DIR / "faq_index"
