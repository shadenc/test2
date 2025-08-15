import React, { useState, useEffect, useMemo } from "react";
import { DataGrid } from "@mui/x-data-grid";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Paper from "@mui/material/Paper";
import RefreshIcon from "@mui/icons-material/Refresh";
import Typography from "@mui/material/Typography";
import Papa from "papaparse";
import Modal from "@mui/material/Modal";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import VisibilityIcon from "@mui/icons-material/Visibility";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
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
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Collapse from '@mui/material/Collapse';
import MenuIcon from '@mui/icons-material/Menu';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import MenuItem from '@mui/material/MenuItem';

// Evidence Modal Component
const EvidenceModal = ({ open, onClose, evidenceData, loading, error }) => {
  const [verifyMode, setVerifyMode] = useState(null); // null | 'confirm' | 'incorrect'
  const [correctionValue, setCorrectionValue] = useState("");
  const [correctionFeedback, setCorrectionFeedback] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="evidence-modal-title"
      aria-describedby="evidence-modal-description"
    >
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: { xs: '95%', md: '80%' },
        maxWidth: 800,
        maxHeight: '90vh',
        bgcolor: 'background.paper',
        borderRadius: 3,
        boxShadow: 24,
        p: 3,
        overflow: 'auto',
        direction: 'rtl'
      }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography id="evidence-modal-title" variant="h5" component="h2" sx={{ fontWeight: 'bold', color: '#1e6641' }}>
            دليل الاستخراج - الأرباح المبقاة
          </Typography>
          <IconButton onClick={onClose} sx={{ color: '#666' }}>
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Content */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
            <CircularProgress sx={{ color: '#1e6641' }} />
            <Typography sx={{ ml: 2, color: '#666' }}>جاري تحميل الدليل...</Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {evidenceData && !loading && (
          <Box>
            {/* Company Info */}
            <Box sx={{ mb: 3, p: 2, bgcolor: '#f8f9fa', borderRadius: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, color: '#1e6641' }}>
                معلومات الشركة
              </Typography>
              <Typography><strong>الرمز:</strong> {evidenceData.company_symbol}</Typography>
              <Typography><strong>اسم الشركة:</strong> {evidenceData.company_name}</Typography>
              {evidenceData.year && <Typography><strong>السنة:</strong> {evidenceData.year}</Typography>}
            </Box>

            {/* Screenshot */}
            {evidenceData.evidence && evidenceData.evidence.has_evidence && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#1e6641' }}>
                  لقطة شاشة من المستند
                </Typography>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center',
                  border: '2px solid #e0e0e0',
                  borderRadius: 2,
                  overflow: 'hidden',
                  bgcolor: '#fafafa'
                }}>
                  <img 
                    src={`http://localhost:5002/api/evidence/${evidenceData.company_symbol}.png`} 
                    alt="Evidence Screenshot"
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: '600px',
                      objectFit: 'contain'
                    }}
                  />
                </Box>
              </Box>
            )}

            {/* Extraction Details */}
            {evidenceData.numeric_value && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#1e6641' }}>
                  تفاصيل الاستخراج
                </Typography>
                <Box sx={{ 
                  p: 2, 
                  bgcolor: '#f8f9fa', 
                  borderRadius: 2,
                  border: '1px solid #e0e0e0'
                }}>
                  <Typography><strong>القيمة المستخرجة:</strong> {evidenceData.numeric_value?.toLocaleString('en-US')} SAR</Typography>
                  {evidenceData.pdf_filename && <Typography><strong>اسم الملف:</strong> {evidenceData.pdf_filename}</Typography>}
                  {evidenceData.extraction_method && <Typography><strong>طريقة الاستخراج:</strong> {evidenceData.extraction_method}</Typography>}
                </Box>
              </Box>
            )}

            {/* Raw Text Context */}
            {evidenceData.context && (
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#1e6641' }}>
                  النص المستخرج
                </Typography>
                <Box sx={{ 
                  p: 2, 
                  bgcolor: '#f8f9fa', 
                  borderRadius: 2,
                  border: '1px solid #e0e0e0',
                  fontFamily: 'monospace',
                  fontSize: '14px',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '200px',
                  overflow: 'auto'
                }}>
                  {evidenceData.context}
                </Box>
              </Box>
            )}
            {evidenceData && evidenceData.context && !loading && (
              <Box sx={{ mt: 2, textAlign: 'left' }}>
                <Tooltip title="تعديل النتيجة" arrow>
                  <IconButton
                    size="small"
                    sx={{ color: '#1e6641', opacity: 0.7, ml: 1, '&:hover': { opacity: 1, bgcolor: '#e8f5ee' } }}
                    onClick={() => setVerifyMode(verifyMode ? null : 'form')}
                  >
                    <InfoOutlinedIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                {verifyMode === 'form' && (
                  <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <TextField
                      size="small"
                      label="القيمة الصحيحة"
                      value={correctionValue}
                      onChange={e => setCorrectionValue(e.target.value)}
                      sx={{ maxWidth: 180 }}
                    />
                    <TextField
                      size="small"
                      label="ملاحظات (اختياري)"
                      value={correctionFeedback}
                      onChange={e => setCorrectionFeedback(e.target.value)}
                      sx={{ maxWidth: 250 }}
                    />
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      sx={{ fontSize: 13, px: 2, py: 0.5, mt: 1, alignSelf: 'flex-start' }}
                      onClick={async () => {
                        setSubmitted(true);
                        // Send correction to backend
                        try {
                          const res = await fetch('http://localhost:5002/api/correct_retained_earnings', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              company_symbol: evidenceData.company_symbol || evidenceData.symbol,
                              correct_value: correctionValue,
                              feedback: correctionFeedback,
                            })
                          });
                          const data = await res.json();
                          if (data.status === 'success' && data.updated) {
                            if (typeof window.updateRowAfterCorrection === 'function') {
                              window.updateRowAfterCorrection(data.updated);
                            }
                          }
                        } catch (e) {}
                        setVerifyMode(null);
                      }}
                    >
                      إرسال التصحيح
                    </Button>
                    {submitted && (
                      <Typography sx={{ color: '#1e6641', fontSize: 14, mt: 1 }}>شكرًا لملاحظتك! تم تسجيل التصحيح.</Typography>
                    )}
                  </Box>
                )}
                {submitted && !verifyMode && (
                  <Typography sx={{ color: '#1e6641', fontSize: 14, mt: 1 }}>شكرًا لملاحظتك! تم تسجيل التصحيح.</Typography>
                )}
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Modal>
  );
};

