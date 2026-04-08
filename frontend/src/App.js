import React, { useState, useEffect, useMemo, useCallback } from "react";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Paper from "@mui/material/Paper";
import RefreshIcon from "@mui/icons-material/Refresh";
import Typography from "@mui/material/Typography";
import Papa from "papaparse";
import IconButton from "@mui/material/IconButton";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Tooltip from '@mui/material/Tooltip';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import MenuIcon from '@mui/icons-material/Menu';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import MenuItem from '@mui/material/MenuItem';
import EditIcon from '@mui/icons-material/Edit';
import Add from '@mui/icons-material/Add';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from "@mui/material/Stack";
import { buildDashboardColumns, GRID_EMPTY_AR } from "./dashboardColumns";
import { mergeCorrectionIntoRows, quarterLabelFromDateString } from "./gridUtils";
import { UpdateJobsDialog } from "./UpdateJobsDialog";
import { createPipelineStatusPoller } from "./pipelineStatusPoll";
import { PipelineProgressModal } from "./PipelineProgressModal";
import { DrawerListLoadingOrError } from "./DrawerListLoadingOrError";
import { API_URL } from "./apiBase";
import { EvidenceModal } from "./EvidenceModal";
import { CustomExportModal } from "./CustomExportModal";
import { DrawerSectionHeader } from "./DrawerSectionHeader";
import { DASHBOARD_DATA_GRID_SX } from "./dashboardDataGridSx";
import { downloadBlobAsFile, refreshUserExportsSidebar } from "./exportDownloadUtils";

function cleanFlowCsvRow(row) {
  const cleanedRow = {};
  Object.keys(row).forEach((key) => {
    const cleanKey = key.trim();
    cleanedRow[cleanKey] = row[key] ? row[key].trim() : "";
  });
  return cleanedRow;
}

function cleanedRowsFromPapaResult(result) {
  console.log("CSV parsing result:", result);
  if (!result.data || result.data.length === 0) {
    console.log("No CSV data found");
    return [];
  }
  const cleanedData = result.data
    .filter((row) => row.company_symbol && row.company_symbol.trim() !== "")
    .map(cleanFlowCsvRow);
  console.log("Cleaned CSV data:", cleanedData);
  return cleanedData;
}

/** Parse retained-earnings flow CSV; shallow callbacks only (Sonar nesting). */
function parseQuarterlyFlowCsvText(csvText) {
  return new Promise((resolve) => {
    Papa.parse(csvText, {
      header: true,
      complete: (result) => resolve(cleanedRowsFromPapaResult(result)),
      error: (error) => {
        console.error("Error parsing CSV data:", error);
        resolve([]);
      },
    });
  });
}

const QUARTERS_Q1_Q4 = ['Q1', 'Q2', 'Q3', 'Q4'];

function messageForCustomExportFailure(error) {
  const msg = error?.message ?? "";
  if (msg.includes("404")) {
    return "🔍 السبب: لم يتم العثور على البيانات المطلوبة\n💡 الحل: تأكد من وجود البيانات للربع المحدد";
  }
  if (msg.includes("500")) {
    return "🔧 السبب: خطأ في الخادم\n💡 الحل: حاول مرة أخرى أو اتصل بالدعم الفني";
  }
  if (msg.includes("fetch")) {
    return "🌐 السبب: مشكلة في الاتصال\n💡 الحل: تأكد من تشغيل الخادم";
  }
  return `🔍 السبب: ${msg}\n💡 الحل: حاول مرة أخرى`;
}

const DATA_GRID_COMPONENTS_PROPS = {
  toolbar: {
    showQuickFilter: true,
    quickFilterProps: { debounceMs: 500 },
  },
};

/** Progress line for pipeline modals: optional label prefix, else status + processed + current symbol. */
function pipelineJobStatusLine(jobStatus, labelWithColon) {
  const status = jobStatus?.status ?? "جاري التنفيذ";
  const sym = jobStatus?.current_symbol;
  if (labelWithColon) {
    return `${labelWithColon}: ${status}${sym ? ` — ${sym}` : ""}`;
  }
  const processed = jobStatus?.processed ?? 0;
  return `الحالة: ${status} — المُنجز: ${processed}${sym ? ` — الحالي: ${sym}` : ""}`;
}

function stopBothJobsButtonSx(stopping) {
  if (stopping) {
    return { color: "#999", borderColor: "#ccc" };
  }
  return { color: "#b71c1c", borderColor: "#b71c1c" };
}

function filenameFromContentDispositionHeader(contentDisposition, fallback = "dashboard_table.xlsx") {
  const m = contentDisposition?.match(/filename="(.+)"/);
  return m ? m[1] : fallback;
}

function userExportRowLabel(file) {
  const datePart = file.export_date.split(" ")[0];
  const [year, month, day] = datePart.split("-");
  return `dashboard-${day}-${month}-${year}`;
}

