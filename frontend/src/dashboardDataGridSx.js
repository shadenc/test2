/**
 * MUI DataGrid theme for the main dashboard (moved out of App.js for Sonar line density).
 */
export const DASHBOARD_DATA_GRID_SX = {
  bgcolor: "white",
  fontFamily: "'Tajawal', 'Cairo', 'Noto Sans Arabic', sans-serif",
  direction: "rtl",
  borderRadius: 4,
  fontSize: 18,
  boxShadow: "0 2px 16px 0 rgba(30,102,65,0.08)",
  border: "none",
  "& .MuiDataGrid-columnHeaders": {
    bgcolor: "#e3ecfa",
    fontWeight: "bold",
    fontSize: 18,
    position: "sticky",
    top: 0,
    zIndex: 1,
    direction: "rtl",
    textAlign: "right",
    boxShadow: "0 2px 8px 0 rgba(30,102,65,0.10)",
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
  },
  "& .MuiDataGrid-columnHeader, & .MuiDataGrid-columnHeaderTitle": {
    direction: "rtl",
    textAlign: "right",
    justifyContent: "flex-end",
    paddingRight: "12px !important",
    paddingLeft: "0 !important",
    display: "flex",
  },
  "& .MuiDataGrid-columnHeaderTitleContainer": {
    flexDirection: "row-reverse",
    direction: "rtl",
    display: "flex",
    justifyContent: "flex-end",
  },
  "& .MuiDataGrid-columnHeaderTitleContainerContent": {
    textAlign: "right",
    justifyContent: "flex-end",
    direction: "rtl",
    display: "flex",
  },
  "& .MuiDataGrid-row": {
    minHeight: 44,
    maxHeight: 44,
    transition: "background 0.2s, box-shadow 0.2s",
    borderRadius: 2,
  },
  "& .MuiDataGrid-row:nth-of-type(even)": { bgcolor: "#f7fafc" },
  "& .MuiDataGrid-row:hover": {
    bgcolor: "#e3f2fd",
    boxShadow: "0 2px 8px 0 rgba(30,102,65,0.08)",
    cursor: "pointer",
  },
  "& .MuiDataGrid-footerContainer": {
    bgcolor: "#f4f6fa",
    fontWeight: "bold",
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
  },
  "& .MuiDataGrid-virtualScroller": { minHeight: 300 },
  "& .MuiDataGrid-cell": {
    borderBottom: "1px solid #e0e0e0",
    fontWeight: 500,
    fontSize: 17,
    letterSpacing: "0.01em",
    direction: "rtl",
    textAlign: "right",
  },
  "& .MuiDataGrid-cell:focus, & .MuiDataGrid-columnHeader:focus": {
    outline: "none",
  },
  "& .MuiDataGrid-root": {
    borderRadius: 4,
  },
};