const getColumns = (quarterFilter) => [
  { field: "symbol", headerName: "رمز الشركة", width: 150, align: "right", headerAlign: "right" },
  { field: "company_name", headerName: "الشركة", width: 250, align: "right", headerAlign: "right" },
  { field: "foreign_ownership", headerName: "ملكية جميع المستثمرين الأجانب", width: 280, align: "right", headerAlign: "right" },
  { field: "max_allowed", headerName: "الملكية الحالية", width: 200, align: "right", headerAlign: "right" },
  { field: "investor_limit", headerName: "ملكية المستثمر الاستراتيجي الأجنبي", width: 280, align: "right", headerAlign: "right" },
  { 
    field: "previous_quarter_value", 
    headerName: `الأرباح المبقاة للربع السابق (${quarterFilter === "Q1" ? "2024Q4" : quarterFilter === "Q2" ? "2025Q1" : quarterFilter === "Q3" ? "2025Q2" : quarterFilter === "Q4" ? "2025Q3" : "2024Q4"})`, 
    width: 300, 
    align: "right", 
    headerAlign: "right",
    renderCell: (params) => {
      const value = params.value;
      if (!value || value === "" || value === "null" || value === "undefined") {
        return "لايوجد";
      }
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography>{numValue.toLocaleString('en-US')}</Typography>
            <IconButton 
              size="small" 
              onClick={(e) => {
                e.stopPropagation();
                params.row.onEvidenceClick && params.row.onEvidenceClick(params.row);
              }}
              sx={{ 
                color: '#1e6641',
                '&:hover': { bgcolor: '#e8f5ee' }
              }}
            >
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Box>
        );
      }
      return value;
    }
  },
  { 
    field: "current_quarter_value", 
    headerName: `الأرباح المبقاة للربع الحالي (${quarterFilter === "Q1" ? "2025Q1" : quarterFilter === "Q2" ? "2025Q2" : quarterFilter === "Q3" ? "2025Q3" : quarterFilter === "Q4" ? "2025Q4" : "2025Q1"})`, 
    width: 300, 
    align: "right", 
    headerAlign: "right",
    renderCell: (params) => {
      const value = params.value;
      if (!value || value === "" || value === "null" || value === "undefined") {
        return "لايوجد";
      }
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography>{numValue.toLocaleString('en-US')}</Typography>
            <IconButton 
              size="small" 
              onClick={(e) => {
                e.stopPropagation();
                params.row.onEvidenceClick && params.row.onEvidenceClick(params.row);
              }}
              sx={{ 
                color: '#1e6641',
                '&:hover': { bgcolor: '#e8f5ee' }
              }}
            >
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Box>
        );
      }
      return value;
    }
  },
  { 
    field: "flow", 
    headerName: "حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)", 
    width: 350, 
    align: "right", 
    headerAlign: "right",
    renderCell: (params) => {
      const value = params.value;
      if (!value || value === "" || value === "null" || value === "undefined") {
        return "لايوجد";
      }
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        const isPositive = numValue >= 0;
        const color = isPositive ? '#2e7d32' : '#d32f2f';
        const sign = isPositive ? '+' : '';
        return (
          <Typography sx={{ color, fontWeight: 'bold' }}>
            {sign}{numValue.toLocaleString('en-US')} SAR
          </Typography>
        );
      }
      return value;
    }
  },
  { 
    field: "foreign_investor_flow", 
    headerName: "تدفق الأرباح المبقاة للمستثمر الأجنبي", 
    width: 350, 
    align: "right", 
    headerAlign: "right",
    renderCell: (params) => {
      const value = params.value;
      if (!value || value === "" || value === "null" || value === "undefined") {
        return "لايوجد";
      }
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        return numValue.toLocaleString('en-US');
      }
      return value;
    }
  },
];

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
  const [snapshotsExpanded, setSnapshotsExpanded] = useState(false);
  const [userExports, setUserExports] = useState([]);
  const [userExportsLoading, setUserExportsLoading] = useState(false);
  const [userExportsError, setUserExportsError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);

  // Function to fetch evidence data
  const fetchEvidence = async (companySymbol) => {
    setEvidenceLoading(true);
    setEvidenceError(null);
    
    try {
      // First fetch the extraction metadata for the company
      const response = await fetch(`http://localhost:5002/api/extractions/${companySymbol}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setEvidenceData(data);
    } catch (error) {
      console.error('Error fetching evidence:', error);
      setEvidenceError('فشل في تحميل دليل الاستخراج. تأكد من تشغيل خادم الأدلة.');
    } finally {
      setEvidenceLoading(false);
    }
  };

  // Function to handle evidence button click
  const handleEvidenceClick = (row) => {
    if (row.current_quarter_value && row.current_quarter_value !== "لايوجد") {
      setEvidenceModalOpen(true);
      fetchEvidence(row.symbol);
    }
  };

  // Function to handle reset (إعادة تعيين)
  const handleReset = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5002/api/refresh', {
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
      alert('تعذر الاتصال بالخادم: ' + error.message);
      setLoading(false);
    }
  };

  // Function to handle Excel export
  const handleExcelExport = async () => {
    try {
      const response = await fetch('http://localhost:5002/api/export_excel');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Get the filename from the response headers
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'dashboard_table.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Refetch user exports so the new file appears in the sidebar
      setUserExportsLoading(true);
      fetch('http://localhost:5002/api/user_exports')
        .then(res => res.json())
        .then(data => {
          setUserExports(data);
          setUserExportsLoading(false);
        })
        .catch(err => {
          setUserExportsError('فشل في تحميل ملفات قام المستخدم بحفظها');
          setUserExportsLoading(false);
        });
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      alert('فشل في تصدير ملف Excel: ' + error.message);
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
    const loadQuarterlyFlowData = fetch("http://localhost:5002/api/retained_earnings_flow.csv")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.text();
      })
      .then((csvText) => {
        return new Promise((resolve) => {
          Papa.parse(csvText, {
            header: true,
            complete: (result) => {
              console.log("CSV parsing result:", result);
              if (result.data && result.data.length > 0) {
                // Clean and process CSV data
                const cleanedData = result.data
                  .filter(row => row.company_symbol && row.company_symbol.trim() !== '')
                  .map((row) => {
                    const cleanedRow = {};
                    Object.keys(row).forEach(key => {
                      const cleanKey = key.trim();
                      cleanedRow[cleanKey] = row[key] ? row[key].trim() : '';
                    });
                    return cleanedRow;
                  });
                console.log("Cleaned CSV data:", cleanedData);
                resolve(cleanedData);
              } else {
                console.log("No CSV data found");
                resolve([]);
              }
            },
            error: (error) => {
              console.error("Error parsing CSV data:", error);
              resolve([]);
            }
          });
        });
      })
      .catch((error) => {
        console.error("Error loading quarterly flow data:", error);
        return [];
      });

    // Combine both datasets
    Promise.all([loadForeignOwnership, loadQuarterlyFlowData])
      .then(([foreignOwnershipData, quarterlyFlowData]) => {
        console.log("Foreign ownership data count:", foreignOwnershipData.length);
        console.log("Quarterly flow data count:", quarterlyFlowData.length);
        
        // Create a map of quarterly flow data by symbol and quarter
        const flowMap = {};
        
        quarterlyFlowData.forEach(row => {
          const symbol = row.company_symbol ? row.company_symbol.toString().trim() : "";
          const quarter = row.quarter ? row.quarter.toString().trim() : "";
          if (symbol && quarter) {
            if (!flowMap[symbol]) {
              flowMap[symbol] = {};
            }
            flowMap[symbol][quarter] = {
              previous_value: row.previous_value || "",
              current_value: row.current_value || "",
              flow: row.flow || "",
              flow_formula: row.flow_formula || "",
              year: row.year || "",
              foreign_investor_flow: row.reinvested_earnings_flow || ""
            };
            console.log(`Mapped flow data for ${symbol} ${quarter}:`, flowMap[symbol][quarter]);
          }
        });

        console.log("Flow map keys:", Object.keys(flowMap));
        console.log("Sample flow data for 2222:", flowMap["2222"]);

        // Merge the data - create a row for each available quarter
        const mergedData = [];
        
        foreignOwnershipData.forEach((row, idx) => {
          const symbol = row.symbol ? row.symbol.toString().trim() : "";
          const flowData = flowMap[symbol] || {};
          const hasFlowData = symbol in flowMap;
          
          if (hasFlowData) {
            console.log(`Found flow data for ${symbol}:`, flowData);
            
            // Create a row for each available quarter
            Object.keys(flowData).forEach(quarter => {
              const quarterData = flowData[quarter] || {};
              
              const mergedRow = {
                ...row,
                previous_quarter_value: quarterData.previous_value || "",
                current_quarter_value: quarterData.current_value || "",
                flow: quarterData.flow || "",
                flow_formula: quarterData.flow_formula || "",
                year: quarterData.year || "",
                foreign_investor_flow: quarterData.foreign_investor_flow || "",
                quarter: quarter,
                id: symbol + "_" + quarter + "_" + idx,
                onEvidenceClick: handleEvidenceClick, // Add the evidence click handler
              };
              
              // Debug: Log first few rows to see the data structure
              if (mergedData.length < 5 || symbol === "2222") {
                console.log(`Row ${mergedData.length} (${symbol} ${quarter}):`, {
                  symbol: mergedRow.symbol,
                  company_name: mergedRow.company_name,
                  quarter: mergedRow.quarter,
                  flow: mergedRow.flow,
                  flow_formula: mergedRow.flow_formula
                });
              }
              
              mergedData.push(mergedRow);
            });
          } else {
            // If no flow data, create a default row
            const mergedRow = {
              ...row,
              previous_quarter_value: "",
              current_quarter_value: "",
              flow: "",
              flow_formula: "",
              year: "",
              foreign_investor_flow: "",
              quarter: "Q1", // Default quarter
              id: symbol + "_default_" + idx,
              onEvidenceClick: handleEvidenceClick,
            };
            mergedData.push(mergedRow);
          }
        });

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
    setSnapshotsLoading(true);
    fetch('http://localhost:5002/api/ownership_snapshots')
      .then(res => res.json())
      .then(data => {
        setSnapshots(data);
        setSnapshotsLoading(false);
      })
      .catch(err => {
        setSnapshotsError('فشل في تحميل ملفات الفترات السابقة');
        setSnapshotsLoading(false);
      });
  }, []);

  // Fetch user exports
  useEffect(() => {
    setUserExportsLoading(true);
    fetch('http://localhost:5002/api/user_exports')
      .then(res => res.json())
      .then(data => {
        setUserExports(data);
        setUserExportsLoading(false);
      })
      .catch(err => {
        setUserExportsError('فشل في تحميل ملفات قام المستخدم بحفظها');
        setUserExportsLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  // In App(), define a function to update the row and attach it to window so the modal can call it
  useEffect(() => {
    window.updateRowAfterCorrection = (updated) => {
      setRows((prevRows) => prevRows.map(row => {
        if (row.symbol && updated.company_symbol && row.symbol.toString() === updated.company_symbol.toString()) {
          return {
            ...row,
            retained_earnings: updated.retained_earnings || updated.value || '',
            reinvested_earnings: updated.reinvested_earnings || '',
            year: updated.year || '',
            error: updated.error || '',
          };
        }
        return row;
      }));
    };
    return () => { window.updateRowAfterCorrection = undefined; };
  }, []);

  // Filter rows based on search and quarter filter
  const filteredRows = useMemo(() => {
    let filtered = rows;
    
    // Show all companies but only those with data for the selected quarter will have actual values
    // Companies without data for the selected quarter will show "لايوجد"
    filtered = filtered.filter(row => {
      // Always show the row, but only if it has the selected quarter data
      return row.quarter === quarterFilter;
    });
    
    // If no companies have data for the selected quarter, show all companies with "لايوجد" values
    if (filtered.length === 0) {
      // Get unique companies from all rows
      const uniqueCompanies = new Map();
      rows.forEach(row => {
        if (!uniqueCompanies.has(row.symbol)) {
          uniqueCompanies.set(row.symbol, {
            ...row,
            previous_quarter_value: "لايوجد",
            current_quarter_value: "لايوجد",
            flow: "لايوجد",
            foreign_investor_flow: "لايوجد",
            quarter: quarterFilter,
            id: row.symbol + "_" + quarterFilter + "_no_data"
          });
        }
      });
      filtered = Array.from(uniqueCompanies.values());
    }
    
    console.log(`Showing ${filtered.length} companies for ${quarterFilter}`);
    
    // Then apply search filter
    if (search) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter((row) =>
        (row.symbol && row.symbol.toString().toLowerCase().includes(searchLower)) ||
        (row.company_name && row.company_name.toLowerCase().includes(searchLower))
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
      await fetch(`http://localhost:5002/api/user_exports/${fileToDelete.filename}`, { method: 'DELETE' });
      setUserExports((prev) => prev.filter(f => f.filename !== fileToDelete.filename));
    } catch (e) {}
    setDeleteDialogOpen(false);
    setFileToDelete(null);
  };

  const cancelDeleteExport = () => {
    setDeleteDialogOpen(false);
    setFileToDelete(null);
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
        maxWidth: 1800,
        mx: 'auto',
        p: { xs: 2, md: 4 },
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
          p: 3,
          mb: 3,
          borderRadius: 2,
          gap: { xs: 2, md: 0 },
        }}>
          {/* Search box in the right corner */}
          <Box sx={{ minWidth: 320, maxWidth: 400, width: '100%', textAlign: 'right' }}>
            <Typography sx={{ mb: 1, fontWeight: 'bold', color: '#37474f', fontSize: 18 }}>
              رمز / شركة بحث
            </Typography>
            <TextField
              fullWidth
              placeholder="رمز / شركة بحث"
              variant="outlined"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ bgcolor: 'white' }}
              inputProps={{ style: { textAlign: 'right' } }}
            />
          </Box>
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
                '&:hover': {
                  bgcolor: '#e9ecef',
                  borderColor: '#dee2e6',
                  transform: 'translateY(-1px)',
                },
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                '&:hover': {
                  boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                },
                transition: 'all 0.2s ease-in-out'
              }}
            >
              <RefreshIcon sx={{ fontSize: 18, color: '#6c757d' }} />
              إعادة تعيين
            </Button>
            
            {/* Primary Download Button */}
            <Tooltip title="تصدير الجدول إلى Excel" arrow placement="top">
              <Button
                variant="contained"
                onClick={handleExcelExport}
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
                  '&:hover': {
                    bgcolor: '#14532d',
                    transform: 'translateY(-1px)',
                  },
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  boxShadow: '0 4px 12px rgba(30, 102, 65, 0.3)',
                  '&:hover': {
                    boxShadow: '0 6px 16px rgba(30, 102, 65, 0.4)',
                  },
                  transition: 'all 0.2s ease-in-out'
                }}
              >
                <FileDownloadIcon sx={{ fontSize: 18, color: 'white' }} />
                تصدير الجدول
              </Button>
            </Tooltip>
          </Box>
        </Box>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 3 }}>
            <TextField
              label="البحث في الجدول"
              variant="outlined"
              size="small"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{
                minWidth: 300,
                "& .MuiOutlinedInput-root": {
                  borderRadius: 2,
                  "& fieldset": { borderColor: "#e0e0e0" },
                  "&:hover fieldset": { borderColor: "#1e6641" },
                  "&:focus fieldset": { borderColor: "#1e6641" },
                },
                "& .MuiInputLabel-root": { color: "#666" },
                "& .MuiInputLabel-root.Mui-focused": { color: "#1e6641" },
              }}
            />
            
            {/* Quarter Filter Dropdown */}
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
            </TextField>
            
            <Tooltip title="تصدير الجدول إلى Excel">
              <Button
                variant="contained"
                onClick={handleExcelExport}
                sx={{
                  bgcolor: "#1e6641",
                  "&:hover": { bgcolor: "#155a35" },
                  borderRadius: 2,
                  px: 3,
                  py: 1,
                  textTransform: "none",
                  fontSize: 16,
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                }}
              >
                <FileDownloadIcon sx={{ fontSize: 18, color: 'white' }} />
                تصدير الجدول
              </Button>
            </Tooltip>
          </Box>
        <DataGrid
          rows={filteredRows}
          columns={getColumns(quarterFilter)}
          pageSize={20}
          loading={loading}
          sx={{
            bgcolor: "white",
            fontFamily: "'Tajawal', 'Cairo', 'Noto Sans Arabic', sans-serif",
            direction: "rtl",
            borderRadius: 4, // more rounded corners
            fontSize: 18,
            boxShadow: '0 2px 16px 0 rgba(30,102,65,0.08)',
            border: 'none',
            "& .MuiDataGrid-columnHeaders": {
              bgcolor: "#e3ecfa",
              fontWeight: "bold",
              fontSize: 18,
              position: 'sticky',
              top: 0,
              zIndex: 1,
              direction: 'rtl',
              textAlign: 'right',
              boxShadow: '0 2px 8px 0 rgba(30,102,65,0.10)', // sticky header shadow
              borderTopLeftRadius: 16,
              borderTopRightRadius: 16,
            },
            "& .MuiDataGrid-columnHeader, & .MuiDataGrid-columnHeaderTitle": {
              direction: "rtl",
              textAlign: "right",
              justifyContent: "flex-end",
              paddingRight: "12px !important",
              paddingLeft: "0 !important",
              display: 'flex',
            },
            "& .MuiDataGrid-columnHeaderTitleContainer": {
              flexDirection: "row-reverse",
              direction: 'rtl',
              display: 'flex',
              justifyContent: 'flex-end',
            },
            "& .MuiDataGrid-columnHeaderTitleContainerContent": {
              textAlign: "right",
              justifyContent: "flex-end",
              direction: 'rtl',
              display: 'flex',
            },
            "& .MuiDataGrid-row": {
              minHeight: 44,
              maxHeight: 44,
              transition: 'background 0.2s, box-shadow 0.2s',
              borderRadius: 2,
            },
            "& .MuiDataGrid-row:nth-of-type(even)": { bgcolor: "#f7fafc" }, // lighter stripe
            "& .MuiDataGrid-row:hover": {
              bgcolor: "#e3f2fd",
              boxShadow: '0 2px 8px 0 rgba(30,102,65,0.08)',
              cursor: 'pointer',
            },
            "& .MuiDataGrid-footerContainer": { bgcolor: '#f4f6fa', fontWeight: 'bold', borderBottomLeftRadius: 16, borderBottomRightRadius: 16 },
            "& .MuiDataGrid-virtualScroller": { minHeight: 300 },
            "& .MuiDataGrid-cell": {
              borderBottom: '1px solid #e0e0e0',
              fontWeight: 500,
              fontSize: 17,
              letterSpacing: '0.01em',
            },
            "& .MuiDataGrid-cell:focus, & .MuiDataGrid-columnHeader:focus": {
              outline: 'none',
            },
            "& .MuiDataGrid-root": {
              borderRadius: 4,
            },
          }}
          disableRowSelectionOnClick
          autoHeight
          localeText={{
            noRowsLabel: 'لا توجد بيانات متاحة',
          }}
        />
      </Paper>
      
      {/* Evidence Modal */}
      <EvidenceModal
        open={evidenceModalOpen}
        onClose={() => setEvidenceModalOpen(false)}
        evidenceData={evidenceData}
        loading={evidenceLoading}
        error={evidenceError}
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
        {/* User-Saved Exports Section */}
        <Box sx={{ mt: 2, pb: 0, px: 0 }}>
          <Box sx={{
            display: 'flex',
            alignItems: 'center',
            bgcolor: '#e9f5ee',
            borderRadius: 4,
            px: 2,
            py: 1.2,
            width: '100%',
            boxSizing: 'border-box',
            mb: 1.5,
            gap: 1.5,
          }}>
            <Box sx={{ width: 3, height: 24, bgcolor: '#1e6641', borderRadius: 6, mr: 0 }} />
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 700,
                color: '#1e6641',
                fontSize: 18,
                letterSpacing: 0.1,
                minWidth: 0,
                pr: 1,
              }}
            >
              ملفاتك المصدّرة
            </Typography>
          </Box>
        </Box>
        <List>
          {userExportsLoading ? (
            <ListItem sx={{ justifyContent: 'center' }}><CircularProgress size={22} sx={{ color: '#1e6641' }} /></ListItem>
          ) : userExportsError ? (
            <ListItem><Alert severity="error">{userExportsError}</Alert></ListItem>
          ) : userExports.length === 0 ? (
            <ListItem sx={{ justifyContent: 'center', alignItems: 'center', minHeight: 80, width: '100%' }}>
              <Typography sx={{ color: '#b0b7be', fontSize: 17, textAlign: 'center', width: '100%' }}>
                لا توجد ملفات محفوظة بعد
              </Typography>
            </ListItem>
          ) : (
            userExports.map((file, idx) => (
              <ListItem
                key={idx}
                tabIndex={0}
                sx={{
                  pl: 3, pr: 3, py: 2.2,
                  mb: 1.5,
                  bgcolor: '#fff',
                  borderRadius: 2.5,
                  boxShadow: '0 1px 6px 0 rgba(30,102,65,0.06)',
                  display: 'flex',
                  alignItems: 'center',
                  '&:hover .export-delete-btn': { opacity: 1 },
                  minHeight: 56,
                  border: 'none',
                  transition: 'box-shadow 0.2s, transform 0.2s',
                  '&:hover': {
                    boxShadow: '0 4px 16px 0 rgba(30,102,65,0.10)',
                    transform: 'translateY(-2px) scale(1.01)',
                  },
                  outline: 'none',
                  '&:focus': {
                    boxShadow: '0 0 0 2px #1e664144',
                  },
                }}
              >
                <Box sx={{ flexGrow: 1 }}>
                  <Typography sx={{ fontWeight: 500, color: '#1e6641', fontSize: 15 }}>
                    {(() => {
                      // file.export_date is 'YYYY-MM-DD HH:mm:ss'
                      const datePart = file.export_date.split(' ')[0];
                      const [year, month, day] = datePart.split('-');
                      return `dashboard-${day}-${month}-${year}`;
                    })()}
                  </Typography>
                </Box>
                <Tooltip title="تحميل" arrow>
                  <IconButton
                    aria-label="تحميل"
                    href={`http://localhost:5002${file.download_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{
                      color: '#1e6641',
                      bgcolor: 'transparent',
                      borderRadius: '50%',
                      p: 0.7,
                      mx: 0.5,
                      transition: 'color 0.2s, background 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
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
                    onClick={() => handleDeleteExport(file)}
                    sx={{
                      ml: 0.5,
                      opacity: 0,
                      color: '#7b7b7b',
                      bgcolor: 'transparent',
                      borderRadius: '50%',
                      p: 0.7,
                      transition: 'opacity 0.2s, color 0.2s, background 0.2s',
                      boxShadow: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 22,
                      height: 36,
                      width: 36,
                      minWidth: 36,
                      '&:hover': { color: '#444', bgcolor: 'rgba(120,120,120,0.07)' },
                    }}
                    size="small"
                  >
                    <DeleteOutlineIcon sx={{ fontSize: 22 }} />
                  </IconButton>
                </Tooltip>
              </ListItem>
            ))
          )}
        </List>
        {/* Divider between sections */}
        <Box sx={{ mt: 2, pb: 0, px: 0 }}>
          <Box sx={{
            display: 'flex',
            alignItems: 'center',
            bgcolor: '#e9f5ee',
            borderRadius: 4,
            px: 2,
            py: 1.2,
            width: '100%',
            boxSizing: 'border-box',
            mb: 1.5,
            gap: 1.5,
          }}>
            <Box sx={{ width: 3, height: 24, bgcolor: '#1e6641', borderRadius: 6, mr: 0 }} />
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 700,
                color: '#1e6641',
                fontSize: 18,
                letterSpacing: 0.1,
                minWidth: 0,
                pr: 1,
              }}
            >
              أرشيف الفترات الربعية
            </Typography>
          </Box>
        </Box>
        <List>
          {snapshotsLoading ? (
            <ListItem sx={{ justifyContent: 'center' }}><CircularProgress size={22} sx={{ color: '#1e6641' }} /></ListItem>
          ) : snapshotsError ? (
            <ListItem><Alert severity="error">{snapshotsError}</Alert></ListItem>
          ) : snapshots.length === 0 ? (
            <ListItem sx={{ justifyContent: 'center', color: '#888' }}>لا توجد ملفات محفوظة بعد</ListItem>
          ) : (
            snapshots.map((snap, idx) => (
              <ListItem key={idx} sx={{ pl: 2, pr: 2, py: 1, borderBottom: '1px solid #e0e0e0', display: 'flex', alignItems: 'center' }}>
                <span style={{ fontSize: 22, marginLeft: 8 }}>📄</span>
                <Typography sx={{ fontWeight: 500, color: '#1e6641', flexGrow: 1, fontSize: 16 }}>
                  {`${snap.year} ${snap.quarter.replace('Q', 'Q')} — ${snap.snapshot_date}`}
                </Typography>
                <Tooltip title={`تاريخ الاستخراج: ${snap.snapshot_date}`} arrow>
                  <Button
                    variant="contained"
                    color="success"
                    size="small"
                    href={`http://localhost:5002${snap.download_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ minWidth: 0, px: 2, py: 1, borderRadius: 2, fontWeight: 600 }}
                    startIcon={<DownloadIcon />}
                  >
                    تحميل
                  </Button>
                </Tooltip>
              </ListItem>
            ))
          )}
        </List>
      </Drawer>
    </Box>
  );
}

export default App;
