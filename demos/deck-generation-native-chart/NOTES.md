# Notes

- Data is hard-coded in `make_deck.py` to keep the demo self-contained. In the real workflow the values
  come from a query on `table_a` (for example `SELECT segment, SUM(value) FROM demo.table_a GROUP BY segment`).
- Chart titles are off on the bar chart because the slide title carries the label.
- The blog screenshot was captured in LibreOffice Impress 25.2 on a virtual display (Xvfb, 1920x1200,
  `SAL_FORCEDPI=180`), driven only by the LibreOffice Basic macro in `src/show_chart_data.xba`
  (no input simulation). PowerPoint is not available on the capture box; the same file opens with an
  editable chart and "Edit Data" in PowerPoint because the chart is stored as standard DrawingML chart XML
  with an embedded workbook.
- To reproduce the capture: copy `show_chart_data.xba` into a LibreOffice profile as
  `user/basic/Standard/Module1.xba`, then run
  `soffice -env:UserInstallation=file:///tmp/lo-profile "macro:///Standard.Module1.ShowChart"`
  (the macro opens the deck from its absolute path in this repo; edit the path if needed).