function UserExportsDrawerList({ loading, error, files, onDeleteExport, apiUrl }) {
  if (loading || error) {
    return <DrawerListLoadingOrError loading={loading} error={error} />;
  }
  if (files.length === 0) {
    return (
      <ListItem sx={{ justifyContent: "center", alignItems: "center", minHeight: 80, width: "100%" }}>
        <Typography sx={{ color: "#b0b7be", fontSize: 17, textAlign: "center", width: "100%" }}>
          لا توجد ملفات محفوظة بعد
        </Typography>
      </ListItem>
    );
  }
  return files.map((file) => (
    <ListItem
      key={file.filename || file.download_url || file.export_date}
      tabIndex={0}
      sx={{
        pl: 3,
        pr: 3,
        py: 2.2,
        mb: 1.5,
        bgcolor: "#fff",
        borderRadius: 2.5,
        boxShadow: "0 1px 6px 0 rgba(30,102,65,0.06)",
        display: "flex",
        alignItems: "center",
        "&:hover .export-delete-btn": { opacity: 1 },
        minHeight: 56,
        border: "none",
        transition: "box-shadow 0.2s, transform 0.2s",
        "&:hover": {
          boxShadow: "0 4px 16px 0 rgba(30,102,65,0.10)",
          transform: "translateY(-2px) scale(1.01)",
        },
        outline: "none",
        "&:focus": {
          boxShadow: "0 0 0 2px #1e664144",
        },
      }}
    >
      <Box sx={{ flexGrow: 1 }}>
        <Typography sx={{ fontWeight: 500, color: "#1e6641", fontSize: 15 }}>
          {userExportRowLabel(file)}
        </Typography>
      </Box>
      <Tooltip title="تحميل" arrow>
        <IconButton
          aria-label="تحميل"
          href={`${apiUrl}${file.download_url}`}
          target="_blank"
          rel="noopener noreferrer"
          sx={{
            color: "#1e6641",
            bgcolor: "transparent",
            borderRadius: "50%",
            p: 0.7,
            mx: 0.5,
            transition: "color 0.2s, background 0.2s",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 22,
            height: 36,
            width: 36,
            minWidth: 36,
          }}
        >
          <DownloadIcon sx={{ fontSize: 22 }} />
        </IconButton>
      </Tooltip>
      <Tooltip title="حذف" arrow>
        <IconButton
          aria-label="حذف"
          className="export-delete-btn"
          onClick={() => onDeleteExport(file)}
          sx={{
            ml: 0.5,
            opacity: 0,
            color: "#7b7b7b",
            bgcolor: "transparent",
            borderRadius: "50%",
            p: 0.7,
            transition: "opacity 0.2s, color 0.2s, background 0.2s",
            boxShadow: "none",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 22,
            height: 36,
            width: 36,
            minWidth: 36,
            "&:hover": { color: "#444", bgcolor: "rgba(120,120,120,0.07)" },
          }}
          size="small"
        >
          <DeleteOutlineIcon sx={{ fontSize: 22 }} />
        </IconButton>
      </Tooltip>
    </ListItem>
  ));
}

function QuarterlySnapshotsDrawerList({ loading, error, snapshots: snapList, apiUrl }) {
  if (loading || error) {
    return <DrawerListLoadingOrError loading={loading} error={error} />;
  }
  if (snapList.length === 0) {
    return (
      <ListItem sx={{ justifyContent: "center", color: "#888" }}>لا توجد ملفات محفوظة بعد</ListItem>
    );
  }
  return snapList.map((snap) => (
    <ListItem
      key={snap.download_url}
      sx={{ pl: 2, pr: 2, py: 1, borderBottom: "1px solid #e0e0e0", display: "flex", alignItems: "center" }}
    >
      <Typography sx={{ fontWeight: 500, color: "#1e6641", flexGrow: 1, fontSize: 16 }}>
        {`${snap.year} ${snap.quarter} — ${snap.snapshot_date}`}
      </Typography>
      <Tooltip title={`تاريخ الاستخراج: ${snap.snapshot_date}`} arrow>
        <Button
          variant="contained"
          color="success"
          size="small"
          href={`${apiUrl}${snap.download_url}`}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ minWidth: 0, px: 2, py: 1, borderRadius: 2, fontWeight: 600 }}
          startIcon={<DownloadIcon />}
        >
          تحميل
        </Button>
      </Tooltip>
    </ListItem>
  ));
}

UserExportsDrawerList.propTypes = {
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string,
  files: PropTypes.arrayOf(PropTypes.object).isRequired,
  onDeleteExport: PropTypes.func.isRequired,
  apiUrl: PropTypes.string.isRequired,
};

UserExportsDrawerList.defaultProps = {
  error: null,
};

QuarterlySnapshotsDrawerList.propTypes = {
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string,
  snapshots: PropTypes.arrayOf(PropTypes.object).isRequired,
  apiUrl: PropTypes.string.isRequired,
};

QuarterlySnapshotsDrawerList.defaultProps = {
  error: null,
};

function buildFlowMapFromQuarterlyRows(quarterlyFlowData) {
  const flowMap = {};
  quarterlyFlowData.forEach((row) => {
    const symbol = row.company_symbol?.toString().trim() ?? "";
    const quarter = row.quarter?.toString().trim() ?? "";
    if (!symbol || !quarter) {
      return;
    }
    if (!flowMap[symbol]) {
      flowMap[symbol] = {};
    }
    flowMap[symbol][quarter] = {
      previous_value: row.previous_value || '',
      current_value: row.current_value || '',
      flow: row.flow || '',
      flow_formula: row.flow_formula || '',
      year: row.year || '',
      foreign_investor_flow: row.reinvested_earnings_flow || '',
      net_profit_foreign_investor: row.net_profit_foreign_investor || '',
      distributed_profits_foreign_investor: row.distributed_profits_foreign_investor || '',
    };
    console.log(`Mapped flow data for ${symbol} ${quarter}:`, {
      ...flowMap[symbol][quarter],
      net_profit_foreign_investor: row.net_profit_foreign_investor,
      distributed_profits_foreign_investor: row.distributed_profit_foreign_investor,
    });
  });
  return flowMap;
}

