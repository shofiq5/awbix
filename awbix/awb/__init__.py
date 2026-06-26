{
 "charts": [],
 "content": "[{\"id\":\"awb_h1\",\"type\":\"header\",\"data\":{\"text\":\"<span class=\\\"h4\\\"><b>Stock Control</b></span>\",\"col\":12}},{\"id\":\"awb_s1\",\"type\":\"shortcut\",\"data\":{\"shortcut_name\":\"AWB Inventory\",\"col\":3}},{\"id\":\"awb_s2\",\"type\":\"shortcut\",\"data\":{\"shortcut_name\":\"Assigned AWBs\",\"col\":3}},{\"id\":\"awb_s3\",\"type\":\"shortcut\",\"data\":{\"shortcut_name\":\"AWB Series Generator\",\"col\":3}},{\"id\":\"awb_h2\",\"type\":\"header\",\"data\":{\"text\":\"<span class=\\\"h4\\\"><b>Reference</b></span>\",\"col\":12}},{\"id\":\"awb_s4\",\"type\":\"shortcut\",\"data\":{\"shortcut_name\":\"AWB Type\",\"col\":3}},{\"id\":\"awb_s5\",\"type\":\"shortcut\",\"data\":{\"shortcut_name\":\"AWB Cycle\",\"col\":3}},{\"id\":\"awb_h3\",\"type\":\"header\",\"data\":{\"text\":\"<span class=\\\"h4\\\"><b>Reports</b></span>\",\"col\":12}},{\"id\":\"awb_s6\",\"type\":\"shortcut\",\"data\":{\"shortcut_name\":\"AWB Customer Summary\",\"col\":3}},{\"id\":\"awb_s7\",\"type\":\"shortcut\",\"data\":{\"shortcut_name\":\"AWB Customer Detail\",\"col\":3}}]",
 "creation": "2026-04-30 00:00:00",
 "custom_blocks": [],
 "docstatus": 0,
 "doctype": "Workspace",
 "for_user": "",
 "hide_custom": 0,
 "icon": "\u2708",
 "idx": 0,
 "indicator_color": "blue",
 "is_hidden": 0,
 "label": "Waybills",
 "links": [],
 "modified": "2026-05-01 16:01:43.118450",
 "modified_by": "shofiq5@gmail.com",
 "module": "AWB",
 "name": "Waybills",
 "number_cards": [],
 "owner": "Administrator",
 "parent_page": "CargoXy",
 "public": 1,
 "quick_lists": [],
 "restrict_to_domain": "Cargo GSA",
 "roles": [
  {
   "role": "Cargo Admin"
  },
  {
   "role": "Cargo AWB Control"
  }
 ],
 "sequence_id": 3.0,
 "shortcuts": [
  {
   "color": "Blue",
   "format": "{} Available",
   "label": "AWB Inventory",
   "link_to": "AWB Inventory",
   "stats_filter": "{\"status\": \"Available\"}",
   "type": "DocType"
  },
  {
   "color": "Orange",
   "format": "{} Assigned",
   "label": "Assigned AWBs",
   "link_to": "AWB Inventory",
   "stats_filter": "{\"status\": \"Assigned\"}",
   "type": "DocType"
  },
  {
   "color": "Green",
   "doc_view": "List",
   "label": "AWB Series Generator",
   "link_to": "AWB Series Generator",
   "stats_filter": "[]",
   "type": "DocType"
  },
  {
   "color": "Grey",
   "doc_view": "List",
   "label": "AWB Type",
   "link_to": "AWB Type",
   "stats_filter": "[]",
   "type": "DocType"
  },
  {
   "color": "Grey",
   "doc_view": "List",
   "label": "AWB Cycle",
   "link_to": "AWB Cycle",
   "stats_filter": "[]",
   "type": "DocType"
  },
  {
   "color": "Green",
   "label": "AWB Customer Summary",
   "link_to": "AWB Customer Summary",
   "report_ref_doctype": "AWB Inventory",
   "type": "Report"
  },
  {
   "color": "Green",
   "label": "AWB Customer Detail",
   "link_to": "AWB Customer Detail",
   "report_ref_doctype": "AWB Inventory",
   "type": "Report"
  }
 ],
 "title": "Waybills"
}