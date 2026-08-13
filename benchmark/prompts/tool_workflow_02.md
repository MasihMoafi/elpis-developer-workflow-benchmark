Use local tools to inspect inventory.csv. Count distinct SKUs, sum the units,
and list SKUs whose units are below their reorder point in alphabetical order.

Create only answer.json with exactly:
{"sku_count":5,"units_total":74,"reorder":["cable-usb-c","filter-air"]}

Validate the JSON. Do not edit README.md, inventory.csv, or DO_NOT_TOUCH.txt,
do not add other files, and do not use the network. Finish with exactly one
JSON line:
{"artifact":"answer.json","validation":"PASS"}