function mergeOwnershipWithQuarterlyFlow(foreignOwnershipData, flowMap, onEvidenceClick) {
  const mergedData = [];
  foreignOwnershipData.forEach((row, idx) => {
    const symbol = row.symbol?.toString().trim() ?? "";
    const flowData = flowMap[symbol] || {};
    QUARTERS_Q1_Q4.forEach((quarter) => {
      const quarterData = flowData[quarter] || {};
      const mergedRow = {
        ...row,
        company_symbol: symbol,
        previous_quarter_value: quarterData.previous_value || '',
        current_quarter_value: quarterData.current_value || '',
        flow: quarterData.flow || '',
        flow_formula: quarterData.flow_formula || '',
        year: quarterData.year || '',
        foreign_investor_flow: quarterData.foreign_investor_flow || '',
        net_profit_foreign_investor: quarterData.net_profit_foreign_investor || '',
        distributed_profits_foreign_investor: quarterData.distributed_profits_foreign_investor || '',
        quarter,
        id: `${symbol}_${quarter}_${idx}`,
        onEvidenceClick,
      };
      if (mergedData.length < 5 || symbol === '2222') {
        console.log(`Row ${mergedData.length} (${symbol} ${quarter}):`, {
          symbol: mergedRow.symbol,
          company_name: mergedRow.company_name,
          quarter: mergedRow.quarter,
          flow: mergedRow.flow,
          flow_formula: mergedRow.flow_formula,
        });
      }
      mergedData.push(mergedRow);
    });
  });
  return mergedData;
}

