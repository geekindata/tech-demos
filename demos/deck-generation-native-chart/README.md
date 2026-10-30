# Deck generation with native, editable charts

Small demo for the post section "Deck generation as a skill-backed workflow".
It builds a three-slide `.pptx` from neutral demo data (`table_a`: segments A, B, C over periods P1 to P6)
on the python-pptx default template (no company master, no logos).

Slides 2 and 3 hold **native charts** (chart XML plus an embedded workbook), not pictures, so anyone
opening the deck in PowerPoint or LibreOffice Impress can edit the values and the chart redraws.

## Run

```bash
pip install python-pptx==1.0.2
python src/make_deck.py            # writes output/demo_deck.pptx
```

## Check it is a real chart

```bash
unzip -l output/demo_deck.pptx | grep -E "charts/|embeddings/"
# ppt/charts/chart1.xml, chart2.xml and ppt/embeddings/Microsoft_Excel_Sheet1.xlsx, Sheet2.xlsx
```

Open the deck, double-click the chart on slide 2, then choose Edit Data (PowerPoint) or
View > Data Table (LibreOffice Impress) to see and change the values.

## Files

- `src/make_deck.py`: builds the deck.
- `src/show_chart_data.xba`: optional LibreOffice Basic macro used to open slide 2 with the chart in
  edit mode and its data table showing, for the blog screenshot.
- `output/demo_deck.pptx`: generated deck.
