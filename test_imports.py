print("Testing imports...")

try:
    import streamlit
    print("✓ Streamlit installed")
except ImportError:
    print("✗ Streamlit missing")

try:
    import google.generativeai
    print("✓ Google Generative AI installed")
except ImportError:
    print("✗ Google Generative AI missing")

try:
    from pdfminer.high_level import extract_text
    print("✓ PDFMiner installed")
except ImportError:
    print("✗ PDFMiner missing")

try:
    import plotly
    print("✓ Plotly installed")
except ImportError:
    print("✗ Plotly missing")

print("\nAll imports successful!")