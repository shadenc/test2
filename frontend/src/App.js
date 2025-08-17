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
import EditIcon from '@mui/icons-material/Edit';

// Evidence Modal Component
const EvidenceModal = ({ open, onClose, evidenceData, loading, error, onDataUpdate }) => {
  const [verifyMode, setVerifyMode] = useState(null); // null | 'confirm' | 'incorrect'
  const [correctionValue, setCorrectionValue] = useState("");
  const [correctionFeedback, setCorrectionFeedback] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

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
        width: { xs: '95%', md: '70%' },
        maxWidth: 600,
        maxHeight: '80vh',
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
            {/* Screenshot */}
            {evidenceData.evidence && evidenceData.evidence.has_evidence && (
              <Box sx={{ mb: 4 }}>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center',
                  border: '2px solid #e0e0e0',
                  borderRadius: 2,
                  overflow: 'auto',
                  bgcolor: '#fafafa',
                  maxHeight: '50vh'
                }}>
                  <img 
                    src={`http://localhost:5002/api/evidence/${evidenceData.company_symbol}.png?quarter=${evidenceData.evidence?.requested_quarter || 'Q1_2025'}&t=${Date.now()}`}
                    alt="Evidence Screenshot"
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: 'none',
                      objectFit: 'contain'
                    }}
                    onLoad={() => {
                      console.log('Evidence image loaded with quarter:', evidenceData.evidence?.requested_quarter);
                      console.log('Full image URL:', `http://localhost:5002/api/evidence/${evidenceData.company_symbol}.png?quarter=${evidenceData.evidence?.requested_quarter || 'Q1_2025'}&t=${Date.now()}`);
                    }}
                  />
                </Box>
              </Box>
            )}

            {/* Extraction Details */}
            {evidenceData.numeric_value && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3, color: '#1e6641' }}>
                  تفاصيل الاستخراج
                </Typography>
                <Box sx={{ 
                  p: 4, 
                  bgcolor: '#ffffff', 
                  borderRadius: 3,
                  border: '2px solid #e8f5ee',
                  boxShadow: '0 4px 20px rgba(30, 102, 65, 0.1)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 3
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                    <Typography sx={{ fontWeight: 'bold', fontSize: '1.2rem', color: '#333' }}>
                      القيمة المستخرجة:
                    </Typography>
                    <Tooltip title="هل تحتاج لتغيير هذه القيمة؟ انقر هنا للتعديل" arrow placement="top">
                      <InlineEditableCell
                        value={evidenceData.numeric_value}
                        onSave={async (newValue) => {
                          try {
                            // Determine the field type based on the evidence data
                            let fieldType = 'current_quarter'; // default to current_quarter
                            if (evidenceData.evidence?.requested_quarter) {
                              const quarter = evidenceData.evidence.requested_quarter;
                              if (quarter.includes('Annual_2024') || quarter.includes('Q4_2024')) {
                                fieldType = 'previous_quarter';
                              } else if (quarter.includes('Q1_2025') || quarter.includes('Q2_2025') || quarter.includes('Q3_2025') || quarter.includes('Q4_2025')) {
                                fieldType = 'current_quarter';
                              }
                            }
                            
                            console.log('Determined field type:', fieldType, 'for quarter:', evidenceData.evidence?.requested_quarter);
                            
                            const requestBody = {
                              company_symbol: parseInt(evidenceData.company_symbol || evidenceData.symbol),
                              field_type: fieldType,
                              new_value: parseFloat(newValue),
                              quarter: evidenceData.evidence?.requested_quarter?.replace('Annual_2024', 'Q4').replace('Q1_2025', 'Q1').replace('Q2_2025', 'Q2').replace('Q3_2025', 'Q3').replace('Q4_2025', 'Q4') || 'Q1',
                              feedback: 'Corrected via evidence modal'
                            };
                            
                            console.log('Sending correction request:', requestBody);
                            
                            const response = await fetch('http://localhost:5002/api/correct_field_value', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify(requestBody),
                            });
                            
                            const data = await response.json();
                            console.log('Correction response:', data);
                            
                            if (data.status === 'success') {
                              // Update the evidence data to show the new value
                              evidenceData.numeric_value = newValue;
                              // Show success message
                              setUpdateSuccess(true);
                              // Call the callback to refresh the main data
                              if (onDataUpdate) {
                                onDataUpdate();
                              }
                              // Hide success message after 3 seconds
                              setTimeout(() => setUpdateSuccess(false), 3000);
                            } else {
                              const errorMessage = data.message || data.error || 'Unknown error occurred';
                              console.error('Correction failed:', errorMessage);
                              alert('فشل في حفظ التصحيح: ' + errorMessage);
                            }
                          } catch (error) {
                            alert('حدث خطأ أثناء حفظ التصحيح: ' + error.message);
                          }
                        }}
                        fieldType="retained_earnings"
                        companySymbol={evidenceData.company_symbol || evidenceData.symbol}
                        companyName={evidenceData.company_name}
                        initialValue={evidenceData.numeric_value}
                      />
                    </Tooltip>
                  </Box>
                  {evidenceData.extraction_method && (
                    <Box sx={{ 
                      p: 3,
                      bgcolor: '#f8f9fa',
                      borderRadius: 2,
                      border: '1px solid #e0e0e0'
                    }}>
                      <Typography sx={{ 
                        fontSize: '1rem',
                        color: '#666',
                        fontWeight: '500'
                      }}>
                        <strong>طريقة الاستخراج:</strong> {evidenceData.extraction_method}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            )}

            {/* Success Message */}
            {updateSuccess && (
              <Box sx={{ mb: 3 }}>
                <Alert severity="success" sx={{ borderRadius: 2 }}>
                  تم تحديث القيمة بنجاح! سيتم تحديث البيانات في الجدول الرئيسي.
                </Alert>
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

// Edit Value Modal Component
const EditValueModal = ({ open, onClose, editData, onSave, loading }) => {
  const [newValue, setNewValue] = useState("");
  const [feedback, setFeedback] = useState("");

  // Update local state when editData changes
  useEffect(() => {
    if (editData) {
      setNewValue(editData.currentValue.toString());
      setFeedback("");
    }
  }, [editData]);

  const handleSave = () => {
    if (newValue.trim() === "") {
      alert("يرجى إدخال قيمة صحيحة");
      return;
    }
    onSave(editData.companySymbol, editData.fieldType, parseFloat(newValue), feedback);
  };

  const getFieldDisplayName = (fieldType) => {
    const fieldNames = {
      'previous_quarter': 'الأرباح المبقاة للربع السابق',
      'current_quarter': 'الأرباح المبقاة للربع الحالي',
      'flow': 'حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)',
      'foreign_investor_flow': 'تدفق الأرباح المبقاة للمستثمر الأجنبي',
      'net_profit_foreign_investor': 'صافي الربح للمستثمر الأجنبي',
      'distributed_profits_foreign_investor': 'الأرباح الموزعة للمستثمر الأجنبي'
    };
    return fieldNames[fieldType] || fieldType;
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="edit-modal-title"
      aria-describedby="edit-modal-description"
    >
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: { xs: '95%', md: '500px' },
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
          <Typography id="edit-modal-title" variant="h5" component="h2" sx={{ fontWeight: 'bold', color: '#ff9800' }}>
            تعديل القيمة المستخرجة
          </Typography>
          <IconButton onClick={onClose} sx={{ color: '#666' }}>
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Content */}
        {editData && (
          <Box>
            {/* Company Info */}
            <Box sx={{ mb: 3, p: 2, bgcolor: '#f8f9fa', borderRadius: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, color: '#1e6641' }}>
                معلومات الشركة
              </Typography>
              <Typography><strong>الرمز:</strong> {editData.companySymbol}</Typography>
              <Typography><strong>اسم الشركة:</strong> {editData.companyName}</Typography>
              <Typography><strong>الحقل:</strong> {getFieldDisplayName(editData.fieldType)}</Typography>
            </Box>

            {/* Current Value */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#666' }}>
                القيمة الحالية
              </Typography>
              <Typography sx={{ fontSize: '1.2rem', color: '#1e6641', fontWeight: 'bold' }}>
                {editData.currentValue.toLocaleString('en-US')} SAR
              </Typography>
            </Box>

            {/* New Value Input */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#ff9800' }}>
                القيمة الجديدة
              </Typography>
              <TextField
                fullWidth
                type="number"
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                placeholder="أدخل القيمة الصحيحة"
                sx={{ direction: 'ltr' }}
                inputProps={{
                  style: { textAlign: 'right', fontSize: '1.1rem' }
                }}
              />
            </Box>

            {/* Feedback Input */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#666' }}>
                ملاحظات (اختياري)
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="أضف ملاحظات حول التصحيح..."
                sx={{ direction: 'rtl' }}
              />
            </Box>

            {/* Actions */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button 
                variant="outlined" 
                onClick={onClose}
                sx={{ color: '#666', borderColor: '#666' }}
              >
                إلغاء
              </Button>
              <Button 
                variant="contained" 
                onClick={handleSave}
                disabled={loading || newValue.trim() === ""}
                sx={{ 
                  bgcolor: '#ff9800', 
                  '&:hover': { bgcolor: '#f57c00' },
                  '&:disabled': { bgcolor: '#ccc' }
                }}
              >
                {loading ? <CircularProgress size={20} sx={{ color: 'white' }} /> : 'حفظ التصحيح'}
              </Button>
            </Box>
          </Box>
        )}
      </Box>
    </Modal>
  );
};

// Inline Editable Cell Component
const InlineEditableCell = ({ value, onSave, fieldType, companySymbol, companyName, initialValue }) => {
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
      const response = await fetch('http://localhost:5002/api/correct_field_value', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_symbol: companySymbol,
          field_type: fieldType,
          new_value: parseFloat(editValue),
          feedback: 'Inline edit'
        }),
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        onSave(parseFloat(editValue));
        setIsEditing(false);
      } else {
        alert('فشل في حفظ التصحيح: ' + (data.message || ''));
      }
    } catch (error) {
      alert('حدث خطأ أثناء حفظ التصحيح: ' + error.message);
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
      <Typography>{value?.toLocaleString('en-US') || 'لايوجد'}</Typography>
      <Tooltip title="هل تحتاج لتغيير هذه القيمة؟ انقر هنا للتعديل" arrow placement="top">
        <IconButton 
          size="small" 
          onClick={handleEdit}
          sx={{ 
            color: '#ff9800',
            '&:hover': { bgcolor: '#fff3e0' },
            opacity: 0.7,
            '&:hover': { opacity: 1 }
          }}
        >
          <EditIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
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
  const [snapshotsExpanded, setSnapshotsExpanded] = useState(false);
  const [userExports, setUserExports] = useState([]);
  const [userExportsLoading, setUserExportsLoading] = useState(false);
  const [userExportsError, setUserExportsError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [selectedExports, setSelectedExports] = useState(new Set());
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  const [netProfitData, setNetProfitData] = useState({});
  // Commented out since we're using inline editing
  // const [editModalOpen, setEditModalOpen] = useState(false);
  // const [editData, setEditData] = useState(null);
  // const [editLoading, setEditLoading] = useState(false);

  // Function to fetch evidence data
  const fetchEvidenceData = async (companySymbol, quarter) => {
    console.log(`Fetching evidence for ${companySymbol} quarter ${quarter}`);
    try {
      const response = await fetch(`http://localhost:5002/api/extractions/${companySymbol}?quarter=${quarter}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Evidence data received:', data);
        console.log('Evidence quarter requested:', quarter);
        console.log('Evidence quarter in response:', data.evidence?.requested_quarter);
        console.log('Screenshot path:', data.evidence?.screenshot_path);
        setEvidenceData(data);
        setEvidenceModalOpen(true);
      } else {
        console.error('Failed to fetch evidence data');
      }
    } catch (error) {
      console.error('Error fetching evidence data:', error);
    }
  };

  // Function to handle edit value button click - Commented out since we're using inline editing
  /* const handleEditValue = (companySymbol, fieldType, currentValue, companyName) => {
    setEditData({
      companySymbol,
      fieldType,
      currentValue,
      companyName,
      newValue: currentValue.toString()
    });
    setEditModalOpen(true);
  }; */

  // Function to fetch net profit data
  const fetchNetProfitData = async () => {
    try {
      const response = await fetch('http://localhost:5002/api/net-profit');
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
    if (row.current_quarter_value && row.current_quarter_value !== "لايوجد") {
      setEvidenceModalOpen(true);
      fetchEvidenceData(row.symbol, row.quarter);
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

  // Function to handle export selection
  const handleExportSelection = (fileId, checked) => {
    const newSelected = new Set(selectedExports);
    if (checked) {
      newSelected.add(fileId);
    } else {
      newSelected.delete(fileId);
    }
    setSelectedExports(newSelected);
  };

  // Function to handle select all exports
  const handleSelectAllExports = (checked) => {
    if (checked) {
      setSelectedExports(new Set(userExports.map(file => file.id)));
    } else {
      setSelectedExports(new Set());
    }
  };

  // Function to fetch user exports
  const fetchUserExports = async () => {
    setUserExportsLoading(true);
    try {
      const response = await fetch('http://localhost:5002/api/user_exports');
      if (response.ok) {
        const data = await response.json();
        setUserExports(data);
        setUserExportsError(null);
      } else {
        setUserExportsError('فشل في تحميل ملفات قام المستخدم بحفظها');
      }
    } catch (error) {
      setUserExportsError('فشل في تحميل ملفات قام المستخدم بحفظها');
    } finally {
      setUserExportsLoading(false);
    }
  };

  // Function to handle bulk delete
  const handleBulkDelete = async () => {
    if (selectedExports.size === 0) return;
    
    try {
      const deletePromises = Array.from(selectedExports).map(fileId => {
        const file = userExports.find(f => f.id === fileId);
        return fetch(`http://localhost:5002${file.download_url}`, { method: 'DELETE' });
      });
      
      await Promise.all(deletePromises);
      
      // Remove deleted files from state
      setUserExports(prev => prev.filter(file => !selectedExports.has(file.id)));
      setSelectedExports(new Set());
      setBulkDeleteDialogOpen(false);
      
      // Refresh the list
      fetchUserExports();
    } catch (error) {
      console.error('Error deleting files:', error);
      alert('حدث خطأ أثناء حذف الملفات');
    }
  };

  // Function to handle Excel export
  const handleExcelExport = async () => {
    try {
      const response = await fetch(`http://localhost:5002/api/export_excel?quarter=${quarterFilter}`);
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
              foreign_investor_flow: row.reinvested_earnings_flow || "",
              net_profit_foreign_investor: row.net_profit_foreign_investor || "",
              distributed_profits_foreign_investor: row.distributed_profits_foreign_investor || ""
            };
            
            // Debug: Log the new fields
            console.log(`Mapped flow data for ${symbol} ${quarter}:`, {
              ...flowMap[symbol][quarter],
              'net_profit_foreign_investor': row.net_profit_foreign_investor,
              'distributed_profits_foreign_investor': row.distributed_profit_foreign_investor
            });
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
          
          // Create rows for all quarters (Q1, Q2, Q3, Q4) for every company
          const allQuarters = ["Q1", "Q2", "Q3", "Q4"];
          
          allQuarters.forEach(quarter => {
            const quarterData = flowData[quarter] || {};
            
            const mergedRow = {
              ...row,
              company_symbol: symbol, // Add this for net profit column access
              previous_quarter_value: quarterData.previous_value || "",
              current_quarter_value: quarterData.current_value || "",
              flow: quarterData.flow || "",
              flow_formula: quarterData.flow_formula || "",
              year: quarterData.year || "",
              foreign_investor_flow: quarterData.foreign_investor_flow || "",
              net_profit_foreign_investor: quarterData.net_profit_foreign_investor || "",
              distributed_profits_foreign_investor: quarterData.distributed_profits_foreign_investor || "",
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

  // Define getColumns function inside the component to access state variables
  const getColumns = (quarterFilter) => [
    { field: "symbol", headerName: "رمز الشركة", width: 120, align: "right", headerAlign: "right" },
    { field: "company_name", headerName: "الشركة", width: 200, align: "right", headerAlign: "right" },
    { field: "foreign_ownership", headerName: "ملكية جميع المستثمرين الأجانب", width: 220, align: "right", headerAlign: "right" },
    { field: "max_allowed", headerName: "الملكية الحالية", width: 150, align: "right", headerAlign: "right" },
    { field: "investor_limit", headerName: "ملكية المستثمر الاستراتيجي الأجنبي", width: 220, align: "right", headerAlign: "right" },
    { 
      field: "previous_quarter_value", 
      headerName: `الأرباح المبقاة للربع السابق (${quarterFilter === "Q1" ? "2024Q4" : quarterFilter === "Q2" ? "2025Q1" : quarterFilter === "Q3" ? "2025Q2" : quarterFilter === "Q4" ? "2025Q3" : "2024Q4"})`, 
      width: 250, 
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
              <Tooltip title="عرض دليل الاستخراج - انقر لرؤية المستند الأصلي" arrow placement="top">
                <IconButton 
                  size="small" 
                  onClick={(e) => {
                    e.stopPropagation();
                    let evidenceQuarter;
                    if (quarterFilter === "Q1") {
                      evidenceQuarter = "Annual_2024"; // Corrected from Q4_2024
                    } else if (quarterFilter === "Q2") {
                      evidenceQuarter = "Q1_2025";
                    } else if (quarterFilter === "Q3") {
                      evidenceQuarter = "Q2_2025";
                    } else {
                      evidenceQuarter = "Q3_2025";
                    }
                    fetchEvidenceData(params.row.symbol, evidenceQuarter);
                    setEvidenceModalOpen(true);
                  }}
                  sx={{ 
                    color: '#1e6641',
                    '&:hover': { bgcolor: '#e8f5ee' },
                    padding: '8px',
                    minWidth: '40px',
                    width: '40px',
                    height: '40px'
                  }}
                >
                  <VisibilityIcon sx={{ fontSize: '16px' }} />
                </IconButton>
              </Tooltip>
            </Box>
          );
        }
        return value;
      }
    },
    { 
      field: "current_quarter_value", 
      headerName: `الأرباح المبقاة للربع الحالي (${quarterFilter === "Q1" ? "2025Q1" : quarterFilter === "Q2" ? "2025Q2" : quarterFilter === "Q3" ? "2025Q3" : quarterFilter === "Q4" ? "2025Q4" : "2025Q1"})`, 
      width: 250, 
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
              <Tooltip title="عرض دليل الاستخراج - انقر لرؤية المستند الأصلي" arrow placement="top">
                <IconButton 
                  size="small" 
                  onClick={(e) => {
                    e.stopPropagation();
                    // For current quarter, use the quarterFilter
                    let evidenceQuarter;
                    if (quarterFilter === "Q1") {
                      evidenceQuarter = "Q1_2025";
                    } else if (quarterFilter === "Q2") {
                      evidenceQuarter = "Q2_2025";
                    } else if (quarterFilter === "Q3") {
                      evidenceQuarter = "Q3_2025";
                    } else {
                      evidenceQuarter = "Q4_2025";
                    }
                    fetchEvidenceData(params.row.symbol, evidenceQuarter);
                    setEvidenceModalOpen(true);
                  }}
                  sx={{ 
                    color: '#1e6641',
                    '&:hover': { bgcolor: '#e8f5ee' },
                    padding: '8px',
                    minWidth: '40px',
                    width: '40px',
                    height: '40px'
                  }}
                >
                  <VisibilityIcon sx={{ fontSize: '16px' }} />
                </IconButton>
              </Tooltip>
            </Box>
          );
        }
        return value;
      }
    },
    { 
      field: "flow", 
      headerName: "حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)", 
      width: 280, 
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
      width: 250, 
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
      field: "net_profit",
      headerName: "صافي الربح",
      width: 150,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => {
        const companySymbol = params.row.company_symbol;
        const companyNetProfit = netProfitData[companySymbol];
        
        if (companyNetProfit && companyNetProfit.quarterly_net_profit) {
          // Map quarter filter to 2025 data
          let quarterKey;
          if (quarterFilter === "Q1") quarterKey = "Q1 2025";
          else if (quarterFilter === "Q2") quarterKey = "Q2 2025";
          else if (quarterFilter === "Q3") quarterKey = "Q3 2025";
          
          const value = companyNetProfit.quarterly_net_profit[quarterKey];
          
          if (value !== undefined && value !== null) {
            return value.toLocaleString('en-US');
          }
        }
        return "لايوجد";
      }
    },
    { 
      field: "net_profit_foreign_investor",
      headerName: "صافي الربح للمستثمر الأجنبي",
      width: 220,
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
            <Typography>{numValue.toLocaleString('en-US')}</Typography>
          );
        }
        return value;
      }
    },
    { 
      field: "distributed_profits_foreign_investor",
      headerName: "الأرباح الموزعة للمستثمر الأجنبي",
      width: 250,
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
    }
  ];

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchNetProfitData();
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
    
    // Filter by quarter - now all companies have rows for all quarters
    filtered = filtered.filter(row => row.quarter === quarterFilter);
    
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
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2 }}>
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
          </Box>
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
            columns={getColumns(quarterFilter)}
            pageSize={20}
            rowsPerPageOptions={[20, 50, 100]}
            disableSelectionOnClick
            autoHeight
            componentsProps={{
              toolbar: {
                showQuickFilter: true,
                quickFilterProps: { debounceMs: 500 },
              },
            }}
            // Optimize column rendering
            columnBuffer={1}
            columnThreshold={1}
            sx={{
              bgcolor: "white",
              fontFamily: "'Tajawal', 'Cairo', 'Noto Sans Arabic', sans-serif",
              direction: "rtl",
              borderRadius: 4,
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
                boxShadow: '0 2px 8px 0 rgba(30,102,65,0.10)',
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
              "& .MuiDataGrid-row:nth-of-type(even)": { bgcolor: "#f7fafc" },
              "& .MuiDataGrid-row:hover": {
                bgcolor: "#e3f2fd",
                boxShadow: '0 2px 8px 0 rgba(30,102,65,0.08)',
                cursor: 'pointer',
              },
              "& .MuiDataGrid-footerContainer": { 
                bgcolor: '#f4f6fa', 
                fontWeight: 'bold', 
                borderBottomLeftRadius: 16, 
                borderBottomRightRadius: 16 
              },
              "& .MuiDataGrid-virtualScroller": { minHeight: 300 },
              "& .MuiDataGrid-cell": {
                borderBottom: '1px solid #e0e0e0',
                fontWeight: 500,
                fontSize: 17,
                letterSpacing: '0.01em',
                direction: 'rtl',
                textAlign: 'right',
              },
              "& .MuiDataGrid-cell:focus, & .MuiDataGrid-columnHeader:focus": {
                outline: 'none',
              },
              "& .MuiDataGrid-root": {
                borderRadius: 4,
              },
            }}
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
      
      {/* Edit Value Modal - Commented out since we're using inline editing */}
      {/* <EditValueModal
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        editData={editData}
        onSave={async (companySymbol, fieldType, newValue, feedback) => {
          setEditLoading(true);
          try {
            const response = await fetch('http://localhost:5002/api/correct_retained_earnings', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                company_symbol: companySymbol,
                field_type: fieldType,
                correct_value: newValue,
                feedback: feedback,
              }),
            });
            const data = await response.json();
            if (data.status === 'success' && data.updated) {
              if (typeof window.updateRowAfterCorrection === 'function') {
                window.updateRowAfterCorrection(data.updated);
              }
              setEditModalOpen(false);
              setEditLoading(false);
            } else {
              alert('فشل في حفظ التصحيح: ' + (data.message || ''));
              setEditLoading(false);
            }
          } catch (e) {
            alert('حدث خطأ أثناء حفظ التصحيح: ' + e.message);
            setEditModalOpen(false);
            setEditLoading(false);
          }
        }}
        loading={editLoading}
      /> */}
      
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

      {/* Bulk delete confirmation dialog */}
      <Dialog open={bulkDeleteDialogOpen} onClose={() => setBulkDeleteDialogOpen(false)}>
        <DialogTitle sx={{ fontWeight: 700, color: '#1e6641' }}>تأكيد الحذف الجماعي</DialogTitle>
        <DialogContent>
          <Typography>
            هل أنت متأكد أنك تريد حذف {selectedExports.size} ملفات محددة؟ لا يمكن التراجع عن هذه العملية.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDeleteDialogOpen(false)} sx={{ color: '#37474f' }}>إلغاء</Button>
          <Button onClick={handleBulkDelete} sx={{ color: '#b71c1c', fontWeight: 700 }}>حذف {selectedExports.size} ملفات</Button>
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
            py: 3.5,
            bgcolor: '#fff',
            borderBottom: '1.5px solid #e0e0e0',
            boxShadow: '0 2px 8px 0 rgba(30,102,65,0.04)',
            borderTopRightRadius: 16,
            borderTopLeftRadius: 16,
            minHeight: 88,
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
        <Box sx={{ height: 24 }} />
        <Box sx={{ width: '100%', height: 2, bgcolor: '#f4f6fa', mb: 3, borderRadius: 2 }} />
        {/* User-Saved Exports Section */}
        <Box sx={{ mt: 3, pb: 0, px: 0 }}>
          <Box sx={{
            display: 'flex',
            alignItems: 'center',
            bgcolor: '#e9f5ee',
            borderRadius: 4,
            px: 2.5,
            py: 1.5,
            width: '100%',
            boxSizing: 'border-box',
            mb: 2,
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
        
        {/* Selection controls */}
        {userExports.length > 0 && (
          <Box sx={{ px: 2.5, mb: 2.5 }}>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              bgcolor: '#f8f9fa',
              borderRadius: 2,
              p: 2,
              border: '1px solid #e0e0e0'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <input
                  type="checkbox"
                  checked={selectedExports.size === userExports.length}
                  onChange={(e) => handleSelectAllExports(e.target.checked)}
                  style={{ width: 18, height: 18, accentColor: '#1e6641' }}
                />
                <Typography sx={{ fontSize: 14, color: '#666', fontWeight: 500 }}>
                  تحديد الكل
                </Typography>
              </Box>
              {selectedExports.size > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  onClick={() => setBulkDeleteDialogOpen(true)}
                  sx={{ 
                    borderRadius: 2, 
                    textTransform: 'none',
                    borderColor: '#d32f2f',
                    color: '#d32f2f',
                    '&:hover': { borderColor: '#b71c1c', bgcolor: '#ffebee' }
                  }}
                >
                  حذف {selectedExports.size} ملفات محددة
                </Button>
              )}
            </Box>
          </Box>
        )}
        
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
                {/* Selection checkbox */}
                <input
                  type="checkbox"
                  checked={selectedExports.has(file.id || idx)}
                  onChange={(e) => handleExportSelection(file.id || idx, e.target.checked)}
                  style={{ 
                    width: 18, 
                    height: 18, 
                    accentColor: '#1e6641',
                    marginRight: 12
                  }}
                />
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
        <Box sx={{ mt: 4, pb: 0, px: 0 }}>
          <Box sx={{
            display: 'flex',
            alignItems: 'center',
            bgcolor: '#e9f5ee',
            borderRadius: 4,
            px: 2.5,
            py: 1.5,
            width: '100%',
            boxSizing: 'border-box',
            mb: 2,
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
              <ListItem key={idx} sx={{ 
                pl: 3, 
                pr: 3, 
                py: 2.2,
                mb: 1.5,
                bgcolor: '#fff',
                borderRadius: 2.5,
                boxShadow: '0 1px 6px 0 rgba(30,102,65,0.06)',
                display: 'flex',
                alignItems: 'center',
                minHeight: 56,
                border: 'none',
                transition: 'box-shadow 0.2s, transform 0.2s',
                '&:hover': {
                  boxShadow: '0 4px 16px 0 rgba(30,102,65,0.10)',
                  transform: 'translateY(-2px) scale(1.01)',
                },
              }}>
                <span style={{ fontSize: 22, marginRight: 12 }}>📄</span>
                <Typography sx={{ fontWeight: 500, color: '#1e6641', flexGrow: 1, fontSize: 15 }}>
                  {`${snap.year} ${snap.quarter.replace('Q', 'Q')} — ${snap.snapshot_date}`}
                </Typography>
                <Tooltip title={`تاريخ الاستخراج: ${snap.snapshot_date}`} arrow>
                  <IconButton
                    aria-label="تحميل"
                    href={`http://localhost:5002${snap.download_url}`}
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
              </ListItem>
            ))
          )}
        </List>
      </Drawer>
    </Box>
  );
}

export default App;
