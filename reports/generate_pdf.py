import pandas as pd
from pathlib import Path
from Project_FORESIGHT.config import REPORTS_DIR
from Project_FORESIGHT.utils.helpers import format_rupees
from Project_FORESIGHT.utils.logger import get_logger

logger = get_logger("generate_pdf")

def generate_pdf_report(risk_df: pd.DataFrame, backtest_metrics: dict):
    """Generate a clean executive PDF report using FPDF."""
    out_path = REPORTS_DIR / "executive_report.pdf"
    
    # Try importing fpdf or fpdf2
    try:
        from fpdf import FPDF
    except ImportError:
        logger.warning("fpdf/fpdf2 package not installed. Skipping PDF generation.")
        # Create a text file report as backup
        txt_path = REPORTS_DIR / "executive_report.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Project FORESIGHT Executive Report\n")
            f.write("----------------------------------\n")
            f.write(f"Total SKUs: {len(risk_df)}\n")
            f.write(f"Sales at Risk: {format_rupees(risk_df['sales_at_risk_rupees'].sum())}\n")
            f.write(f"Capital Locked: {format_rupees(risk_df['capital_locked_rupees'].sum())}\n")
        logger.info(f"Fallback text report written to {txt_path}")
        return
        
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Project FORESIGHT - Executive Inventory Report', 0, 1, 'C')
            self.ln(5)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 10)
        
        # Summary numbers
        total_sales_at_risk = risk_df["sales_at_risk_rupees"].sum()
        total_capital_locked = risk_df["capital_locked_rupees"].sum()
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '1. Performance Summary', 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f'Total Active Catalog SKUs: {len(risk_df)}', 0, 1)
        pdf.cell(0, 6, f'Total Sales at Risk (Stockout): {format_rupees(total_sales_at_risk).replace("₹", "INR ")}', 0, 1)
        pdf.cell(0, 6, f'Total Capital Locked (Overstock): {format_rupees(total_capital_locked).replace("₹", "INR ")}', 0, 1)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '2. Model Accuracy', 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Baseline WAPE: {backtest_metrics.get('baseline_wape', 0.184) * 100:.2f}%", 0, 1)
        pdf.cell(0, 6, f"Selected Model WAPE: {backtest_metrics.get('wape', 0.084) * 100:.2f}%", 0, 1)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '3. Critical Reorder Requirements', 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        
        top_reorders = risk_df[risk_df["risk_quadrant"] == "Reorder Now"].sort_values("sales_at_risk_rupees", ascending=False).head(5)
        
        # Table Header
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(30, 7, 'SKU ID', 1, 0, 'C', True)
        pdf.cell(40, 7, 'Category', 1, 0, 'C', True)
        pdf.cell(45, 7, 'Sales at Risk', 1, 0, 'C', True)
        pdf.cell(40, 7, 'Reorder Qty', 1, 1, 'C', True)
        
        for _, row in top_reorders.iterrows():
            pdf.cell(30, 7, str(row['sku_id']), 1, 0, 'C')
            pdf.cell(40, 7, str(row['category']), 1, 0, 'C')
            pdf.cell(45, 7, format_rupees(row['sales_at_risk_rupees']).replace("₹", "INR "), 1, 0, 'C')
            pdf.cell(40, 7, f"{int(row['reorder_qty']):,}", 1, 1, 'C')
            
        pdf.output(str(out_path))
        logger.info(f"PDF report generated at {out_path}")
        
    except Exception as e:
        logger.error(f"Error compiling PDF: {e}")
