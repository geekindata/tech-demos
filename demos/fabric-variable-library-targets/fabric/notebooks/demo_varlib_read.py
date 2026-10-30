# p31-01: read one variable from the demo_varlib Variable Library (active value set only).
lib = notebookutils.variableLibrary.getLibrary("demo_varlib")
print("target_lakehouse =", lib.target_lakehouse)
print("batch_size       =", notebookutils.variableLibrary.get("$(/**/demo_varlib/batch_size)"))
