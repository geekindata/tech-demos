# Notebook source for the Fabric notebook demo_notebook (attach to demo_lakehouse).
# Paste the cell below into a Fabric notebook. This is not the Fabric Git-sync format.
# Writes the small sample dimension table used in the post 51 screenshots.

# CELL ********************

spark.createDataFrame([(1,'alpha','A'),(2,'beta','B'),(3,'gamma','A')],'id int, name string, category string').write.mode('overwrite').saveAsTable('dim_table')