// Inline Editable Cell Component
const InlineEditableCell = ({ value, onSave, fieldType, companySymbol, companyName }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value?.toString() || "");
  const [saving, setSaving] = useState(false);

  const handleEdit = () => {
    setIsEditing(true);
    setEditValue(value?.toString() || "");
  };

  const handleSave = async () => {
    if (editValue.trim() === "") return;
    
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/correct_field_value`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_symbol: companySymbol,
          field_type: fieldType,
          new_value: Number.parseFloat(editValue),
          feedback: 'Inline edit'
        }),
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        onSave(Number.parseFloat(editValue));
        setIsEditing(false);
      } else {
        alert('فشل في حفظ التصحيح: ' + (data.message || ''));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      alert('حدث خطأ أثناء حفظ التصحيح: ' + message);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditValue(value?.toString() || "");
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TextField
          size="small"
          type="number"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyPress}
          autoFocus
          sx={{ 
            width: '120px',
            direction: 'ltr',
            '& .MuiInputBase-input': { 
              textAlign: 'right',
              fontSize: '0.9rem',
              padding: '4px 8px'
            }
          }}
        />
        <Tooltip title="حفظ التغيير" arrow placement="top">
          <IconButton 
            size="small" 
            onClick={handleSave}
            disabled={saving}
            sx={{ color: '#4caf50', '&:hover': { bgcolor: '#e8f5e8' } }}
          >
            {saving ? <CircularProgress size={16} /> : '✓'}
          </IconButton>
        </Tooltip>
        <Tooltip title="إلغاء التغيير" arrow placement="top">
          <IconButton 
            size="small" 
            onClick={handleCancel}
            sx={{ color: '#f44336', '&:hover': { bgcolor: '#ffebee' } }}
          >
            ✕
          </IconButton>
        </Tooltip>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Typography>{value?.toLocaleString("en-US") || GRID_EMPTY_AR}</Typography>
      <Tooltip title="هل تحتاج لتغيير هذه القيمة؟ انقر هنا للتعديل" arrow placement="top">
        <IconButton 
          size="small" 
          onClick={handleEdit}
          sx={{
            color: '#ff9800',
            opacity: 0.7,
            '&:hover': { bgcolor: '#fff3e0', opacity: 1 },
          }}
        >
          <EditIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

InlineEditableCell.propTypes = {
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  onSave: PropTypes.func.isRequired,
  fieldType: PropTypes.string.isRequired,
  companySymbol: PropTypes.string.isRequired,
  companyName: PropTypes.string,
};

InlineEditableCell.defaultProps = {
  value: null,
  companyName: "",
};

function App() {
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [quarterFilter, setQuarterFilter] = useState("Q1"); // Default to Q1 instead of "all"
  const [loading, setLoading] = useState(false);
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [evidenceData, setEvidenceData] = useState(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [snapshotsLoading, setSnapshotsLoading] = useState(false);
  const [snapshotsError, setSnapshotsError] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [userExports, setUserExports] = useState([]);
  const [userExportsLoading, setUserExportsLoading] = useState(false);
  const [userExportsError, setUserExportsError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [netProfitData, setNetProfitData] = useState({});
  const [customExportDate, setCustomExportDate] = useState("");
  const [customFileName, setCustomFileName] = useState("");
  const [customExportExpanded, setCustomExportExpanded] = useState(false);
  // Background jobs state
  const [pdfJobStatus, setPdfJobStatus] = useState({ status: 'idle' });
  const [netJobStatus, setNetJobStatus] = useState({ status: 'idle' });
  const [pdfPollId, setPdfPollId] = useState(null);
  const [netPollId, setNetPollId] = useState(null);
  const [pdfProgressOpen, setPdfProgressOpen] = useState(false);
  const [netProgressOpen, setNetProgressOpen] = useState(false);
  // Unified update modal state
  const [updateModalOpen, setUpdateModalOpen] = useState(false);
  const [selectPdf, setSelectPdf] = useState(false);
  const [selectNet, setSelectNet] = useState(false);
  // Combined progress modal when running both
  const [bothProgressOpen, setBothProgressOpen] = useState(false);
  const [bothPdfRunning, setBothPdfRunning] = useState(false);
  const [bothNetRunning, setBothNetRunning] = useState(false);
  const [bothIsStopping, setBothIsStopping] = useState(false);

  const requestStopPdfPipeline = useCallback(async () => {
    try {
      await fetch(`${API_URL}/api/pdfs/stop`, { method: 'POST' });
    } catch (e) {
      console.warn('طلب إيقاف مهمة PDF فشل', e);
    }
  }, []);

  const requestStopNetProfitPipeline = useCallback(async () => {
    try {
      await fetch(`${API_URL}/api/net_profit/stop`, { method: 'POST' });
    } catch (e) {
      console.warn('طلب إيقاف مهمة صافي الربح فشل', e);
    }
  }, []);

  const startPollPdf = (onComplete) => {
    createPipelineStatusPoller({
      getPollId: () => pdfPollId,
      setPollId: setPdfPollId,
      apiUrl: API_URL,
      statusPath: "/api/pdfs/status",
      setJobStatus: setPdfJobStatus,
      setProgressOpen: setPdfProgressOpen,
      reloadFns: [fetchData, fetchNetProfitData],
      warnMessage: "تعذر جلب حالة مهمة PDF",
    })(onComplete);
  };

  const startPollNet = (onComplete) => {
    createPipelineStatusPoller({
      getPollId: () => netPollId,
      setPollId: setNetPollId,
      apiUrl: API_URL,
      statusPath: "/api/net_profit/status",
      setJobStatus: setNetJobStatus,
      setProgressOpen: setNetProgressOpen,
      reloadFns: [fetchNetProfitData, fetchData],
      warnMessage: "تعذر جلب حالة مهمة صافي الربح",
    })(onComplete);
  };

  useEffect(() => {
    return () => {
      if (pdfPollId) clearInterval(pdfPollId);
      if (netPollId) clearInterval(netPollId);
    };
  }, [pdfPollId, netPollId]);

  const fetchEvidenceData = useCallback(async (companySymbol, quarter) => {
    console.log(`Fetching evidence for ${companySymbol} quarter ${quarter}`);
    setEvidenceLoading(true);
    setEvidenceError(null);
    setEvidenceData(null);
    setEvidenceModalOpen(true);
    try {
      const response = await fetch(`${API_URL}/api/extractions/${companySymbol}?quarter=${quarter}`);
      if (response.ok) {
        const data = await response.json();
        console.log("Evidence data received:", data);
        setEvidenceData(data);
      } else {
        console.error("Failed to fetch evidence data");
        setEvidenceError("فشل تحميل الدليل");
      }
    } catch (error) {
      console.error("Error fetching evidence data:", error);
      const message = error instanceof Error ? error.message : String(error);
      setEvidenceError(message || "حدث خطأ أثناء التحميل");
    } finally {
      setEvidenceLoading(false);
    }
  }, []);

  const dashboardColumns = useMemo(
    () =>
      buildDashboardColumns({
        quarterFilter,
        netProfitData,
        fetchEvidenceData,
      }),
    [quarterFilter, netProfitData, fetchEvidenceData],
  );

  // Function to fetch net profit data
  const fetchNetProfitData = async () => {
    try {
      const response = await fetch(`${API_URL}/api/net-profit`);
      if (response.ok) {
        const data = await response.json();
        setNetProfitData(data);
      } else {
        console.error('Failed to fetch net profit data');
      }
    } catch (error) {
      console.error('Error fetching net profit data:', error);
    }
  };

  // Function to handle evidence button click
  const handleEvidenceClick = (row) => {
    if (row.current_quarter_value && row.current_quarter_value !== GRID_EMPTY_AR) {
      fetchEvidenceData(row.symbol, row.quarter);
    }
  };

  // Function to handle reset (إعادة تعيين)
  const handleReset = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/refresh`, {
        method: 'POST',
      });
      const data = await response.json();
      if (data.status === 'success') {
        // Optionally show a success message
        fetchData(); // Reload data after refresh
      } else {
        alert('حدث خطأ أثناء التحديث: ' + (data.message || ''));
        setLoading(false);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      alert('تعذر الاتصال بالخادم: ' + message);
      setLoading(false);
    }
  };


  // Function to handle Excel export
  const handleExcelExport = async () => {
    try {
      const response = await fetch(`${API_URL}/api/export_excel?quarter=${quarterFilter}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const filename = filenameFromContentDispositionHeader(
        response.headers.get("content-disposition"),
      );

      const blob = await response.blob();
      downloadBlobAsFile(blob, filename);

      await refreshUserExportsSidebar(
        setUserExports,
        setUserExportsLoading,
        setUserExportsError,
        "تعذر تحديث قائمة ملفات التصدير بعد التحميل",
      );
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      const message = error instanceof Error ? error.message : String(error);
      alert('فشل في تصدير ملف Excel: ' + message);
    }
  };

  const fetchData = () => {
    setLoading(true);
    
    // Load foreign ownership data (JSON)
    const loadForeignOwnership = fetch("/foreign_ownership_data.json")
      .then((res) => res.json())
      .catch((error) => {
        console.error("Error loading foreign ownership data:", error);
        return [];
      });

    // Load quarterly flow data (CSV) from backend API
    const loadQuarterlyFlowData = fetch(`${API_URL}/api/retained_earnings_flow.csv?t=${Date.now()}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.text();
      })
      .then((csvText) => parseQuarterlyFlowCsvText(csvText))
      .catch((error) => {
        console.error("Error loading quarterly flow data:", error);
        return [];
      });

    // Combine both datasets
    Promise.all([loadForeignOwnership, loadQuarterlyFlowData])
      .then(([foreignOwnershipData, quarterlyFlowData]) => {
        console.log("Foreign ownership data count:", foreignOwnershipData.length);
        console.log("Quarterly flow data count:", quarterlyFlowData.length);

        const flowMap = buildFlowMapFromQuarterlyRows(quarterlyFlowData);
        console.log("Flow map keys:", Object.keys(flowMap));
        console.log("Sample flow data for 2222:", flowMap["2222"]);

        const mergedData = mergeOwnershipWithQuarterlyFlow(
          foreignOwnershipData,
          flowMap,
          handleEvidenceClick,
        );
        console.log("Final merged data sample:", mergedData.slice(0, 3));

        setRows(mergedData);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error combining data:", error);
        setLoading(false);
      });
  };

  // Fetch archived snapshots
  useEffect(() => {
    console.log('🔄 Fetching archived snapshots...');
    setSnapshotsLoading(true);
    fetch(`${API_URL}/api/ownership_snapshots`)
      .then(res => {
        console.log('📡 Snapshots response status:', res.status);
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        console.log('✅ Snapshots data received:', data);
        setSnapshots(data);
        setSnapshotsLoading(false);
      })
      .catch(err => {
        console.error('❌ Error fetching snapshots:', err);
        setSnapshotsError('فشل في تحميل ملفات الفترات السابقة');
        setSnapshotsLoading(false);
      });
  }, []);

  useEffect(() => {
    console.log("🔄 Fetching user exports...");
    refreshUserExportsSidebar(
      setUserExports,
      setUserExportsLoading,
      setUserExportsError,
      "❌ Error fetching user exports:",
    );
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchNetProfitData();
  }, []);

  // Expose row update on globalThis so nested modal handlers can invoke it without prop drilling
  useEffect(() => {
    globalThis.updateRowAfterCorrection = (updated) => {
      setRows((prevRows) => mergeCorrectionIntoRows(prevRows, updated));
    };
    return () => {
      globalThis.updateRowAfterCorrection = undefined;
    };
  }, []);

  // Filter rows based on search and quarter filter
  const filteredRows = useMemo(() => {
    let filtered = rows;
    
    // Filter by quarter - now all companies have rows for all quarters
    filtered = filtered.filter(row => row.quarter === quarterFilter);
    
    console.log(`Showing ${filtered.length} companies for ${quarterFilter}`);
    
    // Then apply search filter
    if (search) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter(
        (row) =>
          row.symbol?.toString().toLowerCase().includes(searchLower) ||
          row.company_name?.toLowerCase().includes(searchLower),
      );
    }
    
    return filtered;
  }, [rows, search, quarterFilter]);

  // Delete handler
  const handleDeleteExport = (file) => {
    setFileToDelete(file);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteExport = async () => {
    if (!fileToDelete) return;
    try {
      await fetch(`${API_URL}/api/user_exports/${fileToDelete.filename}`, { method: 'DELETE' });
      setUserExports((prev) => prev.filter(f => f.filename !== fileToDelete.filename));
    } catch (e) {
      console.warn("تعذر حذف ملف التصدير", e);
    }
    setDeleteDialogOpen(false);
    setFileToDelete(null);
  };

  const cancelDeleteExport = () => {
    setDeleteDialogOpen(false);
    setFileToDelete(null);
  };

  // Function to handle custom date export
  const handleCustomDateExport = async () => {
    try {
      setLoading(true);
      
      // Build the API URL with custom date and filename
      let apiUrl = `${API_URL}/api/export_excel?quarter=${quarterFilter}&custom_date=${customExportDate}`;
      if (customFileName.trim()) {
        apiUrl += `&custom_filename=${encodeURIComponent(customFileName.trim())}`;
      }
      
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const filename = filenameFromContentDispositionHeader(
        response.headers.get("content-disposition"),
      );

      const blob = await response.blob();
      downloadBlobAsFile(blob, filename);

      setCustomExportDate("");
      setCustomFileName("");

      await refreshUserExportsSidebar(
        setUserExports,
        setUserExportsLoading,
        setUserExportsError,
        "تعذر تحديث قائمة التصدير بعد التصدير المخصص",
      );
        
      // Show enhanced success message
      const successMessage = `✅ تم التصدير بنجاح!\n\n📁 اسم الملف: ${filename}\n📅 التاريخ: ${customExportDate}\n🎯 الربع: ${quarterLabelFromDateString(customExportDate)}\n\nتم حفظ الملف في مجلد التنزيلات`;
      alert(successMessage);
      
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      alert(`❌ فشل في تصدير ملف Excel\n\n${messageForCustomExportFailure(error)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box dir="rtl" sx={{ minHeight: "100vh", bgcolor: "#f4f6fa", fontFamily: "'Tajawal', 'Cairo', 'Noto Sans Arabic', sans-serif", display: 'flex', flexDirection: 'column' }}>
      {/* Sidebar menu button at the top right, no background */}
      { !drawerOpen && (
        <Box sx={{ width: '100%', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', pt: 1, pr: 0.2 }}>
          <IconButton
            onClick={() => setDrawerOpen(true)}
            sx={{
              bgcolor: 'transparent',
              boxShadow: 'none',
              borderRadius: 2,
              p: 0,
              '&:hover': { bgcolor: '#e3ecfa' },
            }}
            size="large"
            aria-label="فتح القائمة الجانبية"
          >
            <MenuIcon sx={{ color: '#1e6641', fontSize: 32 }} />
          </IconButton>
        </Box>
      )}

      {/* Main app container */}
      {/* Header with gradient */}
      <Box sx={{
        width: '100%',
        py: { xs: 3, md: 4 },
        px: 0,
        mb: 0,
        background: 'linear-gradient(90deg, #0d3b23 0%, #1e6641 100%)',
        boxShadow: '0 6px 24px 0 rgba(20, 83, 45, 0.18)',
        borderBottom: '4px solid #14532d',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        flexDirection: 'row', // logo on the right for RTL
        justifyContent: 'flex-start',
      }}>
        <img
          src="/sama-header.png"
          alt="Saudi Central Bank Logo"
          style={{
            height: '96px',
            width: 'auto',
            marginLeft: 0,
            marginRight: 0,
            display: 'block',
            flexShrink: 0,
            filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.08))',
            objectFit: 'contain',
          }}
        />
      </Box>
      {/* Title and subtitle below header */}
      <Box sx={{ textAlign: 'right', mt: { xs: 3, md: 5 }, mb: { xs: 3, md: 5 }, pr: { xs: 2, md: 8 } }}>
        <Typography variant="h3" fontWeight="bold" sx={{ mb: 1, fontSize: { xs: 26, md: 36 }, color: '#1e6641', display: 'inline-block' }}>
          جدول ملكية الأجانب والأرباح المبقاة
        </Typography>
        <Box sx={{ height: 4, width: 120, bgcolor: '#1e6641', mr: 0, ml: 'unset', borderRadius: 2, mb: 2 }} />
        <Typography variant="subtitle1" sx={{ color: '#37474f', fontSize: { xs: 15, md: 20 } }}>
          بيانات محدثة من تداول السعودية - ملكية الأجانب والأرباح المبقاة في الشركات المدرجة
        </Typography>
      </Box>

              {/* Main card */}
        <Paper elevation={4} sx={{
          maxWidth: '85vw',
          mx: 'auto',
          p: { xs: 2, md: 3 },
          borderRadius: 4,
          boxShadow: '0 6px 32px 0 rgba(30,102,65,0.10)',
          mb: 4,
          width: '100%',
        }}>
        {/* Search/filter area styled like the provided image */}
                  <Box sx={{
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            alignItems: { xs: 'stretch', md: 'center' },
            justifyContent: 'space-between',
            bgcolor: '#f3f4f6',
            p: 2,
            mb: 2,
            borderRadius: 2,
            gap: { xs: 2, md: 0 },
          }}>
          {/* Search box in the right corner */}
          <Stack spacing={1} sx={{ minWidth: 320, maxWidth: 400, width: "100%", textAlign: "right" }}>
            <Typography sx={{ fontWeight: "bold", color: "#37474f", fontSize: 18 }}>
              رمز / شركة بحث
            </Typography>
            <TextField
              fullWidth
              placeholder="رمز / شركة بحث"
              variant="outlined"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ bgcolor: "white" }}
              inputProps={{ style: { textAlign: "right" } }}
            />
          </Stack>
          {/* Reset button in the left corner */}
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: { xs: 'flex-start', md: 'flex-end' }, 
            width: { xs: '100%', md: 'auto' }, 
            height: '100%', 
            gap: 4 
          }}>
            {/* Secondary Reset Button */}
            <Button
              variant="text"
              onClick={handleReset}
              startIcon={<RefreshIcon sx={{ fontSize: 18, color: '#6c757d' }} />}
              sx={{
                minWidth: 150,
                height: 48,
                px: 4,
                py: 2,
                borderRadius: 3,
                bgcolor: '#f8f9fa',
                color: '#6c757d',
                border: '1px solid #e9ecef',
                fontWeight: 500,
                fontSize: 14,
                textTransform: 'none',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  bgcolor: '#e9ecef',
                  borderColor: '#dee2e6',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                },
              }}
            >
              إعادة تعيين
            </Button>
            
            {/* Primary Download Button */}
            <Tooltip title="تصدير الجدول إلى Excel" arrow placement="top">
              <Button
                variant="contained"
                onClick={handleExcelExport}
                startIcon={<FileDownloadIcon sx={{ fontSize: 18, color: 'white' }} />}
                sx={{
                  minWidth: 150,
                  height: 48,
                  px: 4,
                  py: 2,
                  borderRadius: 3,
                  bgcolor: '#1e6641',
                  color: 'white',
                  fontWeight: 600,
                  fontSize: 14,
                  textTransform: 'none',
                  boxShadow: '0 4px 12px rgba(30, 102, 65, 0.3)',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    bgcolor: '#14532d',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 6px 16px rgba(30, 102, 65, 0.4)',
                  },
                }}
              >
                تصدير الجدول
              </Button>
            </Tooltip>

            {/* Unified Update Button */}
            <Tooltip title="تحديث البيانات" arrow placement="top">
              <Button
                variant="outlined"
                onClick={() => setUpdateModalOpen(true)}
                sx={{
                  minWidth: 150,
                  height: 48,
                  px: 3,
                  py: 2,
                  borderRadius: 3,
                  color: '#1e6641',
                  borderColor: '#1e6641',
                  fontWeight: 600,
                  fontSize: 14,
                  textTransform: 'none',
                }}
              >
                تحديث
              </Button>
            </Tooltip>

            <PipelineProgressModal
              open={pdfProgressOpen}
              width={420}
              title="تحديث PDF قيد التنفيذ"
              titleColor="#1e6641"
              linearColor="success"
              footer={
                <Button variant="outlined" onClick={requestStopPdfPipeline} sx={{ color: '#b71c1c', borderColor: '#b71c1c' }}>إيقاف</Button>
              }
            >
              <Typography sx={{ fontSize: 13, color: '#1e6641', mt: 1 }}>
                {pipelineJobStatusLine(pdfJobStatus)}
              </Typography>
            </PipelineProgressModal>

            <UpdateJobsDialog
              open={updateModalOpen}
              onClose={() => setUpdateModalOpen(false)}
              apiUrl={API_URL}
              selectPdf={selectPdf}
              setSelectPdf={setSelectPdf}
              selectNet={selectNet}
              setSelectNet={setSelectNet}
              startPollPdf={startPollPdf}
              startPollNet={startPollNet}
              setPdfJobStatus={setPdfJobStatus}
              setPdfProgressOpen={setPdfProgressOpen}
              setNetJobStatus={setNetJobStatus}
              setNetProgressOpen={setNetProgressOpen}
              setBothProgressOpen={setBothProgressOpen}
              setBothPdfRunning={setBothPdfRunning}
              setBothNetRunning={setBothNetRunning}
              bothPdfRunning={bothPdfRunning}
              bothNetRunning={bothNetRunning}
            />

            <PipelineProgressModal
              open={bothProgressOpen}
              width={520}
              title="التحديث قيد التنفيذ"
              titleColor="#1e6641"
              linearColor="success"
              titleMarginBottom={2}
              footer={
                <Button
                  variant="outlined"
                  onClick={async () => {
                    setBothIsStopping(true);
                    await requestStopPdfPipeline();
                    await requestStopNetProfitPipeline();
                  }}
                  disabled={bothIsStopping}
                  sx={stopBothJobsButtonSx(bothIsStopping)}
                >
                  {bothIsStopping ? 'جاري الإنهاء...' : 'إيقاف'}
                </Button>
              }
            >
              {((pdfJobStatus?.status === 'finalizing') || (netJobStatus?.status === 'finalizing')) && (
                <Typography sx={{ mt: 1, fontSize: 13, color: '#555' }}>
                  جارٍ الإنهاء: إيقاف العمليات، حساب النتائج، وتحديث اللوحة. يرجى الانتظار حتى يكتمل التحديث.
                </Typography>
              )}
              <Typography sx={{ fontSize: 13, color: '#1e6641', mt: 1 }}>
                {pipelineJobStatusLine(pdfJobStatus, "الأرباح المبقاة")}
              </Typography>
              <Typography sx={{ fontSize: 13, color: '#ff9800' }}>
                {pipelineJobStatusLine(netJobStatus, "صافي الربح")}
              </Typography>
            </PipelineProgressModal>
            <PipelineProgressModal
              open={netProgressOpen}
              width={420}
              title="تحديث صافي الربح قيد التنفيذ"
              titleColor="#ff9800"
              linearColor="warning"
              footer={
                <Button variant="outlined" onClick={requestStopNetProfitPipeline} sx={{ color: '#b71c1c', borderColor: '#b71c1c' }}>إيقاف</Button>
              }
            >
              <Typography sx={{ fontSize: 13, color: '#ff9800', mt: 1 }}>
                {pipelineJobStatusLine(netJobStatus)}
              </Typography>
            </PipelineProgressModal>
          </Box>
        </Box>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2, flexWrap: "wrap" }}>
            <TextField
              select
              label="تصفية حسب الربع"
              variant="outlined"
              size="small"
              value={quarterFilter}
              onChange={(e) => setQuarterFilter(e.target.value)}
              sx={{
                minWidth: 200,
                "& .MuiOutlinedInput-root": {
                  borderRadius: 2,
                  "& fieldset": { borderColor: "#e0e0e0" },
                  "&:hover fieldset": { borderColor: "#1e6641" },
                  "&:focus fieldset": { borderColor: "#1e6641" },
                },
                "& .MuiInputLabel-root": { color: "#666" },
                "& .MuiInputLabel-root.Mui-focused": { color: "#1e6641" },
              }}
            >
              <MenuItem value="Q1">الربع الأول (Q1)</MenuItem>
              <MenuItem value="Q2">الربع الثاني (Q2)</MenuItem>
              <MenuItem value="Q3">الربع الثالث (Q3)</MenuItem>
              <MenuItem value="Q4">الربع الرابع (Q4)</MenuItem>
            </TextField>
          </Stack>
        {/* DataGrid */}
        <Box sx={{ 
          width: '100%', 
          overflow: 'auto',
          border: '1px solid #e0e0e0',
          borderRadius: 1,
          maxWidth: '100%',
          p: 0
        }}>
          <DataGrid
            rows={filteredRows}
            columns={dashboardColumns}
            pageSize={20}
            rowsPerPageOptions={[20, 50, 100]}
            disableSelectionOnClick
            autoHeight
            componentsProps={DATA_GRID_COMPONENTS_PROPS}
            columnBuffer={1}
            columnThreshold={1}
            sx={DASHBOARD_DATA_GRID_SX}
          />
        </Box>
      </Paper>
      
      {/* Evidence Modal */}
      <EvidenceModal
        open={evidenceModalOpen}
        onClose={() => setEvidenceModalOpen(false)}
        evidenceData={evidenceData}
        loading={evidenceLoading}
        error={evidenceError}
        onDataUpdate={fetchData}
      />

      {/* Footer */}
      <Box sx={{ textAlign: 'center', color: '#888', py: 2, fontSize: 16, mt: 'auto' }}>
        © {new Date().getFullYear()} مركز الابتكار
      </Box>
      {/* Delete confirmation dialog */}
      <Dialog open={deleteDialogOpen} onClose={cancelDeleteExport}>
        <DialogTitle sx={{ fontWeight: 700, color: '#1e6641' }}>تأكيد الحذف</DialogTitle>
        <DialogContent>
          <Typography>هل أنت متأكد أنك تريد حذف هذا الملف؟ لا يمكن التراجع عن هذه العملية.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelDeleteExport} sx={{ color: '#37474f' }}>إلغاء</Button>
          <Button onClick={confirmDeleteExport} sx={{ color: '#b71c1c', fontWeight: 700 }}>حذف</Button>
        </DialogActions>
      </Dialog>

      {/* Sidebar Drawer */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{ sx: { width: 340, bgcolor: '#f8f9fa', borderTopRightRadius: 16, borderBottomRightRadius: 16 } }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            px: 3,
            py: 2.5,
            bgcolor: '#fff',
            borderBottom: '1.5px solid #e0e0e0',
            boxShadow: '0 2px 8px 0 rgba(30,102,65,0.04)',
            borderTopRightRadius: 16,
            borderTopLeftRadius: 16,
            minHeight: 72,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2 }}>
              <FolderOpenIcon sx={{ color: '#1e6641', fontSize: 24, mb: '2px' }} />
              <Typography variant="h5" sx={{ fontWeight: 800, color: '#1e6641', fontSize: 20, lineHeight: 1.2 }}>
                الملفات المحفوظة
              </Typography>
            </Box>
            <IconButton
              aria-label="إغلاق القائمة الجانبية"
              onClick={() => setDrawerOpen(false)}
              sx={{
                color: '#1e6641',
                bgcolor: '#f4f6fa',
                borderRadius: '50%',
                boxShadow: '0 2px 8px 0 rgba(30,102,65,0.10)',
                p: 0.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'background 0.2s, color 0.2s, box-shadow 0.2s',
                '&:hover': { bgcolor: '#e3ecfa', color: '#14532d', boxShadow: '0 4px 16px 0 rgba(30,102,65,0.18)' },
              }}
            >
              <ArrowBackIosNewIcon sx={{ fontSize: 18, transform: 'scaleX(-1)' }} />
            </IconButton>
          </Box>
        </Box>
        {/* Soft divider and extra space below header */}
        <Box sx={{ height: 18 }} />
        <Box sx={{ width: '100%', height: 2, bgcolor: '#f4f6fa', mb: 2, borderRadius: 2 }} />
        <DrawerSectionHeader title="ملفاتك المصدّرة" />
        <List>
          <UserExportsDrawerList
            loading={userExportsLoading}
            error={userExportsError || undefined}
            files={userExports}
            onDeleteExport={handleDeleteExport}
            apiUrl={API_URL}
          />
        </List>
        <DrawerSectionHeader title="أرشيف الفترات الربعية" />
        
        {/* Custom Export Section - Right next to Quarterly Archives */}
        <Box sx={{ px: 2, mb: 2 }}>
          <Tooltip 
            title="تصدير البيانات المالية لتاريخ محدد أو نطاق زمني معين مع إمكانية تخصيص البيانات المطلوبة"
            arrow
            placement="top"
          >
            <Box sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              bgcolor: '#f8f9fa',
              borderRadius: 3,
              px: 2,
              py: 1.5,
              border: '1px solid #e9ecef',
              cursor: 'pointer',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                bgcolor: '#e9ecef',
                borderColor: '#1e6641',
                transform: 'translateY(-1px)',
                boxShadow: '0 4px 12px rgba(30, 102, 65, 0.15)',
              },
              '&:active': {
                transform: 'translateY(0px)',
              }
            }}
            onClick={() => setCustomExportExpanded(!customExportExpanded)}
            >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ 
                width: 20, 
                height: 20, 
                bgcolor: '#1e6641', 
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 12,
                fontWeight: 'bold',
                transition: 'all 0.3s ease-in-out',
                animation: customExportExpanded ? 'pulse 2s infinite' : 'none',
                '@keyframes pulse': {
                  '0%': { transform: 'scale(1)' },
                  '50%': { transform: 'scale(1.1)' },
                  '100%': { transform: 'scale(1)' },
                }
              }}>
              </Box>
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  color: '#495057',
                  fontSize: 14,
                  transition: 'color 0.3s ease-in-out',
                }}
              >
                تصدير مخصص
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: '#6c757d',
                  fontSize: 11,
                  opacity: 0.8,
                  display: 'block',
                  lineHeight: 1.2
                }}
              >
                تصدير البيانات لتاريخ محدد
              </Typography>
            </Box>
            <IconButton
              size="small"
              sx={{
                color: '#1e6641',
                p: 0.5,
                transition: 'all 0.3s ease-in-out',
                transform: customExportExpanded ? 'rotate(45deg)' : 'rotate(0deg)',
                '&:hover': { 
                  color: '#14532d',
                  bgcolor: 'rgba(30, 102, 65, 0.1)',
                  transform: customExportExpanded ? 'rotate(45deg) scale(1.1)' : 'scale(1.1)',
                },
              }}
            >
              <Add />
            </IconButton>
          </Box>
          </Tooltip>
        </Box>
        
        <CustomExportModal
          open={customExportExpanded}
          onClose={() => setCustomExportExpanded(false)}
          customExportDate={customExportDate}
          onCustomExportDateChange={setCustomExportDate}
          customFileName={customFileName}
          onCustomFileNameChange={setCustomFileName}
          loading={loading}
          onExport={handleCustomDateExport}
        />

        {/* Quarterly Archives List */}
        <List>
          <QuarterlySnapshotsDrawerList
            loading={snapshotsLoading}
            error={snapshotsError || undefined}
            snapshots={snapshots}
            apiUrl={API_URL}
          />
        </List>
      </Drawer>
    </Box>
  );
}

export default App;
